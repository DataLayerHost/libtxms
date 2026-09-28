#!/usr/bin/env python3
"""Exercise the staged download recipe against the archive before publication."""
import argparse
from functools import partial
import http.server
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import yaml

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--recipe", required=True)
	parser.add_argument("--archive", required=True)
	parser.add_argument("--version", required=True)
	args = parser.parse_args()
	archive = Path(args.archive).resolve()
	handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(archive.parent))
	server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
	threading.Thread(target=server.serve_forever, daemon=True).start()
	try:
		with tempfile.TemporaryDirectory(prefix="txms-conan-recipe-") as folder:
			shutil.copytree(args.recipe, folder, dirs_exist_ok=True)
			data_path = Path(folder, "conandata.yml")
			data = yaml.safe_load(data_path.read_text())
			data["sources"][args.version]["url"] = f"http://127.0.0.1:{server.server_port}/{archive.name}"
			data_path.write_text(yaml.safe_dump(data))
			for shared in ("False", "True"):
				subprocess.run(["conan", "create", folder, "--version", args.version, "--build=missing", "--no-remote", "-o", f"libtxms/*:shared={shared}"], check=True)
	finally:
		server.shutdown()
		server.server_close()
