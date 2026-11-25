const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const base=(process.env.SITE_URL||'http://127.0.0.1:8094').replace(/\/$/,'');
 const browser=await chromium.launch(process.env.CHROME_CHANNEL?{channel:process.env.CHROME_CHANNEL}:{});
 const url=base+'/web/toc-fixture/';
 for(const width of [390,1440])for(const javaScriptEnabled of [true,false]) {
  const context=await browser.newContext({viewport:{width,height:900},javaScriptEnabled,reducedMotion:'reduce'});
  const page=await context.newPage();page.setDefaultTimeout(10000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url,{waitUntil:'domcontentloaded'});
  assert.equal(await page.locator('.article-toc').count(),1);
  assert.equal(await page.locator('.article-toc a').count(),6);
  assert.equal(await page.locator('#toc_container').count(),0);
  assert.equal(await page.locator('script[src*="table-of-contents-plus"],link[href*="table-of-contents-plus"]').count(),0);
  const summary=page.locator('.article-toc summary');await summary.focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('.article-toc').getAttribute('open'),'');
  const links=await page.locator('.article-toc a').evaluateAll(nodes=>nodes.map(n=>n.hash));
  assert.equal(await page.locator('.article-toc nav>ol>li>ol').count(),1);
  for(const hash of links)assert.ok(await page.evaluate(h=>!!document.getElementById(decodeURIComponent(h.slice(1))),hash));
  await page.locator('.article-toc a[href="#manual"]').focus();await page.keyboard.press('Enter');
  await page.waitForURL('**/#manual');
  assert.equal(await page.locator('#manual').evaluate(n=>n===document.activeElement),true);
  const y=await page.locator('#manual').evaluate(n=>n.getBoundingClientRect().top);
  const headerBottom=await page.locator('#masthead').evaluate(n=>n.getBoundingClientRect().bottom);
  assert.ok(y>=headerBottom&&y<headerBottom+100,`Heading hidden/offset: ${y}/${headerBottom}`);
  await page.goto(url+'#Como_empezar',{waitUntil:'domcontentloaded'});
  assert.equal(await page.locator('#Como_empezar').count(),1);
  const aliasY=await page.locator('#Como_empezar').evaluate(n=>n.getBoundingClientRect().top);
  assert.ok(aliasY>=headerBottom&&aliasY<headerBottom+100,`Legacy fragment hidden: ${aliasY}`);
  if(javaScriptEnabled){await page.locator('#theme-toggle').click();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');}
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Horizontal overflow');
  if(width===390&&javaScriptEnabled){if(await page.locator('.article-toc').getAttribute('open')===null)await page.locator('.article-toc summary').click();await page.locator('.article-toc').screenshot({path:'/tmp/datogedon-toc-mobile.png'});}
  assert.deepEqual(errors,[]);await context.close();
 }
 const page=await browser.newPage();
 for(const slug of ['toc-short-fixture','toc-disabled-fixture']){
  await page.goto(base+'/web/'+slug+'/',{waitUntil:'domcontentloaded'});assert.equal(await page.locator('.article-toc').count(),0);
 }
 await page.goto(base+'/web/toc-forced-fixture/',{waitUntil:'domcontentloaded'});
 assert.equal(await page.locator('.article-toc').count(),1);assert.match(await page.locator('.article-toc summary').innerText(),/Secciones/);
 const rest=await page.request.get(base+'/wp-json/wp/v2/posts?slug=toc-fixture');
 assert.equal(rest.status(),200);assert.ok(!JSON.stringify(await rest.json()).includes('data-datogedon-toc'));
 await browser.close();console.log('TOC: mobile/desktop, keyboard, no-JS, nesting, targets, legacy fragments, header offset, dark mode, REST and short/explicit articles passed');
})().catch(e=>{console.error(e);process.exit(1)});
