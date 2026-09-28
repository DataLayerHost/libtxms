#!/usr/bin/env python3
"""Open an idempotent recipe PR using an explicitly configured ConanCenter fork."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import yaml
from release import VERSION

UPSTREAM = "conan-io/conan-center-index"


def merge_recipe(stage, destination, version):
	"""Preserve older versions and refuse to replace an existing source checksum."""
	source = Path(stage) / "recipes/libtxms"
	target = Path(destination) / "recipes/libtxms"
	data = yaml.safe_load((source / "all/conandata.yml").read_text())
	new_source = data["sources"][version]
	previous_path = target / "all/conandata.yml"
	previous = yaml.safe_load(previous_path.read_text()) if previous_path.exists() else {"sources": {}}
	old_source = previous.setdefault("sources", {}).get(version)
	if old_source is not None and old_source != new_source:
		raise ValueError("Existing version has different source metadata; never overwrite a published version")
	config_path = target / "config.yml"
	config = yaml.safe_load(config_path.read_text()) if config_path.exists() else {"versions": {}}
	if version in config.get("versions", {}) and config["versions"][version].get("folder") != "all":
		raise ValueError("Existing version uses another recipe folder; manual review is required")
	previous["sources"][version] = new_source
	config.setdefault("versions", {})[version] = {"folder": "all"}
	(target / "all").mkdir(parents=True, exist_ok=True)
	shutil.copy2(source / "all/conanfile.py", target / "all/conanfile.py")
	shutil.copytree(source / "all/test_package", target / "all/test_package", dirs_exist_ok=True)
	previous_path.write_text(yaml.safe_dump(previous, sort_keys=False))
	config_path.write_text(yaml.safe_dump(config, sort_keys=False))


def submit(fork, version, stage):
	if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", fork) or fork.lower() == UPSTREAM.lower():
		raise ValueError("Set CONAN_CENTER_FORK to your own owner/repository fork")
	if not re.fullmatch(VERSION, version):
		raise ValueError("Invalid stable version")
	if not os.environ.get("GH_TOKEN"):
		raise ValueError("CONAN_CENTER_TOKEN is required to submit to the configured fork")
	def run(*args, cwd=None):
		return subprocess.check_output(args, cwd=cwd, text=True).strip()
	info = json.loads(run("gh", "api", f"repos/{fork}"))
	if info.get("parent", {}).get("full_name") != UPSTREAM:
		raise ValueError("Configured repository is not a fork of ConanCenterIndex")
	base = run("gh", "api", f"repos/{UPSTREAM}", "--jq", ".default_branch")
	branch = f"automation/libtxms-{version}"
	owner = fork.split("/")[0]
	with tempfile.TemporaryDirectory(prefix="txms-cci-pr-") as folder:
		repo = Path(folder, "index")
		# gh auth configures a credential helper; the token never appears in URLs.
		run("gh", "auth", "setup-git")
		run("git", "clone", "--filter=blob:none", "--sparse", f"https://github.com/{fork}.git", str(repo))
		run("git", "sparse-checkout", "set", "recipes/libtxms", cwd=repo)
		run("git", "remote", "add", "upstream", f"https://github.com/{UPSTREAM}.git", cwd=repo)
		run("git", "fetch", "upstream", base, cwd=repo)
		existing = run("git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}", cwd=repo)
		if existing:
			run("git", "fetch", "origin", branch, cwd=repo)
			run("git", "checkout", "-b", branch, "FETCH_HEAD", cwd=repo)
		else:
			run("git", "checkout", "-b", branch, f"upstream/{base}", cwd=repo)
		merge_recipe(stage, repo, version)
		run("git", "add", "--", "recipes/libtxms", cwd=repo)
		if run("git", "diff", "--cached", "--name-only", cwd=repo):
			run("git", "-c", "user.name=TxMS release automation", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-m", f"libtxms: add version {version}", cwd=repo)
			run("git", "push", "origin", f"HEAD:refs/heads/{branch}", cwd=repo)
		elif not existing:
			print("ConanCenter already contains this recipe; no PR needed")
			return
		# REST supports organization-owned forks and owner-qualified heads.
		# gh pr create/list do not support all of these combinations.
		if not run("git", "diff", f"upstream/{base}", "HEAD", "--", "recipes/libtxms", cwd=repo):
			print("Recipe changes are already upstream; no PR needed")
			return
		prs = json.loads(run("gh", "api", "--method", "GET", f"repos/{UPSTREAM}/pulls", "-f", f"head={owner}:{branch}", "-f", "state=open"))
		if prs:
			print(prs[0]["html_url"])
			return
		body = Path(folder, "body.md")
		body.write_text(f"Adds libtxms {version}, the standalone C11 TxMS codec.\n\n"
			f"Source release: https://github.com/DataLayerHost/libtxms/releases/tag/{version}\n\n"
			"The recipe downloads the release archive with its SHA-256 checksum. Static and shared packages were built and their C consumer was executed before submission.\n\n"
			"Library license: LicenseRef-libtxms-CORE; the complete CORE license and NOTICE are packaged. Recipe and test_package are MIT licensed. Please review custom-license eligibility.\n")
		request = Path(folder, "pull-request.json")
		request.write_text(json.dumps({"base": base, "head": f"{owner}:{branch}", "head_repo": fork.split("/")[1],
			"title": f"libtxms/{version}: add recipe", "body": body.read_text()}))
		print(run("gh", "api", "--method", "POST", f"repos/{UPSTREAM}/pulls", "--input", str(request), "--jq", ".html_url"))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--fork", required=True)
	parser.add_argument("--version", required=True)
	parser.add_argument("--stage", default="release-stage")
	args = parser.parse_args()
	submit(args.fork, args.version, Path(args.stage).resolve())
