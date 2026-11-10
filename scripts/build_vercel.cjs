/* Vercel serves the explicit standalone frontend, never the persistent Python app. */
const {readFileSync,mkdirSync,writeFileSync,rmSync}=require('node:fs');
const {resolve}=require('node:path');
const root=resolve(__dirname,'..');
const html=readFileSync(resolve(root,'preview.html'),'utf8');
if(!html.includes('window.NVTRA_PREVIEW_CONFIG=')||/<script[^>]+src="(?:studio|platform|cinematic)\.js"/.test(html)){
 throw Error('Rebuild the standalone frontend with python scripts/build_preview.py before deploying.');
}
const output=resolve(root,'dist-vercel');
rmSync(output,{recursive:true,force:true});mkdirSync(output,{recursive:true});
for(const file of ['index.html','nvtra.html','preview.html'])writeFileSync(resolve(output,file),html);
writeFileSync(resolve(output,'robots.txt'),'User-agent: *\nDisallow: /\n');
console.log('Built Vercel standalone frontend: no Python functions, private files or missing API dependencies.');
