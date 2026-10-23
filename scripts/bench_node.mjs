import {Tape} from '../sdk/node/index.mjs';
import {performance} from 'node:perf_hooks';
const trials=[];
for(let t=0;t<3;t++){
 const tape=new Tape();const input={count:3};const fn=async p=>({answer:p.count*14});
 const result={};
 for(const mode of ['disabled','memory']){
  const samples=[];
  for(let i=0;i<300;i++){const start=performance.now();if(mode==='disabled')await fn(input);else await tape.call('tool','lookup',input,fn);samples.push((performance.now()-start)*1000);}
  samples.sort((a,b)=>a-b);result[mode]={calls:samples.length,p50_us:samples[150],p99_us:samples[296],samples_us:samples};
 }trials.push(result);
}
console.log(JSON.stringify({node:process.version,scope:'in-memory async SDK; persistence measured by Python HTTP path only',trials}));
