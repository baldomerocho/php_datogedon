const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const base=process.env.SITE_URL||'http://127.0.0.1:8094';
 const target=process.env.COMMENTS_URL||base+'/web/integracion-ia-1/';
 const browser=await chromium.launch(process.env.CHROME_CHANNEL?{channel:process.env.CHROME_CHANNEL}:{});
 for(const width of [320,390,1440]){
  const page=await browser.newPage({viewport:{width,height:950},reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(target,{waitUntil:'domcontentloaded'});
  const comments=page.locator('#comments');await comments.waitFor();
  assert.equal(await comments.locator('ul.comment-list').count(),1);
  assert.ok(await comments.locator('.children .comment').count()>0);
  assert.equal(await comments.locator('ol.children').count(),0);
  const lists=await comments.locator('.comment-list,.children').evaluateAll(es=>es.map(el=>getComputedStyle(el).listStyleType));
  assert.ok(lists.every(type=>type==='none'));
  assert.ok(await comments.locator('.comment-parent-reference a[href^="#comment-"]').count()>0);
  assert.equal(await comments.locator('.comment-author .says').count(),0);
  if(!process.env.COMMENTS_URL || process.env.COMMENTS_FIXTURE==='1'){
   assert.ok(await comments.locator('.depth-5').count()>0);
   assert.equal(await comments.locator('.depth-3 > .comment-body .comment-level').innerText(),'Nivel 2');
   assert.equal(await comments.locator('.depth-4 > .comment-body .comment-level').innerText(),'Nivel 3');
   const lefts=await comments.locator('.depth-2 > .comment-body,.depth-3 > .comment-body,.depth-4 > .comment-body').evaluateAll(es=>es.map(e=>e.getBoundingClientRect().left));
   assert.ok(lefts[0]<lefts[1] && lefts[1]<lefts[2],'Every response level must remain visually distinct');
   assert.ok(await comments.locator('.comment-author-badge').count()>0);
   assert.equal(await comments.getByText('Texto pendiente que no debe mostrarse al visitante.').count(),0);
   assert.equal(await comments.locator('.comment-content ol').evaluate(el=>getComputedStyle(el).listStyleType),'decimal');
  }
  const parentLink=comments.locator('.comment-parent-reference a').first();
  const parentTarget=await parentLink.getAttribute('href');await parentLink.click();
  const parentTop=await page.locator(parentTarget).evaluate(el=>el.getBoundingClientRect().top);
  assert.ok(parentTop>=70 && parentTop<=140,'Parent anchor must stay below the sticky header');
  // Reply moves the native form below the selected comment without loading another page.
  const reply=comments.locator('.comment-reply-link').first();
  const parentId=await reply.getAttribute('data-commentid');
  await reply.click();
  assert.equal(await page.locator('#comment_parent').inputValue(),parentId);
  assert.equal(await page.locator(`#comment-${parentId} > #respond`).count(),1);
  assert.equal(await page.locator('#comment').evaluate(el=>el===document.activeElement),true);
  assert.equal(await page.locator('#respond').count(),1);
  await page.locator('#cancel-comment-reply-link').click();
  assert.equal(await page.locator('#comment_parent').inputValue(),'0');
  assert.equal(await page.locator('.comment-list #respond').count(),0);
  await comments.locator('.comment-jump').click();
  assert.equal(await page.locator('#comment').evaluate(el=>el===document.activeElement),true);
  for(const id of ['comment','author','email'])assert.ok(await page.locator(`label[for="${id}"]`).count()>0);
  const consent=page.locator('#wp-comment-cookies-consent');
  if(await consent.count()){
   const wasChecked=await consent.isChecked();await page.locator('label[for="wp-comment-cookies-consent"]').click();assert.equal(await consent.isChecked(),!wasChecked);
   assert.ok(!(await page.locator('label[for="wp-comment-cookies-consent"]').innerText()).includes('website'));
  }
  await page.locator('#email').fill('invalid-email');assert.equal(await page.locator('#email').evaluate(el=>el.checkValidity()),false);
  const overflow=await comments.evaluate(section=>[...section.querySelectorAll('.comment-body,.comment-respond,input,textarea')].filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&(r.left<0||r.right>innerWidth+1)}).map(el=>el.className));
  assert.deepEqual(overflow,[]);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  for(const mode of ['light','dark']){
   await page.evaluate(mode=>document.documentElement.setAttribute('data-theme',mode),mode);
   if(process.env.SCREENSHOT_DIR){await comments.locator('.comments-heading').evaluate(el=>scrollTo({top:scrollY+el.getBoundingClientRect().top-90,behavior:'instant'}));await page.screenshot({path:process.env.SCREENSHOT_DIR+`/comments-${width}-${mode}.png`})}
  }
  assert.deepEqual(errors,[]);await page.close();
 }
 await browser.close();console.log('Comments: mobile/desktop, no thread numbering, deep replies, labels, focus, native reply/cancel, pending privacy and long text passed; no comments submitted');
})().catch(e=>{console.error(e);process.exit(1)});
