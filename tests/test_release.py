#!/usr/bin/env python3
import hashlib
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from release import build_release


class ReleaseTests(unittest.TestCase):
	def setUp(self):
		self.temp = tempfile.TemporaryDirectory(prefix="txms-release-test-")
		self.root = Path(self.temp.name)
		self.git("init", "-q")
		self.git("config", "user.email", "test@example.invalid")
		self.git("config", "user.name", "Release test")
		(self.root / "CMakeLists.txt").write_text("project(txms VERSION 0.1.0 LANGUAGES C)\n")
		(self.root / "LICENSE").write_text("Test fixture license\n")
		(self.root / "LIBTXMS_VERSION").write_text("0.1.0\n")
		(self.root / "LIBTXMS_REVISION").write_text("a" * 40 + "\n")
		self.git("add", ".")
		self.git("commit", "-qm", "fixture")
		self.git("tag", "0.1.0")

	def tearDown(self):
		self.temp.cleanup()

	def git(self, *args):
		return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

	def test_archive_is_tagged_tree_with_checksums(self):
		(self.root / "conan.lock").write_text("must not enter release\n")
		out = self.root / "dist"
		metadata = build_release(self.root, "libtxms", "0.1.0", out)
		archive = out / "libtxms-0.1.0.tar.gz"
		with tarfile.open(archive) as source:
			self.assertIn("libtxms-0.1.0/LICENSE", source.getnames())
			self.assertNotIn("libtxms-0.1.0/conan.lock", source.getnames())
		self.assertEqual(metadata["commit"], self.git("rev-parse", "HEAD"))
		self.assertEqual(metadata["source_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())

	def test_gateway_records_tested_dependency(self):
		metadata = build_release(self.root, "kamailio-txms", "0.1.0", self.root / "dist")
		self.assertEqual(metadata["libtxms_version"], "0.1.0")
		self.assertEqual(metadata["libtxms_commit"], "a" * 40)

	def test_mismatched_or_unsafe_version_rejected(self):
		self.git("tag", "0.2.0")
		for tag in ("0.2.0", "v0.1.0", "0.1.0-rc1", "0.1.0;echo bad", "00.1.0"):
			with self.subTest(tag=tag), self.assertRaises(ValueError):
				build_release(self.root, "libtxms", tag, self.root / "dist")

	def test_dirty_tracked_file_rejected(self):
		(self.root / "LICENSE").write_text("changed\n")
		with self.assertRaises(ValueError):
			build_release(self.root, "libtxms", "0.1.0", self.root / "dist")

	def test_checkout_must_match_tag(self):
		(self.root / "LICENSE").write_text("changed\n")
		self.git("commit", "-qam", "changed")
		with self.assertRaises(ValueError):
			build_release(self.root, "libtxms", "0.1.0", self.root / "dist")


	def test_invalid_dependency_revision_rejected(self):
		(self.root / "LIBTXMS_REVISION").write_text("main\n")
		self.git("commit", "-qam", "invalid dependency revision")
		self.git("tag", "-f", "0.1.0")
		with self.assertRaises(ValueError):
			build_release(self.root, "kamailio-txms", "0.1.0", self.root / "dist")


class WorkflowTests(unittest.TestCase):
	def test_published_release_uploads_only_after_tests(self):
		workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
		# YAML 1.1 parses the Actions `on` key as True.
		self.assertEqual(workflow[True], {"release": {"types": ["published"]}})
		jobs = workflow["jobs"]
		self.assertEqual(jobs["tests"]["uses"], "./.github/workflows/ci.yml")
		self.assertEqual(jobs["assets"]["needs"], "tests")
		self.assertEqual(set(jobs["publish"]["needs"]), {"tests", "assets"})
		self.assertEqual(jobs["publish"]["env"]["TAG"], "${{ github.event.release.tag_name }}")
		commands = "\n".join(step.get("run", "") for step in jobs["publish"]["steps"])
		self.assertIn('gh release upload "$TAG"', commands)
		self.assertNotIn("gh release create", commands)
		if "conan-center" in jobs:
			self.assertEqual(jobs["conan-center"]["needs"], "publish")
			self.assertEqual(jobs["conan-center"]["with"]["tag"], "${{ github.event.release.tag_name }}")

	@unittest.skipUnless((ROOT / "LIBTXMS_REVISION").exists(), "Gateway dependency check")
	def test_gateway_checks_out_pinned_commit_in_every_build(self):
		self.assertRegex((ROOT / "LIBTXMS_REVISION").read_text().strip(), r"^[0-9a-f]{40}$")
		workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
		for name in ("core", "kamailio", "fuzz"):
			steps = workflow["jobs"][name]["steps"]
			checkout = next(step for step in steps if step.get("with", {}).get("repository") == "DataLayerHost/libtxms")
			self.assertEqual(checkout["with"]["ref"], "${{ env.LIBTXMS_REF }}")
			self.assertTrue(any("cat LIBTXMS_REVISION" in step.get("run", "") for step in steps))


if (ROOT / "tools/prepare_conan_center.py").exists():
	from prepare_conan_center import prepare
	from submit_conan_center import merge_recipe
	from verify_release import verify

	class ConanCenterTests(unittest.TestCase):
		setUp = ReleaseTests.setUp
		tearDown = ReleaseTests.tearDown
		git = ReleaseTests.git
		def test_release_verification_rejects_tampering(self):
			out = self.root / "dist"
			metadata = build_release(self.root, "libtxms", "0.1.0", out)
			with (out / "SHA256SUMS").open("a") as checksums:
				checksums.write(hashlib.sha256((out / "release.json").read_bytes()).hexdigest() + "  release.json\n")
			self.assertEqual(verify(out, "0.1.0", metadata["commit"]), metadata)
			(out / "libtxms-0.1.0.tar.gz").write_bytes(b"tampered")
			with self.assertRaises(ValueError):
				verify(out, "0.1.0", metadata["commit"])

		def test_conan_metadata_preserves_existing_versions(self):
			out = self.root / "dist"
			build_release(self.root, "libtxms", "0.1.0", out)
			stage = self.root / "stage"
			prepare(ROOT, "0.1.0", out / "libtxms-0.1.0.tar.gz", stage)
			destination = self.root / "index"
			old = destination / "recipes/libtxms/all"
			old.mkdir(parents=True)
			(old / "conandata.yml").write_text(yaml.safe_dump({"sources": {"0.0.9": {"url": "https://example.invalid/old", "sha256": "a"*64}}}))
			(old.parent / "config.yml").write_text(yaml.safe_dump({"versions": {"0.0.9": {"folder": "all"}}}))
			merge_recipe(stage, destination, "0.1.0")
			before = (old / "conandata.yml").read_bytes()
			self.assertEqual(set(yaml.safe_load(before)["sources"]), {"0.0.9", "0.1.0"})
			merge_recipe(stage, destination, "0.1.0")
			self.assertEqual(before, (old / "conandata.yml").read_bytes())
			data = yaml.safe_load((stage / "recipes/libtxms/all/conandata.yml").read_text())
			data["sources"]["0.1.0"]["sha256"] = "b"*64
			(stage / "recipes/libtxms/all/conandata.yml").write_text(yaml.safe_dump(data))
			with self.assertRaises(ValueError):
				merge_recipe(stage, destination, "0.1.0")

if __name__ == "__main__":
	unittest.main()
