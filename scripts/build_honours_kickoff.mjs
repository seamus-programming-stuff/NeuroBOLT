// Reuse the retained Project Kickoff deck. Never modify the reference file.
// Dependencies: the bundled @oai/artifact-tool runtime (see the project README).
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const args = process.argv.slice(2);
const option = (name, fallback) => args.includes(name) ? args[args.indexOf(name)+1] : fallback;
const runtime = path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies');
const modules = process.env.CODEX_ARTIFACT_NODE_MODULES || path.join(runtime, 'node/node_modules');
const { FileBlob, PresentationFile } = await import(pathToFileURL(path.join(modules, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const reference = option('--reference', path.join(os.homedir(), '.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/assets/reference.pptx'));
const contentPath = option('--content', path.join(root, 'reports/honours_kickoff/content.json'));
const out = option('--out', path.join(root, 'tmp/honours_kickoff/build'));
await fs.mkdir(out, {recursive:true});
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const referenceHash = sha(await fs.readFile(reference));
const content = JSON.parse(await fs.readFile(contentPath,'utf8'));
const p = await PresentationFile.importPptx(await FileBlob.load(reference));
const inspected = await p.inspect({kind:'slide,layout,textbox,shape,image,table,chart',maxChars:300000});
const records = inspected.ndjson.split('\n').filter(Boolean).map(l=>JSON.parse(l));
const contentShapes = n => records.filter(r=>r.slideIndex===n-1 && r.kind==='textbox' && r.placeholder!=='slideNumber');
function replaceText(record,text) {
 const target = p.resolve(record.id);
 const frame={...record.position};
 const oldParts=record.text.split('\n').filter(s=>s.trim());
 const newParts=text.split('\n').filter(s=>s.trim());
 // Keep the template's separate heading/body run formatting.
 if(oldParts.length>1 && oldParts.length===newParts.length) {
  oldParts.forEach((part,i)=>target.text.replace(part,newParts[i]));
 } else target.text.replace(record.text,text);
 target.text.autoFit='none';
 target.position=frame;
}
for (const spec of content.slides) {
 const shapes = contentShapes(spec.number);
 if (shapes.length!==spec.text.length) throw new Error(`Slide ${spec.number}: ${shapes.length} shapes, ${spec.text.length} strings`);
 shapes.forEach((shape,i)=>replaceText(shape,spec.text[i]));
 if (spec.table) {
  const tableRecord = records.find(r=>r.slideIndex===spec.number-1 && r.kind==='table');
  const table = p.resolve(tableRecord.id);
  spec.table.forEach((row,r)=>row.forEach((value,c)=>table.cells.set(r,c,value)));
 }
 if (spec.notes) p.slides.items[spec.number-1].speakerNotes.text = spec.notes;
}
// The reference's checkerboard is an explicit picture placeholder. Replace it
// with an editable method diagram inside its original frame.
const diagramSlide = p.slides.items[2];
const picture = records.find(r=>r.slideIndex===2 && r.kind==='image');
p.delete(picture.id);
const addBox = (name,text,x,y,w,h,fill='#284638',font=23) => {
 const s=diagramSlide.shapes.add({name,geometry:'roundRect',position:{left:x,top:y,width:w,height:h},fill,line:{style:'solid',fill:'none',width:0}});
 s.text=text;
 s.text.style={fontSize:font,typeface:'Inter',color:'#FFFFFF',alignment:'center',verticalAlignment:'middle',insets:12};
 return s;
};
addBox('diagram-input','DREAM EEG and report labels\nAudit people, cases and sleep stages',690,92,520,95);
addBox('diagram-features','Fixed pre-awakening history\nSpectral features in time bins',690,223,520,95);
addBox('diagram-models','Logistic baseline / tiny transformer\nOne optional pooling change',690,354,520,95);
addBox('diagram-evaluation','Held-out people\nStage controls, scores and demo',690,485,520,95);
for (const y of [187,318,449]) {
 const s=diagramSlide.shapes.add({name:`connector-${y}`,geometry:'line',position:{left:950,top:y,width:0,height:36},line:{style:'solid',fill:'#BCEF59',width:2}});
}
await fs.writeFile(path.join(out,'edited_inspection.ndjson'),(await p.inspect({kind:'slide,layout,textbox,shape,image,table,chart,notes',maxChars:400000})).ndjson);
for (const [i,s] of p.slides.items.entries()) {
 const b=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(out,`slide_${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
 const layout=await s.export({format:'layout'});
 await fs.writeFile(path.join(out,`slide_${String(i+1).padStart(2,'0')}.layout.json`),await layout.text());
}
const montage=await p.export({format:'webp',montage:true,scale:0.5});
await fs.writeFile(path.join(out,'montage.webp'),new Uint8Array(await montage.arrayBuffer()));
await (await PresentationFile.exportPptx(p)).save(path.join(out,'candidate.pptx'));
await fs.writeFile(path.join(out,'build_manifest.json'),JSON.stringify({referenceSha256:referenceHash,contentSha256:sha(await fs.readFile(contentPath)),slides:p.slides.items.length,referenceUnchanged:referenceHash===sha(await fs.readFile(reference)),buildTool:'@oai/artifact-tool',time:new Date().toISOString()},null,2));
console.log(`Built ${p.slides.items.length} slides in ${out}`);
