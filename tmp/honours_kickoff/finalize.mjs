import path from 'node:path';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const root='C:/Users/Seamus/Documents/GitHub/NeuroBOLT';
const skill='C:/Users/Seamus/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const reference='C:/Users/Seamus/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/assets/reference.pptx';
process.env.RUNTIME_NODE_MODULES='C:/Users/Seamus/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
await fs.mkdir(root+'/output/presentations',{recursive:true});
const result=await finalizePresentation({
 workspaceDir:root,
 candidatePath:root+'/tmp/honours_kickoff/build/candidate.pptx',
 finalPath:root+'/output/presentations/Monash_EEG_honours_kickoff_v2.pptx',
 pythonExecutable:'C:/Users/Seamus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...([2,10,11].flatMap(n=>['--require-native-table-slide',String(n)]))],
 explicitTotalSlideCount:12,
 requiredNativeTableOwnerSlides:[2,10,11],
 requiredNativeChartOwnerSlides:[],
 // The unmodified reference itself fails the template-family parser with
 // duplicate_placeholder_identity. Check every original shape frame/layout
 // separately and compare all slide renders instead of altering the source.
 fontPolicy:{basis:'reference',families:['Inter','Inter Medium','Inter SemiBold','Helvetica Neue','Helvetica Neue Medium'],referencePath:reference,referenceSha256:createHash('sha256').update(await fs.readFile(reference)).digest('hex')},
 verifyArtifactToolImport:true,
 receiptPath:root+'/tmp/honours_kickoff/final_v2.validation.json'
});
console.log(JSON.stringify(result,null,2));
