import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LDrawLoader } from 'three/addons/loaders/LDrawLoader.js';
import { LDrawConditionalLineMaterial } from 'three/addons/materials/LDrawConditionalLineMaterial.js';

const PARTS_LIBRARY = 'https://raw.githubusercontent.com/pybricks/ldraw/c43ed06a128a10ed65675166bf42eb6fd608b9b0/';
const MODELS = Object.freeze({
  toiture: {file:'toiture.ldr',count:10,detail:'TOITURE M040 · 8 vraies pentes 30363 et 2 briques d’appui 3008, en deux rangées. Les raccords au pignon restent non validés.'},
  terrasse: {file:'terrasse.ldr',count:116,detail:'TERRASSE M045 · 116 véritables références de pièces LDraw. 48 pièces provisoires ont été retirées du prototype, garde-corps à reconstruire.'},
  charpente: {file:'charpente.ldr',count:6,detail:'CHARPENTE M041 · 6 pièces, dont le support expérimental sous la pente. Séquence de montage à vérifier.'},
  'escalier-raccord': {file:'escalier-raccord.ldr',count:7,detail:'ESCALIER M042 · 7 pièces réelles de raccord expérimental entre escalier et plateforme. Cela ne représente pas tout l’escalier.'},
  escalier: {file:'escalier.ldr',count:1126,detail:'ESCALIER M038 · Prototype de 1 126 pièces (7 + 9 marches), sans garantie de raccord final. Le chargement sur téléphone est plus lourd.'}
});

const canvas=document.getElementById('preview');
const status=document.getElementById('loading');
const detail=document.getElementById('model-description');
const buttons=[...document.querySelectorAll('[data-preview]')];

const scene=new THREE.Scene();
scene.background=new THREE.Color('#101827');
scene.add(new THREE.HemisphereLight(0xdceaff,0x526078,2.3));
const key=new THREE.DirectionalLight(0xffffff,3.2);
key.position.set(2,4,5);scene.add(key);
const rim=new THREE.DirectionalLight(0xa2c8f7,1.1);
rim.position.set(-4,3,-2);scene.add(rim);

const camera=new THREE.PerspectiveCamera(46,1,.1,50000);
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'low-power'});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
const controls=new OrbitControls(camera,canvas);
controls.enableDamping=false;
controls.screenSpacePanning=true;
controls.minDistance=10;
controls.maxDistance=15000;
const modelHolder=new THREE.Group();scene.add(modelHolder);

const resize=()=>{
 const rect=canvas.getBoundingClientRect();
 if(rect.width<1||rect.height<1)return;
 camera.aspect=rect.width/rect.height;
 camera.updateProjectionMatrix();
 renderer.setSize(rect.width,rect.height,false);
};
window.addEventListener('resize',resize);
new ResizeObserver(resize).observe(canvas);
resize();
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});

let loaderPromise=null;
function getLoader(){
 if(!loaderPromise)loaderPromise=(async()=>{
   const loader=new LDrawLoader();
   loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
   loader.setPartsLibraryPath(PARTS_LIBRARY);
   await loader.preloadMaterials(PARTS_LIBRARY+'LDConfig.ldr');
   return loader;
 })();
 return loaderPromise;
}
let currentRequest=0;
async function loadMode(mode){
 const spec=MODELS[mode];if(!spec)return;
 const request=++currentRequest;
 buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.preview===mode)));
 detail.textContent=spec.detail;
 status.hidden=false;status.textContent='Chargement de '+mode+' : géométries réelles des pièces LEGO…';
 const url=new URL(location.href);url.searchParams.set('mode',mode);history.replaceState(null,'',url);
 try{
   const loader=await getLoader();
   // Source files are copies of the unchanged LDraw prototypes on each team's draft branch.
   const group=await loader.loadAsync('./progress/'+spec.file);
   if(request!==currentRequest)return;
   // LDraw uses Y-down. Turn the model right side up without altering piece placements.
   group.rotation.x=Math.PI;group.updateMatrixWorld(true);
   while(modelHolder.children.length){const child=modelHolder.children[0];modelHolder.remove(child);}
   modelHolder.add(group);
   const box=new THREE.Box3().setFromObject(group,true);
   if(box.isEmpty())throw new Error('Le fichier LDraw ne contient aucune géométrie.');
   const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
   group.position.sub(center);group.updateMatrixWorld(true);
   const radius=Math.max(size.x,size.y,size.z,30);
   const fov=THREE.MathUtils.degToRad(camera.fov);
   const distance=radius/(2*Math.tan(fov/2))*1.45;
   camera.near=Math.max(0.1,distance/2000);
   camera.far=Math.max(1000,distance*20);
   camera.position.set(distance*.85,distance*.58,distance*.93);
   controls.target.set(0,0,0);
   camera.updateProjectionMatrix();controls.update();resize();
   status.hidden=true;
   document.title='BOLDÜNGO — '+mode+' LEGO réel en 3D';
 }catch(err){
   if(request!==currentRequest)return;
   console.error('LDraw preview',err);
   status.textContent='Impossible de charger les vraies pièces LEGO : '+String(err?.message||err)+'. Vérifie ta connexion Internet puis réessaie.';
 }
}
buttons.forEach(b=>b.addEventListener('click',()=>loadMode(b.dataset.preview)));
const requested=new URLSearchParams(location.search).get('mode');
loadMode(MODELS[requested]?requested:'toiture');