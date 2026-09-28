import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
const [binary, reference] = process.argv.slice(2);
if (!binary || !reference) throw new Error('Usage: node tests/compatibility.mjs build/txms_oracle /path/to/txms.js/dist/index.js');
const {default: txms} = await import(pathToFileURL(reference));
const samples = JSON.parse(readFileSync(new URL('./typescript-samples.json', import.meta.url)));
const vectors = samples.valid.map(s => s.hex);
for (let i=0; i<65536; i++) vectors.push(i.toString(16).padStart(4,'0'));
let seed=123456789;
for (let j=0; j<1000; j++) {
	let hex='';
	for (let k=0; k<j%513+1; k++) { seed=(Math.imul(seed,1664525)+1013904223)>>>0; hex+=(seed&255).toString(16).padStart(2,'0'); }
	vectors.push(hex);
}
vectors.push('f','00001','0XABC','00000000','48656c6c6f20576f726c64');
const child=spawnSync(binary,[],{input:vectors.join('\n')+'\n',encoding:'utf8',maxBuffer:32*1024*1024});
assert.equal(child.status,0,child.stderr);
const lines=child.stdout.trimEnd().split('\n'); assert.equal(lines.length,vectors.length);
for (let i=0; i<vectors.length; i++) {
	const encoded=txms.encode(vectors[i]);
	assert.equal(lines[i],`${Buffer.from(encoded).toString('hex')}\t${txms.decode(encoded)}`,`vector ${i}: ${vectors[i]}`);
}
for (const sample of samples.valid) assert.equal(txms.encode(sample.hex),sample.data);
console.log(`${vectors.length} C/TypeScript byte-for-byte encode/decode comparisons passed (Unicode ${process.versions.unicode})`);
