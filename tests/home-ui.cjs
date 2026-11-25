const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const base=(process.env.SITE_URL||'http://127.0.0.1:8094').replace(/\/$/,'');
 const browser=await chromium.launch(process.env.CHROME_CHANNEL?{channel:process.env.CHROME_CHANNEL}:{});
 for(const width of [320,390,768,1440])for(const colorScheme of ['light','dark']){
  const page=await browser.newPage({viewport:{width,height:1000},colorScheme});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'networkidle'});
  assert.equal(await page.locator('h1').count(),1);
  assert.equal(await page.locator('.home-edition').count(),1);
  assert.equal(await page.locator('.home-story--lead').count(),1);
  assert.ok(await page.locator('#home-experiences-title').count());
  assert.equal(await page.locator('.home-story').count(),12);
  const ids=await page.locator('.home-story').evaluateAll(elements=>elements.map(e=>e.dataset.postId));
  assert.equal(new Set(ids).size,ids.length,'A post must appear only once');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow at ${width}/${colorScheme}`);
  assert.equal(await page.locator('html').getAttribute('data-theme'),colorScheme);
  for(const selector of ['.edition-intro h1','.home-story--lead','.edition-headlines','.edition-story-grid']){
   const box=await page.locator(selector).boundingBox();assert.ok(box.x>=0 && box.x+box.width<=width+1,selector);
  }
  if(width===1440){const lead=await page.locator('.home-story--lead').boundingBox();assert.ok(lead.y<500,'Actual news should reach the first viewport');}
  const next=await page.locator('.pagination a.next').getAttribute('href');assert.ok(next);
  await page.goto(next,{waitUntil:'domcontentloaded'});
  assert.equal(await page.locator('.home-edition').count(),0);
  const nextIds=await page.locator('article[data-post-id]').evaluateAll(elements=>elements.map(e=>e.dataset.postId));
  assert.ok(nextIds.length>0);assert.ok(nextIds.every(id=>!ids.includes(id)),'Preserve page boundaries');
  assert.deepEqual(errors,[]);await page.close();
 }
 const page=await browser.newPage({javaScriptEnabled:false,viewport:{width:390,height:900}});
 await page.goto(base);assert.ok(await page.locator('.home-story--lead h3 a').getAttribute('href'));assert.equal(await page.locator('form[role=search]').count(),2);
 await browser.close();console.log('Editorial homepage: responsive light/dark, complete unique feed, preserved pagination and no-JS links passed');
})().catch(error=>{console.error(error);process.exit(1)});
