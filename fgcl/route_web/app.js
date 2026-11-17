'use strict';
const $ = id => document.getElementById(id);
const fmt = (x, digits=1) => Number(x).toLocaleString('pt-BR',{maximumFractionDigits:digits});
const palette = ['#087c62','#dc843e','#6881c2','#b66c92','#a2a747','#5a9fbc','#a16a47','#8661ad','#cc5d56','#509667','#b39b38','#658383'];
const names = {nearest_neighbor:'Vizinho mais próximo',clarke_wright:'Clarke–Wright','nearest_neighbor+2opt':'Vizinho + 2-opt','clarke_wright+2opt':'Economias + 2-opt'};
let state = null, selected = null, visible = new Set(), onlyNodes = false, instanceText = '', solutionText = '';
let view = {scale:1,x:0,y:0}, playing = false, lastFrame = 0, drag = null, moved = false;
const svg = $('map');
const NS = 'http://www.w3.org/2000/svg';
function s(tag, attrs={}, parent=svg) {
  const node = document.createElementNS(NS,tag);
  Object.entries(attrs).forEach(([key,value]) => node.setAttribute(key,String(value)));
  parent.appendChild(node); return node;
}
function text(id, value) { $(id).textContent = value; }
function notify(value, error=false) { text('message',value); $('message').classList.toggle('error',error); }
function download(name, value, type) {
  const url = URL.createObjectURL(new Blob([value],{type}));
  const a = document.createElement('a'); a.href=url;a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function activeSolution() {
  if (state.solution.imported_solution && $('show-imported')?.checked) return state.solution.imported_solution;
  return state.solution;
}
function showReport() {
  const {instance:inst,solution:sol,provenance:record} = state;
  text('instance-name',inst.name);
  text('problem-badge',inst.windows?'VRPTW':'CVRP');
  text('instance-kind',record.config.source==='synthetic'?'SINTÉTICA / SEED '+record.seed:'ARQUIVO LOCAL');
  text('validity',sol.feasible?'✓ Viabilidade verificada · ótimo não provado':'! Candidato inviável');
  text('stat-customers',inst.demands.length-1);
  text('stat-bound','limite por capacidade: '+sol.capacity_lower_bound);
  text('stat-demand',fmt(inst.demands.reduce((a,b)=>a+b,0),0));
  text('stat-capacity','capacidade por veículo: '+fmt(inst.capacity));
  text('objective-label',sol.objective==='distance'?'distância total':'rotas → distância');
  $('baselines').replaceChildren();
  sol.baselines.forEach(candidate => {
    const card=document.createElement('article');
    card.className='baseline'+(candidate.method===sol.method?' selected':'');
    const method=document.createElement('div');method.className='method';
    method.textContent=names[candidate.method]||candidate.method;
    if(candidate.method===sol.method) {const mark=document.createElement('span');mark.className='winner';mark.textContent='ESCOLHIDO';method.appendChild(mark);}
    const value=document.createElement('strong');value.textContent=fmt(candidate.cost);
    const detail=document.createElement('small');detail.textContent=candidate.route_count+' rotas · '+(candidate.feasible?'viável':'inviável');
    card.append(method,value,detail);$('baselines').appendChild(card);
  });
  const imported=sol.imported_solution;
  $('imported-report').hidden=!imported;
  $('imported-report').replaceChildren();
  if(imported) {
    const title=document.createElement('b');title.textContent='Solução importada: '+(imported.feasible?'viável':'não viável');
    const details=document.createElement('div');
    details.textContent=imported.route_count+' rotas · distância recalculada '+fmt(imported.cost)+
      (imported.violations.length?' · '+imported.violations.join(' '):' · ótimo não certificado');
    $('imported-report').append(title,details);
    if(imported.feasible) {
      const label=document.createElement('label');label.className='check';
      const check=document.createElement('input');check.type='checkbox';check.id='show-imported';
      check.onchange=()=>{selected=null;visible=new Set(activeSolution().routes.map((_,i)=>i));drawTable();draw();updateMetrics();};
      label.append(check,document.createTextNode('Exibir a solução importada no mapa'));
      $('imported-report').appendChild(label);
    }
  }
  const info={instance:inst.name,objective:sol.objective,distance:inst.distance,method:sol.method,
    status:sol.status,optimality_proven:false,available_vehicles:inst.vehicles,
    seed:record.seed,config:record.config,versions:record.versions,hardware:record.hardware,
    elapsed_seconds:record.elapsed_seconds,input_sha256:record.input_sha256,sources:record.sources};
  text('provenance',JSON.stringify(info,null,2));
  const first=sol.routes[0], a=inst.coordinates[0], b=inst.coordinates[first.nodes[1]];
  const raw=Math.hypot(a[0]-b[0],a[1]-b[1]);
  text('distance-example','Exemplo 0 → '+inst.ids[first.nodes[1]]+': distância real = '+fmt(raw,4)+
    '; custo usado = '+fmt(inst.distance==='EUC_2D'?Math.floor(raw+.5):raw,4)+'.');
  text('capacity-example','Rota 1: '+first.customers+' clientes, carga '+fmt(first.load)+
    ' ≤ '+fmt(inst.capacity)+'; custo '+fmt(first.cost)+'.');
  const visit=first.visits[1];
  text('time-example','Primeira visita: chegada '+fmt(visit.arrival)+', início '+fmt(visit.start)+
    ', espera '+fmt(visit.waiting)+', saída '+fmt(visit.departure)+'.');
  $('export-report').disabled=false;
  updateMetrics();drawTable();draw();
}
function updateMetrics() {
  if(!state)return;
  const sol=activeSolution();
  for(const [id,key] of [['stat-routes','route_count'],['stat-cost','cost'],['stat-waiting','waiting'],['stat-duration','duration']])text(id,fmt(sol[key]));
  text('validity',sol.feasible?'✓ Viabilidade verificada · ótimo não provado':'! Candidato inviável');
}
function drawTable() {
  const routes=activeSolution().routes;
  $('route-table').replaceChildren();
  routes.forEach((route,index)=>{
    const tr=document.createElement('tr');
    if(selected===index)tr.className='selected';
    tr.tabIndex=0;tr.setAttribute('aria-label','Selecionar rota '+(index+1));
    const first=document.createElement('td');
    const check=document.createElement('input');check.type='checkbox';check.checked=visible.has(index);
    check.setAttribute('aria-label','Exibir rota '+(index+1));
    check.onclick=event=>event.stopPropagation();
    check.onchange=()=>{check.checked?visible.add(index):visible.delete(index);draw();};
    const color=document.createElement('span');color.className='swatch';color.style.background=palette[index%palette.length];
    first.append(check,color,document.createTextNode('Rota '+(index+1)));tr.append(first);
    for(const key of ['customers','load','departure','return','waiting','duration','cost']) {
      const td=document.createElement('td');td.textContent=fmt(route[key]);tr.appendChild(td);
    }
    tr.onclick=()=>chooseRoute(index);tr.onkeydown=e=>{if(e.key==='Enter')chooseRoute(index);};
    $('route-table').appendChild(tr);
  });
  routeDetail();
}
function chooseRoute(index) { selected=selected===index?null:index;drawTable();draw(); }
function routeDetail() {
  const panel=$('route-detail');panel.hidden=selected===null;
  if(selected===null)return;
  const route=activeSolution().routes[selected],inst=state.instance;
  panel.replaceChildren();
  const title=document.createElement('h3');title.textContent='Rota '+(selected+1)+' · visitas e horários';
  const path=document.createElement('div');path.textContent=route.nodes.map(i=>inst.ids[i]).join(' → ');
  const diag=document.createElement('div');
  diag.textContent=route.spectral?'FGCL / MSE de coordenadas: '+fmt(route.spectral.coordinate_mse,4)+
    ' · energia residual relativa: '+fmt(100*route.spectral.residual_energy_ratio,2)+'% · diagnóstico sem efeito no custo.':'';
  const table=document.createElement('table');
  const head=document.createElement('tr');
  ['Nó (ID original)','Chegada','Início','Saída','Espera','Carga'].forEach(label=>{const th=document.createElement('th');th.textContent=label;head.append(th);});
  table.append(head);
  route.visits.forEach(visit=>{
    const tr=document.createElement('tr');
    [inst.ids[visit.node],...['arrival','start','departure','waiting','load'].map(k=>fmt(visit[k]))].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});
    table.append(tr);
  });
  panel.append(title,path,diag,table);
}
function projection() {
  const xy=state.instance.coordinates;
  const xs=xy.map(p=>p[0]),ys=xy.map(p=>p[1]);
  const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const factor=Math.min(850/Math.max(xmax-xmin,1),380/Math.max(ymax-ymin,1));
  const cx=(xmin+xmax)/2,cy=(ymin+ymax)/2;
  return p=>[500+(p[0]-cx)*factor,250-(p[1]-cy)*factor];
}
function draw() {
  if(!state)return;
  svg.replaceChildren();
  const defs=s('defs');
  const grid=s('pattern',{id:'grid',width:32,height:32,patternUnits:'userSpaceOnUse'},defs);
  s('path',{d:'M 32 0 L 0 0 0 32',fill:'none',stroke:'#edf2eb','stroke-width':.7},grid);
  s('rect',{width:1000,height:520,fill:'url(#grid)'});
  const group=s('g',{transform:'translate('+view.x+' '+view.y+') scale('+view.scale+')'});
  const project=projection(),inst=state.instance,sol=activeSolution();
  const time=Math.max(...sol.routes.map(r=>r.return))*Number($('timeline').value)/1000;
  text('time-value',fmt(time,1)+' u.t.');
  const owners=new Map();
  sol.routes.forEach((route,index)=>route.nodes.slice(1,-1).forEach(node=>owners.set(node,index)));
  sol.routes.forEach((route,index)=>{
    if(!visible.has(index)||onlyNodes)return;
    const color=palette[index%palette.length],opacity=selected!==null&&selected!==index?.15:.85;
    const marker=s('marker',{id:'arrow'+index,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'},defs);
    s('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:color},marker);
    route.nodes.slice(1).forEach((node,k)=>{
      const previous=route.nodes[k], depot=previous===0||node===0;
      if(depot&&$('depot-edges').value==='none')return;
      const from=project(inst.coordinates[previous]),to=project(inst.coordinates[node]);
      const attrs={x1:from[0],y1:from[1],x2:to[0],y2:to[1],stroke:color,
        'stroke-width':selected===index?2.8:1.5,
        opacity:depot&&$('depot-edges').value==='light'?opacity*.3:opacity,
        'vector-effect':'non-scaling-stroke'};
      if(depot&&$('depot-edges').value==='light')attrs['stroke-dasharray']='4 4';
      if($('arrows').checked)attrs['marker-end']='url(#arrow'+index+')';
      const line=s('line',attrs,group);line.addEventListener('click',()=>chooseRoute(index));
    });
    if($('spectral').checked&&route.spectral) {
      const points=route.spectral.smooth_coordinates.map(p=>project(p).join(',')).join(' ');
      s('polyline',{points,fill:'none',stroke:color,'stroke-width':2,'stroke-dasharray':'2 5',opacity:.6,'vector-effect':'non-scaling-stroke'},group);
    }
    if(time>=route.departure&&time<route.return) {
      let point=inst.coordinates[0];
      for(let k=1;k<route.visits.length;k++) {
        const a=route.visits[k-1],b=route.visits[k];
        if(time>=a.departure&&time<b.arrival) {
          const fraction=(time-a.departure)/Math.max(b.arrival-a.departure,1e-12);
          point=inst.coordinates[a.node].map((x,j)=>x+(inst.coordinates[b.node][j]-x)*fraction);break;
        }
        if(time>=b.arrival&&time<=b.departure){point=inst.coordinates[b.node];break;}
      }
      const p=project(point);s('circle',{cx:p[0],cy:p[1],r:6/view.scale,fill:color,stroke:'white','stroke-width':2/view.scale},group);
    }
  });
  inst.coordinates.forEach((xy,node)=>{
    const route=owners.get(node);
    if(node&& !visible.has(route)&&!onlyNodes)return;
    const p=project(xy),faded=selected!==null&&route!==selected&&node!==0;
    const shape=node===0?s('rect',{x:p[0]-7,y:p[1]-7,width:14,height:14,rx:2,transform:'rotate(45 '+p[0]+' '+p[1]+')',fill:'#16332e',stroke:'white','stroke-width':2},group):
      s('circle',{cx:p[0],cy:p[1],r:inst.coordinates.length>400?2.3:3.4,fill:onlyNodes?'#789487':palette[route%palette.length],stroke:'white','stroke-width':.8,opacity:faded?.3:1},group);
    shape.style.cursor='pointer';
    shape.addEventListener('click',()=>{if(route!==undefined)chooseRoute(route);});
    shape.addEventListener('pointermove',event=>{
      const rect=svg.parentElement.getBoundingClientRect(),tip=$('tooltip');
      tip.textContent=(node?'Cliente ':'Depósito ')+inst.ids[node]+' · demanda '+fmt(inst.demands[node])+
        ' · ('+fmt(xy[0])+', '+fmt(xy[1])+')'+(inst.windows?' · janela ['+inst.windows[node].map(v=>fmt(v)).join(', ')+']':'');
      tip.hidden=false;tip.style.left=Math.min(event.clientX-rect.left+12,rect.width-225)+'px';tip.style.top=Math.max(5,event.clientY-rect.top-65)+'px';
    });
    shape.addEventListener('pointerleave',()=>{$('tooltip').hidden=true;});
    if(!node){const label=s('text',{x:p[0]+13,y:p[1]+4,fill:'#16332e','font-size':11,'font-family':'Segoe UI,Arial','font-weight':600},group);label.textContent='DEPÓSITO';}
  });
  $('spectral-note').hidden=!$('spectral').checked;
}
async function execute(event) {
  event?.preventDefault();if(!instanceText&&!$('settings').reportValidity())return;
  stopAnimation();$('solve').disabled=true;notify('Calculando candidatos e verificando capacidade, cobertura e horários…');
  try {
    const payload={problem:$('problem').value,distribution:$('distribution').value,
      customers:Number($('customers').value),capacity:Number($('capacity').value),
      seed:Number($('seed').value),improve:$('improve').checked,
      instance_text:instanceText,solution_text:solutionText,numbering:$('numbering').value};
    const response=await fetch('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const result=await response.json();if(!response.ok)throw new Error(result.error||'Erro no servidor.');
    state=result;selected=null;visible=new Set(state.solution.routes.map((_,i)=>i));
    $('timeline').value=1000;view={scale:1,x:0,y:0};
    onlyNodes=false;$('all-routes').classList.add('active');$('instance-only').classList.remove('active');
    showReport();
    notify((state.solution.feasible?'Solução heurística viável':'Nenhum candidato viável')+
      ' · '+(names[state.solution.method]||state.solution.method)+' · '+fmt(state.provenance.elapsed_seconds,3)+' s · Sem prova de ótimo.'+
      (state.solution.violations.length?' '+state.solution.violations.join(' '):''),!state.solution.feasible);
  } catch(error) {notify(error.message,true);} finally {$('solve').disabled=false;}
}
$('settings').addEventListener('submit',execute);
for(const [id,key,label] of [['instance-file','instanceText','filename'],['solution-file','solutionText','solution-name']]) {
  $(id).addEventListener('change',async event=>{
    const file=event.target.files[0];if(!file)return;
    if(file.size>2_000_000){notify('Arquivo deve ter no máximo 2 MB.',true);event.target.value='';return;}
    const value=await file.text();
    if(key==='instanceText')instanceText=value;else solutionText=value;
    text(label,file.name);$(key==='instanceText'?'reset-file':'reset-solution').hidden=false;
    notify('Arquivo carregado. Clique em Gerar e resolver para recalcular.');
  });
}
$('reset-file').onclick=()=>{instanceText='';$('instance-file').value='';text('filename','Nenhum arquivo selecionado');$('reset-file').hidden=true;};
$('reset-solution').onclick=()=>{solutionText='';$('solution-file').value='';text('solution-name','Comparação opcional');$('reset-solution').hidden=true;};
document.querySelectorAll('[data-tab]').forEach(button=>button.onclick=()=>{
  document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b===button));
  document.querySelectorAll('.tab-content').forEach(section=>section.hidden=section.id!=='tab-'+button.dataset.tab);
});
for(const id of ['arrows','spectral','depot-edges'])$(id).onchange=draw;
$('all-routes').onclick=()=>{if(!state)return;onlyNodes=false;visible=new Set(activeSolution().routes.map((_,i)=>i));$('all-routes').classList.add('active');$('instance-only').classList.remove('active');drawTable();draw();};
$('instance-only').onclick=()=>{onlyNodes=true;$('all-routes').classList.remove('active');$('instance-only').classList.add('active');draw();};
$('fit').onclick=()=>{view={scale:1,x:0,y:0};draw();};
$('clear-selection').onclick=()=>{selected=null;drawTable();draw();};
$('timeline').oninput=()=>{stopAnimation();draw();};
function stopAnimation(){playing=false;text('play','▶');}
function frame(timestamp){
  if(!playing||!state)return;
  if(timestamp-lastFrame>60){
    $('timeline').value=Math.min(1000,Number($('timeline').value)+8);
    draw();lastFrame=timestamp;if(Number($('timeline').value)>=1000){stopAnimation();return;}
  }
  requestAnimationFrame(frame);
}
$('play').onclick=()=>{if(!state)return;if(playing){stopAnimation();return;}if(Number($('timeline').value)>=1000)$('timeline').value=0;playing=true;text('play','Ⅱ');requestAnimationFrame(frame);};
svg.addEventListener('wheel',event=>{
  event.preventDefault();const rect=svg.getBoundingClientRect();
  const x=(event.clientX-rect.left)*1000/rect.width,y=(event.clientY-rect.top)*520/rect.height;
  const next=Math.max(.5,Math.min(8,view.scale*(event.deltaY<0?1.12:1/1.12))),ratio=next/view.scale;
  view.x=x-(x-view.x)*ratio;view.y=y-(y-view.y)*ratio;view.scale=next;draw();
},{passive:false});
svg.addEventListener('pointerdown',event=>{if(event.target===svg||event.target.tagName==='rect'&&event.target.getAttribute('fill')==='url(#grid)'){drag={x:event.clientX,y:event.clientY,vx:view.x,vy:view.y};svg.setPointerCapture(event.pointerId);}});
svg.addEventListener('pointermove',event=>{if(!drag)return;const rect=svg.getBoundingClientRect();view.x=drag.vx+(event.clientX-drag.x)*1000/rect.width;view.y=drag.vy+(event.clientY-drag.y)*520/rect.height;draw();});
svg.addEventListener('pointerup',()=>{drag=null;});
$('export-report').onclick=()=>{if(state)download('fgcl-routing-report.json',JSON.stringify(state,null,2),'application/json');};
$('export-svg').onclick=()=>{if(state){const copy=svg.cloneNode(true);copy.setAttribute('xmlns',NS);download('fgcl-routes.svg',new XMLSerializer().serializeToString(copy),'image/svg+xml');}};
$('export-instance').onclick=()=>{if(state)download('fgcl-instance.json',JSON.stringify(state.instance,null,2),'application/json');};
$('export-solution').onclick=()=>{
  if(!state)return;const sol=activeSolution();
  if(!sol.feasible){notify('Exportação .sol requer candidato viável.',true);return;}
  const lines=sol.routes.map((r,i)=>'Route #'+(i+1)+': '+r.nodes.slice(1,-1).join(' '));
  lines.push('Cost '+sol.cost);download('fgcl-internal-indices.sol',lines.join('\n'),'text/plain');
};
$('export-csv').onclick=()=>{
  if(!state)return;const columns=['route','customers','load','departure','return','waiting','duration','cost'];
  const lines=[columns.join(',')];
  activeSolution().routes.forEach((r,i)=>lines.push([i+1,...columns.slice(1).map(k=>r[k])].join(',')));
  download('fgcl-routes.csv',lines.join('\n'),'text/csv');
};
execute();

