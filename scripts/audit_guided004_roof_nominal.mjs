// Read-only nominal roof-stud audit; NOT a LEGO physical certification.
// Run: node scripts/audit_guided004_roof_nominal.mjs [B3.ldr]
import {readFileSync} from "node:fs";
function auditRoof(raw){
 const dims={"3005":[1,1],"3004":[2,1],"3622":[3,1],"3010":[4,1],"3009":[6,1],"3008":[8,1],"3003":[2,2],"3002":[3,2],"3001":[4,2],"2456":[6,2],"3007":[8,2],"3006":[10,2],"3023b":[2,1],"3710":[4,1],"3666":[6,1],"3460":[8,1],"3623":[3,1]};
 const parts=[];let id=null;
 for(const line of raw.split(/\r?\n/)){
  if(line.startsWith("0 // ")){id=line.slice(5);continue}
  if(!line.startsWith("1 "))continue;
  const t=line.trim().split(/\s+/),ref=t[14].toLowerCase().replace(".dat",""),m=t.slice(5,14).map(Number);
  if(!id||t.length!==15||!(ref in dims||ref==="30363"))throw Error("Unexpected LDraw placement");
  parts.push({id,ref,x:+t[2],y:+t[3],z:+t[4],m});
 }
 const key=(x,y,z)=>[x,y,z].map(v=>Math.round(v*1000)/1000).join(","),studs=new Map();
 for(const p of parts){
  const d=dims[p.ref],xs=d?Array.from({length:d[0]},(_,i)=>(i-(d[0]-1)/2)*20):[-10,10],zs=d?Array.from({length:d[1]},(_,i)=>(i-(d[1]-1)/2)*20):[0];
  for(const x of xs)for(const z of zs){
   const k=key(p.x+p.m[0]*x+p.m[2]*z,p.y,p.z+p.m[6]*x+p.m[8]*z),a=studs.get(k)||[];
   a.push({id:p.id,ref:p.ref});studs.set(k,a);
  }
 }
 const roofs=parts.filter(p=>p.ref==="30363"),perRoof=[],byY={};
 for(const r of roofs){
  const cavities=[-10,10].map(x=>key(r.x+r.m[0]*x,r.y+24,r.z+r.m[6]*x));
  const matches=cavities.map(c=>(studs.get(c)||[]).filter(v=>v.id!==r.id)),count=matches.filter(x=>x.length).length;
  const ids=[...new Set(matches.flatMap(x=>x.map(v=>v.id)))];
  const row=byY[r.y]||(byY[r.y]={total:0,with_match:0,none:0});row.total++;if(count)row.with_match++;else row.none++;
  perRoof.push({id:r.id,x:r.x,y:r.y,z:r.z,matched_cavity_count:count,matched_ids:ids,matches_other_roof:ids.some(x=>x.startsWith("roof-"))});
 }
 if(parts.length!==1904||roofs.length!==408)throw Error("Model 1904/408 mismatch");
 const one=perRoof.filter(x=>x.matched_cavity_count===1),two=perRoof.filter(x=>x.matched_cavity_count===2),zero=perRoof.filter(x=>x.matched_cavity_count===0),roof2=perRoof.filter(x=>x.matches_other_roof);
 const known=perRoof.find(x=>x.id==="roof-000223");if(!known||known.matched_cavity_count!==2||!known.matched_ids.includes("wall-000719"))throw Error("Known 223/719 pair mismatch");
 if(zero.length!==369||one.length!==17||two.length!==22||roof2.length!==0)throw Error("Cross-check failed");
 return {source:"B3 1904-piece exact LDraw",ldraw_mirror_pin:"pybricks/ldraw c43ed06a128a10ed65675166bf42eb6fd608b9b0, parts/s/30363s01.dat",method:"30363 local stud centers x=±10,y=0,z=0; underside nominal cavity centers x=±10,y=24,z=0. Transform by actual LDraw matrices and compare to brick studs. Nominal-only, not mesh collision or assembly proof.",parts:parts.length,roof_count:roofs.length,with_both_cavities:two.length,with_one_cavity:one.length,without_cavity_stud_match:zero.length,roof_to_roof_direct_stud_matches:roof2.length,known_positive:"roof-000223 matches wall-000719",by_level:byY,all_roofs:perRoof,verdict:"BUILDABILITY_NOT_DEMONSTRATED"};
}
const p=process.argv[2]??"missions/B3/generated/GUIDED004-B3-1904.ldr";
console.log(JSON.stringify(auditRoof(readFileSync(p,"utf8")),null,2));
