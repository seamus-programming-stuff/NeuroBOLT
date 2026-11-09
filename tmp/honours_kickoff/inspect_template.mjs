import fs from 'node:fs/promises';
import { FileBlob, PresentationFile } from 'file:///C:/Users/Seamus/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const dir = 'C:/Users/Seamus/Documents/GitHub/NeuroBOLT/tmp/honours_kickoff';
const source = 'C:/Users/Seamus/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/assets/reference.pptx';
const p = await PresentationFile.importPptx(await FileBlob.load(source));
console.log('Imported',p.slides.items.length,'slides');
const inspection = await p.inspect({kind:'slide,layout,textbox,shape,image,table,chart',maxChars:200000});
await fs.writeFile(dir+'/source_inspection.ndjson',inspection.ndjson);
await fs.writeFile(dir+'/source_proto.json',JSON.stringify(p.toProto(),null,2));
for (const [i,s] of p.slides.items.entries()) {
 const b=await p.export({slide:s,format:'png',scale:0.8});
 await fs.writeFile(dir+'/source_'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await b.arrayBuffer()));
}
const b=await p.export({format:'webp',montage:true,scale:0.4});
await fs.writeFile(dir+'/source_montage.webp',new Uint8Array(await b.arrayBuffer()));
console.log('Rendered all reference slides');
