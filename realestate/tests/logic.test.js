// 実行: node realestate/tests/logic.test.js  (playwright と chromium が必要)
const assert=require('assert');const path=require('path');
let pw;try{pw=require('playwright')}catch(e){pw=require(process.env.PLAYWRIGHT_PATH||'/opt/node22/lib/node_modules/playwright')}
const near=(a,b,tol,msg)=>assert.ok(Math.abs(a-b)<=tol,`${msg}: ${a} vs ${b}`);
(async()=>{
 const b=await pw.chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined}).catch(()=>pw.chromium.launch({executablePath:'/opt/pw-browsers/chromium'}));
 const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('file://'+path.resolve(__dirname,'../index.html'));
 const ev=(f,a)=>p.evaluate(f,a);let n=0;const t=(name,fn)=>fn().then(()=>{n++;console.log('ok  ',name)},e=>{console.error('FAIL',name,'\n',e.message);process.exitCode=1});
 await t('元利均等返済 PMT',async()=>{const P=3e7,r=0.018/12,N=360,exp=P*r/(1-Math.pow(1+r,-N));near(await ev(()=>pmt(3e7,0.018,30)),exp,0.01,'pmt');near(await ev(()=>pmt(1.2e6,0,10)),10000,1e-6,'rate0')});
 await t('ローン残高(完済で0、途中は定義式と一致)',async()=>{near(await ev(()=>balance(3e7,0.018,30,360)),0,0.5,'end');
  const P=3e7,r=0.018/12,m=P*r/(1-Math.pow(1+r,-360)),k=120,exp=P*Math.pow(1+r,k)-m*(Math.pow(1+r,k)-1)/r;near(await ev(()=>balance(3e7,0.018,30,120)),exp,0.01,'mid')});
 await t('和暦の境界',async()=>{const r=await ev(()=>['2019-05-01','2019-04-30','1989-01-08','1989-01-07','2026-10-07','1926-12-25'].map(WA));
  assert.deepStrictEqual(r,['令和元年5月1日','平成31年4月30日','平成元年1月8日','昭和64年1月7日','令和8年10月7日','昭和元年12月25日'])});
 await t('日付は端末のローカル日付',async()=>{const [a,c]=await ev(()=>{const d=new Date();return [todayStr(),d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')]});assert.strictEqual(a,c)});
 await t('地図タイル座標',async()=>{const o=await ev(()=>tileXY(0,0,1));near(o.x,1,1e-9,'x');near(o.y,1,1e-9,'y');
  const q=await ev(()=>tileXY(35.658,139.7016,16)),n=65536,rad=35.658*Math.PI/180;near(q.x,(139.7016+180)/360*n,1e-6,'lng');near(q.y,(1-Math.log(Math.tan(rad)+1/Math.cos(rad))/Math.PI)/2*n,1e-6,'lat');});
 await t('法定耐用年数と簡便法',async()=>{
  const mk=(s,age,built)=>({type:'マンション',age,reg:{bldg:{struct:s,built}}});
  let r=await ev(mk=>{const p=ensure(JSON.parse(mk));return lifeInfo(p)},JSON.stringify(mk('鉄筋コンクリート造',6,'')));assert.deepStrictEqual([r.L,r.rem,r.loan],[47,42,41]);
  r=await ev(mk=>lifeInfo(ensure(JSON.parse(mk))),JSON.stringify(mk('木造',50,'')));assert.deepStrictEqual([r.L,r.rem,r.loan],[22,4,0]);
  r=await ev(mk=>lifeInfo(ensure(JSON.parse(mk))),JSON.stringify(mk('木造',10,'')));assert.strictEqual(r.rem,14);// (22-10)+10*0.2=14
  r=await ev(mk=>lifeInfo(ensure(JSON.parse(mk))),JSON.stringify(mk('木造モルタル',30,'')));assert.strictEqual(r.rem,4)});
 await t('実効容積率(道路幅員制限)',async()=>{
  const f=(z,far,rw)=>ev(a=>farLimit({zoning:a[0],far:a[1],roadWidth:a[2]}),[z,far,rw]);
  near(await f('第一種住居地域','300','4'),160,1e-9,'住居系4m');near(await f('商業地域','400','6'),360,1e-9,'その他6m');
  near(await f('第一種住居地域','200','12'),200,1e-9,'12m以上は指定');near(await f('第一種住居地域','200','8'),200,1e-9,'指定が小さい')});
 const A=(prop)=>ev(x=>{const p=ensure(JSON.parse(x));return analyze(p).map(i=>i.level+':'+i.title)},JSON.stringify(prop));
 const base={type:'一戸建て',price:6e7,area:100,age:10,det:{seller:'山田 太郎'},reg:{acquired:new Date().toISOString().slice(0,10),land:{lot:'1番',category:'宅地',area:'100'},bldg:{no:'1番',struct:'木造',floorArea:'100',built:'2016-01-01'},kou:[],otsu:[]}};
 const clone=o=>JSON.parse(JSON.stringify(o));
 await t('土地・建物の同一抵当権は二重計上しない',async()=>{const x=clone(base);
  x.reg.kou=[{no:'1',scope:'土地',purpose:'所有権移転',date:'2010-01-01',holder:'山田 太郎'},{no:'1',scope:'建物',purpose:'所有権保存',date:'2016-03-01',holder:'山田 太郎'}];
  x.reg.otsu=[{no:'1',scope:'土地',purpose:'抵当権設定',date:'2016-03-01',amount:'40000000',holder:'A銀行'},{no:'1',scope:'建物',purpose:'抵当権設定',date:'2016-03-01',amount:'40000000',holder:'A銀行'}];
  const r=await A(x);assert.ok(!r.some(s=>s.includes('担保権の合計額が売買価格を超')),r.join('|'));assert.strictEqual(r.filter(s=>s.includes('「抵当権設定」が残')).length,1)});
 await t('担保権の合計が価格を超えると重大',async()=>{const x=clone(base);x.reg.kou=[{no:'1',purpose:'所有権移転',date:'2010-01-01',holder:'山田 太郎'}];
  x.reg.otsu=[{no:'1',purpose:'根抵当権設定',date:'2012-01-01',amount:'70000000',holder:'B信金'}];assert.ok((await A(x)).includes('重大:担保権の合計額が売買価格を超えています'))});
 await t('土地と建物で名義が異なる/売主が片方のみ',async()=>{const x=clone(base);
  x.reg.kou=[{no:'1',scope:'土地',purpose:'所有権移転',date:'2010-01-01',holder:'山田 太郎'},{no:'1',scope:'建物',purpose:'所有権保存',date:'2016-03-01',holder:'山田 花子'}];
  const r=await A(x);assert.ok(r.includes('注意:土地と建物の登記名義人が異なります'));assert.ok(r.some(s=>s.startsWith('重大:(建物) 売主と登記名義人が一致しません')),r.join('|'))});
 await t('名義人が空欄でも売主一致と誤判定しない',async()=>{const x=clone(base);x.reg.kou=[{no:'1',purpose:'所有権移転',date:'2010-01-01',holder:''}];assert.ok((await A(x)).some(s=>s.includes('売主と登記名義人が一致しません')))});
 await t('差押の残存と、抹消済みなら指摘しない',async()=>{const x=clone(base);x.reg.kou=[{no:'1',purpose:'所有権移転',date:'2010-01-01',holder:'山田 太郎'},{no:'2',purpose:'差押',date:'2025-01-01',holder:'市'}];
  assert.ok((await A(x)).some(s=>s.startsWith('重大:甲区2番')));x.reg.kou[1].cleared=true;assert.ok(!(await A(x)).some(s=>s.startsWith('重大:甲区2番')))});
 await t('接道・セットバック・旧耐震',async()=>{const x=clone(base);x.reg.kou=[{no:'1',purpose:'所有権移転',date:'2010-01-01',holder:'山田 太郎'}];
  x.det.frontage='1.8';x.det.roadWidth='3.2';x.reg.bldg.built='1975-05-01';const r=await A(x);
  assert.ok(r.some(s=>s.startsWith('重大:接道が2m未満')));assert.ok(r.some(s=>s.startsWith('注意:前面道路が4m未満')));assert.ok(r.some(s=>s.includes('旧耐震基準の可能性')))});
 await t('スコアと総合判定',async()=>{const v=await ev(()=>verdict([{level:'重大'},{level:'注意'},{level:'注意'},{level:'確認'}]));assert.strictEqual(v.score,100-25-16-2);assert.strictEqual(v.cls,'重大');
  const w=await ev(()=>verdict(Array(5).fill({level:'重大'})));assert.strictEqual(w.score,0)});
 await t('取り込みデータの無害化(ID・画像・数値・列挙)',async()=>{
  const r=await ev(()=>{const o=sanitizeProp({id:'x" onclick="alert(1)',name:'<b>x</b>',price:-5,type:'謎',status:'謎',photos:[{src:'javascript:alert(1)'},{src:'data:image/png;base64,AAAA',cap:'c'}],geo:{lat:'999',lng:'abc'}});return o});
  assert.ok(/^[\w-]+$/.test(r.id));assert.strictEqual(r.price,0);assert.strictEqual(r.type,'マンション');assert.strictEqual(r.status,'検討中');assert.strictEqual(r.photos.length,1);assert.strictEqual(r.geo.lat,'');assert.strictEqual(r.geo.lng,'')});
 await t('JSON読込でも無害化され、重複IDは振り直される',async()=>{const s=await ev(()=>stateFrom({props:[{id:'a',name:'1'},{id:'a',name:'2'},null,'x'],cmp:['a','zz']}));assert.strictEqual(s.props.length,2);assert.notStrictEqual(s.props[0].id,s.props[1].id);assert.ok(s.cmp.length<=1)});
 await t('シミュレーターの極端値でも壊れない',async()=>{const html=await ev(()=>{tab='sim';render();calc({price:3e7,rent:1.2e5,mgmt:1e4,tax:6e4,other:0,down:150,rate:-1,years:0,vac:5,cost:7,hold:60,growth:0,exit:0,tax2:20});return document.querySelector('#out').innerText});assert.ok(!/NaN|Infinity/.test(html),html.slice(0,200))});
 await t('全タブがエラーなく描画できる',async()=>{for(const k of ['dash','list','pipe','cmp','sim','doc','data']){await ev(k=>{tab=k;render()},k)}assert.deepStrictEqual(errs,[])});
 await t('概要書・登記分析書のHTMLに未エスケープの入力が入らない',async()=>{const h=await ev(()=>{const p=ensure(S.props[0]);p.name='<img src=x onerror=alert(1)>';p.reg.kou[0].holder='<script>1</script>';return docGaiyo(p)+docTouki(p)});assert.ok(!/<img src=x|<script>1/.test(h))});
 console.log(`\n${n} tests run`);await b.close();
})();
