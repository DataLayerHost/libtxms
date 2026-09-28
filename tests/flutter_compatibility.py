"""Cross-check Flutter in a temporary copy; never writes to the reference repo."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
oracle, reference = map(lambda p: str(Path(p).resolve()), sys.argv[1:3])
vectors = ['48656c6c6f20576f726c64', '1234abcd', '007e', '0001', 'd800', 'ffff']
with tempfile.TemporaryDirectory(prefix='txms-flutter-') as folder:
	shutil.copytree(reference,folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','.dart_tool','build'))
	Path(folder,'test/c_compatibility_test.dart').write_text('''
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_txms/flutter_txms.dart';
void main() {
	test('emit compatibility vectors', () {
		final txms = Txms();
		for (final hex in '''+json.dumps(vectors)+''') {
			print('DART_VECTOR ${jsonEncode({'hex': hex, 'encoded': txms.encode(hex), 'decoded': txms.decode(txms.encode(hex))})}');
		}
	});
}
''')
	result=subprocess.run(['flutter','test','test/c_compatibility_test.dart','--reporter','expanded'],cwd=folder,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
	assert result.returncode==0,result.stdout
	rows=[json.loads(line.split('DART_VECTOR ',1)[1]) for line in result.stdout.splitlines() if 'DART_VECTOR ' in line]
	assert len(rows)==len(vectors)
	c=subprocess.run([oracle],input='\n'.join(vectors)+'\n',stdout=subprocess.PIPE,text=True,check=True).stdout.splitlines()
	divergences=[]
	for index,(row,line) in enumerate(zip(rows,c)):
		encoded,decoded=line.split('\t')
		assert row['encoded'].encode().hex()==encoded,row
		if index<2: assert row['decoded']==decoded,row
		else:
			assert row['decoded']!=decoded,row
			divergences.append({'hex':row['hex'],'dart':row['decoded'],'typescript_and_c':decoded})
	print('6 C/Flutter encoding comparisons passed; 2 matching decodes and 4 known upstream escape divergences verified')
	print(json.dumps(divergences,indent=2))
