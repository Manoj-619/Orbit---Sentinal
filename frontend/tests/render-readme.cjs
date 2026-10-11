const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { mkdir } = require('node:fs/promises');
const assert = require('node:assert/strict');

(async () => {
  const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4174'], { stdio: 'inherit' });
  let browser;
  try {
    for (let i = 0; i < 100; i++) {
      try { if ((await fetch('http://127.0.0.1:4174')).ok) break; } catch {}
      await new Promise(resolve => setTimeout(resolve, 200));
      if (i === 99) throw new Error('Preview failed');
    }
    browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
    const page = await browser.newPage({viewport:{width:1440,height:560},deviceScaleFactor:1});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {if (message.type()==='error' && message.text().includes('THREE.WebGL')) errors.push(message.text());});
    await page.goto('http://127.0.0.1:4174',{waitUntil:'networkidle'});
    await page.getByText('Verified candidate. Your decision.').waitFor();
    await page.locator('.orbit-render canvas').waitFor();
    assert.ok(await page.locator('.orbit-render canvas').evaluate(canvas=>!!canvas.getContext('webgl2')));
    await page.addStyleTag({content:[
      'html,body{margin:0;width:1440px;height:560px;overflow:hidden;background:#040912;}',
      '.app{display:block;width:1440px;height:560px;max-width:none;margin:0;}',
      '.topbar,.sidebar{display:none!important;} main{position:absolute;inset:0;padding:0!important;}',
      'main>*{display:none!important;} main>.visual-row{display:block!important;position:absolute;inset:0;}',
      '.orbit-panel{position:absolute;right:0;top:0;width:780px;height:560px!important;border:0;background:transparent;overflow:visible;}',
      '.orbit-render{inset:-80px -160px -80px -160px!important;}',
      '.encounter-panel,.panel-heading,.scene-label,.scene-time,.legend,.view-toggle,.timeline{display:none!important;}',
      '#hero-copy{position:fixed;inset:0;z-index:5;pointer-events:none;background:linear-gradient(90deg,#040912 0%,#040912 35%,transparent 72%);color:#e2edf4;font-family:Arial,sans-serif;}',
      '#hero-copy .kicker{position:absolute;left:72px;top:56px;color:#58e5cb;font:11px monospace;letter-spacing:4px;}',
      '#hero-copy h1{position:absolute;left:65px;top:115px;margin:0;font-size:94px;line-height:.98;letter-spacing:-4px;text-shadow:0 2px #163649,0 5px #102e42,0 12px 40px #25bddb20;}',
      '#hero-copy h1 span{font-weight:300;color:#bfd7e7;}',
      '#hero-copy .tagline{position:absolute;left:72px;top:338px;font-size:23px;font-weight:300;color:#91b1c8;}',
      '#hero-copy .rule{position:absolute;left:72px;top:396px;width:500px;height:1px;background:linear-gradient(90deg,#58e5cb,transparent);}',
      '#hero-copy .roles{position:absolute;left:72px;top:422px;font:10px monospace;color:#a8c6d6;letter-spacing:1px;}',
      '#hero-copy .scope{position:absolute;left:72px;bottom:33px;font:8px monospace;letter-spacing:1.5px;color:#557e95;}',
      '#phase{position:absolute;right:50px;bottom:38px;color:#58e5cb;font:9px monospace;letter-spacing:1.3px;}',
      '#hero-copy .corner{position:absolute;right:50px;top:53px;width:8px;height:8px;border:1px solid #58e5cb;}'
    ].join('')});
    await page.evaluate(()=>{
      const hero=document.createElement('div');hero.id='hero-copy';
      hero.innerHTML='<div class="kicker">CONJUNCTION INTELLIGENCE / V0.1</div><h1>ORBIT<br/><span>SENTINAL</span></h1><div class="tagline">Evidence before every burn.</div><div class="rule"></div><div class="roles">TRACK → CHALLENGE → PLAN → VERIFY → DECIDE</div><div class="scope">SYNTHETIC TRAJECTORIES · TWO-BODY PHYSICS · HUMAN AUTHORITY</div><div id="phase">BASELINE / RECORDED SIMULATION</div><div class="corner"></div>';
      document.body.appendChild(hero);
    });
    await mkdir('../docs/assets/frames',{recursive:true});
    await page.waitForTimeout(500);
    await page.screenshot({path:'../docs/assets/hero-3d.png'});
    for(let i=0;i<60;i++){
      const after=i>=30;
      if(i===30)await page.evaluate(()=>document.querySelectorAll('.view-toggle button')[1].click());
      await page.evaluate(({time,after})=>{
        const input=document.querySelector('.timeline input');
        const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
        setter.call(input,String(time));input.dispatchEvent(new Event('input',{bubbles:true}));
        document.querySelector('#phase').textContent=after?'VERIFIED MANEUVER / PREVIEW':'BASELINE / RECORDED SIMULATION';
      },{time:(i%30)/29*2400,after});
      await page.waitForTimeout(90);
      await page.screenshot({path:'../docs/assets/frames/'+String(i).padStart(3,'0')+'.png'});
    }
    assert.deepEqual(errors,[]);
    console.log('Rendered original WebGL2 mission imagery from recorded numerical trajectories.');
  }finally{await browser?.close();server.kill('SIGTERM');}
})().catch(error=>{console.error(error);process.exitCode=1;});
