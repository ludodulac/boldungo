// BOLDUNGO — Reproducible roof construction. Node 18+, read-only input, separate outputs.
// Run from repo root: node scripts/build_guided004_b3_stepped_roof.mjs [source.ldr] [out-dir]
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {join} from "node:path";
function buildSteppedRoof(raw) {
  // Prototype whole house, genuine LDraw parts. Nominal stud and solid-body check, NOT physical certification.
  const defs={"3005":[1,1,24],"3004":[2,1,24],"3622":[3,1,24],"3010":[4,1,24],"3009":[6,1,24],"3008":[8,1,24],"3003":[2,2,24],"3002":[3,2,24],"3001":[4,2,24],"2456":[6,2,24],"3007":[8,2,24],"3006":[10,2,24],"3023b":[2,1,8],"3710":[4,1,8],"3666":[6,1,8],"3460":[8,1,8],"3623":[3,1,8]};
  const all=[];let id=null;
  for(const line of raw.split(/\r?\n/)){
    if(line.startsWith("0 // ")){id=line.slice(5);continue}
    if(!line.startsWith("1 "))continue;
    const a=line.trim().split(/\s+/),ref=a[14]?.toLowerCase().replace(/\.dat$/,"");
    if(!id||a.length!==15||!(ref in defs||ref==="30363"))throw Error("Unknown LDraw line/part");
    const m=a.slice(5,14).map(Number);
    if(m[1]||m[3]||m[5]||m[7]||m[4]!==1)throw Error("Non-upright part");
    all.push({id,ref,x:+a[2],y:+a[3],z:+a[4],m,line});
  }
  if(all.length!==1904||all.filter(p=>p.ref==="30363").length!==408||new Set(all.map(x=>x.id)).size!==1904)throw Error("B3 expected 1904/408 unique parts");
  const fixed=all.filter(p=>p.ref!=="30363"),I=[1,0,0,0,1,0,0,0,1],R=[0,0,1,0,1,0,-1,0,0];
  const box=p=>{
    const d=defs[p.ref];if(!d)throw Error("Non-orthogonal part in box");
    const rx=10*(Math.abs(p.m[0])*d[0]+Math.abs(p.m[2])*d[1]),rz=10*(Math.abs(p.m[6])*d[0]+Math.abs(p.m[8])*d[1]);
    return [p.x-rx,p.x+rx,p.y,p.y+d[2],p.z-rz,p.z+rz];
  };
  const intersects=(a,b)=>a[0]<b[1]-.00001&&a[1]>b[0]+.00001&&a[2]<b[3]-.00001&&a[3]>b[2]+.00001&&a[4]<b[5]-.00001&&a[5]>b[4]+.00001;
  function cells(p) {
    const d=defs[p.ref],a=[];
    for(let i=0;i<d[0];i++)for(let j=0;j<d[1];j++){
      const x=(i-(d[0]-1)/2)*20,z=(j-(d[1]-1)/2)*20;
      a.push([p.x+p.m[0]*x+p.m[2]*z,p.z+p.m[6]*x+p.m[8]*z]);
    }return a;
  }
  const atTop=new Map(),key=(x,y,z)=>[x,y,z].join(",");
  function register(p){for(const [x,z] of cells(p)){const k=key(x,p.y,z),v=atTop.get(k)||[];v.push(p.id);atTop.set(k,v)}}
  for(const p of fixed)register(p);
  const fixedBB=fixed.map(part=>({part,bb:box(part)})),newParts=[],missed=[],courses=[],blockedReasons={};
  const validSupport=id=>id.startsWith("wall-")||id.startsWith("REBUILD-ROOF-");
  function supporting(x,y,z){return (atTop.get(key(x,y+24,z))||[]).filter(validSupport)}
  let seq=0;
  const kindByShape={
    "6,2":["2456",I],"4,2":["3001",I],"3,2":["3002",I],"2,2":["3003",I],"1,2":["3004",R],
    "6,1":["3009",I],"4,1":["3010",I],"3,1":["3622",I],"2,1":["3004",I],"1,1":["3005",I]
  };
  function tile(side,k,x,z,l,w,supports){
    const shape=kindByShape[`${l},${w}`];if(!shape)throw Error("Noncanonical tile");
    const p={id:`REBUILD-ROOF-${String(++seq).padStart(4,"0")}-${side}-K${k}`,x:x+(l-1)*10,y:-768-24*k,z:z+(w-1)*10,
             ref:shape[0],m:shape[1],side,k,support_ids:[...new Set(supports)],stud_supports:supports.length,
             footprint_studs:l*w};
    if(p.stud_supports<2)throw Error("Tile below support threshold");
    return p;
  }
  function tileBand(side,k,x0,zs,near){
    const n=zs.length,N=6*n,y=-768-24*k,conflict=[],support=[];
    for(let j=0;j<n;j++)for(let i=0;i<6;i++){
      const x=x0+20*i,z=zs[j],cell=[x-10,x+10,y,y+24,z-10,z+10];
      const bad=near.filter(o=>intersects(cell,o.bb)).map(o=>o.part.id);
      conflict.push(bad);support.push(supporting(x,y,z));
      for(const v of bad){const tag=v.startsWith("scene-chimney:")?"chimney":v.startsWith("gable-")?"gable":v.startsWith("wall-")?"wall":"other";blockedReasons[tag]=(blockedReasons[tag]||0)+1}
    }
    const valid=[];
    for(let zi=0;zi<n;zi++)for(let zlen=1;zlen<=2&&zi+zlen<=n;zlen++)
      for(let xi=0;xi<6;xi++)for(const xlen of [6,4,3,2,1]){
        if(xi+xlen>6||!kindByShape[`${xlen},${zlen}`])continue;
        let mask=0,ok=true,s=[];
        for(let a=zi;a<zi+zlen;a++)for(let b=xi;b<xi+xlen;b++){const v=a*6+b;mask|=(1<<v);if(conflict[v].length)ok=false;s.push(...support[v])}
        if(ok&&s.length>=2)valid.push({mask,xi,zi,xlen,zlen,s,score:xlen*zlen*100-1});
      }
    const FULL=(1<<N)-1;
    let chosen=valid.find(p=>p.mask===FULL&&p.xlen===6&&p.zlen===n);
    let selections;
    if(chosen)selections=[chosen];
    else{
      const memo=new Map();
      function solve(mask){
        if(mask===FULL)return {score:0,items:[]};
        if(memo.has(mask))return memo.get(mask);
        let idx=0;while(mask&(1<<idx))idx++;
        const skip=solve(mask|(1<<idx));let best={score:skip.score,items:skip.items};
        for(const p of valid)if((p.mask&(1<<idx))&&!(p.mask&mask)){
          const next=solve(mask|p.mask),score=p.score+next.score;
          if(score>best.score)best={score,items:[p,...next.items]};
        }
        memo.set(mask,best);return best;
      }
      selections=solve(0).items;
    }
    let covered=0;
    const out=[];
    for(const p of selections){covered|=p.mask;out.push(tile(side,k,x0+p.xi*20,zs[p.zi],p.xlen,p.zlen,p.s));}
    for(let zidx=0;zidx<n;zidx++)for(let xidx=0;xidx<6;xidx++){
      const v=zidx*6+xidx;
      if(!(covered&(1<<v)))missed.push({side,course:k,x:x0+xidx*20,z:zs[zidx],blocked_by:conflict[v],had_support:support[v].length>0});
    }
    return out;
  }
  for(let k=0;k<=7;k++){
    for(const side of (k===7?["RIDGE"]:["L","R"])){
      const x0=side==="L"?330+60*k:side==="R"?1170-60*k:750,y=-768-24*k;
      const zRows=Array.from({length:40},(_,i)=>70+20*i);
      const near=fixedBB.filter(o=>o.bb[2]<y+24&&o.bb[3]>y);
      const bands=[];
      if(k%2===0){for(let i=0;i<40;i+=2)bands.push(zRows.slice(i,i+2))}
      else{bands.push([zRows[0]]);for(let i=1;i<39;i+=2)bands.push(zRows.slice(i,i+2));bands.push([zRows[39]])}
      const begin=newParts.length,missStart=missed.length;
      for(const zBand of bands)for(const p of tileBand(side,k,x0,zBand,near)){
        const bb=box(p);
        for(const o of near)if(intersects(bb,o.bb))throw Error("Variant collides with original "+p.id+"/"+o.part.id);
        for(const q of newParts)if(intersects(bb,box(q)))throw Error("New roof collision "+p.id+"/"+q.id);
        newParts.push(p);register(p);
      }
      courses.push({course:k,side,roof_bricks:newParts.length-begin,uncovered_cells:missed.length-missStart});
    }
  }
  if(newParts.length<270||newParts.length>700)throw Error("Unexpected roof brick count "+newParts.length);
  if(missed.length>260)throw Error("Coverage below 92.7%: "+missed.length);
  const anchored=new Set();
  for(const p of newParts){
    if(p.stud_supports<2||!p.support_ids.length||!p.support_ids.every(id=>id.startsWith("wall-")||anchored.has(id)))throw Error("Missing true nominal path to wall "+p.id);
    anchored.add(p.id);
  }
  const ridge=newParts.filter(p=>p.side==="RIDGE");
  const byId=new Map(newParts.map(p=>[p.id,p]));
  const bridge=ridge.filter(p=>new Set(p.support_ids.map(id=>byId.get(id)?.side)).has("L")&&new Set(p.support_ids.map(id=>byId.get(id)?.side)).has("R")).length;
  if(bridge<15)throw Error("Ridge not bonded to both sides "+bridge);
  const eaves=newParts.filter(p=>p.k===0),wallAnchors=eaves.filter(p=>p.support_ids.some(id=>id.startsWith("wall-")));
  if(wallAnchors.length<25)throw Error("Too few eave to wall links "+wallAnchors.length);
  let coll=0;for(let i=0;i<newParts.length;i++)for(let j=i+1;j<newParts.length;j++)if(intersects(box(newParts[i]),box(newParts[j])))coll++;
  if(coll)throw Error("New collisions");
  const partLine=p=>["1","1",p.x,p.y,p.z,...p.m,p.ref+".dat"].join(" ");
  const ldr=[
    "0 FILE GUIDED004-B3-STEPPED-ROOF.ldr","0 BOLDUNGO - COMPLETE HOUSE EXPERIMENTAL STEPPED ROOF","0 !CATEGORY Model",
    "0 // All original B3 non-roof lines preserved, original 408 slopes removed only here.",
    "0 // Genuine LEGO references; nominal body and stud checks ONLY, no load or physical insertion certification.",
    ...fixed.flatMap(p=>["0 // "+p.id,p.line]),...newParts.flatMap(p=>["0 // "+p.id,partLine(p)]),"0 NOFILE",""
  ].join("\n");
  const partsByType={};for(const p of [...fixed,...newParts])partsByType[p.ref]=(partsByType[p.ref]||0)+1;
  const roofByType={};for(const p of newParts)roofByType[p.ref]=(roofByType[p.ref]||0)+1;
  const bboxTest="AABB nominal solid body only (orthogonal upright official LDraw standard dimensions); not mesh verification";
  const metric={
    status:"FULL_HOUSE_ROOF_VARIANT_NOMINALLY_CONNECTED_NOT_PHYSICALLY_CERTIFIED",
    B3_original_pieces:all.length,B3_original_nonroof_preserved:fixed.length,
    removed_old_sloped_30363_in_variant:408,
    new_roof_bricks:newParts.length,variant_total_pieces:fixed.length+newParts.length,
    new_roof_parts_with_2_or_more_nominal_support_studs:newParts.length,
    eave_parts_directly_on_original_wall_studs:wallAnchors.length,
    ridge_parts:ridge.length,ridge_parts_on_both_slopes:bridge,
    new_roof_total_stud_mates:newParts.reduce((a,b)=>a+b.stud_supports,0),
    projected_roof_grid_cells:3600,uncovered_grid_cells:missed.length,
    uncovered_due_to_nominal_obstacles:missed.filter(v=>v.blocked_by.length).length,
    uncovered_due_to_tiling_or_support:missed.filter(v=>!v.blocked_by.length).length,
    nominal_3D_body_overlap_new_vs_old:0,nominal_3D_body_overlap_new_vs_new:0,
    original_gables_preserved:fixed.filter(p=>p.id.startsWith("gable-")).length,
    original_chimney_parts_preserved:fixed.filter(p=>p.id.startsWith("scene-chimney:")).length,
    pitch:"7 brick courses, rise 24 LDU per 60 LDU horizontal; ridge at course 7",
    disclaimer:[bboxTest,"No full LDraw mesh collision audit.","No full insertion path, load/torque or real LEGO build test.","Openings around pre-existing chimneys; original external-platform issues remain."]
  };
  const bom={total:fixed.length+newParts.length,new_roof:newParts.length,new_roof_by_ldraw_ref:Object.fromEntries(Object.entries(roofByType).sort()),whole_by_ldraw_ref:Object.fromEntries(Object.entries(partsByType).sort()),safe_to_purchase:false};
  const order={status:"PROPOSED_ROOF_STEPS_INSERTION_UNVERIFIED",original_nonroof_placements_unchanged:fixed.length,steps:courses.map(c=>({side:c.side,course:c.course,ids:newParts.filter(p=>p.side===c.side&&p.k===c.course).map(p=>p.id)}))};
  return {ldr,metric,bom,order,courses,missing:missed,blockedReasons,newParts};
}
const source=process.argv[2]??"missions/B3/generated/GUIDED004-B3-1904.ldr";
const dir=process.argv[3]??"artifacts/maison-complete2";
if(dir.includes("missions/B3/generated")||dir.includes("frontend/data"))throw Error("Source overwrite refused");
const r=buildSteppedRoof(readFileSync(source,"utf8"));
mkdirSync(dir,{recursive:true});
for(const [path,value] of [["GUIDED004-B3-STEPPED-ROOF.ldr",r.ldr],["RESULTAT.json",JSON.stringify({metric:r.metric,courses:r.courses,holes:r.missing},null,2)+"\n"],["BOM.json",JSON.stringify(r.bom,null,2)+"\n"],["ORDRE-TOIT-PROPOSE.json",JSON.stringify(r.order,null,2)+"\n"]])writeFileSync(join(dir,path),value);
console.log(JSON.stringify(r.metric,null,2));
