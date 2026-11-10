/* Read-only browser checks for the spatial design. No production records are created. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {mkdirSync}=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,args:['--no-sandbox','--enable-unsafe-swiftshader']});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const origin=process.env.NVTRA_URL||'http://127.0.0.1:8080';
 await page.goto(origin);await page.waitForTimeout(1800);
 assert.equal(await page.locator('#hero-canvas').getAttribute('data-renderer'),'webgl');
 await page.locator('#home-exhibition').evaluate(el=>scrollTo({top:scrollY+el.getBoundingClientRect().top,behavior:'instant'}));
 await page.locator('[data-exhibit-index="2"]').click();await page.waitForTimeout(1200);
 assert.equal(await page.locator('[data-exhibit-index="2"]').getAttribute('aria-pressed'),'true');
 await page.locator('.exhibit-frame[data-study=orbit]').click();await page.locator('#study-dialog[open]').waitFor();await page.waitForTimeout(800);
 await page.locator('[data-region=forms]').click();assert.match(await page.locator('.explorer-description').innerText(),/server-side checks/);
 await page.keyboard.press('Escape');assert.equal(await page.locator('#study-dialog').isVisible(),false);
 await page.locator('[data-process-index="4"]').click();await page.waitForTimeout(1300);assert.match(await page.locator('#process-index').innerText(),/LAUNCH/);
 await page.evaluate(()=>go('lab'));await page.locator('[data-step="2"]').click();
 const choices={layout:'grid',radius:'round',depth:'flat',background:'aurora',navigation:'minimal',cards:'solid',composition:'centered'};
 for(const [key,value] of Object.entries(choices)){await page.locator(`#brief-form [name=${key}]`).selectOption(value);assert.equal(await page.locator('.brief-preview').getAttribute('data-'+key),value);}
 await page.reload();await page.locator('#brief-form').waitFor();for(const [key,value] of Object.entries(choices))assert.equal(await page.locator(`#brief-form [name=${key}]`).inputValue(),value);
 await page.evaluate(()=>go('pricing'));await page.locator('#estimate-form input[value=spatial]').check();assert.match(await page.locator('#estimate-live').innerText(),/3D \/ spatial experience/);
 await page.locator('#package-comparison details').last().locator('summary').click();await page.locator('[data-choose-package=deluxe]').click();assert.equal(await page.locator('#estimate-form [name=pages]').inputValue(),'6');
 mkdirSync('/tmp/nvtra-design-preview',{recursive:true});
 for(const width of [768,390]){
  await page.setViewportSize({width,height:width===390?844:1024});
  for(const route of ['home','lab','pricing','portfolio']){await page.evaluate(id=>go(id),route);await page.waitForTimeout(150);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Overflow ${width} ${route}`);}
 }
 await page.evaluate(()=>go('lab'));await page.locator('.brief-controls .brief-preview-jump').click();await page.waitForTimeout(800);assert(await page.locator('#page-lab').isVisible());assert.equal(await page.evaluate(()=>document.activeElement.id),'brief-live-preview');
 await page.evaluate(()=>go('home'));await page.waitForTimeout(1600);await page.screenshot({path:'/tmp/nvtra-design-preview/home-mobile.png'});
 await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:1440,height:1000});
 assert.equal(await page.locator('.hero').evaluate(e=>getComputedStyle(e).position),'relative');
 await page.locator('[data-process-index="1"]').click();assert.match(await page.locator('#process-index').innerText(),/CONCEPT/);
 await page.evaluate(()=>go('portfolio'));
 for(const id of ['corner','forma','orbit']){await page.locator(`#page-portfolio [data-study=${id}]`).click();await page.locator('#study-dialog[open]').waitFor();assert.match(await page.locator('.study-facts').innerText(),/No client outcome/);await page.keyboard.press('Escape');}
 const fallback=await browser.newPage();await fallback.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'?null:original.call(this,type,...args)};});await fallback.goto(origin);await fallback.waitForTimeout(700);assert.equal(await fallback.locator('#hero-canvas').getAttribute('data-renderer'),'fallback');assert(await fallback.locator('.hero .sculpture-fallback').isVisible());await fallback.close();
 assert.deepEqual(errors,[]);console.log('PASS: WebGL and fallback, exhibition navigation, study regions, process stages, seven live brief settings and persistence, scoped 3D pricing, package controls, tablet/mobile, preview jump, reduced motion, keyboard dialog close.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
