const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const base=(process.env.SITE_URL||'http://127.0.0.1:8094').replace(/\/$/,'');
 const browser=await chromium.launch(process.env.CHROME_CHANNEL?{channel:process.env.CHROME_CHANNEL}:{});
 const context=await browser.newContext({viewport:{width:390,height:900}});
 const page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{window.auditCommands=[];window._paq={push(command){window.auditCommands.push(command)}}});
 const commands=()=>page.evaluate(()=>window.auditCommands);
 const count=async(category,action)=>(await commands()).filter(x=>x[0]==='trackEvent'&&x[1]===category&&x[2]===action).length;
 await page.goto(base,{waitUntil:'domcontentloaded'});
 await page.locator('#theme-toggle').click();assert.equal(await count('Interface','theme_change'),1);
 await page.locator('#menu-toggle').click();assert.equal(await count('Navigation','open'),1);
 await page.keyboard.press('Escape');
 await page.locator('#search-toggle').click();assert.equal(await count('Search','open'),1);
 const input=page.locator('#header-search-container .search-field');
 let releaseOld;
 const oldWaiting=new Promise(resolve=>releaseOld=resolve);
 let receivedOld;
 const oldReceived=new Promise(resolve=>receivedOld=resolve);
 await page.route('**/wp-json/datogedon-reader/v1/search?*',async route=>{
  const q=new URL(route.request().url()).searchParams.get('q');
  if(q==='old'){receivedOld();await oldWaiting;}
  try{await route.fulfill({json:[{id:123,title:q==='old'?'Stale result':'Latest result',permalink:base+'/web/integracion-ia-1/',date:'2026',thumbnail:''}]})}catch(_){/* aborted request */}
 });
 await input.fill('old');await oldReceived;
 await input.fill('new');
 await page.locator('#header-search-container .autocomplete-item').waitFor();
 assert.equal(await input.getAttribute('aria-expanded'),'true');
 await page.keyboard.press('ArrowDown');
 assert.ok(await input.getAttribute('aria-activedescendant'));
 releaseOld();await page.waitForTimeout(150);
 assert.equal(await page.locator('#header-search-container .autocomplete-title').innerText(),'Latest result');
 // Exercise selection without leaving the page; preserve its emitted event for inspection.
 await page.evaluate(()=>document.querySelector('.autocomplete-item').addEventListener('click',e=>e.preventDefault()));
 await page.keyboard.press('Enter');assert.equal(await count('Search','autocomplete_select'),1);
 await page.keyboard.press('Escape');assert.equal(await input.getAttribute('aria-expanded'),'false');
 assert.equal(await input.getAttribute('aria-activedescendant'),null);
 await page.keyboard.press('Escape');
 const hero=page.locator('.home-hero .search-form');
 await hero.locator('input').fill('private-query@example.invalid');
 await hero.evaluate(form=>form.addEventListener('submit',e=>e.preventDefault()));
 await hero.locator('button').click();assert.equal(await count('Search','submit'),1);
 assert.ok(!JSON.stringify(await commands()).includes('private-query'));
 await page.locator('.hero-links a').first().evaluate(a=>a.addEventListener('click',e=>e.preventDefault()));
 await page.locator('.hero-links a').first().click();assert.equal(await count('Navigation','section_open'),1);
 const card=page.locator('.featured-post-card h2 a').first();const articleUrl=await card.getAttribute('href');
 await card.evaluate(a=>a.addEventListener('click',e=>e.preventDefault()));await card.click();assert.equal(await count('Navigation','article_open'),1);
 const collab=page.locator('#main-nav a[href$="/colabora/"]').first();
 await collab.evaluate(a=>a.addEventListener('click',e=>e.preventDefault()));await page.locator('#menu-toggle').click();await collab.click();
 assert.equal(await count('Collaboration','open'),1);
 assert.ok((await commands()).every(x=>x[0]==='trackEvent'),'Must not initialize Matomo or duplicate pageviews/searches');
 await page.unroute('**/wp-json/datogedon-reader/v1/search?*');
 await page.clock.install();
 await page.goto(articleUrl,{waitUntil:'domcontentloaded'});await page.bringToFront();
 const body=page.locator('article .post-content');
 // Long synthetic content makes article-based progress measurable independently of the footer.
 await body.evaluate(el=>{el.style.minHeight='4200px'});
 async function scrollTo(percent){await body.evaluate((el,p)=>{const top=el.getBoundingClientRect().top+scrollY;scrollTo({top:top+el.getBoundingClientRect().height*p-innerHeight,behavior:'instant'})},percent);await page.evaluate(()=>dispatchEvent(new Event('scroll')));await page.clock.runFor(50)}
 await scrollTo(.55);assert.equal(await count('Reading','progress_50'),0);
 await page.clock.runFor(11000);assert.equal(await count('Reading','progress_50'),1);assert.equal(await count('Reading','progress_90'),0);
 // Emulate browser visibility/focus transitions deterministically under the virtual clock.
 // Headless Chromium does not consistently unfocus a page when opening another tab.
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))});
 await page.clock.runFor(60000);
 await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))});
 await page.evaluate(()=>{window.auditNativeFocus=document.hasFocus;document.hasFocus=()=>false;dispatchEvent(new Event('blur'))});
 await page.clock.runFor(60000);
 await page.evaluate(()=>{document.hasFocus=window.auditNativeFocus;delete window.auditNativeFocus;dispatchEvent(new Event('focus'))});
 await scrollTo(.95);
 assert.equal(await count('Reading','progress_90'),0);
 await page.clock.runFor(21000);assert.equal(await count('Reading','progress_90'),1);
 await scrollTo(.5);await scrollTo(.95);await page.clock.runFor(1000);
 assert.equal(await count('Reading','progress_50'),1);assert.equal(await count('Reading','progress_90'),1);
 const related=page.locator('.related-posts a').first();await related.evaluate(a=>a.addEventListener('click',e=>e.preventDefault()));await related.click();assert.equal(await count('Navigation','related_open'),1);
 await page.goto(base+'/?s=integracion',{waitUntil:'domcontentloaded'});assert.equal(await count('Search','results'),1);
 await page.goto(base+'/colabora/',{waitUntil:'domcontentloaded'});
 const contact=page.locator('.post-content a[href$="/contacto/"]').first();await contact.evaluate(a=>a.addEventListener('click',e=>e.preventDefault()));await contact.click();assert.equal(await count('Collaboration','contact_open'),1);
 assert.deepEqual(errors,[]);
 await browser.close();console.log('Analytics: controls, private labels, autocomplete races, navigation, foreground reading milestones, deduplication and collaboration passed');
})().catch(e=>{console.error(e);process.exit(1)});
