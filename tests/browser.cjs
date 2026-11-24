const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const base=process.env.SITE_URL||'http://127.0.0.1:8094';
 const browser=await chromium.launch(process.env.CHROME_CHANNEL?{channel:process.env.CHROME_CHANNEL}:{});
 for(const width of [390,1440]) {
  const page=await browser.newPage({viewport:{width,height:900}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'domcontentloaded'});
  assert.equal(await page.locator('h1').count(),1);
  const bounds=await page.locator('#masthead').boundingBox();assert.ok(Math.abs(bounds.width-width)<2,`Header width ${bounds.width}/${width}`);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.equal(await page.locator('#menu-toggle').isVisible(),width<961);
  if(width<961){await page.locator('#menu-toggle').click();assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'false');assert.equal(await page.locator('#menu-toggle').evaluate(e=>e===document.activeElement),true);}
  await page.locator('#theme-toggle').click();await page.waitForTimeout(400);assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.locator('#search-toggle').click();assert.equal(await page.locator('#search-toggle').getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await page.locator('#search-toggle').getAttribute('aria-expanded'),'false');
  assert.deepEqual(errors,[]);await page.close();
 }
 await browser.close();console.log('Desktop/mobile, header, overflow, menu, focus, dark mode and search passed');
})().catch(e=>{console.error(e);process.exit(1)});
