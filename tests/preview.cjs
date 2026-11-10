/* Exercises the exported file without a backend and rejects accidental API traffic. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {resolve}=require('node:path');
const {readFileSync}=require('node:fs');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,args:['--no-sandbox','--enable-unsafe-swiftshader']});
 try{
  const p=await b.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});const errors=[],requests=[];
  p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(r.url().includes('/api/'))requests.push(r.url())});
  // Test truly standalone: fonts and images may fall back, no remote dependency needed.
  await p.route(/^https?:/,r=>r.request().url()==='https://nvtra-preview.test/'?r.fulfill({contentType:'text/html',body:readFileSync(resolve(process.env.NVTRA_PREVIEW_FILE||resolve(__dirname,'../preview.html')),'utf8')}):r.abort());
  await p.goto('https://nvtra-preview.test/');await p.locator('.preview-notice').waitFor();
  await p.evaluate(()=>go('pricing'));await p.locator('#estimate-form').waitFor();await p.locator('#estimate-form [name=pages]').fill('8');assert.match(await p.locator('#estimate-live').innerText(),/2[\s,]?400/);
  const estimate=p.waitForEvent('download');await p.locator('#estimate-save').click();assert.equal((await estimate).suggestedFilename(),'nvtra-direction.json');
  await p.locator('#estimate-send').click();const form=p.locator('#project-form');await form.locator('[name=name]').fill('Preview visitor');await form.locator('[name=email]').fill('preview@example.test');await form.locator('[name=message]').fill('Please discuss my website.');await form.locator('[name=consent]').check();await form.getByRole('button',{name:'Prepare enquiry email'}).click();
  assert.match(await form.locator('.form-status').innerText(),/has not been sent or stored/);assert.match(await form.locator('.form-status a').getAttribute('href'),/^mailto:nvtra\.official@icloud\.com\?/);
  const enquiry=p.waitForEvent('download');await p.locator('[data-download-enquiry]').click();assert.equal((await enquiry).suggestedFilename(),'nvtra-enquiry.json');
  await p.evaluate(()=>go('lab'));await p.locator('[data-step="2"]').click();await p.locator('#brief-form [name=radius]').selectOption('round');assert.equal(await p.locator('.brief-preview').getAttribute('data-radius'),'round');
  await p.getByRole('button',{name:'Search NVTRA',exact:true}).click();await p.locator('#site-search').fill('maintenance');await p.locator('.search-result').first().waitFor();await p.keyboard.press('Escape');
  await p.getByRole('button',{name:'Open studio support'}).click();await p.locator('#assistant-message').fill('Do you offer maintenance?');await p.locator('#assistant-form button').click();assert.match(await p.locator('#assistant-mode').innerText(),/not live AI/);assert.match(await p.locator('#support-answer').innerText(),/R99/);await p.keyboard.press('Escape');
  await p.evaluate(()=>go('login'));assert(await p.locator('#auth-form [name=password]').isDisabled());assert.match(await p.locator('#auth-status').innerText(),/Design preview/);
  await p.evaluate(()=>go('dashboard'));assert.match(await p.locator('#dashboard-content').innerText(),/No account or record was created/);
  await p.evaluate(()=>go('tools'));await p.locator('#comparison-slider').fill('72');assert.equal(await p.locator('.comparison-stage').evaluate(e=>e.style.getPropertyValue('--split')),'28%');await p.locator('#health-url').fill('https://example.com');await p.locator('#health-form button').click();assert.match(await p.locator('#health-results a').getAttribute('href'),/^https:\/\/pagespeed.web.dev/);assert.equal(await p.locator('.score-grid').count(),0);
  await p.setViewportSize({width:390,height:844});
  for(const route of ['home','lab','pricing','tools','login']){await p.evaluate(id=>go(id),route);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Overflow '+route)}
  await p.evaluate(()=>go('home'));await p.waitForTimeout(1600);await p.screenshot({path:'/tmp/nvtra-preview-mobile.png'});
  await p.setViewportSize({width:1440,height:1000});await p.waitForTimeout(1000);await p.screenshot({path:'/tmp/nvtra-preview-desktop.png'});
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);console.log('PASS: standalone offline preview, estimator, brief download, explicit unsent email composer, live design controls, search, local FAQ, disabled authentication, external real audit, mobile layouts; zero backend requests.');
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
