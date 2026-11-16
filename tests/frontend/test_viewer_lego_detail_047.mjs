import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { legoDetailFootprint, legoStudOffsets, selectLegoDetailIds, LEGO_DETAIL_M047_BUDGET } from '../../frontend/viewer-lego-detail-047.mjs';

const checks = [];
function check(label, run) { run(); checks.push(label); }
const brick=(placement_id, x_studs, y_studs, z_plates=0)=>({placement_id,part_id:'BRICK_1X2',category:'brick',x_studs,y_studs,z_plates,facade:'front'});
const windowBrick={placement_id:'glass',category:'window_pane',x_studs:20,y_studs:0,z_plates:9,facade:'front'};
check('1. Recognize real-format simple brick',()=>assert.deepEqual(legoDetailFootprint(brick('a',0,0)),{width:1,length:2}));
check('2. Correct quarter-turn dimensions',()=>assert.deepEqual(legoDetailFootprint({...brick('b',0,0),rotation_quarter_turns:1}),{width:2,length:1}));
check('3. Exclude non-brick glazing',()=>assert.equal(legoDetailFootprint(windowBrick),null));
check('4. Exclude slopes and oversized parts',()=>{assert.equal(legoDetailFootprint({...brick('s',0,0),part_id:'BRICK_SLOPED_2X1'}),null);assert.equal(legoDetailFootprint({...brick('o',0,0),part_id:'BRICK_2X8'}),null);});
check('5. Exact stud centers for 2x2',()=>assert.deepEqual(legoStudOffsets(2,2),[[-.5,-.5],[-.5,.5],[.5,-.5],[.5,.5]]));
check('6. Invalid footprint does not create studs',()=>assert.deepEqual(legoStudOffsets(0,3),[]));
const fixtures=[brick('far',0,0),brick('close',20,1),windowBrick,brick('closer',20,0,9)];
check('7. Detail picks bricks nearest actual window',()=>assert.deepEqual(selectLegoDetailIds(fixtures,2),['closer','close']));
check('8. Excluded pane never gets studs',()=>assert.ok(!selectLegoDetailIds(fixtures,4).includes('glass')));
check('9. Cap applies even to 2000 pieces',()=>{const p=Array.from({length:2000},(_,i)=>brick('p'+i,i,0));assert.equal(selectLegoDetailIds(p,48).length,48);});
check('10. No opening falls back to front facade',()=>{const p=[{...brick('rear',0,0),facade:'rear'},brick('front',9,9)];assert.deepEqual(selectLegoDetailIds(p,1),['front']);});
check('11. Blank or disabled budget safe',()=>{assert.deepEqual(selectLegoDetailIds([],24),[]);assert.deepEqual(selectLegoDetailIds(fixtures,0),[]);});
check('12. Mobile budget lower than desktop',()=>assert.ok(LEGO_DETAIL_M047_BUDGET.mobile<LEGO_DETAIL_M047_BUDGET.desktop));
const viewer=readFileSync(new URL('../../frontend/viewer.js',import.meta.url),'utf8');
const html=readFileSync(new URL('../../frontend/viewer.html',import.meta.url),'utf8');
check('13. Three.js instance studs limited and geometry rounded',()=>{assert.match(viewer,/new THREE\.InstancedMesh\(studGeometry/);assert.match(viewer,/new RoundedBoxGeometry\(/);});
check('14. Detail opt-out is wired and old loading kept',()=>{assert.match(viewer,/legoDetailToggle\?\.addEventListener\('change'/);assert.match(viewer,/function loadPendingExport\(/);assert.match(html,/id="lego-detail-toggle"/);});
check('15. Orbit damping disabled after release',()=>assert.match(viewer,/controls\.enableDamping=false/));
console.log(JSON.stringify({mission:'M047',total:checks.length,passed:checks.length,cases:checks},null,2));
