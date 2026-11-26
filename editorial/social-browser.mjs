// One local Chrome MCP connection shared by scheduled publishing jobs.
import {createRequire} from 'node:module';
import {homedir} from 'node:os';
import {readFileSync,chmodSync,unlinkSync,existsSync} from 'node:fs';
import {createServer} from 'node:net';
const home=homedir(),base=home+'/.local/share/datogedon-browser';
const require=createRequire(base+'/package.json');
const {Client}=require('@modelcontextprotocol/sdk/client/index.js');
const {StdioClientTransport}=require('@modelcontextprotocol/sdk/client/stdio.js');
const {ListRootsRequestSchema}=require('@modelcontextprotocol/sdk/types.js');
const pkg=JSON.parse(readFileSync(base+'/node_modules/chrome-devtools-mcp/package.json','utf8'));
const socket=base+'/control.sock',root=home+'/Movies/Datogedon';
let client,connecting,chain=Promise.resolve();
const publishingPages=new Set();
async function connect(){
 if(client)return client;
 if(connecting)return connecting;
 connecting=(async()=>{
  const transport=new StdioClientTransport({command:process.execPath,args:[base+'/node_modules/chrome-devtools-mcp/'+pkg.bin['chrome-devtools-mcp'],'--autoConnect','--no-usage-statistics','--no-performance-crux','--redact-network-headers','--categoryNetwork=false','--categoryPerformance=false','--categoryDebugging=true','--categoryMemory=false','--no-file-navigations','--filesystemRoot='+root],stderr:'inherit'});
  const next=new Client({name:'Datogedon scheduled publisher',version:'1.0.0'},{capabilities:{roots:{listChanged:false}}});
  next.setRequestHandler(ListRootsRequestSchema,async()=>({roots:[{uri:'file://'+root,name:'Datogedon publishing assets'}]}));
  await next.connect(transport);client=next;return next;
 })();
 try{return await connecting;}finally{connecting=undefined;}
}
async function call(request){
 const c=await connect();
 if(request.operation==='tools')return {tools:(await c.listTools()).tools.filter(t=>!request.names||request.names.includes(t.name))};
 if(request.tool==='new_page')throw new Error('Open tabs with the validated Profile 7 opener.');
 const allowed=new Set(['list_pages','select_page','take_snapshot','take_screenshot','evaluate_script','click','fill','fill_form','press_key','type_text','upload_file','navigate_page','wait_for','hover','handle_dialog','drag']);
 if(!allowed.has(request.tool))throw new Error('Unsupported publishing tool');
 if(request.tool!=='list_pages'&&!publishingPages.has(request.args?.pageId))throw new Error('Call list_pages and use a publishing platform page only.');
 const result=await c.callTool({name:request.tool,arguments:request.args||{}},undefined,{timeout:120000});
 if(request.tool==='list_pages'){
  publishingPages.clear();
  for(const part of result.content||[])if(part.type==='text')part.text=part.text.split('\n').filter(line=>{
   const match=line.match(/^(\d+): .*\((https:\/\/[^)]+)\)/);if(!match)return !/^\d+: /.test(line);
   const host=new URL(match[2]).hostname;
   if(!['www.tiktok.com','www.youtube.com','studio.youtube.com','www.instagram.com'].includes(host))return false;
   publishingPages.add(Number(match[1]));return true;
  }).join('\n');
 }
 return result;
}
if(existsSync(socket))unlinkSync(socket);
const server=createServer(connection=>{
 let input='';connection.setEncoding('utf8');
 connection.on('data',chunk=>{
  input+=chunk;if(input.length>1024*1024){connection.destroy();return;}
  const end=input.indexOf('\n');if(end<0)return;
  const line=input.slice(0,end);input='';
  chain=chain.then(async()=>{
   try{connection.end(JSON.stringify(await call(JSON.parse(line)))+'\n');}
   catch(error){connection.end(JSON.stringify({isError:true,error:error.message})+'\n');}
  }).catch(()=>{});
 });
 connection.on('error',()=>{});
});
server.listen(socket,()=>{chmodSync(socket,0o600);console.log('Datogedon browser relay ready; Chrome connects on first request.');});
async function stop(){server.close();if(client)await client.close();if(existsSync(socket))unlinkSync(socket);process.exit(0);}
process.on('SIGTERM',stop);process.on('SIGINT',stop);
