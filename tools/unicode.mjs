// Regenerate with the same Node Unicode version used by the behavioral oracle.
const ranges = [];
for (let c = 0; c < 65536; c++) {
	if (!/[\p{C}\p{Z}]/u.test(String.fromCharCode(c))) continue;
	if (ranges.length && ranges.at(-1)[1] === c - 1) ranges.at(-1)[1] = c;
	else ranges.push([c, c]);
}
console.log(`/* Generated from Node ${process.version}, Unicode ${process.versions.unicode}. */`);
console.log('static const uint16_t txms_ranges[][2] = {');
for (const [a,b] of ranges) console.log(`\t{0x${a.toString(16)}, 0x${b.toString(16)}},`);
console.log('};');
