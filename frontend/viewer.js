import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const PLATE_WORLD_HEIGHT=1/2.5;const noticeMode=new URLSearchParams(window.location.search).get('notice');const noticeMatch=/^step-(\d{4})$/.exec(noticeMode??'');const noticeStepNumber=noticeMatch?Number(noticeMatch[1]):null;const noticePrototypeMode=noticeStepNumber!==null&&noticeStepNumber>=1&&noticeStepNumber<=34;const canvas=document.querySelector('#viewer'),messageEl=document.querySelector('#message'),summaryEl=document.querySelector('#model-summary'),fileInput=document.querySelector('#file-input'),resetButton=document.querySelector('#reset-view'),frontButton=document.querySelector('#view-front'),rearButton=document.querySelector('#view-rear'),leftButton=document.querySelector('#view-left'),rightButton=document.querySelector('#view-right'),sampleButton=document.querySelector('#load-sample'),downloadBomButton=document.querySelector('#download-bom'),fidelityCard=document.querySelector('#fidelity-card'),fidelityList=document.querySelector('#fidelity-list'),assemblyCard=document.querySelector('#assembly-card'),assemblyTitle=document.querySelector('#assembly-title'),assemblyProgress=document.querySelector('#assembly-progress'),assemblyRange=document.querySelector('#assembly-range'),assemblyPrev=document.querySelector('#assembly-prev'),assemblyNext=document.querySelector('#assembly-next'),assemblyFull=document.querySelector('#assembly-full');
const scene=new THREE.Scene();scene.background=new THREE.Color(0x101827);const camera=new THREE.PerspectiveCamera(45,1,.1,1000);const renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;controls.screenSpacePanning=true;scene.add(new THREE.HemisphereLight(0xdcecff,0x20283a,2.35));const keyLight=new THREE.DirectionalLight(0xfff4df,3.1);keyLight.position.set(18,28,16);keyLight.castShadow=true;scene.add(keyLight);const fillLight=new THREE.DirectionalLight(0x9ec5ff,.75);fillLight.position.set(-14,10,-18);scene.add(fillLight);const ground=new THREE.GridHelper(80,80,0x53627c,0x27344b);ground.position.y=-.01;scene.add(ground);const modelGroup=new THREE.Group();modelGroup.scale.z=-1;scene.add(modelGroup);
const exteriorCategories=['timber','concrete','masonry','stone','metal','composite'];const palette={brick:0xd8c7a4,facade_detail:0xf2eee5,window_frame:0xf2eee5,window_pane:0x91c7e8,roof_tile:0x565b61,ridge_tile:0x565b61,timber:0xa87845,concrete:0xb8b8b2,masonry:0xd4d0c5,stone:0x96938b,metal:0x8b9299,composite:0x8d8175,terrain:0x72777b};const namedColors={off_white:0xe8e5dc,white:0xf3f3ef,cream:0xe4d7b5,beige:0xcbb991,gray:0x777b7e,grey:0x777b7e,dark_gray:0x4d5257,dark_grey:0x4d5257,black:0x24272b,dark_brown:0x49382e,brown:0x77543d,red:0xa94b42,terracotta:0xa85b46};const materials=Object.fromEntries(Object.entries(palette).map(([k,c])=>[k,new THREE.MeshStandardMaterial({color:c,roughness:k==='window_pane'?.18:k==='timber'?.58:k==='metal'?.28:.48,metalness:k==='metal'?.55:0,transparent:k==='window_pane',opacity:k==='window_pane'?.58:1})]));const fadedMaterials=Object.fromEntries(Object.entries(palette).map(([k,c])=>[k,new THREE.MeshStandardMaterial({color:c,roughness:.62,transparent:true,opacity:.32,depthWrite:false})]));const noticeOutlineMaterial=new THREE.LineBasicMaterial({color:0x2563eb,linewidth:1});
const highlightMaterials=Object.fromEntries(Object.entries(palette).map(([k,c])=>[k,new THREE.MeshStandardMaterial({color:c,roughness:.34,emissive:c,emissiveIntensity:.18})]));const noticeActionMaterial=new THREE.MeshStandardMaterial({color:0xf59e0b,roughness:.28,emissive:0xf59e0b,emissiveIntensity:.34});const semanticMaterials=new Map();const edgeMaterial=new THREE.LineBasicMaterial({color:0x171b24,transparent:true,opacity:.30});const studGeometry=new THREE.CylinderGeometry(.30,.30,.15,14);const studDetailEnabled=!window.matchMedia('(max-width: 760px)').matches;let studMeshBudgetEnabled=true;let lastBundle=null,meshByPlacementId=new Map(),currentAssemblyStep=null;
function semanticColorValue(value){if(typeof value!=='string')return null;const text=value.trim().toLowerCase();const named=namedColors[text];if(named!==undefined)return named;if(/^#[0-9a-f]{6}$/i.test(text))return Number.parseInt(text.slice(1),16);return null;}function colorValue(value,fallback){const semantic=semanticColorValue(value);return semantic===null?fallback:semantic;}function setPaletteColor(category,color){palette[category]=color;materials[category].color.setHex(color);fadedMaterials[category].color.setHex(color);highlightMaterials[category].color.setHex(color);highlightMaterials[category].emissive.setHex(color);semanticMaterials.clear();}function applyAppearance(b){const a=b?.appearance;if(!a)return;const wall=colorValue(a.walls?.color,palette.brick),roof=colorValue(a.roof?.color,palette.roof_tile),frame=colorValue(a.frames?.color,palette.window_frame);setPaletteColor('brick',wall);setPaletteColor('roof_tile',roof);setPaletteColor('ridge_tile',roof);setPaletteColor('window_frame',frame);}
function setMessage(t=''){messageEl.textContent=t;}function rawDims(p){const m=p.part_id.match(/_(\d+)X(\d+)(?:X(\d+))?(?:_|$)/);if(!m)throw new Error(`Dimensions inconnues pour ${p.part_id}`);return{a:+m[1],b:+m[2],c:m[3]?+m[3]:null};}function dims(p){const{a,b,c}=rawDims(p);let w=a,l=b;if(p.rotation_quarter_turns%2)[w,l]=[l,w];let heightPlates=1;if(['brick','facade_detail','terrain',...exteriorCategories].includes(p.category))heightPlates=3;else if(['window_frame','window_pane'].includes(p.category))heightPlates=(c??1)*3;return{width:w,length:l,heightPlates};}
function validateBundle(b){if(!b||b.schema_version!=='0.1'||!Array.isArray(b.brick_model?.parts)||!Array.isArray(b.bom?.lines))throw new Error('Export BrickHouse invalide.');if(b.bom.total_parts!==b.brick_model.parts.length)throw new Error('BOM incohérente.');}function clearModel(){while(modelGroup.children.length)modelGroup.remove(modelGroup.children[0]);meshByPlacementId=new Map();}function mat(p,s='normal'){const k=palette[p.category]?p.category:'brick',c=semanticColorValue(p.semantic_color);if(s==='notice-current')return mat(p,'normal');if(c===null)return s==='current'?highlightMaterials[k]:s==='previous'?fadedMaterials[k]:materials[k];const cacheKey=`${s}:${k}:${c}`;if(semanticMaterials.has(cacheKey))return semanticMaterials.get(cacheKey);const source=s==='current'?highlightMaterials[k]:s==='previous'?fadedMaterials[k]:materials[k],m=source.clone();m.color.setHex(c);if(s==='current')m.emissive.setHex(c);semanticMaterials.set(cacheKey,m);return m;}function setPartState(g,s){g.visible=s!=='hidden';if(!g.visible)return;const m=mat(g.userData.part,s);g.traverse(c=>{if(c.isMesh)c.material=m;});}
function wedgeGeometry(run,span){const x0=-run/2,x1=run/2,z0=-span/2,z1=span/2,low=.10,high=3*PLATE_WORLD_HEIGHT;const v=new Float32Array([x0,0,z0,x0,0,z1,x1,0,z0,x1,0,z1,x0,low,z0,x0,low,z1,x1,high,z0,x1,high,z1]);const idx=[0,2,3,0,3,1,4,5,7,4,7,6,0,1,5,0,5,4,2,6,7,2,7,3,0,4,6,0,6,2,1,3,7,1,7,5];const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(v,3));g.setIndex(idx);g.computeVertexNormals();return g;}function makeSlopeMesh(p){const{a:run,b:span}=rawDims(p),world=dims(p),group=new THREE.Group(),geo=wedgeGeometry(run,span),body=new THREE.Mesh(geo,mat(p));body.castShadow=true;body.receiveShadow=true;body.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),edgeMaterial));group.userData={part:p};group.add(body);if(studMeshBudgetEnabled&&(studDetailEnabled||span<=4)){for(let i=0;i<span;i++){const s=new THREE.Mesh(studGeometry,mat(p));s.position.set(run/2-.5,3*PLATE_WORLD_HEIGHT+.075,i-(span-1)/2);s.castShadow=true;group.add(s);}}if(p.roof_side==='slope')group.rotation.y=p.rotation_quarter_turns*Math.PI/2;else if(p.rotation_quarter_turns%2===0)group.rotation.y=p.roof_side==='negative'?0:Math.PI;else group.rotation.y=p.roof_side==='negative'?-Math.PI/2:Math.PI/2;group.position.set(p.x_studs+world.width/2,p.z_plates*PLATE_WORLD_HEIGHT,p.y_studs+world.length/2);return group;}
function makePartMesh(p){const{width:w,length:l,heightPlates:hp}=dims(p),h=hp*PLATE_WORLD_HEIGHT,g=new THREE.Group();g.userData={part:p};if(p.category==='roof_tile'&&p.part_id.startsWith('BRICK_SLOPED_'))return makeSlopeMesh(p);let geo;if(p.category==='window_pane'){const thickness=.12;geo=p.rotation_quarter_turns%2?new THREE.BoxGeometry(thickness,h,l*.82):new THREE.BoxGeometry(w*.82,h,thickness);}else geo=new THREE.BoxGeometry(w,h,l);const body=new THREE.Mesh(geo,mat(p));body.castShadow=p.category!=='window_pane';body.receiveShadow=true;body.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),edgeMaterial));g.add(body);if(['brick','facade_detail','window_frame','terrain',...exteriorCategories].includes(p.category)&&studMeshBudgetEnabled&&(noticePrototypeMode||studDetailEnabled||w*l<=4)){for(let x=0;x<w;x++)for(let z=0;z<l;z++){const s=new THREE.Mesh(studGeometry,mat(p));s.position.set(x-(w-1)/2,h/2+.075,z-(l-1)/2);s.castShadow=true;g.add(s);}}g.position.set(p.x_studs+w/2,p.z_plates*PLATE_WORLD_HEIGHT+h/2,p.y_studs+l/2);return g;}
function updateSummary(b){const m=b.brick_model,v=[b.building_id,String(b.bom.total_parts),String(b.bom.unique_part_types),`${m.width_studs} × ${m.depth_studs} tenons`];[...summaryEl.querySelectorAll('dd')].forEach((n,i)=>n.textContent=v[i]??'—');}
function updateFidelity(b){const issues=Array.isArray(b.fidelity_issues)?b.fidelity_issues:[];if(!fidelityCard||!fidelityList)return;if(!issues.length){fidelityCard.hidden=true;fidelityList.innerHTML='';return;}fidelityCard.hidden=false;fidelityList.innerHTML=issues.map(issue=>`<li><strong>${issue.severity==='blocker'?'Bloquant':issue.severity==='warning'?'À vérifier':'Information'}</strong> — ${String(issue.message??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}</li>`).join('');}
function modelFrame(){const box=new THREE.Box3().setFromObject(modelGroup);if(box.isEmpty())return null;return{box,size:box.getSize(new THREE.Vector3()),center:box.getCenter(new THREE.Vector3())};}function cameraDistance(size){return Math.max(size.x,size.y,size.z,1)/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov/2)))*1.55;}function placeCamera(center,direction,d,up=new THREE.Vector3(0,1,0)){controls.target.copy(center);camera.up.copy(up);camera.position.copy(center).addScaledVector(direction,d);camera.near=Math.max(d/100,.05);camera.far=d*20;camera.lookAt(center);camera.updateProjectionMatrix();controls.update();}
// Canonical BrickHouse frame: model x = left→right on the front facade, model y = front→rear, model z = bottom→top.
// Three.js is right-handed with world y up. Mapping model (x,y,z) -> world (x,z,-y) preserves the architectural handedness instead of reflecting the building.
// Therefore the architectural front camera stands at positive world z and sees increasing model x from screen left to screen right.
function frameCanonicalView(view='perspective'){const f=modelFrame();if(!f)return;const d=cameraDistance(f.size),c=f.center;const directions={front:new THREE.Vector3(0,0,1),rear:new THREE.Vector3(0,0,-1),left:new THREE.Vector3(-1,0,0),right:new THREE.Vector3(1,0,0),perspective:new THREE.Vector3(.9,.65,1.05)};placeCamera(c,directions[view].normalize(),d,new THREE.Vector3(0,1,0));}
function frameModel(){frameCanonicalView('perspective');}
function noticePlacementFrame(placementIds){
  const box=new THREE.Box3();
  for(const id of placementIds){
    const mesh=meshByPlacementId.get(id);
    if(mesh)box.expandByObject(mesh,true);
  }
  if(box.isEmpty())return null;
  return{box,size:box.getSize(new THREE.Vector3()),center:box.getCenter(new THREE.Vector3())};
}
function frameNoticePlacements(placementIds,view='perspective',distanceScale=1.22){
  resizeRenderer();
  const f=noticePlacementFrame(placementIds);
  if(!f)return;
  const directions={front:new THREE.Vector3(0,0,1),rear:new THREE.Vector3(0,0,-1),left:new THREE.Vector3(-1,0,0),right:new THREE.Vector3(1,0,0),perspective:new THREE.Vector3(.9,.65,1.05)};
  const direction=(view==='perspective'?new THREE.Vector3(.72,.92,1.18):view==='perspective-left'?new THREE.Vector3(-.72,.92,1.18):(directions[view]??directions.perspective)).clone().normalize();
  const forward=direction.clone().negate();
  const right=new THREE.Vector3().crossVectors(forward,new THREE.Vector3(0,1,0)).normalize();
  const viewUp=new THREE.Vector3().crossVectors(right,forward).normalize();
  const corners=[];
  for(const x of [f.box.min.x,f.box.max.x])for(const y of [f.box.min.y,f.box.max.y])for(const z of [f.box.min.z,f.box.max.z])corners.push(new THREE.Vector3(x,y,z).sub(f.center));
  const halfWidth=Math.max(...corners.map(p=>Math.abs(p.dot(right))));
  const halfHeight=Math.max(...corners.map(p=>Math.abs(p.dot(viewUp))));
  const halfDepth=Math.max(...corners.map(p=>Math.abs(p.dot(direction))));
  const verticalFov=THREE.MathUtils.degToRad(camera.fov);
  const horizontalFov=2*Math.atan(Math.tan(verticalFov/2)*camera.aspect);
  const fitDistance=Math.max(
    halfWidth/Math.tan(horizontalFov/2),
    halfHeight/Math.tan(verticalFov/2),
    1,
  );
  placeCamera(f.center,direction,halfDepth+fitDistance*distanceScale,new THREE.Vector3(0,1,0));
}
function noticeAssemblyStepState(bundle,index){
  const plan=bundle?.assembly_plan;
  if(!plan?.steps?.length)throw new Error('AssemblyPlan absent du bundle NOTICE.');
  if(plan.total_steps!==34||plan.steps.length!==34)throw new Error('Le prototype NOTICE doit contenir exactement 34 AssemblySteps.');
  const step=plan.steps[index];
  if(!step)throw new Error('AssemblyStep NOTICE absent.');
  const before=new Set(plan.steps.slice(0,index).flatMap(item=>item.placement_ids));
  const added=new Set(step.placement_ids);
  const partsById=new Map(bundle.brick_model.parts.map(part=>[part.placement_id,part]));
  const pli=new Map();
  for(const id of added){
    const part=partsById.get(id);
    if(!part)throw new Error(`Placement ${id} absent du BrickModel.`);
    pli.set(part.part_id,(pli.get(part.part_id)??0)+1);
  }
  return{plan,step,before,added,pli};
}
function noticeStep12InsertionArrows(state,supportEvidence){
  const arrows=[];
  if(!supportEvidence)return arrows;
  const partsById=new Map(lastBundle.brick_model.parts.map(part=>[part.placement_id,part]));
  for(const item of supportEvidence){
    const part=partsById.get(item.placement_id),d=dims(part);
    const mesh=meshByPlacementId.get(item.placement_id);
    if(!mesh)continue;
    const targetY=part.z_plates*PLATE_WORLD_HEIGHT+d.heightPlates*PLATE_WORLD_HEIGHT+.16;
    const x=mesh.position.x,z=mesh.position.z;
    const startY=mesh.position.y-.12;
    const length=Math.max(.45,startY-targetY);
    const arrow=new THREE.ArrowHelper(new THREE.Vector3(0,-1,0),new THREE.Vector3(x,startY,z),length,0xe87520,.22,.12);
    arrow.userData.noticeInsertionArrow=true;scene.add(arrow);arrows.push(arrow);
  }
  return arrows;
}
function clearNoticeInsertionArrows(){for(const obj of [...scene.children])if(obj.userData?.noticeInsertionArrow||obj.userData?.noticeStepHighlight)scene.remove(obj);}
function noticeStep12SupportEvidence(state){
  if(state.step.step_id!=='step-0012')return null;
  const partsById=new Map(lastBundle.brick_model.parts.map(part=>[part.placement_id,part]));
  const footprint=part=>{const d=dims(part);return{x0:part.x_studs,x1:part.x_studs+d.width,y0:part.y_studs,y1:part.y_studs+d.length};};
  const overlap=(a,b)=>Math.max(a.x0,b.x0)<Math.min(a.x1,b.x1)&&Math.max(a.y0,b.y0)<Math.min(a.y1,b.y1);
  const evidence=[];
  for(const id of state.added){
    const part=partsById.get(id),area=footprint(part);
    const supports=[...state.before].map(pid=>partsById.get(pid)).filter(Boolean).filter(candidate=>candidate.z_plates+3===part.z_plates&&overlap(area,footprint(candidate)));
    if(!supports.length)return null;
    evidence.push({placement_id:id,support_placement_ids:supports.map(item=>item.placement_id),axis:'vertical',direction:'down'});
  }
  return evidence;
}
function applyNoticeAssemblyStep(index){
  clearNoticeInsertionArrows();
  const state=noticeAssemblyStepState(lastBundle,index);
  const visualActionPrototype=index===11&&new URLSearchParams(window.location.search).get('visual')==='action';
  const supportEvidence=visualActionPrototype?noticeStep12SupportEvidence(state):null;
  for(const[id,m]of meshByPlacementId)setPartState(m,state.added.has(id)?(visualActionPrototype?'notice-current':'current'):state.before.has(id)?'normal':'hidden');
  const insertionArrows=[];
  if(visualActionPrototype){
    for(const id of state.added){
      const mesh=meshByPlacementId.get(id);if(!mesh)continue;
      const outline=new THREE.BoxHelper(mesh,0x2563eb);outline.userData.noticeStepHighlight=true;scene.add(outline);
    }
  }
  scene.background.setHex(0xf3f4f6);ground.visible=false;document.body.classList.add('notice-prototype-mode');
  const hud=document.querySelector('#notice-prototype-hud');
  if(hud){
    hud.hidden=false;
    hud.querySelector('strong').textContent=`${index+1} / 34`;
    const parts=hud.querySelector('.notice-parts');
    parts.replaceChildren(...[...state.pli].map(([partId,quantity])=>{
      const span=document.createElement('span'),preview=document.createElement('canvas'),qty=document.createElement('b');
      preview.className='notice-part-preview';preview.width=96;preview.height=58;preview.dataset.partId=partId;
      const part=lastBundle.brick_model.parts.find(item=>item.part_id===partId);
      const d=dims(part),ctx=preview.getContext('2d'),studs=Math.max(d.width,d.length),bodyW=Math.min(78,18+studs*7),x=(96-bodyW)/2,y=24;
      ctx.fillStyle='#e8e3d8';ctx.strokeStyle='#5f6368';ctx.lineWidth=1.5;ctx.fillRect(x,y,bodyW,22);ctx.strokeRect(x,y,bodyW,22);
      for(let stud=0;stud<studs;stud++){const sx=x+(stud+.5)*bodyW/studs;ctx.beginPath();ctx.ellipse(sx,y,Math.min(4,bodyW/studs*.28),2.3,0,0,Math.PI*2);ctx.fill();ctx.stroke();}
      qty.textContent=`×${quantity}`;span.append(preview,qty);return span;
    }));
    const prev=hud.querySelector('#notice-prev'),next=hud.querySelector('#notice-next');
    if(prev)prev.disabled=index===0;
    if(next)next.disabled=index===33;
  }
  frameNoticePlacements([...state.before,...state.added],visualActionPrototype?'perspective-left':'perspective',visualActionPrototype?.92:1.22);
  window.__NOTICE_PROOF__={
    total_assembly_steps:34,
    current_step:state.step.step_id,
    current_sequence:index+1,
    visual_action_prototype:visualActionPrototype,
    support_evidence:supportEvidence,
    insertion_arrow_count:insertionArrows.length,
    before_placement_ids:[...state.before],
    added_placement_ids:[...state.added],
    pli:[...state.pli].map(([part_id,quantity])=>({part_id,quantity})),
    visible_placement_ids:[...meshByPlacementId].filter(([,mesh])=>mesh.visible).map(([id])=>id),
  };
}
function goToNoticeStep(index){
  const n=Math.max(0,Math.min(index,33));
  applyNoticeAssemblyStep(n);
  const url=new URL(window.location.href);url.searchParams.set('notice',`step-${String(n+1).padStart(4,'0')}`);
  history.replaceState(null,'',url);
}
async function loadNoticePrototype(){
  try{
    const r=await fetch('./notice-reconstructed-steps-1-34-export.json',{cache:'no-store'});
    if(!r.ok)throw new Error(`HTTP ${r.status}`);
    renderBundle(await r.json(),{persist:false});
    const index=(noticeStepNumber??1)-1;
    applyNoticeAssemblyStep(index);
    document.querySelector('#notice-prev')?.addEventListener('click',()=>goToNoticeStep((window.__NOTICE_PROOF__?.current_sequence??1)-2));
    document.querySelector('#notice-next')?.addEventListener('click',()=>goToNoticeStep(window.__NOTICE_PROOF__?.current_sequence??1));
  }catch(e){setMessage(`NOTICE indisponible : ${e.message}`);}
}
function configureAssembly(b){const p=b.assembly_plan;if(!p?.steps?.length){assemblyCard.hidden=true;return;}assemblyCard.hidden=false;assemblyRange.min='0';assemblyRange.max=String(p.steps.length-1);assemblyRange.value='0';assemblyPrev.disabled=true;assemblyNext.disabled=p.steps.length<=1;showFullModel();}function showAssemblyStep(i){const p=lastBundle?.assembly_plan;if(!p?.steps?.length)return;const n=Math.max(0,Math.min(i,p.steps.length-1));currentAssemblyStep=n;assemblyRange.value=String(n);const prev=new Set();let cum=0;for(let j=0;j<n;j++){for(const id of p.steps[j].placement_ids)prev.add(id);cum+=p.steps[j].placement_ids.length;}const step=p.steps[n],cur=new Set(step.placement_ids);cum+=cur.size;for(const[id,m]of meshByPlacementId)setPartState(m,cur.has(id)?'current':prev.has(id)?'previous':'hidden');assemblyTitle.textContent=step.title;assemblyProgress.textContent=`Étape ${step.sequence}/${p.total_steps} · +${step.placement_ids.length} · ${cum}/${p.total_parts} pièces`;assemblyPrev.disabled=n===0;assemblyNext.disabled=n===p.steps.length-1;}function showFullModel(){for(const m of meshByPlacementId.values())setPartState(m,'normal');currentAssemblyStep=null;assemblyTitle.textContent='Modèle complet';assemblyProgress.textContent=lastBundle?.assembly_plan?`${lastBundle.assembly_plan.total_parts} pièces`:'';}
function csvCell(value){const text=String(value??'');return /[",\n]/.test(text)?`"${text.replace(/"/g,'""')}"`:text;}function downloadBom(b){const text=['part_id,category,semantic_color,quantity',...b.bom.lines.map(l=>[l.part_id,l.category,l.semantic_color??'',l.quantity].map(csvCell).join(','))].join('\n')+'\n',blob=new Blob([text],{type:'text/csv;charset=utf-8'}),u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=`${b.building_id}-bom.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(u);}function renderBundle(b,{persist=true}={}){validateBundle(b);applyAppearance(b);clearModel();studMeshBudgetEnabled=b.brick_model.parts.length<=1200;for(const p of b.brick_model.parts){const m=makePartMesh(p);modelGroup.add(m);meshByPlacementId.set(p.placement_id,m);}lastBundle=b;updateSummary(b);updateFidelity(b);configureAssembly(b);frameModel();if(persist)localStorage.setItem('brickhouse.currentExport',JSON.stringify(b));setMessage('');}function loadPendingExport(){const raw=localStorage.getItem('brickhouse.pendingExport');if(!raw)return false;try{renderBundle(JSON.parse(raw));localStorage.removeItem('brickhouse.pendingExport');setMessage('Votre maquette BrickHouse est prête.');return true;}catch(error){localStorage.removeItem('brickhouse.pendingExport');setMessage(`Export généré invalide : ${error.message}`);return false;}}function loadCurrentExport(){const raw=localStorage.getItem('brickhouse.currentExport');if(!raw)return false;try{renderBundle(JSON.parse(raw),{persist:false});setMessage('Dernière maquette rechargée.');return true;}catch{localStorage.removeItem('brickhouse.currentExport');return false;}}async function loadSample(){try{const r=await fetch('./sample-export.json',{cache:'no-store'});if(!r.ok)throw new Error(`HTTP ${r.status}`);renderBundle(await r.json());setMessage('Exemple BrickHouse chargé.');}catch(e){setMessage(`Impossible de charger l’exemple : ${e.message}`);}}fileInput.addEventListener('change',async()=>{const f=fileInput.files?.[0];if(!f)return;try{renderBundle(JSON.parse(await f.text()));setMessage('Export chargé.');}catch(e){setMessage(`JSON invalide : ${e.message}`);}finally{fileInput.value='';}});resetButton.addEventListener('click',()=>{if(lastBundle)frameCanonicalView('perspective');});frontButton.addEventListener('click',()=>{if(lastBundle)frameCanonicalView('front');});rearButton.addEventListener('click',()=>{if(lastBundle)frameCanonicalView('rear');});leftButton.addEventListener('click',()=>{if(lastBundle)frameCanonicalView('left');});rightButton.addEventListener('click',()=>{if(lastBundle)frameCanonicalView('right');});sampleButton.addEventListener('click',loadSample);downloadBomButton.addEventListener('click',()=>{if(lastBundle)downloadBom(lastBundle);});assemblyRange.addEventListener('input',()=>showAssemblyStep(Number(assemblyRange.value)));assemblyPrev.addEventListener('click',()=>showAssemblyStep((currentAssemblyStep??0)-1));assemblyNext.addEventListener('click',()=>showAssemblyStep((currentAssemblyStep??-1)+1));assemblyFull.addEventListener('click',showFullModel);function resizeRenderer(){const w=canvas.clientWidth,h=canvas.clientHeight;if(canvas.width!==Math.floor(w*renderer.getPixelRatio())||canvas.height!==Math.floor(h*renderer.getPixelRatio())){renderer.setSize(w,h,false);camera.aspect=w/Math.max(h,1);camera.updateProjectionMatrix();}}renderer.setAnimationLoop(()=>{resizeRenderer();controls.update();renderer.render(scene,camera);});if(noticePrototypeMode)loadNoticePrototype();else if(!loadPendingExport()&&!loadCurrentExport())loadSample();