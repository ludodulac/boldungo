/*
BOLDUNGO — Mission 034, Construction 3. Independent experimental LEGO stair.
Run from repository root:
node missions/parallel-034-escalier/build-stair.mjs
Only files inside this mission directory are written. No production engine changes.
All geometry is a provisional architectural placement, NOT an as-built survey.
*/
function buildStairM034(sourceLDraw) {
  const cells = [];
  const add=(x,z,height,zone,step)=>cells.push({x,z,height,zone,step});
  // x positive = north, z(LDraw) positive = west, altitude is -y.
  // 1 stud = 20 LDU = 0.20 m at the GUIDED004 nominal scale.
  // Upper flight along +west (9 treads), lower along -south (7 treads).
  for(let s=0;s<9;s++) for(let x=-3;x<=-1;x++) add(x,15+s,34-2*s,"upper",s+1);
  for(let x=-3;x<=-1;x++) for(let z=24;z<=26;z++) add(x,z,16,"landing",0);
  for(let s=0;s<7;s++) for(let z=24;z<=26;z++) add(-4-s,z,14-2*s,"lower",s+1);
  const cellkey=(x,z)=>x+","+z;
  const seen=new Set(); for(const c of cells) {
    if(seen.has(cellkey(c.x,c.z))) throw Error("DUPLICATE_STAIR_CELL");
    seen.add(cellkey(c.x,c.z));
  }
  const pieces=[], partForLen={1:"3022.dat",2:"3020.dat",3:"3795.dat"};
  for(let h=0;h<34;h++) {
    const active=cells.filter(c=>c.height>h);
    // Alternating X / Z bond and staggered seams. One cell = 2x2 studs.
    const axis=h%2===0?"x":"z",other=axis==="x"?"z":"x";
    const by=new Map();
    for(const c of active) {if(!by.has(c[other]))by.set(c[other],[]);by.get(c[other]).push(c);}
    for(const [otherVal,line] of [...by].sort((a,b)=>a[0]-b[0])) {
      line.sort((a,b)=>a[axis]-b[axis]);
      const runs=[]; let run=[];
      for(const c of line) {
        if(run.length&&c[axis]!==run[run.length-1][axis]+1){runs.push(run);run=[];}
        run.push(c);
      }
      if(run.length)runs.push(run);
      for(const segment of runs) {
        const shift=(Math.floor(h/2)+Math.abs(otherVal))%3;
        let k=0;
        while(k<segment.length) {
          const remaining=segment.length-k;
          let n=k===0 && shift>0?Math.min(shift,remaining):Math.min(3,remaining);
          const chunk=segment.slice(k,k+n);
          const first=chunk[0], last=chunk[chunk.length-1];
          const x1=axis==="x"?first.x:first.x, x2=axis==="x"?last.x+1:first.x+1;
          const z1=axis==="z"?first.z:first.z, z2=axis==="z"?last.z+1:first.z+1;
          const top=chunk.some(c=>c.height===h+1);
          pieces.push({
            id:"M034-"+String(pieces.length+1).padStart(4,"0"), 
            h, x1,z1,x2,z2, cells:chunk.map(c=>[c.x,c.z]),
            color:top?71:7, ref:partForLen[n], axis, zone:chunk[0].zone
          });
          k+=n;
        }
      }
    }
  }
  // Test solid orthogonal footprint collision, plate dimensions, vertical bonds.
  const occupied=new Map(), layerPieces=new Map();
  for(let i=0;i<pieces.length;i++) {
    const p=pieces[i], key=p.h; if(!layerPieces.has(key))layerPieces.set(key,[]);
    layerPieces.get(key).push(i);
    if(p.x2-p.x1<1||p.z2-p.z1<1||p.x2-p.x1>3||p.z2-p.z1>3)
      throw Error("BAD_PART_FOOTPRINT");
    if((p.x2-p.x1)*(p.z2-p.z1)!==p.cells.length)throw Error("BAD_PART_AREA");
    for(const [x,z] of p.cells) {
      const v=x+","+z+","+p.h;
      if(occupied.has(v))throw Error("SOLID_VOLUME_COLLISION:"+v);
      occupied.set(v,i);
    }
  }
  const parent=pieces.map((_,i)=>i);
  const find=(i)=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  const union=(a,b)=>{a=find(a);b=find(b);if(a!==b)parent[b]=a;};
  let nominalStudCavitySites=0, nominalPairs=0, unsupported=0;
  for(let i=0;i<pieces.length;i++) {
    const p=pieces[i];if(p.h===0)continue;
    let supports=new Set();
    for(const [x,z] of p.cells) {
      const below=occupied.get(x+","+z+","+(p.h-1));
      if(below!==undefined){union(i,below);supports.add(below);nominalStudCavitySites+=4;}
    }
    if(supports.size===0)unsupported++;
    nominalPairs+=supports.size;
  }
  const components=new Set(parent.map((_,i)=>find(i))).size;
  const exposed=cells.filter(c=>c.height>0);
  const risers=[...new Set(cells.filter(c=>c.zone==="upper").map(c=>c.height))].sort((a,b)=>b-a);
  const lowerRisers=[...new Set(cells.filter(c=>c.zone==="lower").map(c=>c.height))].sort((a,b)=>b-a);
  if(components!==1||unsupported!==0||pieces.length===0||
      risers.length!==9||lowerRisers.length!==7)
    throw Error("M034_QUALITY_GATE_FAIL components="+components+" unsupported="+unsupported);
  const count={};for(const p of pieces)count[p.ref]=(count[p.ref]||0)+1;
  const bom = [
    "# M034 - nomenclature prototype escalier LEGO",
    "",
    "Toutes les references sont des pieces LEGO documentees par LDraw.org (catalogue officiel).",
    "Le comptage correspond exactement aux lignes de type 1 du LDraw genere.",
    "",
    "| Reference LDraw | Type de piece | Quantite |",
    "| --- | --- | ---: |",
    ...Object.entries(count).sort().map(([id,n])=>"| "+id+" | "+({"3022.dat":"Plate 2 x 2","3020.dat":"Plate 2 x 4","3795.dat":"Plate 2 x 6"}[id])+" | "+n+" |"),
    "| **TOTAL** | | **"+pieces.length+"** |",
    "",
    "Couleurs: 7 = gris clair (sous-couches); 71 = gris bleute fonce (surfaces visibles).",
    "La conception utilise intentionnellement un noyau plein de plaques LEGO comme prototype de liaisons. Il ne represente PAS les vides de la plateforme beton reelle."
  ].join("\n")+"\n";
  const ldraw = [
    "0 FILE BOLDUNGO-M034-ESCALIER-PROTOTYPE.ldr",
    "0 BOLDUNGO / M034 / CONSTRUCTION 3 / two-flight L staircase",
    "0 !CATEGORY Model",
    "0 // PROVISIONAL placement relative to GUIDED004 B3, no house attachment",
    "0 // Two flights: courtyard 7, upper along south facade 9; 6 studs wide",
    "0 // Pieces are standard 2x2, 2x4, 2x6 plates, all real LDraw refs",
    "0 // WARNING: nominal LEGO bonds, not verified force/insertion or house attachment",
    ...pieces.map(p=>{
      const x=(p.x1+p.x2)*20, z=(p.z1+p.z2)*20, y=-8*(p.h+1);
      const m=p.axis==="x"?"0 0 -1 0 1 0 1 0 0":"1 0 0 0 1 0 0 0 1";
      return "0 // "+p.id+" "+p.zone+" level_plate="+(p.h+1)+"\n"+
             "1 "+p.color+" "+x+" "+y+" "+z+" "+m+" "+p.ref;
    }),
    "0 NOFILE"
  ].join("\n")+"\n";
  // Orthogonal-only preflight with all B3 source brick & plate bounding boxes.
  let sourceParts=0, sourceRoof=0, checkedOrthogonal=0, orthogonalOverlaps=0, orthogonalCollisionExamples=[];
  let unknownSourceParts = new Set(), roofCenters=[];
  const defs={
    "3005.dat":[1,1,3],"3004.dat":[1,2,3],"3622.dat":[1,3,3],
    "3010.dat":[1,4,3],"3009.dat":[1,6,3],"3008.dat":[1,8,3],
    "3003.dat":[2,2,3],"3002.dat":[2,3,3],"3001.dat":[2,4,3],
    "2456.dat":[2,6,3],"3007.dat":[2,8,3],"3006.dat":[2,10,3],
    "3666.dat":[1,6,1],"3460.dat":[1,8,1],"3623.dat":[1,3,1],
    "3023b.dat":[1,2,1],"3710.dat":[1,4,1],
    "3020.dat":[2,4,1],"3022.dat":[2,2,1],"3795.dat":[2,6,1]
  };
  if(sourceLDraw){
    for(const line of sourceLDraw.split(/\r?\n/)) {
      if(!line.startsWith("1 "))continue;
      sourceParts++;
      const t=line.trim().split(/\s+/),ref=t[14].toLowerCase();
      const X=+t[2],Y=+t[3],Z=+t[4],m00=+t[5],m02=+t[7],m20=+t[11],m22=+t[13];
      if(ref==="30363.dat"){sourceRoof++;roofCenters.push(X);continue;}
      const d=defs[ref];if(!d){unknownSourceParts.add(ref);continue;}
      checkedOrthogonal++;
      const w=Math.abs(m00)*d[0]+Math.abs(m02)*d[1];
      const depth=Math.abs(m20)*d[0]+Math.abs(m22)*d[1];
      const a=[X-10*w,Y,Z-10*depth,X+10*w,Y+8*d[2],Z+10*depth];
      for(const p of pieces){
        const b=[40*p.x1,-8*(p.h+1),40*p.z1,40*p.x2,-8*p.h,40*p.z2];
        if(a[0]<b[3]&&b[0]<a[3]&&a[1]<b[4]&&b[1]<a[4]&&a[2]<b[5]&&b[2]<a[5]){
          orthogonalOverlaps++;
          if(orthogonalCollisionExamples.length<6)orthogonalCollisionExamples.push({original_part:ref,original_center:[X,Y,Z],new_piece:p.id});
        }
      }
    }
  }
  const roofXMin = roofCenters.length ? Math.min(...roofCenters) : null;
  // Roof 30363 has max 4-stud horizontal footprint: its min x is >= center - 40.
  const roofPlanarClear = roofXMin!==null && roofXMin-40>=0;
  const qa = {
    status:"PROTOTYPE_NOMINAL_ONLY_NOT_CERTIFIED",
    base_commit:"0f5bfe1836598f7050089c54a415123f06d33945",
    original_model:"missions/B3/generated/GUIDED004-B3-1904.ldr",
    original_model_type1_count:sourceParts,
    original_slope_30363_count:sourceRoof,
    original_unknown_nonroof_refs:[...unknownSourceParts].sort(),
    original_orthogonal_parts_checked:checkedOrthogonal,
    prototype_plate_count:pieces.length,
    prototype_part_numbers:count,
    number_of_flights:2,
    lower_ascending_flight_treads:lowerRisers.length,
    upper_ascending_flight_treads:risers.length,
    landing_2x2_cell_count:9,
    clear_width_studs:6,
    scaled_width_m:1.2,
    owner_approx_width_m:1.12,
    scaled_width_error_percent:+((1.2/1.12-1)*100).toFixed(2),
    assumed_scale:"100 LDU per metre, approximately 1:25",
    provisional_tread_going_m:0.4,
    provisional_riser_m:0.16,
    provisional_upper_level_m:2.72,
    rear_plane_in_source_survey_m:8.2,
    prototype_west_extent_m:[6,10.8],
    rear_overrun_m:2.6,
    overrun_is_not_owner_measured:true,
    horizontal_volume_overlap_cells:0,
    nominal_stud_cavity_sites:nominalStudCavitySites,
    nominal_part_pair_links:nominalPairs,
    nominal_stud_graph_components:components,
    nominal_unsupported_plates:unsupported,
    B3_orthogonal_aabb_overlap_pairs:orthogonalOverlaps,
    B3_aabb_overlap_examples:orthogonalCollisionExamples,
    B3_roof_nominal_planar_disjoint:roofPlanarClear,
    B3_slope_mesh_not_instantiated:true,
    connection_to_existing_house:"NOT_DEMONSTRATED",
    photographed_masonry_and_parapets:"NOT_RECONSTRUCTED",
    full_photo_metric_fidelity:"NOT_DEMONSTRATED",
    genuine_stud_clutch_force:"NOT_MEASURED",
    insertion_sequence:"NOT_TESTED",
    physical_stability:"NOT_TESTED",
    limitation:"Bounding boxes and stud/cavity lattice are nominal; no LDraw mesh test. No original piece moved or removed."
  };
  if(sourceLDraw && (sourceParts!==1904||sourceRoof!==408||
    unknownSourceParts.size||orthogonalOverlaps!==0||!roofPlanarClear))
    throw Error("M034_B3_SOURCE_OR_COLLISION_PREFLIGHT_FAIL "+JSON.stringify({
      sourceParts,sourceRoof,unknown:[...unknownSourceParts],
      orthogonalOverlaps,roofPlanarClear
    }));
  // SVG plan, accurately drawn from the stair cell-level geometry.
  const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;");
  const S=['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="810" viewBox="0 0 1220 810">',
    '<rect width="1220" height="810" fill="#f8fafc"/>',
    '<text x="38" y="53" font-family="sans-serif" font-size="31" font-weight="700" fill="#162a40">BOLDÜNGO · M034 — escalier expérimental en L</text>',
    '<text x="38" y="81" font-family="sans-serif" font-size="15" fill="#5e7081">Plan à l’échelle de la grille LEGO + profils des 16 marches • modèle autonome, NON raccordé à la maison</text>',
    '<rect x="25" y="100" width="570" height="630" rx="15" fill="#ffffff" stroke="#dde4eb"/>',
    '<text x="45" y="135" font-family="sans-serif" font-size="20" font-weight="600" fill="#162a40">Vue en plan · coordonnées GUIDED004</text>',
    '<text x="52" y="165" font-family="sans-serif" font-size="13" fill="#718399">← Sud (−x)        Ouest (+z) ↓</text>'];
  const px=c=>65+(c.x+10)*43,py=c=>184+(c.z-15)*43;
  for(const c of cells) {
    const col=c.zone==="upper"?"#7f91ae":c.zone==="landing"?"#d7a76e":"#7ca49b";
    S.push('<rect x="'+px(c)+'" y="'+py(c)+'" width="42" height="42" fill="'+col+'" stroke="#fff" stroke-width="1.2"/>');
  }
  for(let j=0;j<7;j++) {
    const c=cells.find(q=>q.zone==="lower"&&q.step===j+1);
    S.push('<text x="'+(px(c)+16)+'" y="'+(py(c)+28)+'" font-size="16" font-family="sans-serif" font-weight="600" fill="white">'+(j+1)+'</text>');
  }
  for(let j=0;j<9;j++) {
    const c=cells.find(q=>q.zone==="upper"&&q.step===j+1);
    S.push('<text x="'+(px(c)+49)+'" y="'+(py(c)+28)+'" font-size="15" font-family="sans-serif" font-weight="600" fill="#fff">'+(9-j)+'</text>');
  }
  S.push('<text x="431" y="637" font-family="sans-serif" font-size="13" fill="#4b637d">6 tenons ≈ 1,20 m</text>',
    '<text x="45" y="692" font-family="sans-serif" font-size="13" fill="#728294">L’implantation n’est pas la position relevée sur les photos.</text>',
    '<rect x="615" y="100" width="577" height="630" rx="15" fill="#fff" stroke="#dde4eb"/>',
    '<text x="644" y="135" font-family="sans-serif" font-size="20" font-weight="600" fill="#162a40">Profils d’élévation (du bas vers le haut)</text>');
  const plot=(x,y,width,labels,top,accent)=>{
    S.push('<line x1="'+x+'" y1="'+(y+220)+'" x2="'+(x+width)+'" y2="'+(y+220)+'" stroke="#8c9eab" stroke-width="2"/>');
    let w=Math.floor(width/labels.length);
    labels.forEach((h,i)=>{
      let hei=h*5.3;S.push('<rect x="'+(x+i*w)+'" y="'+(y+220-hei)+'" width="'+w+'" height="'+hei+'" fill="'+accent+'" stroke="white" stroke-width="1"/>');
      S.push('<text x="'+(x+i*w+w/2)+'" y="'+(y+240)+'" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#596e83">'+(i+1)+'</text>');
    });
  };
  plot(649,188,502,[2,4,6,8,10,12,14],14,"#7ca49b");
  S.push('<text x="645" y="167" font-family="sans-serif" font-size="14" fill="#48655e">Volée basse : 7 marches → palier (16 plaques = 1,28 m)</text>');
  plot(649,465,502,[18,20,22,24,26,28,30,32,34],34,"#7f91ae");
  S.push('<text x="645" y="444" font-family="sans-serif" font-size="14" fill="#4b5e86">Volée haute : 9 marches → 2,72 m (provisoire)</text>',
    '<text x="37" y="774" font-family="sans-serif" font-size="14" fill="#945f38">Attention : liaisons tenons/logements nominales ; stabilité, insertion et raccord à la vraie maison non prouvés.</text>',
    '</svg>');
  return {ldraw,svg:S.join("\n")+"\n",bom,qa,plates:pieces.length};
}
/* CLI: regenerate reproducibly after checkout */
if(typeof process!=="undefined" && process.argv[1] && process.argv[1].endsWith("build-stair.mjs")){
  const fs=await import("node:fs");
  const here=new URL(".",import.meta.url);
  const source=fs.readFileSync(new URL("../B3/generated/GUIDED004-B3-1904.ldr",here),"utf8");
  const out=buildStairM034(source);
  fs.writeFileSync(new URL("ESCALIER-M034-PROTOTYPE.ldr",here),out.ldraw);
  fs.writeFileSync(new URL("APERCU-M034.svg",here),out.svg);
  fs.writeFileSync(new URL("NOMENCLATURE-M034.md",here),out.bom);
  fs.writeFileSync(new URL("CONTROLES-M034.json",here),JSON.stringify(out.qa,null,2)+"\n");
  console.log("M034 verified:",JSON.stringify({
    pieces:out.plates,components:out.qa.nominal_stud_graph_components,
    overlaps:out.qa.B3_orthogonal_aabb_overlap_pairs
  }));
}
