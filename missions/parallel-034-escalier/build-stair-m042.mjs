/**
 * BOLDUNGO / CONSTRUCTION 3 / M042: adapter between the unchanged B3
 * concrete platform and the unchanged M038 stair.
 *
 * Strictly nominal LEGO connector lattice (not full LDraw mesh certification).
 * No changes to original source, terrace, roof or common engine.
 * Regenerate: node missions/parallel-034-escalier/build-stair-m042.mjs
 */
import fs from "node:fs";

const D={
 "3005.dat":[1,1,3],"3004.dat":[1,2,3],"3622.dat":[1,3,3],
 "3010.dat":[1,4,3],"3009.dat":[1,6,3],"3008.dat":[1,8,3],
 "3003.dat":[2,2,3],"3002.dat":[2,3,3],"3001.dat":[2,4,3],
 "2456.dat":[2,6,3],"3007.dat":[2,8,3],"3006.dat":[2,10,3],
 "3666.dat":[1,6,1],"3460.dat":[1,8,1],"3623.dat":[1,3,1],
 "3023b.dat":[1,2,1],"3023.dat":[1,2,1],"3024.dat":[1,1,1],
 "3710.dat":[1,4,1],"3794b.dat":[1,2,1]
};
const face=(a,b)=>a[0]<b[3]&&b[0]<a[3]&&a[1]<b[4]&&b[1]<a[4]&&a[2]<b[5]&&b[2]<a[5];
const unique=a=>[...new Set(a)];
const key=(x,z)=>x+","+z;
function parse(source,origin) {
  let id="",parts=[],slopes=0;
  for(const line of source.split(/\r?\n/)){
    if(line.startsWith("0 // "))id=line.slice(5);
    if(!line.startsWith("1 "))continue;
    let t=line.trim().split(/\s+/);
    if(t.length!==15)throw Error("BAD_LDRAW_TYPE1:"+origin);
    let ref=t[14].toLowerCase(),d=D[ref],xyz=t.slice(2,5).map(Number),rot=t.slice(5,14).map(Number);
    if(ref==="30363.dat"){slopes++;continue;}
    if(!d)throw Error("UNKNOWN_REFERENCE:"+ref);
    const w=Math.abs(rot[0])*d[0]+Math.abs(rot[2])*d[1],
          depth=Math.abs(rot[6])*d[0]+Math.abs(rot[8])*d[1];
    if(w<1||depth<1||w%1||depth%1||w*depth!==d[0]*d[1]||
        rot[4]!==1||rot[1]||rot[3]||rot[5]||rot[7])throw Error("NON_ORTHOGONAL");
    const [X,Y,Z]=xyz;
    parts.push({id,origin,ref,xyz,rot,
      box:[X-w*10,Y,Z-depth*10,X+w*10,Y+8*d[2],Z+depth*10]});
  }
  return {parts,slopes};
}
function points(p,kind) {
  const b=p.box,xs=[],zs=[];
  for(let x=b[0]+10;x<b[3];x+=20)xs.push(x);
  for(let z=b[2]+10;z<b[5];z+=20)zs.push(z);
  if(kind==="stud"&&p.ref==="3794b.dat")
    return [[(b[0]+b[3])/2,(b[2]+b[5])/2]];
  return xs.flatMap(x=>zs.map(z=>[x,z]));
}
function links(lower,upper) {
  // lower's upper studs at its TOP plane == upper's cavities at its BOTTOM plane.
  if(lower.box[1]!==upper.box[4])return [];
  const s=new Set(points(lower,"stud").map(q=>key(...q)));
  return points(upper,"cavity").filter(q=>s.has(key(...q)));
}
const fmt=(p)=>"0 // "+p.id+" "+p.origin+"\n"+
 "1 "+p.color+" "+p.xyz.join(" ")+" "+p.rot.join(" ")+" "+p.ref;
function partsAsLDraw(title,parts) {
  return ["0 FILE "+title,"0 BOLDUNGO M042 — experimental adapter only; no physical strength claim",
          "0 !CATEGORY Model",...parts.map(fmt),"0 NOFILE",""].join("\n");
}
function appendToLDraw(title,source,stair,parts) {
  const lines=(s)=>s.split(/\r?\n/).filter(l=>l&&!l.startsWith("0 FILE ")&&!l.startsWith("0 NOFILE"));
  return ["0 FILE "+title,"0 !CATEGORY Model",
    "0 // Full-house experiment: original B3 1904 and M038 1126 unchanged",
    "0 // 7 new adapter parts only; nominal connector lattice, insertion NOT certified",
    "0 // SOURCE B3 UNCHANGED",...lines(source),
    "0 // SOURCE M038 UNCHANGED",...lines(stair),
    "0 // NEW M042 ADAPTER",...parts.map(fmt),
    "0 NOFILE",""].join("\n");
}
function make(x) {
 const R=[0,0,-1,0,1,0,1,0,0],I=[1,0,0,0,1,0,0,0,1],a=[];
 const part=(id,ref,X,Y,Z,rot,color)=> {
   const d=D[ref],w=Math.abs(rot[0])*d[0]+Math.abs(rot[2])*d[1],
       depth=Math.abs(rot[6])*d[0]+Math.abs(rot[8])*d[1];
   a.push({id:"M042-"+id,ref,origin:"new-adapter",color,xyz:[X,Y,Z],rot,
     box:[X-10*w,Y,Z-10*depth,X+10*w,Y+8*d[2],Z+10*depth]});
 };
 // Exact half-stud transition: existing M038 cap has x=160/180 studs,
 // existing B3 concrete deck has x=170 studs.
 for(const z of [350,370]){
   part("jumper-"+z,"3794b.dat",x,-272,z,R,8);
   part("stem-1-"+z,"3024.dat",x,-280,z,I,7);
   part("stem-2-"+z,"3024.dat",x,-288,z,I,7);
 }
 part("bridge-1x6","3666.dat",x,-296,320,I,71);
 return a;
}
function validateCandidate(b3,stair,a) {
 const errors=[];
 for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)
  if(face(a[i].box,a[j].box))errors.push({kind:"new-new",a:a[i].id,b:a[j].id});
 for(const p of a)for(const q of b3.parts)
  if(face(p.box,q.box))errors.push({kind:"new-B3",a:p.id,b:q.id});
 for(const p of a)for(const q of stair.parts)
  if(face(p.box,q.box))errors.push({kind:"new-M038",a:p.id,b:q.id});
 const found=[],seenEdges=new Set(),edge=(lo,up)=>{
   const pairKey=lo.id+"|"+up.id;
   if(seenEdges.has(pairKey))return;
   const sites=links(lo,up);
   if(sites.length){seenEdges.add(pairKey);found.push({lower:lo.id,upper:up.id,origin_low:lo.origin,origin_up:up.origin,sites});}
 };
 // Limit connectors to physically precise neighbours (no side contact).
 for(const p of [...b3.parts,...stair.parts,...a])for(const q of a)
   if(p!==q){edge(p,q);edge(q,p);}
 const concrete=b3.parts.filter(p=>p.id.startsWith("scene-platform:south-concrete-platform:deck:"));
 const joinedConcrete=found.filter(e=>e.origin_low==="B3"&&e.origin_up==="new-adapter"&&e.lower.startsWith("scene-platform:south-concrete-platform:deck:"));
 const joinedStair=found.filter(e=>e.origin_low==="M038"&&e.origin_up==="new-adapter"&&e.lower.includes(" high cap"));
 const newNew=found.filter(e=>e.origin_low==="new-adapter"&&e.origin_up==="new-adapter");
 const byId=new Map(a.map(p=>[p.id,p]));
 const parent=new Map(a.map(p=>[p.id,p.id]));
 const root=i=>{while(parent.get(i)!==i)i=parent.get(i);return i;};
 for(const e of newNew)parent.set(root(e.lower),root(e.upper));
 const componentCount=new Set(a.map(p=>root(p.id))).size;
 return {errors,found,concrete,joinedConcrete,joinedStair,newNew,componentCount,
  allM038:stair.parts.length, allB3:b3.parts.length};
}
function drawPlan(b3,stair,adapter,report) {
 const X=x=>80+(350-x)*1.15,Z=z=>145+(z-100)*0.67;
 const rect=(b,c,opacity=1,stroke="none")=>'<rect x="'+X(b[3]).toFixed(2)+'" y="'+Z(b[2]).toFixed(2)+
   '" width="'+((b[3]-b[0])*1.15).toFixed(2)+'" height="'+((b[5]-b[2])*.67).toFixed(2)+
   '" fill="'+c+'" opacity="'+opacity+'" stroke="'+stroke+'"/>';
 const concrete=b3.parts.filter(p=>p.id.startsWith("scene-platform:south-concrete-platform:deck:")&&p.box[1]===-288);
 const walls=b3.parts.filter(p=>p.id.startsWith("wall-")&&p.xyz[0]===330&&p.box[2]<900).slice(0,50);
 const wood=b3.parts.filter(p=>p.id.startsWith("scene-platform:south-timber-deck")&&p.id.includes("board")&&p.box[1]<=-288);
 const caps=stair.parts.filter(p=>p.id.includes(" high cap")&&p.box[1]>=-280);
 const landing=stair.parts.filter(p=>p.id.includes(" landing")&&p.box[1]===-128);
 const lower=stair.parts.filter(p=>p.id.includes(" low cap"));
 const highlights=report.joinedConcrete.map(e=>e.lower);
 return ['<svg xmlns="http://www.w3.org/2000/svg" width="1150" height="820" viewBox="0 0 1150 820">',
 '<rect width="1150" height="820" fill="#f5f8fc"/>',
 '<text x="30" y="43" font-family="Arial" font-size="26" font-weight="bold" fill="#1d3452">BOLDÜNGO M042 · jonction escalier / béton B3</text>',
 '<text x="30" y="68" font-family="Arial" font-size="15" fill="#62798d">Plan coté en LDU du B3 existant + M038 inchangé + 7 pièces neuves (connexion nominale seulement)</text>',
 '<rect x="30" y="92" width="690" height="665" rx="12" fill="white" stroke="#d7e0e9"/>',
 ...walls.map(p=>rect(p.box,"#687c88",.22)),
 ...wood.map(p=>rect(p.box,"#e4b27d",.22)),
 ...concrete.map(p=>rect(p.box,highlights.includes(p.id)?"#8399b1":"#9daeba",.5)),
 ...lower.map(p=>rect(p.box,"#57a08e",.8)),
 ...landing.map(p=>rect(p.box,"#dbab63",.4)),
 ...caps.map(p=>rect(p.box,"#417fa7",.75)),
 ...adapter.filter(p=>p.ref==="3666.dat").map(p=>rect(p.box,"#ec6340",.93)),
 ...adapter.filter(p=>p.ref==="3794b.dat").map(p=>rect(p.box,"#fbbe3d",.93)),
 '<text x="46" y="120" font-family="Arial" font-size="15" fill="#384f63">Façade Sud à droite → (x positif Nord)</text>',
 '<text x="45" y="724" font-family="Arial" font-size="14" fill="#607889">Ouest (+z) ↓ · Le débord arrière photographique reste à coter.</text>',
 '<rect x="738" y="92" width="390" height="665" rx="12" fill="white" stroke="#d7e0e9"/>',
 '<text x="764" y="135" font-family="Arial" font-size="20" font-weight="bold" fill="#1d3452">Raccord ajouté à l’arrivée haute</text>',
 ...[[0,"#8399b1","Plateforme béton existante B3"],[1,"#417fa7","9 marches hautes M038"],[2,"#57a08e","7 marches basses M038"],[3,"#dbab63","Palier intermédiaire M038"],[4,"#ec6340","Plaque-pont 1×6 M042"],[5,"#fbbe3d","Jumpers à demi-tenon M042"],[6,"#e4b27d","Terrasse bois conservée"]].map(([i,c,label])=>'<rect x="765" y="'+(169+i*38)+'" width="18" height="18" fill="'+c+'"/><text x="795" y="'+(183+i*38)+'" font-family="Arial" font-size="14" fill="#2b4053">'+label+'</text>'),
 '<text x="765" y="491" font-family="Arial" font-size="17" font-weight="bold" fill="#34546d">Largeur : 1,10 m ≈ 1,12 m</text>',
 '<text x="765" y="531" font-family="Arial" font-size="15" fill="#34546d">B3 : '+report.allB3+' pièces intactes</text>',
 '<text x="765" y="560" font-family="Arial" font-size="15" fill="#34546d">M038 : '+report.allM038+' pièces intactes</text>',
 '<text x="765" y="589" font-family="Arial" font-size="15" fill="#34546d">M042 : '+adapter.length+' pièces ajoutées</text>',
 '<text x="765" y="635" font-family="Arial" font-size="15" fill="#a34539">⚠ Insertabilité non testée</text>',
 '<text x="765" y="663" font-family="Arial" font-size="15" fill="#a34539">⚠ Résistance non démontrée</text>',
 '<text x="765" y="691" font-family="Arial" font-size="15" fill="#a34539">⚠ Plan photo partiellement inféré</text>',
 '</svg>'].join("\n")+"\n";
}
export function buildM042(b3Text,m038Text) {
 const b3=parse(b3Text,"B3"),stair=parse(m038Text,"M038");
 if(b3.parts.length!==1496||b3.slopes!==408||stair.parts.length!==1126||stair.slopes)
   throw Error("SOURCE_CHANGED_B3_OR_M038");
 const copper=b3.parts.filter(p=>p.id.startsWith("scene-platform:south-concrete-platform:deck:"));
 if(copper.length!==22)throw Error("CONCRETE_DECK_CHANGED");
 const candidates=[170,190].map(x=>({x,parts:make(x)}));
 const reports=candidates.map(c=>({x:c.x,...validateCandidate(b3,stair,c.parts)}));
 const valid=reports.find(r=>!r.errors.length&&r.componentCount===1&&r.joinedConcrete.length>0&&r.joinedStair.length>=2);
 if(!valid)throw Error("NO_NOMINAL_ADAPTER_CAN_BE_BUILT:"+reports.map(r=>r.x+":"+r.errors.length+":"+r.joinedConcrete.length+":"+r.joinedStair.length).join(";"));
 const adapter=candidates.find(c=>c.x===valid.x).parts;
 // Each of the seven authentic parts must be within the connected adapter graph.
 if(new Set(adapter.map(p=>p.ref)).size!==3||valid.newNew.length<6||
    valid.joinedConcrete.reduce((s,e)=>s+e.sites.length,0)<2)
   throw Error("UNPROVEN_ADAPTER_CONNECTIONS");
 const originalB3Types=b3Text.split(/\r?\n/).filter(l=>l.startsWith("1 ")).length;
 const originalStairTypes=m038Text.split(/\r?\n/).filter(l=>l.startsWith("1 ")).length;
 const combined=appendToLDraw("GUIDED004-B3-ESCALIER-M042-EXPERIMENTAL.ldr",b3Text,m038Text,adapter);
 if(combined.split(/\r?\n/).filter(l=>l.startsWith("1 ")).length!==originalB3Types+originalStairTypes+7)
  throw Error("FULL_HOUSE_COUNT_DRIFT");
 const q={
  mission:"M042",source_B3_parts:originalB3Types,source_M038_parts:originalStairTypes,
  source_B3_slope_parts_not_mesh_tested:b3.slopes,
  retained_M038_steps:{upper:9,lower:7},retained_M038_width_m:1.10,
  new_adapter_parts:7,new_adapter_refs:{"3794b.dat":2,"3024.dat":4,"3666.dat":1},
  joined_concrete_b3_refs:unique(valid.joinedConcrete.map(e=>e.lower)),
  joined_stair_m038_refs:unique(valid.joinedStair.map(e=>e.lower)),
  concrete_to_adapter_nominal_edges:valid.joinedConcrete.length,
  concrete_to_adapter_nominal_sites:valid.joinedConcrete.reduce((s,e)=>s+e.sites.length,0),
  stair_to_adapter_nominal_edges:valid.joinedStair.length,
  stair_to_adapter_nominal_sites:valid.joinedStair.reduce((s,e)=>s+e.sites.length,0),
  adapter_to_adapter_nominal_edges:valid.newNew.length,
  adapter_internal_connected_components:valid.componentCount,
  coordinates_LDU:{adapter_x:valid.x,upper_cap_top_y:-264,concrete_top_y:-288,bridge_top_y:-296,
    original_deck_end_z:300,stair_start_z:340},
  empty_bridge_span_z_LDU:[300,340],
  failures_for_rejected_x190:reports.find(r=>r.x===190).errors.slice(0,12),
  b3_vs_new_aabb_collision_pairs:0,m038_vs_new_aabb_collision_pairs:0,new_vs_new_aabb_collision_pairs:0,
  original_B3_untouched:true,original_M038_untouched:true,
  true_LDraw_solid_mesh_intersection_tested:false,
  ldraw_official_refs_verified:"3794b jumper 1x2 centre stud, 3024 plate 1x1, 3666 plate 1x6",
  LDCad_shadow_socket_clutch_tested:false,
  connection_strength_certified:false,insertion_sequence_tested:false,
  photo_fit_fully_certified:false,
  roof_collision_note:"408 slope meshes uninstantiated; nearest slope center x>=350 LDU, adapter occupies x<=190.",
  comment:"Only nominal stud/cavity mating at identified planes; existing platform wood/wall kept unchanged."
 };
 return {
  qa:q,adapter,links:valid.found,
  adapterLDraw:partsAsLDraw("ADAPTATEUR-M042-7-PIECES.ldr",adapter),
  experimentalFull:combined,
  overview:drawPlan(b3,stair,adapter,valid),
  inventory:["# M042 — ajout uniquement (M038 et B3 intacts)","","| Référence LDraw | Nom | Quantité |","|---|---|---:|",
    "| 3794b.dat | Jumper 1 × 2, tenon centré | 2 |",
    "| 3024.dat | Plaque 1 × 1 | 4 |",
    "| 3666.dat | Plaque 1 × 6 | 1 |",
    "| **TOTAL ajouté** | | **7** |",
    "","Le fichier complet expérimental contient 1 904 + 1 126 + 7 = 3 037 pièces.",
    "Points d'attache: joints nominaux, pas de certification de serrage / d'insertion / de stabilité."].join("\n")+"\n"
 };
}
if(process.argv[1]&&process.argv[1].endsWith("build-stair-m042.mjs")){
 const dir=new URL(".",import.meta.url),
   b3=fs.readFileSync(new URL("../B3/generated/GUIDED004-B3-1904.ldr",dir),"utf8"),
   m038=fs.readFileSync(new URL("ESCALIER-M038-IMPLANTATION.ldr",dir),"utf8"),
   o=buildM042(b3,m038);
 const out=[["ADAPTATEUR-M042-7-PIECES.ldr",o.adapterLDraw],
   ["GUIDED004-B3-ESCALIER-M042-EXPERIMENTAL.ldr",o.experimentalFull],
   ["APERCU-M042-LIAISON.svg",o.overview],
   ["NOMENCLATURE-M042.md",o.inventory],
   ["CONTROLES-M042.json",JSON.stringify(o.qa,null,2)+"\n"]];
 for(const [name,value] of out)fs.writeFileSync(new URL(name,dir),value);
 console.log("M042 PASS",JSON.stringify({pieces:o.qa.new_adapter_parts,concrete_sites:o.qa.concrete_to_adapter_nominal_sites,stair_sites:o.qa.stair_to_adapter_nominal_sites,collisions:0}));
}
