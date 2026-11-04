// BOLDUNGO: exact 1 792 LDraw placement converter to existing viewer JSON.
// node scripts/convert_b3_roof_to_brickhouse_viewer.mjs [source.ldr] [output.json]
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {dirname} from "node:path";
function convert(source){
const refs={"3005":[1,1,24],"3004":[1,2,24],"3622":[1,3,24],"3010":[1,4,24],"3009":[1,6,24],"3008":[1,8,24],
"3003":[2,2,24],"3002":[2,3,24],"3001":[2,4,24],"2456":[2,6,24],"3007":[2,8,24],"3006":[2,10,24],
"3023b":[1,2,8],"3710":[1,4,8],"3666":[1,6,8],"3460":[1,8,8],"3623":[1,3,8]};
const parts=[],seen=new Set(),bb=[Infinity,Infinity,Infinity,-Infinity,-Infinity,-Infinity];let placementId=null;
for(const line of source.split(/\r?\n/)){
if(line.startsWith("0 // ")){placementId=line.slice(5);continue;}
if(!line.startsWith("1 "))continue;
const a=line.trim().split(/\s+/),ref=a[14]?.toLowerCase().replace(".dat",""),d=refs[ref];
if(a.length!==15||!d||!placementId||seen.has(placementId))throw Error("Invalid part "+placementId);
seen.add(placementId);
const m=a.slice(5,14).map(Number),t=m.join(","),rot={"1,0,0,0,1,0,0,0,1":1,"0,0,-1,0,1,0,1,0,0":0,"0,0,1,0,1,0,-1,0,0":2}[t];
if(rot===undefined)throw Error("Unsupported LDraw matrix "+placementId+" "+t);
const [w,l,h]=d,x=+a[2],y=+a[3],z=+a[4],dx=(rot%2?l:w),dz=(rot%2?w:l);
const sx=(x-10*dx)/20,sy=(z-10*dz)/20,sp=(-y-h)/8;
if(![sx,sy,sp].every(Number.isInteger))throw Error("Off-grid "+placementId);
const roof=placementId.startsWith("REBUILD-ROOF-"),win=placementId.startsWith("window-"),wall=placementId.startsWith("wall-"),gable=placementId.startsWith("gable-"),chimney=placementId.startsWith("scene-chimney:"),stair=placementId.startsWith("scene-stair:"),platform=placementId.startsWith("scene-platform:"),timber=placementId.includes("timber"),concrete=placementId.includes("concrete");
const cat=roof?"roof_tile":win?"facade_detail":chimney?"metal":timber?"timber":concrete?"concrete":stair?"masonry":platform?"concrete":h===8?"plate":"brick";
const comp=roof?"roof":win?"facade_detail":wall?"wall":gable?"gable":chimney?"chimney":stair?"stairs":platform?"platform":placementId.startsWith("EXPERIMENT")?"roof_support":"wall";
const col=roof?"#555d68":win?"#8bbfd8":chimney?"#6a717c":timber?"#aa8057":concrete?"#bbb9b2":stair?"#b8ab97":gable?"#c3b1a0":null;
const p={placement_id:placementId,part_id:(h===8?"PLATE_":"BRICK_")+w+"X"+l,category:cat,component:comp,
x_studs:sx,y_studs:sy,z_plates:sp,rotation_quarter_turns:rot,width_studs:w,length_studs:l,height_plates:h/8,
ldraw_ref:ref+".dat",ldraw_color:+a[1],ldraw_matrix:m,ldraw_xyz_ldu:[x,y,z],
source_annotation:roof?"MAISON_COMPLETE2_NEW_ROOF":"B3_UNCHANGED",visual_proxy_not_actual_glazing:win};
if(col)p.semantic_color=col;
parts.push(p);
bb[0]=Math.min(bb[0],sx);bb[1]=Math.min(bb[1],sy);bb[2]=Math.min(bb[2],sp);
bb[3]=Math.max(bb[3],sx+dx);bb[4]=Math.max(bb[4],sy+dz);bb[5]=Math.max(bb[5],sp+h/8);
}
if(parts.length!==1792||parts.filter(p=>p.component==="roof").length!==296||new Set(parts.map(p=>p.placement_id)).size!==1792)throw Error("Wrong variant parts");
const buildingId="GUIDED-004-MAISON-COMPLETE-1792",types=new Set(),lines=new Map();
for(const p of parts){types.add(p.part_id);const key=p.part_id+"|"+p.category,e=lines.get(key)||{part_id:p.part_id,category:p.category,quantity:0,ldraw_ref:p.ldraw_ref};e.quantity++;lines.set(key,e);}
return {schema_version:"0.1",building_id:buildingId,volume_id:"guided004-full-house-stepped-roof",
metadata:{generator:"B3 actual LDraw -> BrickHouse viewer",source_repository:"ludodulac/boldungo",
source_commit:"527f6550ea886c84a56b4d78f6bf29443df763e9",
source_ldraw:"missions/MAISON_COMPLETE2/GUIDED004-B3-STEPPED-ROOF.ldr",
source_part_locations:"Exact LDraw grid 20 LDU/stud, 8 LDU/plate",original_non_roof_preserved:1496,new_roof_orthogonal_bricks:296,
old_sloped_parts_replaced_only_in_variant:408,physical_mechanics:"NOT_CERTIFIED",viewer_only:true},
brick_model:{schema_version:"0.1",building_id:buildingId,volume_id:"guided004-full-house-stepped-roof",width_studs:bb[3]-bb[0],depth_studs:bb[4]-bb[1],height_plates:bb[5]-bb[2],origin_x_studs:bb[0],origin_y_studs:bb[1],canvas_width_studs:bb[3],canvas_depth_studs:bb[4],parts},
bom:{schema_version:"0.1",building_id:buildingId,volume_id:"guided004-full-house-stepped-roof",total_parts:parts.length,unique_part_types:types.size,lines:[...lines.values()].sort((a,b)=>a.part_id.localeCompare(b.part_id)||a.category.localeCompare(b.category))},
fidelity_issues:[
{severity:"warning",message:"Maison LEGO complète de 1 792 pièces : emboîtements du nouveau toit testés sur grille nominale, pas encore au maillage intégral ni physiquement."},
{severity:"warning",message:"Toiture provisoire en escalier au lieu de la pente photographiée. Ouvertures résiduelles autour des cheminées."},
{severity:"warning",message:"Terrasses, escaliers, cheminées et fondations du modèle B-3 : tenue et assemblage réel non certifiés."},
{severity:"warning",message:"Les fenêtres bleues sont des briques symbolisant les ouvertures, pas des vrais vitrages LEGO."}
]};
}
const input=process.argv[2]??"missions/MAISON_COMPLETE2/GUIDED004-B3-STEPPED-ROOF.ldr";
const output=process.argv[3]??"frontend/data/guided004-maison-complete-1792-brickhouse.json";
if(input===output||output.endsWith(".ldr"))throw Error("Original LDraw file cannot be overwritten");
const result=convert(readFileSync(input,"utf8"));
mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(result)+"\n");
console.log(JSON.stringify({parts:result.bom.total_parts,roof:result.brick_model.parts.filter(x=>x.component==="roof").length,output}));
