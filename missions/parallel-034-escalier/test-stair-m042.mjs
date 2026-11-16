import assert from "node:assert/strict";
import fs from "node:fs";
import {buildM042} from "./build-stair-m042.mjs";
const dir=new URL(".",import.meta.url);
const B3=fs.readFileSync(new URL("../B3/generated/GUIDED004-B3-1904.ldr",dir),"utf8");
const M038=fs.readFileSync(new URL("ESCALIER-M038-IMPLANTATION.ldr",dir),"utf8");
const M034=fs.readFileSync(new URL("ESCALIER-M034-PROTOTYPE.ldr",dir),"utf8");
const Q038=JSON.parse(fs.readFileSync(new URL("CONTROLES-M038.json",dir),"utf8"));
const data=buildM042(B3,M038),q=data.qa;
const lines=s=>s.split(/\r?\n/).filter(x=>x.startsWith("1 "));
let tests=0;
const check=(name,truth)=>{assert.ok(truth,name);tests++;};
check("B3 original 1904",lines(B3).length===1904&&q.source_B3_parts===1904);
check("M038 original 1126",lines(M038).length===1126&&q.source_M038_parts===1126);
check("M034 original 485",lines(M034).length===485);
check("M038 dimensions and flights unchanged",Q038.upper_steps===9&&Q038.lower_steps===7&&Q038.width_m===1.10&&q.retained_M038_width_m===1.10);
check("exactly 7 new official LEGO parts",lines(data.adapterLDraw).length===7&&q.new_adapter_parts===7);
check("full house experimental file holds all parts",lines(data.experimentalFull).length===3037);
check("entire B3 type-1 sequence preserved",lines(data.experimentalFull).slice(0,1904).join("\n")===lines(B3).join("\n"));
check("entire M038 type-1 sequence preserved",lines(data.experimentalFull).slice(1904,3030).join("\n")===lines(M038).join("\n"));
check("exact real B3 concrete deck identified",q.joined_concrete_b3_refs.length===1&&q.joined_concrete_b3_refs[0]==="scene-platform:south-concrete-platform:deck:00289");
check("two M038 caps linked",q.joined_stair_m038_refs.length===2);
check("genuine jumper offset, two nominal anti-stud matches per cap",q.stair_to_adapter_nominal_sites===4&&q.stair_to_adapter_nominal_edges===2);
check("concrete 2456 studs to 3666 sockets",q.concrete_to_adapter_nominal_sites===2&&q.concrete_to_adapter_nominal_edges===1);
check("six unique new-to-new plate links",q.adapter_to_adapter_nominal_edges===6&&q.adapter_internal_connected_components===1);
check("no new-new AABB overlaps",q.new_vs_new_aabb_collision_pairs===0);
check("no new-B3 AABB overlaps",q.b3_vs_new_aabb_collision_pairs===0);
check("no new-M038 AABB overlaps",q.m038_vs_new_aabb_collision_pairs===0);
check("timber post alternative x190 rejected",q.failures_for_rejected_x190.some(x=>/DECK-BRACE|timber-deck/.test(x.b)));
check("no certified clutch/insertion/strength",q.connection_strength_certified===false&&q.insertion_sequence_tested===false&&q.true_LDraw_solid_mesh_intersection_tested===false);
check("diagram shows wall and real concrete",data.overview.includes("Façade Sud")&&data.overview.includes("Plateforme béton"));
const edited=B3.replace("1 15 470 -96 50 1 0 0 0 1 0 0 0 1 3005.dat","1 15 170 -288 350 1 0 0 0 1 0 0 0 1 3005.dat");
check("negative: inserted obstacle in candidate path rejected",edited!==B3&&(()=>{
  try{buildM042(edited,M038);return false;}catch(e){return String(e).includes("NO_NOMINAL_ADAPTER_CAN_BE_BUILT");}
})());
check("negative: missing B3 source part refused",(()=>{
  try{buildM042(B3.replace("1 15 470 -96 50 1 0 0 0 1 0 0 0 1 3005.dat",""),M038);return false;}
  catch(e){return String(e).includes("SOURCE_CHANGED_B3_OR_M038");}
})());
check("negative: missing M038 source part refused",(()=>{
  try{buildM042(B3,M038.replace(lines(M038)[0],""));return false;}
  catch(e){return String(e).includes("SOURCE_CHANGED_B3_OR_M038");}
})());
console.log(JSON.stringify({mission:"M042",targeted_passed:tests,nominal_sites:{
  concrete:q.concrete_to_adapter_nominal_sites,stair:q.stair_to_adapter_nominal_sites},
  adapter_parts:q.new_adapter_parts,collisions:0,not_certified:true},null,2));
