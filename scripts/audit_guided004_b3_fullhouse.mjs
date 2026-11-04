// BOLDÜNGO: nominal whole-house screening, NOT a constructibility certificate.
// Run: node scripts/audit_guided004_b3_fullhouse.mjs [path-to-B3.ldr]
// Read-only: prints JSON to stdout; never mutates models.
import {readFileSync} from "node:fs";
function analyze(source) {
 const dims={"3005":[1,1,24],"3004":[2,1,24],"3622":[3,1,24],"3010":[4,1,24],"3009":[6,1,24],"3008":[8,1,24],"3003":[2,2,24],"3002":[3,2,24],"3001":[4,2,24],"2456":[6,2,24],"3007":[8,2,24],"3006":[10,2,24],"3023b":[2,1,8],"3710":[4,1,8],"3666":[6,1,8],"3460":[8,1,8],"3623":[3,1,8]};
 const parts=[];let id=null;
 for(const line of source.split(/\r?\n/)){
  if(line.startsWith("0 // ")){id=line.slice(5);continue;}
  if(!line.startsWith("1 "))continue;
  const a=line.trim().split(/\s+/);
  if(a.length!==15 || !id)throw Error("LDraw placement/header malformed");
  const ref=a[14].toLowerCase().replace(/\.dat$/,"");
  if(!dims[ref]&&ref!=="30363")throw Error("Unmodelled LEGO part "+ref);
  const d=dims[ref], m=a.slice(5,14).map(Number);
  if(m[4]!==1 || m[1]!==0 || m[3]!==0 || m[5]!==0 || m[7]!==0)throw Error("Non-upright part; nominal audit cannot apply: "+id);
  const p={id,ref,x:+a[2],y:+a[3],z:+a[4],height:d?.[2]??null,cells:null};
  if(d){
   p.cells=[];
   for(let i=0;i<d[0];i++)for(let j=0;j<d[1];j++){
    const lx=(i-(d[0]-1)/2)*20,lz=(j-(d[1]-1)/2)*20;
    const x=p.x+m[0]*lx+m[2]*lz,z=p.z+m[6]*lx+m[8]*lz;
    p.cells.push(`${Math.round(x*100)/100},${Math.round(z*100)/100}`);
   }
  }
  parts.push(p);
 }
 if(parts.length!==1904 || new Set(parts.map(p=>p.id)).size!==1904)throw Error("Expected exact B-3 1904 unique placements");
 const n=parts.length,parent=Array.from({length:n},(_,i)=>i),sizes=Array(n).fill(1),supported=Array(n).fill(0),layers=new Map();
 function root(i){while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i]}return i}
 function union(i,j){let a=root(i),b=root(j);if(a===b)return;if(sizes[a]<sizes[b])[a,b]=[b,a];parent[b]=a;sizes[a]+=sizes[b]}
 function family(id){if(id.startsWith("wall-"))return "walls";if(id.startsWith("window-"))return "windows";if(id.startsWith("gable-"))return "gables";if(id.startsWith("roof-"))return "roof";if(id.startsWith("scene-platform:"))return "terraces";if(id.startsWith("scene-stair:"))return "stairs";if(id.startsWith("scene-chimney:"))return "chimneys";if(id.startsWith("EXPERIMENT"))return "experiments";return "other"}
 for(let i=0;i<n;i++){
  const p=parts[i];if(!p.cells)continue;
  if(!layers.has(p.y))layers.set(p.y,new Map());
  const level=layers.get(p.y);
  for(const c of p.cells){if(!level.has(c))level.set(c,[]);level.get(c).push(i)}
 }
 let links=0,nominalStudMatches=0;
 for(let i=0;i<n;i++){
  const p=parts[i];if(!p.cells)continue;
  const matches=new Map();
  for(const h of [8,24]){
   const below=layers.get(p.y+h);if(!below)continue;
   for(const cell of p.cells)for(const j of below.get(cell)||[]){
    if(parts[j].height===h)matches.set(j,(matches.get(j)||0)+1);
   }
  }
  for(const [j,studs] of matches){links++;nominalStudMatches+=studs;supported[i]++;union(i,j)}
 }
 const cc=new Map();
 for(let i=0;i<n;i++){if(!parts[i].cells)continue;const r=root(i);if(!cc.has(r))cc.set(r,[]);cc.get(r).push(i)}
 const groups=[...cc.values()].sort((a,b)=>b.length-a.length).map(g=>{
  const byFamily={};for(const i of g)byFamily[family(parts[i].id)]=(byFamily[family(parts[i].id)]||0)+1;
  return {size:g.length,by_family:byFamily,examples:g.slice(0,4).map(i=>parts[i].id)};
 });
 const noNominalBelow=parts.flatMap((p,i)=>p.cells && !supported[i]?[{id:p.id,reference:p.ref,y_ldu:p.y,family:family(p.id)}]:[]);
 const noBelowByFamily={};for(const p of noNominalBelow)noBelowByFamily[p.family]=(noBelowByFamily[p.family]||0)+1;
 return {
  audit:"MAISON_COMPLETE1_NOMINAL_SCREENING_NOT_PHYSICAL_CERTIFICATE",
  input:"missions/B3/generated/GUIDED004-B3-1904.ldr",
  source_commit:"TO_BE_SET_FROM_CALLER",
  rules:"Only upright orthogonal brick/plate nominal stud footprint overlap; roofing 30363 excluded. No LDraw mesh, insertion, friction, structural load, or plastic tolerances. Missing vertical mate does not prove a part floats.",
  part_count:parts.length,
  orthogonal_bricks_and_plates:parts.filter(p=>p.cells).length,
  slopes_30363_unassessed:parts.filter(p=>p.ref==="30363").length,
  possible_vertical_part_links:links,
  matched_stud_centres:nominalStudMatches,
  nominal_orthogonal_components:groups.length,
  largest_groups:groups.slice(0,15),
  group_size_distribution:groups.reduce((a,g)=>{const k=g.size>=100?"100+":g.size>=10?"10-99":g.size>=2?"2-9":"1";a[k]=(a[k]||0)+1;return a},{}),
  without_nominal_vertical_mate: noNominalBelow.length,
  without_nominal_vertical_mate_at_local_lowest_course: noNominalBelow.filter(x=>x.y_ldu===-24).length,
  without_nominal_vertical_mate_above_local_lowest_course: noNominalBelow.filter(x=>x.y_ldu!==-24).length,
  without_nominal_mate_by_family:noBelowByFamily,
  all_parts_without_nominal_mate:noNominalBelow,
  verdict:"INITIAL_DIAGNOSTIC_ONLY"
 };
}
const filename=process.argv[2] ?? "missions/B3/generated/GUIDED004-B3-1904.ldr";
const r=analyze(readFileSync(filename,"utf8"));
console.log(JSON.stringify(r,null,2));
