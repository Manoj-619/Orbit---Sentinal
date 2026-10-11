const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs/promises');
(async()=>{
await fs.mkdir('dist/film',{recursive:true});await fs.mkdir('../film/frames',{recursive:true});
for(const name of ['three.module.js','three.core.js'])await fs.copyFile('node_modules/three/build/'+name,'dist/film/'+name);
await fs.writeFile('dist/film/index.html', '<html><body style="margin:0;background:#02060d"><script type="module" src="/film/scene.js"></script></body></html>');
await fs.copyFile('../scripts/film-scene.js','dist/film/scene.js');
const server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port','4174'],{stdio:'inherit'});let browser;
try{
for(let i=0;i<100;i++){try{if((await fetch('http://127.0.0.1:4174')).ok)break;}catch{} await new Promise(r=>setTimeout(r,200));}
browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:4174/film/index.html',{waitUntil:'networkidle'});await page.waitForFunction(()=>window.filmReady);
for(let i=0;i<576;i++){await page.evaluate(t=>window.renderFilm(t),i/12);await page.screenshot({path:'../film/frames/'+String(i).padStart(4,'0')+'.png'});if(i%48===0)console.log('3D film frame',i);}
if(errors.length)throw Error(errors.join('\n'));
}finally{await browser?.close();server.kill('SIGTERM');}
})().catch(e=>{console.error(e);process.exitCode=1;});
