
import * as T from './three.module.js';
const data=(await (await fetch('/demo/crossing.json')).json()).result;
const renderer=new T.WebGLRenderer({antialias:true});renderer.setSize(960,540);document.body.appendChild(renderer.domElement);
renderer.setClearColor(0x02060d);
const scene=new T.Scene(),camera=new T.PerspectiveCamera(42,960/540,.01,100);camera.up.set(0,0,1);
scene.add(new T.Mesh(new T.SphereGeometry(1,80,48),new T.ShaderMaterial({vertexShader:"varying vec3 vNormal; varying vec3 vPosition; void main(){vNormal=normalize(normalMatrix*normal);vPosition=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",fragmentShader:"varying vec3 vNormal;varying vec3 vPosition;\nfloat hash(vec3 p){p=fract(p*.3183099+vec3(.1,.2,.3));p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}\nfloat noise(vec3 x){vec3 i=floor(x),f=fract(x);f=f*f*(3.-2.*f);return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1)),f.x),f.y),f.z);}\nvoid main(){vec3 p=normalize(vPosition);float continent=noise(p*3.)*.65+noise(p*9.)*.25+noise(p*25.)*.1;float land=smoothstep(.49,.54,continent);vec3 ocean=vec3(.012,.046,.085),ground=vec3(.035,.18,.19);vec3 color=mix(ocean,ground,land);float lat=asin(p.z),lon=atan(p.y,p.x);float grid=max(pow(abs(cos(lat*18.)),85.),pow(abs(cos(lon*18.)),85.));color+=grid*vec3(.016,.07,.09);float light=.2+.8*max(dot(normalize(vNormal),normalize(vec3(-.4,.6,1.))),0.);float rim=pow(1.-abs(vNormal.z),3.);color=color*light+rim*vec3(.03,.14,.22);gl_FragColor=vec4(color,1.);}"})));
scene.add(new T.Mesh(new T.SphereGeometry(1.027,64,48),new T.MeshBasicMaterial({color:0x2cbedf,side:T.BackSide,transparent:true,opacity:.2})));
let seed=619;const rnd=()=>{seed=seed*16807%2147483647;return(seed-1)/2147483646};const points=[];
for(let i=0;i<2200;i++){let z=rnd()*2-1,a=rnd()*6.283,r=Math.sqrt(1-z*z);points.push(15*r*Math.cos(a),15*r*Math.sin(a),15*z);}
const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(points,3));scene.add(new T.Points(geo,new T.PointsMaterial({size:.016,color:0x99c8ef})));
const markers=[];
function line(path,color,opacity){const g=new T.BufferGeometry().setFromPoints(path.positions_km.map(p=>new T.Vector3(...p).multiplyScalar(1/6378.137)));const l=new T.Line(g,new T.LineBasicMaterial({color,transparent:true,opacity}));scene.add(l);return l;}
data.objects.forEach((o,i)=>{const color=[0x58e5cb,0xff715c,0x8b9cff][i];line(o,color,.65);let m=new T.Mesh(new T.SphereGeometry(.014,16,10),new T.MeshBasicMaterial({color}));scene.add(m);markers.push(m);});
const after=line(data.after_trajectory,0x58e5cb,1);
function point(path,time){let f=time/path.times_s.at(-1)*(path.times_s.length-1);let i=Math.floor(f),j=Math.min(i+1,path.times_s.length-1);return new T.Vector3(...path.positions_km[i]).lerp(new T.Vector3(...path.positions_km[j]),f-i).multiplyScalar(1/6378.137);}
window.renderFilm=t=>{
const act=Math.floor(t/8),u=(t%8)/8;const enabled=t>=24;
let az=-.7+t*.024,dist=act===0?3.8-u*.7:act===1?3.15-u*.25:act===2?3.2:act===3?2.9+u*.2:act===4?3.2:3.4+u*.8;
camera.position.set(Math.cos(az)*dist,Math.sin(az)*dist,1.15+.2*Math.sin(t*.13));camera.lookAt(0,0,.08);
const tm=act===1?500+u*400:act===3?u*2400:(t/48*2400);
markers.forEach((m,i)=>m.position.copy(point(i===0&&enabled?data.after_trajectory:data.objects[i],tm)));
after.visible=enabled;renderer.render(scene,camera);
};
window.renderFilm(0);window.filmReady=true;
