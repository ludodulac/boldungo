import {addPackagePhotos,savePackageOrder,deletePackagePhoto,savePackageMetadata,packageSnapshot,importPhotoPackage} from './photo-package-import-v1.js';
import {buildGuidedHousePackageV1} from './guided-house-package-v1.js';
const host=document.querySelector('#cards'),status=document.querySelector('#status'),fileInput=document.querySelector('#files'),zipInput=document.querySelector('#zip');
const fields=[['title','Titre'],['orientation','Orientation'],['description','Description'],['must_reproduce','À reproduire'],['do_not_confuse','À ne pas confondre'],['known_dimensions','Dimensions connues'],['connections_to_other_photos','Liens avec d’autres photos'],['provenance','Provenance']];
const lists=new Set(['must_reproduce','do_not_confuse','known_dimensions','connections_to_other_photos']);
const orientations=['FRONT','LEFT','RIGHT','REAR','ROOF','STAIR','WOOD_TERRACE','CONCRETE_PLATFORM','DETAIL','OTHER','UNKNOWN'];
const provenances=['USER_CONFIRMED','PHOTO','INFERRED','UNKNOWN'];
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let photos=[],project=null,urls=[],saveQueue=Promise.resolve();
function queueSave(fn){saveQueue=saveQueue.catch(()=>{}).then(fn);return saveQueue;}
function displayStatus(s){status.textContent=s;}
async function render(){
 urls.forEach(URL.revokeObjectURL);urls=[];
 const snap=await packageSnapshot();photos=snap.photos;project=snap.project;
 host.innerHTML=photos.map((p,i)=>{
 const g=project?.photo_guidance?.[p.photo_id]||{};
 const input=fields.map(([key,label])=>{
  const value=g[key]??(key==='orientation'?'UNKNOWN':key==='provenance'?'UNKNOWN':'');
  if(key==='orientation'||key==='provenance'){const opts=key==='orientation'?orientations:provenances;return '<label>'+label+'<select data-field="'+key+'">'+opts.map(o=>'<option value="'+o+'"'+(value===o?' selected':'')+'>'+o+'</option>').join('')+'</select></label>';}
  const txt=lists.has(key)?(Array.isArray(value)?value.join('\n'):String(value||'')):String(value||'');
  return '<label>'+label+'<textarea data-field="'+key+'" rows="2">'+escape(txt)+'</textarea></label>';
 }).join('');
 return '<article class="card" data-id="'+escape(p.photo_id)+'"><div class="head"><img data-image="'+escape(p.photo_id)+'" alt="Miniature"><div><strong>Photo '+(i+1)+'</strong><small>'+escape(p.original_filename)+'</small><small>ID interne : '+escape(p.photo_id)+'</small></div></div><div class="actions"><button data-action="up" '+(i===0?'disabled':'')+'>↑ Monter</button><button data-action="down" '+(i===photos.length-1?'disabled':'')+'>↓ Descendre</button><button data-action="delete" class="danger">Supprimer</button></div><div class="fields">'+input+'</div></article>';
 }).join('')||'<p>Aucune photo. Ajoutez votre premier lot.</p>';
 for(const p of photos){const img=Array.from(host.querySelectorAll('img[data-image]')).find(el=>el.dataset.image===p.photo_id);if(img){const url=URL.createObjectURL(p.blob);urls.push(url);img.src=url;}}
 document.querySelector('#count').textContent=photos.length+' photo(s)';
}
document.querySelector('#add').onclick=()=>fileInput.click();
fileInput.onchange=async()=>{try{displayStatus('Ajout…');await queueSave(()=>addPackagePhotos(fileInput.files));fileInput.value='';await render();displayStatus('Photos enregistrées sur cet appareil.');}catch(e){displayStatus('Erreur : '+e.message);}};
host.addEventListener('click',async e=>{const button=e.target.closest('button[data-action]');if(!button)return;const card=button.closest('[data-id]'),id=card.dataset.id,index=photos.findIndex(p=>p.photo_id===id);if(index<0)return;const action=button.dataset.action;
 try{if(action==='delete'){if(!confirm('Supprimer cette photo du dossier ?'))return;await queueSave(()=>deletePackagePhoto(id));}
 else{const target=index+(action==='up'?-1:1);if(target<0||target>=photos.length)return;const ids=photos.map(p=>p.photo_id);[ids[index],ids[target]]=[ids[target],ids[index]];await queueSave(()=>savePackageOrder(ids));}
 await render();displayStatus('Modification enregistrée.');}catch(err){displayStatus('Erreur : '+err.message);}
});
host.addEventListener('change',e=>{const el=e.target.closest('[data-field]');if(!el)return;const id=el.closest('[data-id]').dataset.id,key=el.dataset.field;const value=lists.has(key)?el.value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean):el.value;queueSave(()=>savePackageMetadata(id,key,value)).then(()=>displayStatus('Métadonnées enregistrées.')).catch(err=>displayStatus('Erreur : '+err.message));});
function readmeFor(prepared,guidance){return 'BOLDÜNGO PHOTO PACKAGE\n\nPhoto count: '+prepared.length+'\n\n'+prepared.map((p,i)=>{const g=guidance[p.photo_id]||{};const list=(k)=>'\n'+(Array.isArray(g[k])&&g[k].length?g[k].map(v=>'- '+v).join('\n'):'- (none)');return [p.photo_id,'Original filename: '+p.original_filename,'Orientation: '+(g.orientation||'UNKNOWN'),'Title: '+(g.title||''),'Description: '+(g.description||''),'Must reproduce:'+list('must_reproduce'),'Do not confuse:'+list('do_not_confuse'),'Known dimensions:'+list('known_dimensions'),'Connections:'+list('connections_to_other_photos'),'Provenance: '+(g.provenance||'UNKNOWN')].join('\n');}).join('\n\n')+'\n';}
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);}
document.querySelector('#export').onclick=async()=>{try{await saveQueue;const snap=await packageSnapshot();if(!snap.photos.length)throw new Error('Aucune photo');const guidance={},prepared=snap.photos.map((p,i)=>{const id='P'+String(i+1).padStart(3,'0');guidance[id]={...(snap.project.photo_guidance?.[p.photo_id]||{})};return {...p,photo_id:id,export_order:i+1};});const synthetic={project:{...snap.project,photo_guidance:guidance},photos:prepared,photo_package_readme:readmeFor(prepared,guidance)};const result=await buildGuidedHousePackageV1(synthetic);download(result.blob,'boldungo-photo-package-'+new Date().toISOString().slice(0,10)+'.zip');displayStatus('ZIP exporté : '+prepared.length+' photos.');}catch(e){displayStatus('Export impossible : '+e.message);}};
document.querySelector('#import').onclick=()=>zipInput.click();
zipInput.onchange=async()=>{const file=zipInput.files[0];if(!file)return;try{if(!confirm('Importer dans un nouveau projet photo local ?'))return;displayStatus('Import ZIP…');const count=await queueSave(()=>importPhotoPackage(file));await render();displayStatus('Dossier restauré : '+count+' photos.');}catch(e){displayStatus('Import refusé : '+e.message);}finally{zipInput.value='';}};
render().catch(e=>displayStatus('Initialisation impossible : '+e.message));
