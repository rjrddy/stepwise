// Explicit async call boundaries; no global monkey-patching or model-provider dependency.
const mask = '[REDACTED]';
export function redact(value, secrets = []) {
  if (Array.isArray(value)) return value.map(v => redact(v, secrets));
  if (value !== null && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v]) => [k, /password|secret|token|authorization|api.?key|cookie/i.test(k) ? mask : redact(v, secrets)]));
  if (typeof value === 'string') {
    for (const secret of secrets.filter(Boolean).toSorted((a,b) => b.length-a.length)) value = value.split(secret).join(mask);
    return value.replace(/bearer\s+[A-Za-z0-9._~+/-]+={0,2}/gi, 'Bearer ' + mask);
  }
  if (typeof value === 'number' && !Number.isFinite(value)) throw Error('non-finite JSON');
  if (value === undefined || typeof value === 'bigint' || typeof value === 'function') throw Error('JSON only');
  return value;
}
function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k=>[k,sorted(value[k])]));
  return value;
}
export class Tape {
  constructor({sink, replay = null, secrets = []} = {}) {
    this.sink=sink; this.source=structuredClone(replay); this.secrets=secrets;
    this.events=[]; this.cursor=0; this.busy=false;
  }
  async call(kind, name, input, fn) {
    if(this.busy) throw Error('concurrent calls require separate tapes');
    this.busy=true;
    try {
      const publicInput=redact(input,this.secrets);
      if(this.source !== null) {
        const event=this.source[this.cursor];
        if(!event || event.kind!==kind || event.name!==name || JSON.stringify(sorted(event.input))!==JSON.stringify(sorted(publicInput))) throw Error('replay divergence at '+this.cursor);
        this.cursor++; this.events.push(structuredClone(event));
        if(event.error!==null) throw Error(event.error);
        return structuredClone(event.output);
      }
      const event={kind,name,input:publicInput,output:null,error:null};
      let result;
      try { result=await fn(input); event.output=redact(result,this.secrets); }
      catch(error) {
        event.error=redact(`${error.name}: ${error.message}`,this.secrets);
        if(this.sink) await this.sink(event);
        this.events.push(structuredClone(event)); throw error;
      }
      if(this.sink) await this.sink(event);
      this.events.push(structuredClone(event)); return result;
    } finally {this.busy=false;}
  }
  finish(){if(this.source!==null && this.cursor!==this.source.length) throw Error('unconsumed frames');}
}
export class Client {
  constructor(base,{token='',secrets=[]}={}){this.base=base;this.token=token;this.secrets=secrets;}
  async request(path,data){
    const response=await fetch(this.base+path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+this.token},body:data===undefined?undefined:JSON.stringify(redact(data,this.secrets)),signal:AbortSignal.timeout(10000)});
    if(!response.ok) throw Error('Stepwise HTTP '+response.status);
    return response.json();
  }
  async record(label){
    const {id}=await this.request('/api/runs',{label,mode:'sdk'});let seq=0;
    const tape=new Tape({secrets:this.secrets,sink:async event=>{await this.request(`/api/runs/${id}/events`,{seq,event});seq++;}});
    return {id,tape};
  }
  async replay(id){const run=await this.request('/api/runs/'+id);return new Tape({replay:run.events,secrets:this.secrets});}
}
