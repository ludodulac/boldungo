// M046 — run from repository root: node missions/PARALLEL-033-CHARPENTE/audit_046.mjs
// The existing 019 visual bundle is not a fully certified LEGO model.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const b=JSON.parse(readFileSync('frontend/data/boldungo2-lego-house-019.json','utf8'));
const viewer=readFileSync('frontend/viewer.js','utf8');
const parts=b.brick_model.parts;
const targets=new Set(['right_glass_blocks','front_glazed_door','left_french_door']);
const protectedParts=JSON.stringify(parts.filter(x=>!targets.has(x.opening_id)));
let h=0;for(let i=0;i<protectedParts.length;i++)h=(Math.imul(h,31)+protectedParts.charCodeAt(i))|0;
assert.equal(h,1864835743,'Other opening, roof, gable, terrace or structural parts changed');
assert.equal(parts.length,2879);
const get=id=>{const p=parts.find(x=>x.placement_id===id);assert.ok(p,id);return p;};
const A=parts.filter(x=>x.opening_id==='right_glass_blocks'&&x.part_id==='PANE_1X1X1');
assert.equal(A.length,30);
for(let row=0;row<5;row++)for(let col=0;col<6;col++){
  const p=A.find(x=>x.y_studs===23+col&&x.z_plates===9+3*row);
  assert.ok(p,'A square glass block missing');assert.equal(p.height_plates,3);
}
for(const [id,z] of [['M046-A-LOWER-1X6',6],['M046-A-UPPER-1X6',24]]){
  const p=get(id);assert.equal(p.part_id,'BRICK_1X6');assert.equal(p.z_plates,z);
  assert.equal(p.length_studs,6);assert.equal(p.height_plates,3);
}
const headA=get('M046-B-HEAD-1X6'),headB=get('M046-B-HEAD-1X4');
assert.equal(headA.x_studs,45);assert.equal(headA.width_studs,6);
assert.equal(headB.x_studs,51);assert.equal(headB.width_studs,4);
assert.ok([headA,headB].every(x=>x.z_plates===24&&x.height_plates===3));
for(const id of ['b2-005-0946','b2-005-0947'])assert.equal(get(id).height_plates,24);
const pane=get('b2-005-0998');assert.equal(pane.opening_id,'left_french_door');
assert.equal(pane.x_studs,17);assert.equal(pane.length_studs,7);
const bars=parts.filter(x=>x.placement_id.startsWith('M046-C-'));
assert.equal(bars.length,24);
for(const y of [6,9,12])for(let n=0;n<8;n++)assert.ok(bars.find(x=>
  x.part_id==='BRICK_1X1'&&x.x_studs===17&&x.y_studs===y&&x.z_plates===32+3*n&&x.height_plates===3));
assert.ok(viewer.includes("p.opening_id==='right_glass_blocks'"));
assert.ok(viewer.includes("p.opening_id==='left_french_door'"));
const tallies=new Map();
for(const p of parts){const k=p.category+'|'+p.part_id;tallies.set(k,(tallies.get(k)||0)+1)}
assert.equal(b.bom.total_parts,parts.length);assert.equal(b.bom.unique_part_types,new Set(parts.map(x=>x.part_id)).size);
for(const l of b.bom.lines)assert.equal(l.quantity,tallies.get(l.category+'|'+l.part_id),'BOM line mismatch');
assert.equal(b.bom.lines.length,tallies.size);
console.log('M046 3/3 OPENINGS PASS; A 30 glass blocks + 2 true-brick courses; B 6+4 full upper beam; C recessed pane + 24 standard 1x1 jamb/mullion bricks');
console.log('M046 OUTSIDE THESE OPENINGS UNCHANGED; visual fidelity only, not physical LEGO certification');
