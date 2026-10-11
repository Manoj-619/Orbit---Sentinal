"""Render a reproducible launch film; all displayed measurements come from the recorded synthetic mission."""
import json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DURATION=1920,1080,24,48
OUT=Path("film");OUT.mkdir(exist_ok=True)
record=json.loads(Path("frontend/public/demo/crossing.json").read_text())
r=record["result"];b=r["baseline"][0];a=r["after"][0];m=r["maneuver"]
assert r["source"].startswith("synthetic") and record["events"][-1]["payload"]["simulation_only"]
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
fonts={}
def font(n,bold=False,mono=False):
    key=(n,bold,mono)
    if key not in fonts:fonts[key]=ImageFont.truetype(MONO if mono else BOLD if bold else FONT,n)
    return fonts[key]
TEAL=(88,229,203);WHITE=(233,245,255);MUTED=(131,164,191);RED=(255,115,99)
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
# Original score: minor synth ostinato, sub pulses, impacts and noise risers.
sr=48000;t=np.arange(sr*DURATION)/sr;audio=np.zeros_like(t)
for hz in [55,82.4069,110,130.8128]:
    audio+=.035*np.sin(2*np.pi*hz*t)*(0.65+0.35*np.sin(2*np.pi*.125*t))
rng=np.random.default_rng(619)
for start in np.arange(0,47.5,.5):
    n=int(sr*.45);tt=np.arange(n)/sr;idx=int(start*sr)
    hz=[220,261.6256,329.6276,391.9954,329.6276,261.6256,440,329.6276][int(start*2)%8]
    audio[idx:idx+n]+=.085*(np.sin(2*np.pi*hz*tt)+.22*np.sin(4*np.pi*hz*tt))*np.exp(-tt*8)*np.minimum(1,tt*200)
    if start>=8:
        audio[idx:idx+n]+=.19*np.sin(2*np.pi*(46*tt+10*(1-np.exp(-tt*25))))*np.exp(-tt*13)
for start in [0,8,16,24,32,40]:
    n=sr*2;tt=np.arange(n)/sr;idx=start*sr
    noise=rng.normal(0,1,n);noise=np.convolve(noise,np.ones(12)/12,mode="same")
    audio[idx:idx+n]+=.18*noise*np.exp(-tt*3)+.16*np.sin(2*np.pi*37*tt)*np.exp(-tt*2)
for end in [8,16,24,32,40]:
    n=sr*2;tt=np.arange(n)/sr;idx=(end-2)*sr
    noise=rng.normal(0,1,n);noise=np.convolve(noise,np.ones(8)/8,mode="same")
    audio[idx:idx+n]+=.14*noise*(tt/2)**2
audio=np.tanh(audio*1.7)*.72*np.minimum(t/2,1)*np.minimum((48-t)/2,1)
stereo=np.stack((audio,np.roll(audio,360)*.94),axis=1)
with wave.open(str(OUT/"score.wav"),"wb") as wav:
    wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(sr);wav.writeframes((stereo*32767).astype("<i2").tobytes())
cmd=["ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",str(OUT/"score.wav"),"-c:v","libx264","-preset","fast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",str(OUT/"Orbit_Sentinal_Launch_Film.mp4")]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
cache={}
gradient=np.zeros((H,W,4),dtype=np.uint8)
gradient[:,:,:3]=[2,6,13]
gradient[:,:,3]=np.tile(np.clip(242-np.arange(W)*.096,50,242).astype(np.uint8),(H,1))
shade=Image.fromarray(gradient,"RGBA")
def bg(i):
    i=min(i,575)
    if i not in cache:
        cache[i]=Image.open(OUT/"frames"/f"{i:04d}.png").convert("RGB").resize((W,H),Image.Resampling.LANCZOS)
        for k in list(cache):
            if k<i-2:del cache[k]
    return cache[i]
for frame in range(FPS*DURATION):
    sec=frame/FPS;act=min(5,int(sec/8));u=sec%8
    im=Image.blend(bg(frame//2),bg(frame//2+1),.5 if frame%2 else 0).convert("RGBA")
    im=Image.alpha_composite(im,shade)
    layer=Image.new("RGBA",(W,H));d=ImageDraw.Draw(layer)
    opacity=int(255*min(smooth(u/.75),smooth((8-u)/.55)))
    def txt(x,y,s,n=32,color=WHITE,bold=False,mono=False):
        d.text((x,y),s,font=font(n,bold,mono),fill=(*color,opacity))
    def rule(x,y,length,color=TEAL):d.line((x,y,x+length,y),fill=(*color,opacity),width=2)
    x=118+int(45*(1-smooth(u/1.2)))
    txt(x,140,["ORBITAL INTELLIGENCE","01 / CONJUNCTION DETECTED","02 / COORDINATED REASONING","03 / MANEUVER CANDIDATE","04 / INDEPENDENT CHECKS","05 / HUMAN AUTHORITY"][act],24,TEAL,mono=True)
    if act==0:
        txt(x,225,"ORBIT",132,bold=True);txt(x,365,"SENTINAL",132,bold=True)
        rule(x,555,640);txt(x,600,"Evidence before every burn.",42)
        txt(x,682,"Agent workflows. Orbital mathematics.",28,MUTED)
        txt(x,730,"One decision that must be earned.",28,MUTED)
    elif act==1:
        txt(x,230,"SPACE DOESN'T",74,bold=True);txt(x,320,"WAIT FOR CERTAINTY.",65,bold=True)
        p=smooth(u/2)
        txt(x,460,f"{b['miss_distance_m']*p:05.2f} m",95,RED,bold=True)
        txt(x,575,"PREDICTED CLOSEST APPROACH",24,MUTED,mono=True)
        txt(x,655,f"Nominal collision probability  {b['probability']:.2e}",27)
        txt(x,707,f"Relative speed  {b['relative_speed_kms']:.2f} km/s",27)
        txt(x,770,"DEBRIS-17  /  SYNTHETIC ENCOUNTER",23,RED,mono=True)
        # Animated covariance ellipsoid: geometric illustration only.
        cx,cy=1450,550
        for rad in [120,190,260]:
            d.ellipse((cx-rad,cy-rad*.46,cx+rad,cy+rad*.46),outline=(*RED,int(opacity*.55)),width=2)
        sweep=sec*1.8
        d.line((cx,cy,cx+260*math.cos(sweep),cy+120*math.sin(sweep)),fill=(*RED,opacity),width=2)
        txt(1250,860,"UNCERTAINTY / SCHEMATIC",21,MUTED,mono=True)
    elif act==2:
        txt(x,235,"FOUR ROLES.",86,bold=True);txt(x,337,"ONE EVIDENCE CHAIN.",65,bold=True)
        roles=[("TRACKER","Propagate and screen trajectories"),("RISK ANALYST","Challenge covariance assumptions"),("MANEUVER PLANNER","Search bounded burn candidates"),("VERIFIER","Recompute with independent tools")]
        for k,(name,desc) in enumerate(roles):
            y=465+k*98
            active=u>=k*.9+.5
            color=TEAL if active else MUTED
            d.rectangle((x,y,x+7,y+65),fill=(*color,opacity))
            txt(x+30,y,name,29,color,bold=True);txt(x+30,y+40,desc,23,MUTED)
        txt(1200,795,"OPTIONAL GEMINI POLICY",24,TEAL,mono=True)
        txt(1200,838,"Numerical tools produce the evidence.",22,MUTED)
        txt(1200,875,"This replay uses deterministic roles.",22,MUTED)
    elif act==3:
        txt(x,235,"A SMALL IMPULSE.",77,bold=True);txt(x,340,"A DIFFERENT FUTURE.",68,bold=True)
        txt(x,475,f"{m['delta_v_ms']:.3f} m/s",95,TEAL,bold=True)
        txt(x,596,"SELECTED SIMULATED DELTA-V",24,MUTED,mono=True)
        rule(x,654,650)
        txt(x,705,f"{b['miss_distance_m']:.1f} m  →  {a['miss_distance_m']:.1f} m",58,bold=True)
        txt(x,790,"Predicted miss distance / DEBRIS-17",26,MUTED)
        # Actual finite-search candidate scatter, logarithmic risk axis.
        gx,gy,gw,gh=1160,310,620,390
        d.rectangle((gx,gy,gx+gw,gy+gh),outline=(45,75,94,opacity),width=2)
        limit=gy+gh*(4/10);d.line((gx,limit,gx+gw,limit),fill=(*TEAL,opacity),width=2)
        rows=r["candidate_search"][:max(1,int(smooth(u/5)*len(r["candidate_search"])))]
        for row in rows:
            px=gx+row["delta_v_ms"]*gw;py=gy+min(10,max(0,-math.log10(max(row["worst_probability"],1e-10))))/10*gh
            color=TEAL if row["feasible"] else RED
            d.ellipse((px-3,py-3,px+3,py+3),fill=(*color,opacity))
        txt(gx,gy-45,"RECORDED CANDIDATE SEARCH",22,TEAL,mono=True)
        txt(gx,gy+gh+22,"DELTA-V 0–1 m/s  /  LOG RISK ↓",20,MUTED,mono=True)
        txt(gx,gy+gh+66,"Acceptance threshold: 1.0e-4",22,MUTED)
    elif act==4:
        txt(x,230,"TRUST THE CHECKS.",77,bold=True)
        txt(x,345,"NOT THE CONFIDENCE.",62,bold=True)
        checks=[("RK4 × DOP853","Independent trajectory integration"),("COVARIANCE STRESS","0.5× / 1× / 2× sigma perturbations"),("100,000 SAMPLES","Monte Carlo diagnostic")]
        for k,(title,desc) in enumerate(checks):
            yy=470+k*110
            txt(x,yy,title,32,TEAL,bold=True);txt(x,yy+45,desc,24,MUTED)
            if u>k*.7+.5:txt(x+790,yy,"✓",40,TEAL,bold=True)
        txt(1220,335,"POST-MANEUVER RISK",25,TEAL,mono=True)
        txt(1220,420,f"{a['probability']:.2e}",65,bold=True)
        txt(1220,505,"Nominal probability",26,MUTED)
        txt(1220,585,f"{a['worst_stress_probability']:.2e}",65,bold=True)
        txt(1220,670,"Worst sigma-stress probability",24,MUTED)
        txt(x,854,"Zero Monte Carlo hits does not mean zero risk.",24,MUTED)
    else:
        txt(x,235,"AI CAN PROPOSE.",82,bold=True)
        txt(x,347,"HUMANS DECIDE.",82,TEAL,bold=True)
        txt(x,520,"ORBIT SENTINAL",55,bold=True)
        txt(x,605,"An agentic orbital-safety research prototype.",30,MUTED)
        txt(x,697,"BUILD THE NEXT ORBIT WITH ME.",29,TEAL,bold=True)
        txt(x,757,"Open to AI, space and simulation collaborators.",25)
        txt(x,829,"github.com/Manoj-619/Orbit---Sentinal",24,MUTED,mono=True)
    # Persistent HUD and cinematic framing.
    d.rectangle((0,0,W,63),fill=(2,6,13,245));d.rectangle((0,H-65,W,H),fill=(2,6,13,245))
    d.text((118,22),"OS / MISSION INTELLIGENCE",font=font(20,mono=True),fill=(*TEAL,230))
    d.text((1310,22),"SYNTHETIC MISSION / SIMULATION",font=font(20,mono=True),fill=(*MUTED,255))
    d.text((118,H-44),"TWO-BODY PHYSICS  ·  RESEARCH PROTOTYPE",font=font(18,mono=True),fill=(*MUTED,220))
    d.text((1690,H-44),f"00:{int(sec):02d} / 00:48",font=font(18,mono=True),fill=(*TEAL,255))
    d.line((118,H-76,118+int(1684*sec/48),H-76),fill=(*TEAL,220),width=2)
    im=Image.alpha_composite(im,layer).convert("RGB")
    # Brief radial bloom at scene boundaries; ending holds then fades.
    pulse=math.exp(-u*14)*.10 if act else 0
    if pulse:im=Image.blend(im,Image.new("RGB",(W,H),(100,190,220)),pulse)
    fade=min(1,sec/.7,(48-sec)/.7)
    if fade<1:im=Image.blend(Image.new("RGB",(W,H)),im,max(0,fade))
    if frame in [96,288,480,672,864,1056]:im.save(OUT/f"poster-{act}.jpg",quality=92)
    proc.stdin.write(im.tobytes())
    if frame%192==0:print("Composited frame",frame,flush=True)
proc.stdin.close()
if proc.wait()!=0:raise RuntimeError("Video encoding failed")
probe=json.loads(subprocess.check_output(["ffprobe","-v","quiet","-show_streams","-show_format","-of","json",str(OUT/"Orbit_Sentinal_Launch_Film.mp4")]))
video=next(s for s in probe["streams"] if s["codec_type"]=="video")
assert (video["width"],video["height"],video["codec_name"],video["pix_fmt"])==(1920,1080,"h264","yuv420p")
assert float(probe["format"]["duration"])>=47.9 and any(s["codec_type"]=="audio" for s in probe["streams"])
(OUT/"export-report.json").write_text(json.dumps(probe,indent=2))
print("Validated 48-second 1080p H.264/AAC film.",flush=True)
