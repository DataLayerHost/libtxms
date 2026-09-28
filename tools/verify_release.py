#!/usr/bin/env python3
"""Verify downloaded release sources and metadata against the checked-out tag."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from release import VERSION


def verify(directory, tag, commit):
	if not re.fullmatch(VERSION, tag):
		raise ValueError("Invalid stable release tag")
	directory = Path(directory)
	archive_name = f"libtxms-{tag}.tar.gz"
	checksums = {}
	for line in (directory / "SHA256SUMS").read_text().splitlines():
		match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
		if not match or match.group(2) in checksums:
			raise ValueError("Malformed or duplicate checksum entry")
		checksums[match.group(2)] = match.group(1)
	for name in (archive_name, "release.json"):
		if checksums.get(name) != hashlib.sha256((directory / name).read_bytes()).hexdigest():
			raise ValueError(f"Checksum mismatch for {name}")
	metadata = json.loads((directory / "release.json").read_text())
	if metadata != {"project": "libtxms", "version": tag, "tag": tag, "commit": commit, "source_sha256": checksums[archive_name]}:
		raise ValueError("Release metadata does not match the checked-out tag")
	return metadata

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--tag", required=True)
	parser.add_argument("--directory", default="dist")
	args = parser.parse_args()
	commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
	tag_commit = subprocess.check_output(["git", "rev-parse", f"refs/tags/{args.tag}^{{commit}}"], text=True).strip()
	if commit != tag_commit:
		raise ValueError("Checkout differs from release tag")
	print(json.dumps(verify(args.directory, args.tag, commit), indent=2))
