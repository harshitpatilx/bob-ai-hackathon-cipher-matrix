const SAMPLE = {
  complaint: `Complainant Asha Verma (AC-VA1) received a call at 09:41 from +91-90000-11122 posing as a CBI officer. She was told a parcel in her name held illegal items and that she was under "digital arrest". She was kept on video call and told to move savings to a "verification account". She transferred Rs 4.5 lakh at 10:02 and Rs 1.5 lakh at 10:40. Two other people reported the same caller.`,
  tx: `id,time,from,to,amount
T1,10:02,AC-VA1,AC-4412,450000
T2,10:15,AC-VR2,AC-7781,320000
T3,10:31,AC-VM3,AC-9034,280000
T4,10:40,AC-VA1,AC-2265,150000
T5,10:19,AC-4412,AC-5590,445000
T6,10:33,AC-7781,AC-5590,315000
T7,10:48,AC-9034,AC-5590,275000
T8,10:55,AC-2265,AC-5590,148000
T9,11:20,AC-5590,AC-0071,1170000`,
  links: `account,name,device
AC-VA1,Asha Verma,
AC-VR2,Ravi Kulkarni,
AC-VM3,Meena Joshi,
AC-4412,Sunil Pawar,DEV-A
AC-7781,Kiran Dhote,DEV-A
AC-9034,Rehan Sheikh,DEV-A
AC-2265,Pooja Nair,DEV-A
AC-5590,Deepak Traders,DEV-A;DEV-B
AC-0071,V K Exports,DEV-B`
};

const $ = id => document.getElementById(id);
let CASE = null;
const inr = n => 'Rs ' + Number(n).toLocaleString('en-IN');
const mins = t => { const [h, m] = t.split(':').map(Number); return h * 60 + m };

function loadSample() { 
  $('complaint').value = SAMPLE.complaint; 
  $('txcsv').value = SAMPLE.tx; 
  $('linkcsv').value = SAMPLE.links; 
}

const csv = s => s.trim().split(/\r?\n/).slice(1).filter(Boolean).map(l => l.split(',').map(x => x.trim()));

function extractWithAI(text) {
  const phones = [...new Set(text.match(/\+91[-\d ]{10,}/g) || [])];
  const kw = /CBI|police|arrest|parcel|customs/i.test(text);
  return { phones, impersonation: kw };
}

function analyze() {
  const tx = csv($('txcsv').value).map(([id, time, from, to, amt]) => ({ id, time, from, to, amt: +amt }));
  const links = csv($('linkcsv').value);
  const N = {};
  const get = id => N[id] || (N[id] = { id, name: id, in: 0, out: 0, senders: new Set(), firstIn: null, firstOut: null, devs: [] });
  
  links.forEach(([a, name, dev]) => { const n = get(a); n.name = name || a; n.devs = dev ? dev.split(';') : [] });
  
  tx.forEach(t => {
    const f = get(t.from), o = get(t.to), m = mins(t.time);
    f.out += t.amt; f.firstOut = f.firstOut == null ? m : Math.min(f.firstOut, m);
    o.in += t.amt; o.senders.add(t.from); o.firstIn = o.firstIn == null ? m : Math.min(o.firstIn, m);
  });
  
  const byDev = {}; Object.values(N).forEach(n => n.devs.forEach(d => (byDev[d] = byDev[d] || []).push(n.id)));
  const nodes = Object.values(N);
  
  nodes.forEach(n => {
    n.dwell = (n.firstIn != null && n.firstOut != null) ? n.firstOut - n.firstIn : null;
    n.shared = [...new Set(n.devs.flatMap(d => byDev[d]).filter(x => x !== n.id))];
    n.why = [];
    if (n.in === 0 && n.out > 0) { n.role = 'victim'; n.conf = .95; n.why.push('Only sends money into the network; never receives (' + inr(n.out) + ' out).') }
    else if (n.out === 0 && n.in > 0) { n.role = 'kingpin'; n.conf = .6; n.why.push('Terminal account: received ' + inr(n.in) + ' and nothing left it.') }
    else if (n.senders.size >= 3) { n.role = 'handler'; n.conf = .7; n.why.push('Consolidation point: ' + n.senders.size + ' accounts fund it, then it forwards ' + inr(n.out) + ' onward.') }
    else { n.role = 'mule'; n.conf = .75; n.why.push('Pass-through account: money in and out' + (n.dwell != null ? ' within ' + n.dwell + ' min.' : '.')) }
  });
  
  nodes.forEach(n => {
    if (n.shared.length) n.why.push('Shares device ' + n.devs.filter(d => byDev[d].length > 1).join(', ') + ' with ' + n.shared.length + ' other account(s).');
    if (n.role === 'mule' && n.shared.length >= 2) n.conf = Math.min(.95, n.conf + .1);
    if (n.role === 'mule' && n.dwell != null && n.dwell <= 30) n.conf = Math.min(.95, n.conf + .05);
  });
  
  const h = nodes.find(n => n.role === 'handler'), k = nodes.find(n => n.role === 'kingpin');
  if (k && h && k.shared.includes(h.id)) { k.conf = .8; k.why.push('Shares a device with the consolidating account (' + h.name + ').') }
  
  const ai = extractWithAI($('complaint').value);
  const mules = nodes.filter(n => n.role === 'mule'), dw = mules.map(m => m.dwell).filter(x => x != null);
  const ind = []; let score = .4;
  
  if (ai.impersonation) { ind.push('Complaint describes impersonation of an authority figure'); score += .25 }
  if (h) { ind.push('Fan-in of ' + h.senders.size + ' accounts to one consolidator'); score += .1 }
  if (dw.length && Math.max(...dw) <= 30) { ind.push('All mules forwarded funds within ' + Math.max(...dw) + ' min'); score += .1 }
  
  const sd = Object.entries(byDev).filter(([d, a]) => a.length >= 3);
  if (sd.length) { ind.push('Device ' + sd[0][0] + ' shared by ' + sd[0][1].length + ' accounts'); score += .1 }
  
  const type = ai.impersonation ? 'Digital arrest / impersonation scam' : 'UPI mule-account layering';
  CASE = { tx, nodes, N, ai, pattern: { type, conf: Math.min(.97, score), ind }, victims: nodes.filter(n => n.role === 'victim'), mules, h, k };
  render();
}

function render() {
  const c = CASE;
  $('graphEmpty').hidden = true; 
  $('graphBody').hidden = false;
  const lost = c.victims.reduce((s, v) => s + v.out, 0);
  
  $('pattern').innerHTML = `<p><b>${c.pattern.type}</b> <span class="note">confidence ${(c.pattern.conf * 100).toFixed(0)}%</span></p>
   <div class="stats"><div class="stat"><b>${inr(lost)}</b><span>Reported loss</span></div>
   <div class="stat"><b>${c.victims.length}</b><span>Victims</span></div>
   <div class="stat"><b>${c.mules.length + (c.h ? 1: 0)}</b><span>Intermediary accounts</span></div>
   <div class="stat"><b>${c.k ? inr(c.k.in) : 'n/a'}</b><span>At terminal account</span></div></div>
   <ul>${c.pattern.ind.map(i => '<li>' + i + '</li>').join('')}</ul>`;
  
  drawGraph();
  
  $('txtable').innerHTML = '<tr><th>ID</th><th>Time</th><th>From</th><th>To</th><th>Amount</th></tr>' +
    c.tx.map(t => `<tr><td>${t.id}</td><td>${t.time}</td><td>${c.N[t.from].name}</td><td>${c.N[t.to].name}</td><td>${inr(t.amt)}</td></tr>`).join('');
  buildBrief();
}

function drawGraph() {
  const rows = ['victim', 'mule', 'handler', 'kingpin'], c = CASE, pos = {};
  const active = rows.filter(r => c.nodes.some(n => n.role === r));
  active.forEach((r, i) => {
    const list = c.nodes.filter(n => n.role === r);
    list.forEach((n, j) => { pos[n.id] = { x: 360 * (j + 1) / (list.length + 1), y: 50 + i * (340 / Math.max(1, active.length - 1)) } })
  });
  let s = '<defs><marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L8 4L0 8z" fill="currentColor" opacity=".5"/></marker></defs>';
  const mx = Math.max(...c.tx.map(t => t.amt));
  c.tx.forEach(t => {
    const a = pos[t.from], b = pos[t.to];
    s += `<line class="edge" style="color:var(--mut)" x1="${a.x}" y1="${a.y + 18}" x2="${b.x}" y2="${b.y - 22}" stroke-width="${1 + 3 * t.amt / mx}" marker-end="url(#ar)"/>`
  });
  c.nodes.forEach(n => {
    const p = pos[n.id];
    s += `<g class="node ${n.role}" data-id="${n.id}" tabindex="0" role="button" aria-label="${n.name}, ${n.role}"><circle cx="${p.x}" cy="${p.y}" r="18"/><text x="${p.x}" y="${p.y + 4}" fill="#fff" style="fill:#fff;font-weight:700">${n.role[0].toUpperCase()}</text><text x="${p.x}" y="${p.y+32}">${n.name.length > 13 ? n.name.slice(0, 12) + '…' : n.name}</text></g>`
  });
  $('svg').innerHTML = s;
  $('svg').querySelectorAll('.node').forEach(g => {
    const pick = () => select(g.dataset.id); g.onclick = pick; g.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick() } }
  });
}

function select(id) {
  const n = CASE.N[id];
  $('svg').querySelectorAll('.node').forEach(g => g.classList.toggle('sel', g.dataset.id === id));
  const refs = CASE.tx.filter(t => t.from === id || t.to === id).map(t => t.id);
  $('detail').innerHTML = `<p><b>${n.name}</b><br><span class="note">${n.id}</span></p>
   <p><span class="pill ${n.role}">${n.role === 'kingpin' ? 'probable kingpin' : n.role}</span> <span class="note">confidence ${(n.conf * 100).toFixed(0)}%</span></p>
   <ul>${n.why.map(w => '<li>' + w + '</li>').join('')}</ul>
   <p class="note">Evidence: ${refs.map(r => '<span class="cite">' + r + '</span>').join(' ')}</p>
   <p class="note">Probable role only. Officer review required.</p>`;
}

function cites(ids) { return ids.map(i => `<span class="cite">${i}</span>`).join(' ') }

function buildBrief(){
  const c=CASE,lost=c.victims.reduce((s,v)=>s+v.out,0);
  const first=c.tx.slice().sort((a,b)=>mins(a.time)-mins(b.time));
  const freeze=[c.h,...c.mules,c.k].filter(Boolean).sort((a,b)=>(b.in-b.out)-(a.in-a.out)||b.in-a.in);
  const devs=[...new Set(c.nodes.flatMap(n=>n.devs))];
  const chrono=[...first].map(t=>`<li>${t.time}: ${c.N[t.from].name} to ${c.N[t.to].name}, ${inr(t.amt)} ${cites([t.id])}</li>`).join('');
  const chain=[c.k,c.h,...c.mules].filter(Boolean);
  
  $('briefBody').innerHTML=`<h2>Case brief (draft for IO review)</h2>
  <div class="warn">AI-generated draft. Roles are probable, legal sections are suggestions, and both must be verified by the Investigating Officer or legal officer.</div>
  <h3>1. Complainant and victims</h3>
  <ul>${c.victims.map(v=>`<li>v.name ({v.id}): inr(v.out) transferred {cites(c.tx.filter(t=>t.from===v.id).map(t=>t.id))}</li>`).join('')}</ul>
  <h3>2. Chronology</h3><ul>${chrono}</ul>
  <h3>3. Modus operandi</h3>
  <p>${c.pattern.type} (${(c.pattern.conf*100).toFixed(0)}% confidence). ${c.pattern.ind.join('. ')}.</p>
  ${c.ai.phones.length?`<p>Calling number named in complaint: \${c.ai.phones.join(', ')}</p>`:''}
  <h3>4. Accused and suspects (probable roles)</h3>
  <ul>${chain.map(n=>`<li>\${n.name} (n.id): {n.role==='kingpin'?'probable principal / cash-out':n.role} , \({(n.conf*100).toFixed(0)}\%.\){n.why.join(' ')}</li>`).join('')}</ul>
  <h3>5. Money trail</h3>
  <p>Total reported loss ${inr(lost)}. ${c.k?inr(c.k.in)+' reached '+c.k.name+' ('+c.k.id+').':''}</p>
  <h3>6. Digital evidence index</h3>
  <p>Devices: ${devs.join(', ')||'none'}. Phones: ${c.ai.phones.join(', ')||'none'}. Reminder: prepare Section 63 BSA certificate for electronic records.</p>
  <h3>7. Suggested legal provisions (verify before use)</h3>
  <ul><li>BNS 318 (cheating), BNS 319 (cheating by personation), BNS 61 (criminal conspiracy)</li><li>IT Act 66C, 66D</li></ul>
  <h3>8. Recommended actions, in priority order</h3>
  <ol>
   <li>Request immediate freeze or lien on: ${freeze.map(n=>n.name+' ('+n.id+')').join('; ')}.</li>
   <li>Report on NCRP and 1930 helpline; share account list with I4C.</li>
   <li>Ask telecom provider for CDR and SIM KYC of ${c.ai.phones.join(', ')||'the calling numbers'}.</li>
   <li>Request bank KYC, login IPs and device data for all listed accounts.</li>
   <li>Check ${devs.filter(d=>c.nodes.filter(n=>n.devs.includes(d)).length>2).join(', ')||'shared devices'} for links to other complaints.</li>
   <li>Send evidence preservation notices to banks and platforms.</li>
  </ol>`;
  $('briefEmpty').hidden=true;$('briefBody').hidden=false;$('briefBtns').hidden=false;
}

function tab(t){
  document.querySelectorAll('section').forEach(s=>s.classList.toggle('on',s.id===t));
  document.querySelectorAll('nav button').forEach(b=>b.setAttribute('aria-selected',b.dataset.t===t));
  window.scrollTo(0,0);
}

document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>tab(b.dataset.t));

$('run').onclick=()=>{try{analyze();tab('graph')}catch(e){console.error(e);alert('Could not parse the inputs. Check the CSV columns and time format (HH:MM).')}};
$('reset').onclick=loadSample;
$('print').onclick=()=>window.print();

$('copy').onclick=async()=>{
  try{
    await navigator.clipboard.writeText($('briefBody').innerText);
    $('copy').textContent='Copied';
  }catch(e){
    $('copy').textContent='Copy failed';
  }
  setTimeout(()=>$('copy').textContent='Copy brief',1500);
};

// Safe initialization wait wrapper
document.addEventListener('DOMContentLoaded', () => {
  loadSample();
});
