import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// BOLDUNGO-STAIR-PROTOTYPE-001 — isolated visual proof, NOT a house scene.
// Width and counts and upper-east direction: USER_CONFIRMED.
// All other numeric dimensions and lower-north direction: PROTOTYPE_REPRESENTATION_CHOICE.
const WIDTH = 1.12, RISE = 0.17, GOING = 0.29, LOWER = 7, UPPER = 9;
const LANDING_Z = LOWER * RISE, TOP_Z = (LOWER + UPPER) * RISE;
const canvas = document.querySelector('#viewer');
const status = document.querySelector('#prototype-status');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x152033);
const camera = new THREE.PerspectiveCamera(48, 1, 0.05, 150);
const renderer = new THREE.WebGLRenderer({canvas, antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(1.7, 1.15, 1.7);
scene.add(new THREE.HemisphereLight(0xffffff, 0x45536c, 2.6));
const sunlight = new THREE.DirectionalLight(0xfff1d9, 3.0);
sunlight.position.set(-4, 10, 8); scene.add(sunlight);
const concrete = new THREE.MeshStandardMaterial({color:0xc6c3b9,roughness:.82});
const masonry = new THREE.MeshStandardMaterial({color:0x958b7d,roughness:.94});
const outline = new THREE.LineBasicMaterial({color:0x252b34});
function box(name, x,y,z, w,h,d, mat) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), mat);
  mesh.name=name; mesh.position.set(x+w/2,y+h/2,z+d/2);
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry),outline));
  scene.add(mesh); return mesh;
}
// Lower flight ascends north (+Z). Independent treads, no inclined beam.
for(let i=0;i<LOWER;i++){
  const top=(i+1)*RISE, z=i*GOING;
  box('lower-tread-'+(i+1),0,top-.115,z,WIDTH,.115,GOING-.012,concrete);
  // Stepped masonry parapet: each piece rises with its corresponding tread,
  // remains locally elevated, and never extends down to the ground.
  box('lower-parapet-left-'+(i+1),-.14,top-.12,z,.13,.78,GOING-.012,masonry);
  box('lower-parapet-right-'+(i+1),WIDTH+.01,top-.12,z,.13,.78,GOING-.012,masonry);
}
// Distinct horizontal turning landing, wider than a tread.
const landingStartZ=LOWER*GOING;
box('TURNING-LANDING',-.14,LANDING_Z-.15,landingStartZ,1.60,.15,1.60,concrete);
// Upper flight ascends EAST (+X), at the northern edge of the landing.
const upperStartX=1.46, upperStartZ=landingStartZ+.23;
for(let i=0;i<UPPER;i++){
  const top=LANDING_Z+(i+1)*RISE, x=upperStartX+i*GOING;
  box('upper-tread-'+(i+1),x,top-.115,upperStartZ,GOING-.012,.115,WIDTH,concrete);
  box('upper-parapet-near-'+(i+1),x,top-.12,upperStartZ-.14,GOING-.012,.78,.13,masonry);
  box('upper-parapet-far-'+(i+1),x,top-.12,upperStartZ+WIDTH+.01,GOING-.012,.78,.13,masonry);
}
const arrivalX=upperStartX+UPPER*GOING;
box('ARRIVAL-PLATFORM',arrivalX,TOP_Z-.18,upperStartZ-.3,2.0,.18,1.72,concrete);
// Mark east visually with an arrow, not as a claim about the actual low flight.
const arrow = new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(upperStartX,TOP_Z+1.0,upperStartZ+.56),1.5,0xf0b64c,.25,.12);
scene.add(arrow);
const ground = new THREE.GridHelper(15,30,0x69758a,0x344257);scene.add(ground);
const lowerCount=scene.children.filter(x=>x.name?.startsWith('lower-tread-')).length;
const upperCount=scene.children.filter(x=>x.name?.startsWith('upper-tread-')).length;
const landing=!!scene.getObjectByName('TURNING-LANDING');
const arrival=!!scene.getObjectByName('ARRIVAL-PLATFORM');
const parapets=scene.children.filter(x=>x.name?.includes('parapet-')).length;
status.textContent=`Prototype chargé : ${lowerCount} marches basses, palier ${landing?'oui':'non'}, ${upperCount} marches hautes, plateforme ${arrival?'oui':'non'}, ${parapets} éléments de parapet. Montée haute vers l’Est (+X).`;
if(lowerCount!==7||upperCount!==9||!landing||!arrival||parapets!==32) throw new Error('Prototype invariant failed');
function view(x,y,z){camera.position.set(x,y,z);controls.update();}
document.querySelector('#reset-view').addEventListener('click',()=>view(8,7,10));
document.querySelector('#top-view').addEventListener('click',()=>view(2,13,2));
document.querySelector('#east-view').addEventListener('click',()=>view(10,4,2));
view(8,7,10);
function animate(){
  const w=canvas.clientWidth,h=canvas.clientHeight;
  if(w&&h&&(canvas.width!==Math.round(w*renderer.getPixelRatio())||canvas.height!==Math.round(h*renderer.getPixelRatio()))){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);
}
animate();
