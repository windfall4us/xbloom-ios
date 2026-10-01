const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const js = fs.readFileSync(__dirname + '/ios_p2a.js','utf8');
class El {
  constructor(id='') {this.id=id;this.hidden=false;this.disabled=false;this.isConnected=true;this.classList={add:()=>{},remove:()=>{},contains:()=>true};this.listeners={};this.dataset={};this.attrs={};this.textContent='';}
  set innerHTML(v){ for(const m of v.matchAll(/id=\"([^\"]+)\"/g)) els[m[1]]=new El(m[1]); }
  setAttribute(k,v){this.attrs[k]=v;}
  removeAttribute(k){delete this.attrs[k];}
  addEventListener(t,fn){this.listeners[t]=fn;}
  closest(){return this;}
}
const els={};
const body = new El('body');body.appendChild=x=>{els[x.id]=x;};
const doc={readyState:'complete',body,documentElement:{classList:{contains:()=>true}},createElement:()=>new El(),getElementById:id=>els[id],addEventListener:(k,v)=>{doc[k]=v;}};
const request=[];
let unblock;
let fail=false;
let pending = new Promise(res => {unblock=res;});
const oldApi=(u,o)=>{request.push({u,method:o?.method||'GET'});if(fail)return Promise.reject(new TypeError('Failed to fetch'));if(o?.method==='POST')return pending;return Promise.resolve({ok:true})};
const context={document:doc,window:{Capacitor:{},__xbP2AInstalled:false},api:oldApi,TypeError,Date,Set,Promise,clearTimeout,setTimeout,console};
vm.runInNewContext(js,context);
(async()=>{
  assert(context.window.__xbP2AInstalled);
  const first=context.api('/api/beans',{method:'POST'});
  await assert.rejects(context.api('/api/beans',{method:'POST'}),/已阻止重复请求/);
  assert.strictEqual(request.length,1);
  unblock({bean:{bean_id:'demo-1'}});
  await first;
  assert.strictEqual(els.xbP2AToast.textContent,'咖啡豆已创建');
  fail=true;
  await assert.rejects(context.api('/api/tasting/detailed',{method:'POST'}),/Failed to fetch/);
  assert.strictEqual(els.xbP2ANetwork.hidden,false);
  assert.match(els.xbP2ANetworkText.textContent,/结果可能未知/);
  const reqCount=request.length;
  fail=false;
  await els.xbP2ARetry.listeners.click.call(els.xbP2ARetry);
  assert.strictEqual(request.length,reqCount+1);
  assert.strictEqual(request.at(-1).u,'/api/health');
  assert.strictEqual(request.at(-1).method,'GET');
  console.log('RUNTIME duplicate POST guard PASS');
  console.log('RUNTIME completed create feedback PASS');
  console.log('RUNTIME failed write uncertainty PASS');
  console.log('RUNTIME retry GET-only PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
