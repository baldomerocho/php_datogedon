// Capture a cited public source in a fresh browser, never a signed-in profile.
import {createRequire} from 'node:module';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve,dirname,join,relative,isAbsolute} from 'node:path';
import {homedir} from 'node:os';
import {lookup} from 'node:dns/promises';
import {BlockList} from 'node:net';
import {createHash} from 'node:crypto';

const args={};
for(let i=2;i<process.argv.length;i+=2){if(!process.argv[i].startsWith('--')||!process.argv[i+1])throw Error('Use --name value arguments');args[process.argv[i].slice(2)]=process.argv[i+1];}
for(const key of ['url','output','credit','modules-root'])if(!args[key])throw Error('Missing --'+key);
if(args.credit.length>65)throw Error('Use a short visible credit');
const root=join(homedir(),'claude-activity-audit/videos/evidence'),output=resolve(args.output),rel=relative(root,output);
if(rel.startsWith('..')||isAbsolute(rel)||!output.endsWith('.png'))throw Error('Output must be a PNG inside the public evidence directory');
const blocked=new BlockList();
for(const [ip,bits] of [['0.0.0.0',8],['10.0.0.0',8],['100.64.0.0',10],['127.0.0.0',8],['169.254.0.0',16],['172.16.0.0',12],['192.168.0.0',16],['224.0.0.0',4],['240.0.0.0',4]])blocked.addSubnet(ip,bits,'ipv4');
for(const [ip,bits] of [['::',128],['::1',128],['fc00::',7],['fe80::',10],['ff00::',8]])blocked.addSubnet(ip,bits,'ipv6');
const hosts=new Map();
async function publicUrl(value){
 const u=new URL(value);
 if(u.protocol!=='https:'||u.username||u.password||u.port&&u.port!=='443'||u.hostname.endsWith('.local')||u.hostname.endsWith('.localhost'))throw Error('Use a public HTTPS source');
 const host=u.hostname.replace(/^\[|\]$/g,'');
 if(!hosts.has(host))hosts.set(host,lookup(host,{all:true}).then(values=>values.length>0&&values.every(v=>!blocked.check(v.address,v.family===6?'ipv6':'ipv4'))));
 if(!await hosts.get(host))throw Error('Private-network source is not allowed');
 return u;
}
await publicUrl(args.url);if(args['image-url'])await publicUrl(args['image-url']);
const require=createRequire(join(resolve(args['modules-root']),'..','package.json'));
const {chromium}=require('playwright');
const options={headless:true};
if(process.platform==='darwin')options.executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch(options);
try{
 const context=await browser.newContext({viewport:{width:900,height:800},serviceWorkers:'block',acceptDownloads:false});
 await context.route('**/*',async route=>{try{await publicUrl(route.request().url());await route.continue();}catch{await route.abort();}});
 const page=await context.newPage();
 await page.goto(args['image-url']||args.url,{waitUntil:'domcontentloaded',timeout:30000});
 await Promise.race([page.evaluate(()=>document.fonts.ready),new Promise(r=>setTimeout(r,2500))]);
 if(/verify you are human|access denied|just a moment|captcha/i.test((await page.title())))throw Error('Source requires interactive access; choose another source');
 const zoom=Number(args.zoom||1);if(!Number.isFinite(zoom)||zoom<1||zoom>2)throw Error('Zoom must be between 1 and 2');
 if(!args['image-url'])await page.evaluate(z=>document.body.style.zoom=String(z),zoom);
 const selector=args.selector||(args['image-url']?'img':'main');const element=page.locator(selector).first();
 await element.waitFor({state:'visible',timeout:10000});const box=await element.boundingBox();
 if(!box||box.width<240||box.height<80||box.width*box.height>16_000_000)throw Error('Choose a readable source excerpt, not a tiny label or an entire long page');
 await mkdir(dirname(output),{recursive:true});
 let crop=null;
 if(args['image-url'])await element.screenshot({path:output,timeout:15000});
 else{
  await element.scrollIntoViewIfNeeded();const rect=await element.boundingBox();
  const height=Math.min(rect.height,Number(args.height||540)),width=rect.width;
  if(width>1600)throw Error('Choose a narrower source fragment');
  if(!Number.isFinite(height)||height<80||height>800)throw Error('Use an excerpt height between 80 and 800 pixels');
  crop={x:Math.max(0,rect.x),y:Math.max(0,rect.y),width,height};
  await page.screenshot({path:output,clip:crop,timeout:15000});
 }
 const metadata={asset:output,sha256:createHash('sha256').update(await readFile(output)).digest('hex'),source_url:args.url,asset_url:args['image-url']||null,
  credit:args.credit,kind:args['image-url']?'source_image':'screenshot',captured_at:new Date().toISOString(),selector,crop,zoom:args['image-url']?1:zoom,fresh_unsigned_browser:true};
 await writeFile(output+'.json',JSON.stringify(metadata,null,2)+'\n',{mode:0o600});process.stdout.write(JSON.stringify(metadata)+'\n');
}finally{await browser.close();}
