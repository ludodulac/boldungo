// BOLDUNGO M038: photo-guided, isolated L stair. Run: node missions/parallel-034-escalier/build-stair-m038.mjs
export function buildM038(b3){
 const lowH=[13,11,9,8,6,5,3];
 const C=[],P=[],part={1:"3024.dat",2:"3023.dat",3:"3623.dat",4:"3710.dat"};
 const put=(x,z,H,g,s)=>C.push({x,z,H,g,s});
 for(let s=0;s<9;s++)for(let x=0;x<5;x++)for(let z=2*s;z<2*s+2;z++)put(x,z,33-2*s,"high",9-s);
 for(let x=0;x<5;x++)for(let z=18;z<23;z++)put(x,z,16,"landing",0);
 for(let s=0;s<7;s++)for(let x=-2-2*s;x<-2*s;x++)for(let z=19;z<24;z++)put(x,z,lowH[s],"low",7-s);
 if(new Set(C.map(c=>c.x+","+c.z)).size!==C.length)throw Error("DUPLICATE_PLANE");
 const add=(kind,x,z,X,Z,h,ref,g,s)=>P.push({kind,x,z,X,Z,h,ref,g,s,id:"M038-"+String(P.length+1).padStart(5,"0")});
 // Orthogonal 1xN plate courses, staggered, complete interior without overlap.
 for(let h=0;h<35;h++){
  const axis=h%2?"z":"x",other=axis==="x"?"z":"x",rows=new Map();
  for(const c of C){if(h>=(c.g==="landing"?c.H:c.H-2))continue;
   if(!rows.has(c[other]))rows.set(c[other],[]);rows.get(c[other]).push(c);}
  for(const [k,a] of rows){a.sort((u,v)=>u[axis]-v[axis]);let i=0;
   while(i<a.length){let j=i+1;while(j<a.length&&a[j][axis]===a[j-1][axis]+1)j++;
    let pos=i;while(pos<j){const n=Math.min(pos===i?1+(h+Math.abs(k))%4:4,j-pos),f=a[pos],l=a[pos+n-1];
     add("core",f.x,f.z,axis==="x"?l.x+1:f.x+1,axis==="z"?l.z+1:f.z+1,h,part[n],f.g,f.s);pos+=n;}i=j;
   }
  }
 }
 // 3794b official 1x2 jumper: ONE centre stud, standard underside cavities.
 // Upper cap shifts +0.5 stud toward house; lower cap shifts -0.5 toward front.
 for(let s=0;s<9;s++){const h=33-2*s;
  for(let z=2*s;z<2*s+2;z++){
   add("jumper",0,z,2,z+1,h-2,"3794b.dat","high",9-s);
   add("jumper",3,z,5,z+1,h-2,"3794b.dat","high",9-s);
   add("cap",.5,z,3.5,z+1,h-1,"3623.dat","high",9-s);
   add("cap",3.5,z,5.5,z+1,h-1,"3023.dat","high",9-s);
  }
 }
 for(let s=0;s<7;s++){const h=lowH[s];
  for(let x=-2-2*s;x<-2*s;x++){
   add("jumper",x,19,x+1,21,h-2,"3794b.dat","low",7-s);
   add("jumper",x,21,x+1,23,h-2,"3794b.dat","low",7-s);
   add("cap",x,18.5,x+1,20.5,h-1,"3023.dat","low",7-s);
   add("cap",x,20.5,x+1,23.5,h-1,"3623.dat","low",7-s);
  }
 }
 const box=p=>[140+20*p.x,-8*(p.h+1),340+20*p.z,140+20*p.X,-8*p.h,340+20*p.Z];
 const boxes=P.map(box);
 const hit=(a,b)=>a[0]<b[3]&&b[0]<a[3]&&a[1]<b[4]&&b[1]<a[4]&&a[2]<b[5]&&b[2]<a[5];
 let collision=0;
 for(let i=0;i<P.length;i++)for(let j=i+1;j<P.length;j++)if(P[i].h===P[j].h&&hit(boxes[i],boxes[j]))collision++;
 if(collision)throw Error("NEW_BOX_COLLISION:"+collision);
 // Determine exact nominal stud/cavity matches, not blind face overlap.
 const cavity=p=>{let o=[];for(let x=p.x+.5;x<p.X;x++)for(let z=p.z+.5;z<p.Z;z++)o.push([x,z]);return o;};
 const stud=p=>p.kind==="jumper"?(p.X-p.x===2?[[p.x+1,p.z+.5]]:[[p.x+.5,p.z+1]]):cavity(p);
 const K=([x,z])=>Math.round(x*2)+","+Math.round(z*2),byLevel=new Map();
 for(let i=0;i<P.length;i++){const lev=P[i].h+1;if(!byLevel.has(lev))byLevel.set(lev,new Map());const m=byLevel.get(lev);
  for(const c of stud(P[i])){const k=K(c);if(!m.has(k))m.set(k,[]);m.get(k).push(i);}}
 const parent=P.map((_,i)=>i);const root=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
 const join=(a,b)=>{a=root(a);b=root(b);if(a!==b)parent[b]=a;};
 let site=0,edge=0,unsupported=0,cap=0,jump=0;
 for(let i=0;i<P.length;i++){if(P[i].h===0)continue;const m=byLevel.get(P[i].h)||new Map(),s=new Set();
  for(const c of cavity(P[i]))for(const j of m.get(K(c))||[]){s.add(j);site++;
   if(P[i].kind==="cap"&&P[j].kind==="jumper")cap++;
   if(P[i].kind==="jumper"&&P[j].kind==="core")jump++;
  }
  if(!s.size)unsupported++;for(const j of s){join(i,j);edge++;}
 }
 let roots=new Map();for(let i=0;i<P.length;i++){let r=root(i);if(!roots.has(r))roots.set(r,[]);roots.get(r).push(i);}
 const components=roots.size,compInfo=[...roots.values()].map(ids=>({n:ids.length,kind:[...new Set(ids.map(i=>P[i].g))],box:[Math.min(...ids.map(i=>boxes[i][0])),Math.max(...ids.map(i=>boxes[i][3])),Math.min(...ids.map(i=>boxes[i][2])),Math.max(...ids.map(i=>boxes[i][5]))]}));
 // Precise AABB collision check vs immutable authentic B3 (do not erase any old part).
 const D={"3005.dat":[1,1,3],"3004.dat":[1,2,3],"3622.dat":[1,3,3],"3010.dat":[1,4,3],"3009.dat":[1,6,3],"3008.dat":[1,8,3],
  "3003.dat":[2,2,3],"3002.dat":[2,3,3],"3001.dat":[2,4,3],"2456.dat":[2,6,3],"3007.dat":[2,8,3],"3006.dat":[2,10,3],
  "3666.dat":[1,6,1],"3460.dat":[1,8,1],"3623.dat":[1,3,1],"3023b.dat":[1,2,1],"3710.dat":[1,4,1]};
 let cnt=0,slopes=0,ortho=0,against=0,group="",examples=[],concrete=[],timber=[];
 for(const l of b3.split(/\n/)){if(l.startsWith("0 // "))group=l.slice(5);if(!l.startsWith("1 "))continue;cnt++;
  let t=l.trim().split(/\s+/),ref=t[14].toLowerCase();
  if(ref==="30363.dat"){slopes++;continue;}
  let d=D[ref];if(!d)throw Error("UNKNOWN_B3_REF:"+ref);ortho++;
  const X=+t[2],Y=+t[3],Z=+t[4],w=Math.abs(+t[5])*d[0]+Math.abs(+t[7])*d[1],dep=Math.abs(+t[11])*d[0]+Math.abs(+t[13])*d[1];
  const b=[X-10*w,Y,Z-10*dep,X+10*w,Y+8*d[2],Z+10*dep];
  if(group.startsWith("scene-platform:south-concrete-platform:deck"))concrete.push(b);
  if(group.startsWith("scene-platform:south-timber-deck")&&group.includes("board"))timber.push(b);
  for(let j=0;j<boxes.length;j++)if(hit(boxes[j],b)){against++;if(examples.length<8)examples.push({source:group,ref,prototype:P[j].id});}
 }
 if(cnt!==1904||slopes!==408||ortho!==1496)throw Error("B3_SIZE_MISMATCH");
 const inventory={};for(const p of P)inventory[p.ref]=(inventory[p.ref]||0)+1;
 const ldraw=["0 FILE ESCALIER-M038.ldr","0 BOLDUNGO M038 7+9 stair in L / 5.5-stud tread envelope",
  "0 // Model only, NO wall connector, NO proof of real strength or insertability",...P.map((p)=>{
   const b=box(p),orientation=p.X-p.x>1?"0 0 -1 0 1 0 1 0 0":"1 0 0 0 1 0 0 0 1",color=p.kind==="cap"?71:p.kind==="jumper"?8:7;
   return "0 // "+p.id+" "+p.g+" "+p.kind+"\n1 "+color+" "+((b[0]+b[3])/2)+" "+b[1]+" "+((b[2]+b[5])/2)+" "+orientation+" "+p.ref;
  }),"0 NOFILE",""].join("\n");
 const bom=["# M038 — pièces LEGO réelles","", "5,5 tenons ≈ 1,10 m ; jumpers 3794b à tenon central (officiels LDraw).","",
  "| Pièce LDraw | Quantité |","|---|---:|",...Object.entries(inventory).sort().map(([k,v])=>"| "+k+" | "+v+" |"),"| **TOTAL** | **"+P.length+"** |",""].join("\n");
 const qa={source_head:"20fc51c988e1f478fecadd4d32c2a19ce378e332",b3_parts:cnt,slopes_not_mesh_checked:slopes,
  orthogonal_original_parts_checked:ortho,prototype_parts:P.length,inventory,upper_steps:9,lower_steps:7,
  width_studs:5.5,width_m:1.1,target_approx_m:1.12,width_delta_m:-0.02,
  upper_flight_Z_LDU:[340,700],landing_Z_LDU:[700,800],wall_south_surface_X_LDU:320,
  upper_cap_X_LDU:[150,250],concrete_edge_Z_LDU_approx:340,
  highest_tread_height_m_assumed:2.64,going_m_assumed:0.40,riser_m_assumed:0.16,
  original_vs_new_volume_collisions:against,new_volume_collisions:collision,
  nominal_stud_cavity_sites:site,nominal_piece_to_piece_edges:edge,nominal_components:components,component_info:compInfo,
  nominal_unsupported_pieces:unsupported,offical_jumper_3794b_cap_sites:cap,jumper_3794b_core_sites:jump,
  bbox_collision_examples:examples,full_mesh_check:false,load_bearing_verified:false,continuous_insertion:false,
  actual_house_attachment:"NONE_PROVEN",rear_overrun_not_retained:"Unresolved contradiction with original B3 concrete platform location",
  photos_directly_viewed:["IMG_20261007_092854.jpg","IMG_20261007_092818.jpg","IMG_20261007_092901.jpg","IMG_20260919_170032.jpg"]};
 const X=x=>140+(320-x)*.5,Z=z=>115+(z-40)*.5;
 const draw=(b,fill,opacity)=>'<rect x="'+X(b[3])+'" y="'+Z(b[2])+'" width="'+((b[3]-b[0])*.5)+'" height="'+((b[5]-b[2])*.5)+'" fill="'+fill+'" opacity="'+opacity+'"/>';
 const svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="810" viewBox="0 0 1080 810">',
  '<rect width="1080" height="810" fill="#f6f9fd"/>',
  '<text x="30" y="42" font-family="Arial" font-size="26" font-weight="bold" fill="#183853">M038 — Escalier en L sur plan GUIDED004 B3</text>',
  '<text x="30" y="68" font-family="Arial" font-size="15" fill="#567187">Schéma projeté des pièces existantes / nouvelle variante isolée</text>',
  '<rect x="24" y="88" width="700" height="675" rx="12" fill="white" stroke="#dbe5ed"/>',
  '<rect x="'+X(340)+'" y="'+Z(40)+'" width="10" height="'+(Z(900)-Z(40))+'" fill="#546b7c"/>',
  ...timber.map(b=>draw(b,"#d9a26f",.25)),...concrete.map(b=>draw(b,"#92a6b7",.42)),
  ...P.filter(p=>p.kind==="cap"||p.g==="landing"&&p.h===15).map(p=>draw(box(p),p.g==="high"?"#367ca7":p.g==="low"?"#3b987d":"#d7a04e",1)),
  '<line x1="40" y1="'+Z(870)+'" x2="715" y2="'+Z(870)+'" stroke="#8069a2" stroke-dasharray="7 5" stroke-width="2"/>',
  '<text x="50" y="'+(Z(870)-10)+'" font-family="Arial" font-size="13" fill="#765d93">Limite Ouest maison (estimation B3)</text>',
  '<text x="158" y="'+(Z(340)-9)+'" font-family="Arial" font-size="13" fill="#ae5146">Béton : raccordement non prouvé</text>',
  '<text x="43" y="120" font-family="Arial" font-size="14" fill="#456479">SUD ←</text>',
  '<rect x="742" y="88" width="314" height="675" rx="12" fill="white" stroke="#dbe5ed"/>',
  '<text x="760" y="130" font-family="Arial" font-size="20" font-weight="bold">Vue en plan</text>',
  ...[["#367ca7","Volée haute : 9 marches"],["#d7a04e","Palier de retournement"],["#3b987d","Volée basse : 7 marches"],["#92a6b7","Béton existant B3"],["#d9a26f","Bois existant B3"]].map(([c,l],i)=>'<rect x="765" y="'+(167+i*39)+'" width="20" height="20" fill="'+c+'"/><text x="796" y="'+(183+i*39)+'" font-size="14" font-family="Arial">'+l+'</text>'),
  '<text x="760" y="431" font-family="Arial" font-size="18" font-weight="bold" fill="#254a60">5,5 tenons ≈ 1,10 m</text>',
  '<text x="760" y="469" font-family="Arial" font-size="14" fill="#567187">Pour 1,12 m (écart 2 cm).</text>',
  '<text x="760" y="521" font-family="Arial" font-size="14" fill="#9a493d">⚠ Fixation non prouvée</text>',
  '<text x="760" y="549" font-family="Arial" font-size="14" fill="#9a493d">⚠ Arrière et métrique non validés</text>',
  '<text x="760" y="597" font-family="Arial" font-size="14" fill="#567187">Nouveaux éléments LEGO séparés</text>',
  '<text x="760" y="620" font-family="Arial" font-size="14" fill="#567187">du modèle 1 904 pièces.</text>',
  '</svg>'].join("\n");
 return {P,ldraw,bom,qa,svg};
}
if(import.meta.url===new URL(process.argv[1],"file://").href){
 const fs=await import("node:fs"),base=new URL(".",import.meta.url);
 const b3=fs.readFileSync(new URL("../B3/generated/GUIDED004-B3-1904.ldr",base),"utf8"),r=buildM038(b3);
 if(r.qa.nominal_components!==1||r.qa.nominal_unsupported_pieces||r.qa.original_vs_new_volume_collisions)throw Error("M038_QUALITY_GATE_FAIL");
 for(const [name,data] of [["ESCALIER-M038-IMPLANTATION.ldr",r.ldraw],["APERCU-M038-MAISON.svg",r.svg],["NOMENCLATURE-M038.md",r.bom],["CONTROLES-M038.json",JSON.stringify(r.qa,null,2)+"\n"]])
  fs.writeFileSync(new URL(name,base),data);
 console.log("M038 CHECKS PASS",r.qa.prototype_parts);
}