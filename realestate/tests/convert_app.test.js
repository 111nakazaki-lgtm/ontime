// 実行: node realestate/tests/convert_app.test.js
// アプリ内「概要書の変換」画面の確認。PDF.js が必要です（npm i pdfjs-dist@3.11.174 を realestate/tests か上位に入れる。なければスキップ）。
const assert=require('assert');const path=require('path');const fs=require('fs');
let pw;try{pw=require('playwright')}catch(e){pw=require(process.env.PLAYWRIGHT_PATH||'/opt/node22/lib/node_modules/playwright')}
const cands=[process.env.PDFJS_DIR,path.resolve(__dirname,'node_modules/pdfjs-dist/build'),path.resolve(__dirname,'../../node_modules/pdfjs-dist/build'),'/tmp/pdfjs/node_modules/pdfjs-dist/build'].filter(Boolean);
const dir=cands.find(d=>fs.existsSync(path.join(d,'pdf.min.js')));
if(!dir){console.log('skip: pdfjs-dist が見つかりません');process.exit(0)}
(async()=>{
 const b=await pw.chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined}).catch(()=>pw.chromium.launch({executablePath:'/opt/pw-browsers/chromium'}));
 const ctx=await b.newContext({acceptDownloads:true}),p=await ctx.newPage(),errs=[];p.on('pageerror',e=>errs.push(e.message));
 await ctx.route('https://cdnjs.cloudflare.com/**',r=>r.fulfill({path:path.join(dir,r.request().url().split('/').pop()),headers:{'access-control-allow-origin':'*'}}));
 await p.goto('file://'+path.resolve(__dirname,'../index.html'));
 await p.click('#nav button[data-t=conv]');
 const S=path.resolve(__dirname,'../samples'),tmp=fs.mkdtempSync(path.join(require('os').tmpdir(),'cv'));
 const files=['物件概要書_サンプル横浜.pdf','物件概要書_サンプル渋谷.pdf','投資分析書_サンプル横浜.pdf'].map((n,i)=>{const f=path.join(tmp,'s'+i+'.pdf');fs.copyFileSync(path.join(S,n),f);return f});
 await p.setInputFiles('#cvf',files);
 await p.waitForFunction(()=>cvItems.length>=3&&!cvBusy,null,{timeout:60000});
 const r=await p.evaluate(()=>cvItems.map(x=>({state:x.state,name:x.prop&&x.prop.name,price:x.prop&&x.prop.price,zoom:x.zoom})));
 assert.deepStrictEqual(r.map(x=>x.state.startsWith('変換OK')),[true,true,false],'概要書は変換、投資分析書はスキップ');
 assert.strictEqual(r[0].price,120000000,'価格を読み取る');assert.ok(/横浜/.test(r[0].name),'物件名を読み取る');
 const html=await p.evaluate(()=>cvPage([cvItems[0]],false));
 assert.ok(html.includes(r[0].name)&&html.includes('<script>')===false,'標準HTMLに物件名が入る');
 const [dl]=await Promise.all([p.waitForEvent('download'),p.click('button[data-cv="zip"]')]);
 const z=fs.readFileSync(await dl.path());assert.strictEqual(z.readUInt32LE(0),0x04034b50,'ZIPの先頭');
 const n=await p.evaluate(()=>{const a=S.props.length;cvAdd([cvItems[0]],false);return S.props.length-a});assert.strictEqual(n,1,'物件一覧に追加');
 assert.deepStrictEqual(errs,[],'ページのエラー');
 console.log('ok   概要書の変換画面（読み取り・スキップ・HTML・ZIP・追加）');await b.close();
})().catch(e=>{console.error('FAIL',e);process.exit(1)});
