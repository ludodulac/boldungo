import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// BOLDUNGO-STAIR-PROTOTYPE-001C — isolated visual proof, NOT a house scene.
// Width and counts and upper-east direction: USER_CONFIRMED.
// Lower ascent NORTH (+Z), upper ascent EAST (+X), right turn: HUMAN_CONFIRMED V2.\n// All non-confirmed numeric dimensions: PROTOTYPE_REPRESENTATION_CHOICE.
const WIDTH = 1.12, RISE = 0.17, GOING = 0.29, LOWER = 7, UPPER = 9;
const LANDING_Z = LOWER * RISE, TOP_Z = (LOWER + UPPER) * RISE;\nconst EPS=1e-7;\nfunction assertGeometry(ok,message){if(!ok)throw new Error('001C GEOMETRY: '+message);}
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
// East is +X. Reference camera is south (+Z), looking north (-Z):
// +X therefore appears on SCREEN RIGHT. Prototype lower flight climbs north (+Z).
// Smooth parapets are individual sloped masonry solids, not stair-step blocks.
function slopingParapet(name, from, to, thickness=.13, wallHeight=.68) {
  const a=new THREE.Vector3(...from), b=new THREE.Vector3(...to);
  const delta=b.clone().sub(a), length=delta.length();
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(thickness,wallHeight,length),masonry);
  mesh.name=name;
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),delta.clone().normalize());
  mesh.position.copy(a).add(b).multiplyScalar(.5);
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry),outline));
  scene.add(mesh);
  return mesh;
}
for(let i=0;i<LOWER;i++){
  const top=(i+1)*RISE, z=i*GOING;
  box('lower-tread-'+(i+1),0,top-.115,z,WIDTH,.115,GOING,concrete);
}
const lowerStartY=RISE+.38, lowerEndY=LANDING_Z+.38;
slopingParapet('lower-parapet-left',[-.075,lowerStartY,GOING/2],[-.075,lowerEndY,LOWER*GOING-GOING/2]);
slopingParapet('lower-parapet-right',[WIDTH+.075,lowerStartY,GOING/2],[WIDTH+.075,lowerEndY,LOWER*GOING-GOING/2]);
// Turning landing: a horizontal slab distinct from both flights.
const landingStartZ=LOWER*GOING;
box('TURNING-LANDING',-.14,LANDING_Z-.15,landingStartZ,1.60,.15,1.60,concrete);
// Low flight enters at the SOUTH edge of the landing; upper flight exits EAST.
// Masonry protects the WEST and NORTH edges; the entrance and exit remain open.
box('landing-parapet-west',-.27,LANDING_Z,landingStartZ+.06,.13,.70,1.48,masonry);
box('landing-parapet-north',-.14,LANDING_Z,landingStartZ+1.47,1.60,.70,.13,masonry);
// Short SOUTH return only outside the incoming lower-flight passage.
box('landing-parapet-south-return',WIDTH+.01,LANDING_Z,landingStartZ,.34,.70,.13,masonry);
const upperStartX=1.46, upperStartZ=landingStartZ+.23;
for(let i=0;i<UPPER;i++){
  const top=LANDING_Z+(i+1)*RISE, x=upperStartX+i*GOING;
  box('upper-tread-'+(i+1),x,top-.115,upperStartZ,GOING,.115,WIDTH,concrete);
}
const upperStartY=LANDING_Z+RISE+.38, upperEndY=TOP_Z+.38;
slopingParapet('upper-parapet-near',[upperStartX+GOING/2,upperStartY,upperStartZ-.075],[upperStartX+UPPER*GOING-GOING/2,upperEndY,upperStartZ-.075]);
slopingParapet('upper-parapet-far',[upperStartX+GOING/2,upperStartY,upperStartZ+WIDTH+.075],[upperStartX+UPPER*GOING-GOING/2,upperEndY,upperStartZ+WIDTH+.075]);
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
function bounds(name){const mesh=scene.getObjectByName(name);assertGeometry(!!mesh,'missing '+name);return new THREE.Box3().setFromObject(mesh);}
function close(a,b){return Math.abs(a-b)<EPS;}
const lowerBoxes=Array.from({length:LOWER},(_,i)=>bounds('lower-tread-'+(i+1)));
const upperBoxes=Array.from({length:UPPER},(_,i)=>bounds('upper-tread-'+(i+1)));
const landingBox=bounds('TURNING-LANDING'),arrivalBox=bounds('ARRIVAL-PLATFORM');
assertGeometry(lowerBoxes.every((b,i)=>close(b.max.x-b.min.x,WIDTH)&&(!i||(b.min.z>lowerBoxes[i-1].min.z&&b.max.y>lowerBoxes[i-1].max.y))),'lower steps must ascend NORTH');
assertGeometry(upperBoxes.every((b,i)=>close(b.max.z-b.min.z,WIDTH)&&(!i||(b.min.x>upperBoxes[i-1].min.x&&b.max.y>upperBoxes[i-1].max.y))),'upper steps must ascend EAST');
assertGeometry(close(lowerBoxes[LOWER-1].max.z,landingBox.min.z),'lower flight must meet SOUTH landing edge');
assertGeometry(close(lowerBoxes[LOWER-1].max.y,landingBox.max.y),'lower flight must meet landing elevation');
assertGeometry(close(upperBoxes[0].min.x,landingBox.max.x),'upper flight must leave EAST landing edge');
assertGeometry(upperBoxes[0].min.z>=landingBox.min.z&&upperBoxes[0].max.z<=landingBox.max.z,'upper flight must fit landing exit');
assertGeometry(close(upperBoxes[UPPER-1].max.x,arrivalBox.min.x),'upper flight must meet arrival platform');
assertGeometry(close(upperBoxes[UPPER-1].max.y,arrivalBox.max.y),'upper flight must meet arrival elevation');
assertGeometry(landingBox.max.y<arrivalBox.max.y,'arrival must be above landing');
const north=new THREE.Vector3(0,0,1),east=new THREE.Vector3(1,0,0);
assertGeometry(close(north.clone().cross(east).y,1),'NORTH to EAST must turn RIGHT');
const entry=new THREE.Box3(new THREE.Vector3(0,LANDING_Z-.02,landingStartZ-.001),new THREE.Vector3(WIDTH,LANDING_Z+.22,landingStartZ+.18));
const exit=new THREE.Box3(new THREE.Vector3(upperStartX-.02,LANDING_Z,upperStartZ),new THREE.Vector3(upperStartX+.03,LANDING_Z+.22,upperStartZ+WIDTH));
for(const mesh of scene.children.filter(x=>x.name?.startsWith('landing-parapet-'))){
 const b=new THREE.Box3().setFromObject(mesh);
 assertGeometry(!b.intersectsBox(entry)&&!b.intersectsBox(exit),'landing masonry obstructs passage: '+mesh.name);
}

status.textContent=`STAIR PROTOTYPE 001C · Prototype chargé : ${lowerCount} marches basses, palier ${landing?'oui':'non'}, ${upperCount} marches hautes, plateforme ${arrival?'oui':'non'}, ${parapets} éléments de parapet. Montée haute vers l’Est (+X).`;
if(lowerCount!==7||upperCount!==9||!landing||!arrival||parapets!==7) throw new Error('Prototype invariant failed');
function view(x,y,z){camera.position.set(x,y,z);camera.lookAt(controls.target);controls.update();}
document.querySelector('#reset-view').addEventListener('click',()=>view(1.7,6.4,12));
document.querySelector('#top-view').addEventListener('click',()=>view(2,13,2));
document.querySelector('#east-view').addEventListener('click',()=>view(10,4,2));
view(1.7,6.4,12);
function animate(){
  const w=canvas.clientWidth,h=canvas.clientHeight;
  if(w&&h&&(canvas.width!==Math.round(w*renderer.getPixelRatio())||canvas.height!==Math.round(h*renderer.getPixelRatio()))){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);
}
animate();
