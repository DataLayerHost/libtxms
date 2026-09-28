#!/usr/bin/env python3
"""Stage a ConanCenter recipe with an exact release archive checksum."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import yaml
from release import VERSION

def prepare(root, version, archive, output):
	root, archive, output = Path(root), Path(archive), Path(output)
	if not re.fullmatch(VERSION, version):
		raise ValueError("Expected a stable MAJOR.MINOR.PATCH version")
	if archive.name != f"libtxms-{version}.tar.gz":
		raise ValueError("Archive filename does not match the version")
	recipe = output / "recipes" / "libtxms"
	all_dir = recipe / "all"
	all_dir.mkdir(parents=True, exist_ok=True)
	shutil.copy2(root / "packaging/LICENSE", output / "LICENSE")
	shutil.copy2(root / "packaging/conan-center/conanfile.py", all_dir / "conanfile.py")
	shutil.copytree(root / "test_package", all_dir / "test_package", dirs_exist_ok=True,
		ignore=shutil.ignore_patterns("build*", "__pycache__", "CMakeUserPresets.json"))
	data = {"sources": {version: {
		"url": f"https://github.com/DataLayerHost/libtxms/releases/download/{version}/{archive.name}",
		"sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
	}}}
	(all_dir / "conandata.yml").write_text(yaml.safe_dump(data, sort_keys=False))
	(recipe / "config.yml").write_text(yaml.safe_dump({"versions": {version: {"folder": "all"}}}, sort_keys=False))
	return recipe

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--version", required=True)
	parser.add_argument("--archive", required=True)
	parser.add_argument("--output", default="release-stage")
	parser.add_argument("--root", default=".")
	args = parser.parse_args()
	print(prepare(args.root, args.version, args.archive, args.output))
