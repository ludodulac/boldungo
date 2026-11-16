// M037: standalone targeted checks on original B3; no shared engine modifications.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {resolve,dirname} from "node:path";
import {fileURLToPath} from "node:url";
const model=resolve(dirname(fileURLToPath(import.meta.url)),"../B3/generated/GUIDED004-B3-1904.ldr");
const source=readFileSync(model), sha=createHash("sha1").update("blob "+source.length+"\0").update(source).digest("hex");
const need=(v,msg)=>{if(!v)throw Error("M037_"+msg)};
need(sha==="288c60fde76918128d8b955f78ebfa9afc2dfe8e","IMMUTABLE_B3_SHA");
const dims={"3001.dat":[2,4,24],"3002.dat":[2,3,24],"3003.dat":[2,2,24],"3004.dat":[1,2,24],"3005.dat":[1,1,24],"3006.dat":[2,10,24],"3007.dat":[2,8,24],"3008.dat":[1,8,24],"3009.dat":[1,6,24],"3010.dat":[1,4,24],"2456.dat":[2,6,24],"3622.dat":[1,3,24],"3623.dat":[1,3,8],"3460.dat":[1,8,8],"3023b.dat":[1,2,8],"3666.dat":[1,6,8],"3710.dat":[1,4,8]};
let id="";const parts=[];
for(const line of source.toString("utf8").split(/\r?\n/)){if(line.startsWith("0 // "))id=line.slice(5);else if(line.startsWith("1 ")){const a=line.split(/\s+/);need(a.length===15&&id,"LDR_RECORD");parts.push({id,ref:a[14],xyz:a.slice(2,5).map(Number),rot:a.slice(5,14).map(Number)})}}
need(parts.length===1904&&parts.filter(p=>p.ref==="30363.dat").length===408,"B3_INVENTORY");
const map=new Map(parts.map(p=>[p.id,p]));
const expected=[["wall-000699",[400,-744,50]],["wall-000704",[1200,-744,50]],["gable-000001",[480,-768,50]],["gable-000005",[1120,-768,50]],["gable-000006",[480,-792,50]],["roof-000025",[410,-792,60]],["roof-000048",[470,-816,60]]];
for(const [id,xyz] of expected)need(map.has(id)&&map.get(id).xyz.join()===xyz.join(),"ANCHOR_"+id);
const added={ref:"3004.dat",xyz:[440,-792,50],rot:[1,0,0,0,1,0,0,0,1]};
const T=(p,l)=>p.xyz.map((q,i)=>q+p.rot.slice(i*3,i*3+3).reduce((s,n,j)=>s+n*l[j],0));
function bounds(p){const d=dims[p.ref];need(d||p.ref==="30363.dat","PART_"+p.ref);const xs=d?[-d[1]*10,d[1]*10]:[-20,20],ys=[0,d?d[2]:24],zs=d?[-d[0]*10,d[0]*10]:[-70,10];let q=[];for(let x of xs)for(let y of ys)for(let z of zs)q.push(T(p,[x,y,z]));return [0,1,2].map(i=>[Math.min(...q.map(p=>p[i])),Math.max(...q.map(p=>p[i]))])}
const srcBoxes=parts.map(p=>({id:p.id,b:bounds(p)}));
const collides=(a,b)=>a.every((p,i)=>Math.min(p[1],b[i][1])-Math.max(p[0],b[i][0])>1e-5);
const hits=p=>srcBoxes.filter(q=>collides(bounds(p),q.b)).map(q=>q.id);
function studs(p,face){const d=dims[p.ref],a=[];for(let x=0;x<d[1];x++)for(let z=0;z<d[0];z++)a.push(T(p,[(x-(d[1]-1)/2)*20,face==="bottom"?d[2]:0,(z-(d[0]-1)/2)*20]));return a}
const eq=(a,b)=>a.every((n,i)=>n===b[i]),match=(a,b)=>a.filter(x=>b.some(y=>eq(x,y)));
const wall=map.get("wall-000699"),gable=map.get("gable-000001"),roof=map.get("roof-000048");
const wg=match(studs(wall,"top"),studs(gable,"bottom")),ga=match(studs(gable,"top"),studs(added,"bottom"));
const fem=[0,-20,-40,-60].flatMap((z,i)=>[-10,10].map(x=>({xyz:T(roof,[x,24,z]),depth:[20,14,8,4][i]})));
const ra=fem.filter(f=>studs(added,"top").some(p=>eq(f.xyz,p)));
need(wg.length===4&&ga.length===2&&ra.length===2&&ra.map(x=>x.depth).sort((a,b)=>a-b).join()==="8,14","NOMINAL_CONNECTIONS");
need(hits(added).length===0,"NEW_BODY_BOX_COLLISION");
need(hits({...added,xyz:[420,-792,50]}).includes("roof-000025"),"NEG_LEFT");
need(hits({...added,xyz:[460,-792,50]}).includes("gable-000006"),"NEG_RIGHT");
need(hits({...added,xyz:[440,-816,50]}).includes("roof-000048"),"NEG_UP");
need(readFileSync(model).equals(source),"B3_CHANGED");
console.log("M037 TARGETED PASS: 1904 originals, 4+2+2 nominal sites, zero positive body AABB overlap, 3/3 negative collision controls; mesh/insertion NOT RUN");
