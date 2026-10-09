import { openProjectDb, createProject, updateProject, getActiveProjectSnapshot } from './project-photo-store.js';
const SCHEMA='boldungo.guided-house-package.v1';
function request(r){return new Promise((resolve,reject)=>{r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
function done(tx){return new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||new Error('Transaction annulée'));});}
export async function addPackagePhotos(files){
 const snap=await getActiveProjectSnapshot();let project=snap.project;
 if(!project)project=await createProject('Dossier photo');
 const db=await openProjectDb(),tx=db.transaction(['photos_v2','projects'],'readwrite');
 const store=tx.objectStore('photos_v2');const existing=await request(store.index('project_id').getAll(project.project_id));
 let order=Math.max(0,...existing.map(p=>p.package_order||0));
 const added=[];
 for(const file of files){if(!file.type.startsWith('image/')||!file.size)continue;
 const photo_id='PACK_'+crypto.randomUUID().replaceAll('-','');
 const rec={project_id:project.project_id,photo_id,primary_face:null,detail_group_id:null,original_filename:file.name,mime_type:file.type,blob:file,capture_order:++order,package_order:order,note:'',created_at:new Date().toISOString()};
 store.put(rec);added.push(rec);
 }
 await done(tx);return added;
}
export async function savePackageOrder(orderedIds){
 const snap=await getActiveProjectSnapshot();if(!snap.project)return;
 const db=await openProjectDb(),tx=db.transaction('photos_v2','readwrite'),store=tx.objectStore('photos_v2');
 for(let i=0;i<orderedIds.length;i++){const p=await request(store.get([snap.project.project_id,orderedIds[i]]));if(p){p.package_order=i+1;store.put(p);}}
 await done(tx);
}
export async function deletePackagePhoto(id){
 const snap=await getActiveProjectSnapshot();if(!snap.project)return;
 const db=await openProjectDb(),tx=db.transaction('photos_v2','readwrite');tx.objectStore('photos_v2').delete([snap.project.project_id,id]);await done(tx);
 const guidance={...(snap.project.photo_guidance||{})};delete guidance[id];await updateProject(snap.project.project_id,{photo_guidance:guidance});
}
export async function savePackageMetadata(id,field,value){
 const snap=await getActiveProjectSnapshot();if(!snap.project)return;
 const guidance={...(snap.project.photo_guidance||{})};
 guidance[id]={...(guidance[id]||{}),[field]:value};
 await updateProject(snap.project.project_id,{photo_guidance:guidance});
}
export async function packageSnapshot(){
 const snap=await getActiveProjectSnapshot();
 return {...snap,photos:snap.photos.filter(p=>p.photo_id.startsWith('PACK_')).sort((a,b)=>(a.package_order||0)-(b.package_order||0))};
}
function u16(a,i){return a[i]|(a[i+1]<<8);}function u32(a,i){return (a[i]|a[i+1]<<8|a[i+2]<<16|a[i+3]<<24)>>>0;}
async function unzipStored(blob){
 const a=new Uint8Array(await blob.arrayBuffer());const files=new Map();let i=0;const decoder=new TextDecoder();
 while(i+30<=a.length&&u32(a,i)===0x04034b50){
  const method=u16(a,i+8),flags=u16(a,i+6),size=u32(a,i+18),nameLen=u16(a,i+26),extra=u16(a,i+28);
  if(method!==0||flags&8)throw new Error('ZIP non pris en charge : compression ou descripteur de données');
  const start=i+30+nameLen+extra,end=start+size;if(end>a.length)throw new Error('ZIP tronqué');
  const name=decoder.decode(a.slice(i+30,i+30+nameLen));
  if(files.has(name))throw new Error('ZIP invalide : entrée dupliquée '+name);
  files.set(name,a.slice(start,end));i=end;
 }
 if(!files.size)throw new Error('ZIP vide ou incompatible');return files;
}
export async function importPhotoPackage(blob){
 const files=await unzipStored(blob),decode=new TextDecoder();
 const manifestBytes=files.get('manifest.json'),guidedBytes=files.get('guided-house.json');
 if(!manifestBytes||!guidedBytes)throw new Error('manifest.json ou guided-house.json absent');
 let manifest,guided;try{manifest=JSON.parse(decode.decode(manifestBytes));guided=JSON.parse(decode.decode(guidedBytes));}catch{throw new Error('JSON du package invalide');}
 if(manifest.schema_version!==SCHEMA||guided.schema_version!==SCHEMA||!Array.isArray(guided.photos)||!Array.isArray(manifest.photos))throw new Error('Schéma de dossier incompatible');
 if(manifest.photos.length!==guided.photos.length||!guided.photos.length)throw new Error('Inventaire photographique incohérent');
 const byId=new Map(manifest.photos.map(p=>[p.photo_id,p]));const seen=new Set(),records=[],guidance={};
 for(let i=0;i<guided.photos.length;i++){
  const p=guided.photos[i],m=byId.get(p.photo_id);
  if(!p.photo_id||seen.has(p.photo_id)||!m||m.file_path!==p.file_path)throw new Error('Association photo/manifeste invalide');seen.add(p.photo_id);
  if(!/^photos\/[A-Za-z0-9_-]+\.[A-Za-z0-9]+$/.test(p.file_path))throw new Error('Chemin photo invalide');
  const bytes=files.get(p.file_path);if(!bytes||!bytes.length)throw new Error('Photo référencée absente : '+p.file_path);
  const ext=p.file_path.split('.').pop().toLowerCase();const mime=ext==='png'?'image/png':ext==='webp'?'image/webp':'image/jpeg';
  const id='PACK_'+crypto.randomUUID().replaceAll('-','');
  records.push({photo_id:id,original_filename:p.original_filename||m.original_filename||p.file_path.split('/').pop(),blob:new Blob([bytes],{type:mime}),mime_type:mime,package_order:i+1,capture_order:i+1});
  guidance[id]={title:p.title||'',orientation:p.orientation||'UNKNOWN',description:p.description||'',must_reproduce:p.must_reproduce||[],do_not_confuse:p.do_not_confuse||[],known_dimensions:p.known_dimensions||[],connections_to_other_photos:p.connections_to_other_photos||[],provenance:p.provenance||'UNKNOWN'};
 }
 const project=await createProject('Dossier photo importé');
 const db=await openProjectDb(),tx=db.transaction('photos_v2','readwrite'),store=tx.objectStore('photos_v2');
 for(const p of records)store.put({...p,project_id:project.project_id,primary_face:null,detail_group_id:null,note:'',created_at:new Date().toISOString()});
 await done(tx);await updateProject(project.project_id,{photo_guidance:guidance,general_notes:guided.general_notes||'',known_front_width:guided.known_front_width??null});
 return records.length;
}
