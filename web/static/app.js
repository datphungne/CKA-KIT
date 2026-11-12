'use strict';
const TITLES = ['Core Objects','Workloads & Scheduling','Services & Networking','Persistent Storage','Cluster Architecture','Cluster Maintenance','App Troubleshooting','Cluster Recovery','Speed Challenge','Mock Exam I','Advanced Recovery','Mock Exam II','Final Speed Drills','Final Mock Exam'];
const state = { day:1, leftTab:'tasks', resourceTab:'pods', resources:null, status:null, markdown:'', socket:null, term:null, fit:null, jobId:null, jobTimer:null, checks:{}, fallback:false, statusBusy:false, resourcesBusy:false, selection:0, jobDay:null };
const $ = id => document.getElementById(id);
const escapeHTML = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const timeout = ms => new Promise(resolve => setTimeout(resolve,ms));
async function request(url, opts){ const r = await fetch(url, opts); let json; try{json=await r.json()}catch{json={detail:`HTTP ${r.status}`}} if(!r.ok) throw new Error(json.detail||`HTTP ${r.status}`); return json; }
function toast(message, error=false){const e=document.createElement('div');e.className=`toast ${error?'error':''}`;e.textContent=message;$('toastArea').append(e);setTimeout(()=>e.remove(),4500)}
function linkify(s){return escapeHTML(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');}
function formatTask(s){const lines=s.split('\n');let insideCode=false,html='';for(const line of lines){if(line.startsWith('```')){html+=insideCode?'</code></pre>':'<pre><code>';insideCode=!insideCode;continue}if(insideCode){html+=escapeHTML(line)+'\n';continue}if(/^\s*$/.test(line))continue;if(line.startsWith('**Pass when:**')){html+=`<p><span class="verify-label">✓ PASS WHEN</span> ${linkify(line.slice(14))}</p>`;continue}if(line.startsWith('**Check yourself:**')){html+='<p class="verify-label">SELF-CHECK</p>';continue}if(line.startsWith('**Your mission:**')){html+=`<p>${linkify(line.slice(17))}</p>`;continue}html+=`<p>${linkify(line.replace(/^[-*] /,''))}</p>`}return html}
function tasksFromMarkdown(md){const parts=md.split(/(?=^## Exercise\s+\d{2}\.\d+\s+—\s+)/m).slice(1);return parts.map((part,i)=>{const lines=part.split('\n');const titleLine=lines.shift();const m=titleLine.match(/## Exercise\s+(\d{2}\.\d+)\s+—\s+(.+?)(?:\s+\((\d+) min\))?\s*$/);let body=lines.join('\n').split(/^## /m)[0];return {id:m?.[1]||`${state.day}.${i+1}`,title:m?.[2]||'Exercise',min:m?.[3]||'',body}})}
function renderDayNav(){const nav=$('dayList');nav.innerHTML=TITLES.map((title,i)=>{const day=i+1,check=state.checks[day]||{},passed=Object.values(check).filter(x=>x==='PASS').length;return `<button class="day ${state.day===day?'active':''}" data-day="${day}"><span class="day-number">${String(day).padStart(2,'0')}</span><span class="day-name">${escapeHTML(title)}</span>${passed===5?'<span class="day-check">✓</span>':''}</button>`}).join('');nav.querySelectorAll('[data-day]').forEach(btn=>btn.addEventListener('click',()=>selectDay(Number(btn.dataset.day))))}
function renderTasks(){const list=tasksFromMarkdown(state.markdown), checks=state.checks[state.day]||{}; if(!list.length){$('taskList').innerHTML='<div class="empty-message">No tasks found for this day.</div>';return} $('taskList').innerHTML=list.map((task,i)=>{const result=checks[i+1];return `<article class="task ${result==='PASS'?'complete':''}"><div class="task-head"><span class="task-id">${escapeHTML(task.id)}</span><div class="task-name">${escapeHTML(task.title)}</div>${result?`<span class="task-result ${result.toLowerCase()}">${result}</span>`:`<span class="task-time">${task.min?'◷ '+task.min+'m':''}</span>`}</div><div class="task-details">${formatTask(task.body)}</div></article>`}).join('');renderProgress()}
function renderProgress(){const results=state.checks[state.day]||{}, passed=Object.values(results).filter(x=>x==='PASS').length, manual=Object.values(results).filter(x=>x==='MANUAL').length;$('metricProgress').innerHTML=`${passed}<span class="metric-suffix">/ 5</span>`;$('metricProgressDesc').textContent=manual?`${manual} admin task(s) require manual review`:'Auto-graded tasks';}
function setConnected(ready,exists){$('sidebarDot').className='dot '+(ready?'ok':'bad');$('topDot').className='live-dot '+(ready?'ok':'bad');$('sidebarState').textContent=ready?'kind-cka-14d is online':'Cluster offline';$('connectionText').textContent=ready?'kind-cka-14d · Ready':(exists?'kind-cka-14d · Offline':'No cluster');$('metricCluster').textContent=ready?'Healthy':(exists?'Offline':'Not Created');$('metricCluster').className='metric-value '+(ready?'status-good':'status-bad');$('metricClusterDesc').textContent=ready?'API server responding':exists?'Check Docker / kind':'Create a cluster to begin';$('setupBtn').textContent=exists?'↻ Prepare Lab':'＋ Create Cluster';}
async function refreshStatus(){
  if(state.statusBusy)return;state.statusBusy=true;
  try{
    const s=await request('/api/status');state.status=s;setConnected(s.ready,s.clusterExists);
    if(s.ready&&s.readyNodes<s.nodes){$('metricCluster').textContent='Degraded';$('metricCluster').className='metric-value status-warn';$('metricClusterDesc').textContent=`API up · ${s.nodes-s.readyNodes} node(s) NotReady`;}
    $('metricNodes').textContent=s.ready?s.readyNodes+'/'+s.nodes:'—';
    $('metricNodesDesc').textContent=s.ready?'Kubernetes nodes Ready':'1 control plane · 2 workers';
    $('setupBtn').disabled=!!state.jobId;
    $('setupBtn').textContent=s.clusterExists?'Start Lab':'Create cluster & start';
    $('verifyBtn').disabled=!s.ready||!!state.jobId;
    $('cleanupBtn').disabled=!s.ready||!!state.jobId;
    $('resetBtn').disabled=!s.ready||!!state.jobId;
    const notice=$('workspaceNotice');notice.classList.toggle('error',!!s.error);
    notice.textContent=s.error||(!s.clusterExists?'Welcome to your local workspace. Select a day and start the lab. First launch creates a three-node Kubernetes cluster.':!s.ready?'Cluster is starting. Watch the action log for progress.':state.resources?.connected?'Workspace ready. Solve the five exercises in the terminal, then verify your work.':'Cluster ready. Start this day to seed its exercise resources.');
    if(!s.ready && state.socket){state.socket.close();state.socket=null;}
    return s;
  }catch(e){state.status=null;setConnected(false,false);$('workspaceNotice').textContent='Console connection lost. Check that docker compose is running.';$('workspaceNotice').classList.add('error');}
  finally{state.statusBusy=false;}
}
async function refreshResources(){
  const day=state.day,selection=state.selection;
  if(state.resourcesBusy)return;state.resourcesBusy=true;
  try{
    const r=await request(`/api/resources/${day}`);if(selection!==state.selection)return;
    state.resources=r;
    const count=r.pods.filter(p=>p.status==='Running'&&p.ready.split('/')[0]===p.ready.split('/')[1]).length;
    $('metricPods').textContent=r.connected?count+'/'+r.pods.length:'?';
    $('metricPodsDesc').textContent=r.connected?`Ready Pods in ${ns()}`:'Kubernetes data unavailable';
    $('resourceUpdated').textContent=r.connected?'Updated '+new Date().toLocaleTimeString():'Disconnected';
    if(state.leftTab==='resources')renderResourceTable();if(state.leftTab==='events')renderEvents();
  }catch(e){if(selection===state.selection){state.resources={connected:false,error:e.message,pods:[],events:[]};$('resourceUpdated').textContent='Refresh failed';}}
  finally{state.resourcesBusy=false;}
}
function ns(){return `cka-d${String(state.day).padStart(2,'0')}`}
function tableRow(cols){return `<tr>${cols.map(v=>`<td title="${escapeHTML(v)}">${escapeHTML(v)}</td>`).join('')}</tr>`}
function renderResourceTable(){if(!state.resources?.connected){$('resourceTable').innerHTML=`<div class="empty-message">${escapeHTML(state.resources?.error||'Waiting for Kubernetes. Start the lab to connect.')}</div>`;return}const list=state.resources?.[state.resourceTab]||[];let columns,rows;if(state.resourceTab==='pods'){columns=['Name','Status','Ready','Restarts','Node'];rows=list.map(v=>[v.name,v.status,v.ready,v.restarts,v.node])}else if(state.resourceTab==='deployments'){columns=['Name','Ready','Image'];rows=list.map(v=>[v.name,v.ready,v.image])}else if(state.resourceTab==='services'){columns=['Name','Type','Cluster IP','Ports'];rows=list.map(v=>[v.name,v.type,v.clusterIP,v.ports])}else{columns=['Node','Status','Role','Version'];rows=list.map(v=>[v.name,v.ready?'Ready':'NotReady',v.roles,v.version])}if(!rows.length){$('resourceTable').innerHTML='<div class="empty-message">No resources found. Prepare the lab first or use the terminal to create some.</div>';return}$('resourceTable').innerHTML=`<table class="res-table"><thead><tr>${columns.map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody>${rows.map(tableRow).join('')}</tbody></table>`}
function renderEvents(){if(!state.resources?.connected){$('eventList').innerHTML='<div class="empty-message">Events unavailable. Check the cluster connection.</div>';return}const ev=state.resources?.events||[];$('eventList').innerHTML=ev.length?ev.map(e=>`<article class="event"><div class="event-title"><span class="${e.type==='Warning'?'warn':''}">${escapeHTML(e.reason)}</span> · ${escapeHTML(e.name)}</div><div class="event-message">${escapeHTML(e.message)}</div><div class="event-foot">${escapeHTML(e.kind)} · ${escapeHTML(e.type)} · ${escapeHTML(e.time)}</div></article>`).join(''):'<div class="empty-message">No events in this namespace. Events will appear here as you work.</div>'}
function showTab(tab){state.leftTab=tab;document.querySelectorAll('[data-left-tab]').forEach(b=>b.classList.toggle('active',b.dataset.leftTab===tab));['tasks','resources','events'].forEach(t=>$(t+'Panel').classList.toggle('hidden',t!==tab));if(tab==='resources')renderResourceTable();if(tab==='events')renderEvents();}
async function selectDay(day){
  if(state.day===day && state.markdown)return;
  const selection=++state.selection;state.day=day;state.markdown='';state.resources=null;
  renderDayNav();$('breadcrumb').textContent=`DAY ${String(day).padStart(2,'0')}`;
  $('dayHeading').innerHTML=`Day ${String(day).padStart(2,'0')} <span class="dash">/</span> ${escapeHTML(TITLES[day-1])}`;
  $('daySubheading').textContent=[10,12,14].includes(day)?'120-minute mock examination. Admin sections require manual review.':'Select a day → Start the lab → Solve → Verify';
  $('namespaceLabel').textContent=`Namespace: ${ns()}`;$('terminalContext').textContent=`kind-cka-14d · ${ns()}`;
  $('taskList').innerHTML='<div class="empty-message">Loading exercises…</div>';$('metricPods').textContent='?';
  showTab('tasks');$('sidebar').classList.remove('open');
  if(state.socket){state.socket.onclose=null;state.socket.close();state.socket=null;}
  try{
    const dayData=await request(`/api/day/${day}`);if(selection!==state.selection)return;
    state.markdown=dayData.markdown;renderTasks();refreshResources();
    if(state.status?.ready)connectTerminal();else terminalOffline();
  }catch(e){if(selection===state.selection)toast(e.message,true)}
}
function showConfirm(title, description, callback){$('confirmTitle').textContent=title;$('confirmDescription').textContent=description;$('confirmModal').classList.remove('hidden');$('acceptConfirm').onclick=()=>{$('confirmModal').classList.add('hidden');callback()};$('acceptConfirm').textContent='Continue';$('cancelConfirm').focus();$('cancelConfirm').onclick=()=>{$('confirmModal').classList.add('hidden')}}
async function runAction(action,day=state.day,thenStart=false){
  if(state.jobId){toast('A lab action is already running.');return;}
  try{
    const req=await request('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,day})});
    state.jobId=req.id;state.jobDay=day;sessionStorage.setItem('cka-job',JSON.stringify({id:req.id,action,day,thenStart}));
    $('jobModal').classList.remove('hidden');$('jobTitle').textContent=({'create-cluster':'Creating Kubernetes cluster','setup':`Starting Day ${day}`,'verify':`Checking Day ${day}`,'cleanup':`Cleaning Day ${day}`,'doctor':'Diagnosing environment'})[action];
    $('jobOutput').textContent='';$('jobDone').disabled=true;$('jobState').textContent='Running…';
    refreshStatus();pollJob(req.id,action,day,thenStart);
  }catch(e){toast(e.message,true)}
}
async function pollJob(id,action,day,thenStart=false){
  try{
    const job=await request(`/api/job/${id}`);if(state.jobId!==id)return;
    const e=$('jobOutput'),nearEnd=e.scrollTop+e.clientHeight>=e.scrollHeight-65;
    e.textContent=job.output||'Preparing…';if(nearEnd)e.scrollTop=e.scrollHeight;
    if(job.state!=='finished'){state.jobTimer=setTimeout(()=>pollJob(id,action,day,thenStart),900);return;}
    state.jobId=null;sessionStorage.removeItem('cka-job');$('jobDone').disabled=false;
    const graded=action==='verify' && /Summary:/.test(job.output);
    $('jobState').textContent=graded?'Verification finished — review task results':job.code===0?'✓ Completed successfully':`Failed (exit ${job.code})`;
    $('jobState').style.color=job.code===0||graded?'#5cdaa8':'#ff9292';
    if(action==='verify'){
      const results={};for(const line of job.output.split('\n')){const m=line.match(/\[(PASS|FAIL|MANUAL)\]\s+(\d{2})\.(\d+)/);if(m&&Number(m[2])===day)results[Number(m[3])]=m[1]}
      if(Object.keys(results).length)state.checks[day]=results;
    }
    if(['setup','cleanup'].includes(action)){delete state.checks[day];}
    try{localStorage.setItem('cka-checks',JSON.stringify(state.checks));}catch{}
    renderTasks();renderDayNav();await refreshStatus();await refreshResources();
    if(action==='create-cluster'&&job.code===0&&thenStart){runAction('setup',day);return;}
    if(job.code===0&&state.day===day&&['setup','create-cluster'].includes(action))connectTerminal();
  }catch(e){state.jobTimer=setTimeout(()=>pollJob(id,action,day,thenStart),3000);$('jobState').textContent='Connection interrupted — retrying…';$('jobDone').disabled=false;}
}
function terminalOffline(){if(state.term){state.term.dispose();state.term=null}$('terminal').textContent='Start the lab to open your interactive Kubernetes terminal.';$('terminalState').textContent='DISCONNECTED';}
function connectTerminal(){if(!state.status?.ready){terminalOffline();return;}if(state.socket){state.socket.onclose=null;state.socket.close();state.socket=null}if(state.term){state.term.dispose();state.term=null}$('terminalState').textContent='CONNECTING';const terminalEl=$('terminal');terminalEl.innerHTML='';const fallback=$('fallback');const hasXterm=window.Terminal && window.FitAddon?.FitAddon;state.fallback=!hasXterm;fallback.classList.toggle('hidden',hasXterm);terminalEl.classList.toggle('hidden',!hasXterm);if(hasXterm){state.term=new window.Terminal({cursorBlink:true,fontFamily:'JetBrains Mono, monospace',fontSize:12,lineHeight:1.45,theme:{background:'#07111f',foreground:'#cbdcf6',cursor:'#72adfa',selectionBackground:'#355a8c',black:'#10182a',red:'#f17e90',green:'#62d5a3',yellow:'#dbbf78',blue:'#7eaefc',magenta:'#bca9ff',cyan:'#59d4e7',white:'#e6eefc'}});state.fit=new window.FitAddon.FitAddon();state.term.loadAddon(state.fit);state.term.open(terminalEl);state.fit.fit();state.term.writeln('\x1b[36mConnecting to real Kubernetes terminal...\x1b[0m');state.term.onData(data=>{if(state.socket?.readyState===1)state.socket.send(JSON.stringify({type:'input',data}))})}else{$('fallbackOutput').textContent='Connecting to real Kubernetes terminal...\n'}const protocol=location.protocol==='https:'?'wss':'ws';const sock=new WebSocket(`${protocol}://${location.host}/ws/terminal/${state.day}`);state.socket=sock;sock.onopen=()=>{$('terminalState').textContent='CONNECTED';if(state.term){state.fit.fit();sock.send(JSON.stringify({type:'resize',cols:state.term.cols,rows:state.term.rows}))}};sock.onmessage=e=>{if(state.term)state.term.write(e.data);else{const out=$('fallbackOutput');out.textContent+=e.data;out.scrollTop=out.scrollHeight}};sock.onclose=()=>{$('terminalState').textContent='DISCONNECTED';if(state.socket===sock)state.socket=null;if(state.term)state.term.writeln('\r\n\x1b[33m[Disconnected — use ↻ to reconnect]\x1b[0m\r\n');else $('fallbackOutput').textContent+='\n[Disconnected]\n'};sock.onerror=()=>{if(state.term)state.term.writeln('\r\n\x1b[31mWebSocket error. Check app server logs.\x1b[0m');};}
function typeCommand(cmd){const data=cmd.replaceAll('\\n','\n');if(state.socket?.readyState!==1){toast('Terminal not connected. Create cluster or retry.',true);return}state.socket.send(JSON.stringify({type:'input',data}));state.term?.focus();}
function registerEvents(){renderDayNav();document.querySelectorAll('[data-left-tab]').forEach(el=>el.addEventListener('click',()=>showTab(el.dataset.leftTab)));document.querySelectorAll('[data-resource]').forEach(el=>el.addEventListener('click',()=>{state.resourceTab=el.dataset.resource;document.querySelectorAll('[data-resource]').forEach(b=>b.classList.toggle('active',b===el));renderResourceTable()}));$('setupBtn').onclick=()=>{if(!state.status){toast('Waiting for console status.',true);return}if(!state.status.clusterExists)runAction('create-cluster',state.day,true);else showConfirm(`Start Day ${state.day}?`,`This seeds ${ns()}. If you already started this day, its resources will be reset. Other days and answer files are preserved.`,()=>runAction('setup'))};$('cleanupBtn').onclick=()=>showConfirm(`Clean up Day ${state.day}?`,`Delete namespace ${ns()} and restore lab scheduling state. Answer files are preserved.`,()=>runAction('cleanup'));$('doctorBtn').onclick=()=>runAction('doctor');$('verifyBtn').onclick=()=>runAction('verify');$('resetBtn').onclick=()=>showConfirm(`Reset Day ${state.day}?`,`This erases resources in namespace ${ns()} and prepares the lab again.`,()=>runAction('setup'));$('refreshResources').onclick=refreshResources;$('refreshEvents').onclick=refreshResources;$('restartTerminal').onclick=connectTerminal;$('clearTerminal').onclick=()=>{if(state.term)state.term.clear();else $('fallbackOutput').textContent=''};$('closeJob').onclick=()=>{$('jobModal').classList.add('hidden')};$('jobDone').onclick=()=>{$('jobModal').classList.add('hidden')};$('fallbackCommand').addEventListener('keydown',e=>{if(e.key==='Enter'){typeCommand(e.target.value+'\n');e.target.value=''}});document.querySelectorAll('[data-cmd]').forEach(el=>el.addEventListener('click',()=>typeCommand(el.dataset.cmd)));$('menuButton').onclick=()=>$('sidebar').classList.toggle('open');$('navOverview').onclick=()=>selectDay(1);window.addEventListener('resize',()=>{if(state.term&&state.fit){state.fit.fit();if(state.socket?.readyState===1)state.socket.send(JSON.stringify({type:'resize',cols:state.term.cols,rows:state.term.rows}))}});}
async function main(){
  try{state.checks=JSON.parse(localStorage.getItem('cka-checks')||'{}')}catch{state.checks={}}
  registerEvents();await refreshStatus();await selectDay(1);
  try{const job=JSON.parse(sessionStorage.getItem('cka-job')||'null');if(job){state.jobId=job.id;$('jobModal').classList.remove('hidden');pollJob(job.id,job.action,job.day,job.thenStart);}}catch{}
  new ResizeObserver(()=>{if(state.term&&state.fit){state.fit.fit();if(state.socket?.readyState===1)state.socket.send(JSON.stringify({type:'resize',cols:state.term.cols,rows:state.term.rows}));}}).observe($('terminal'));
  setInterval(()=>{if(document.visibilityState==='visible'){refreshStatus();refreshResources()}},5000);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('confirmModal').classList.add('hidden');$('jobModal').classList.add('hidden');}});
}
document.addEventListener('DOMContentLoaded',main);
