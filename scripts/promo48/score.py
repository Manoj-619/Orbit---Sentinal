import numpy as np,wave
from pathlib import Path
sr=48000;t=np.arange(sr*48)/sr;audio=np.zeros_like(t);rng=np.random.default_rng(619)
for hz in [55,82.4069,110,130.8128]:audio+=.025*np.sin(2*np.pi*hz*t)*(.65+.35*np.sin(2*np.pi*.125*t))
for start in np.arange(0,47.5,.5):
 n=int(sr*.45);tt=np.arange(n)/sr;i=int(start*sr);hz=[220,261.6256,329.6276,391.9954,329.6276,261.6256,440,329.6276][int(start*2)%8]
 audio[i:i+n]+=.07*(np.sin(2*np.pi*hz*tt)+.2*np.sin(4*np.pi*hz*tt))*np.exp(-tt*8)*np.minimum(1,tt*200)
 if start>=5:audio[i:i+n]+=.16*np.sin(2*np.pi*(46*tt+10*(1-np.exp(-tt*25))))*np.exp(-tt*13)
for start in [0,5,12,22,32,40]:
 n=sr*2;tt=np.arange(n)/sr;i=start*sr;noise=np.convolve(rng.normal(0,1,n),np.ones(12)/12,mode='same');audio[i:i+n]+=.18*noise*np.exp(-tt*3)+.2*np.sin(2*np.pi*37*tt)*np.exp(-tt*2)
for end in [5,12,22,32,40]:
 n=sr*2;tt=np.arange(n)/sr;i=(end-2)*sr;noise=np.convolve(rng.normal(0,1,n),np.ones(8)/8,mode='same');audio[i:i+n]+=.12*noise*(tt/2)**2
audio=np.tanh(audio*1.7)*.7*np.minimum(t/1.5,1)*np.minimum((48-t)/2,1);stereo=np.stack([audio,np.roll(audio,350)*.94],axis=1)
with wave.open(str(Path(__file__).with_name('score.wav')),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((stereo*32767).astype('<i2').tobytes())
