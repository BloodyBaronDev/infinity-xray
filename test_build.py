"""Проверки целостности релиза и экспорта Infinity Xray."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build


class ReleaseTests(unittest.TestCase):
    def test_current_release_and_export_files(self):
        release = build.load_release()
        self.assertEqual(release["name"], "Infinity Xray")
        self.assertEqual(len(release["upstream"]["commit"]), 40)
        for name in build.PUBLIC_FILES:
            self.assertTrue((build.ROOT / name).is_file(), name)

    def make_release(self, root, version="0.1.0-rc.1", filename="infinity-xray.patch"):
        (root / "VERSION").write_text(version, encoding="utf-8")
        (root / "infinity-xray.patch").write_bytes(b"patch\n")
        (root / "release.json").write_text(json.dumps({
            "patch": {"file": filename, "sha256": build.sha256(root / "infinity-xray.patch")},
        }), encoding="utf-8")

    def test_modified_patch_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_release(root)
            (root / "infinity-xray.patch").write_bytes(b"changed\n")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                build.load_release(root)

    def test_version_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for version in ("1", "01.0.0", "0.1.0-rc.0", "0.1.0;cmd"):
                self.make_release(root, version)
                with self.assertRaisesRegex(ValueError, "VERSION"):
                    build.load_release(root)

    def test_patch_outside_root_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_release(root, filename="../outside.patch")
            with self.assertRaisesRegex(ValueError, "корне"):
                build.load_release(root)

    def test_export_is_allowlist_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "public"
            build.export(destination)
            self.assertEqual({file.name for file in destination.iterdir()}, set(build.PUBLIC_FILES))
            self.assertFalse((destination / "lab").exists())
            self.assertEqual(build.load_release(destination), build.load_release())
            (destination / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "существует"):
                build.export(destination)
            self.assertEqual((destination / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_checks_do_not_inherit_cross_compile_target(self):
        with patch.dict(os.environ, {"GOOS": "linux", "GOARCH": "arm64", "GOFLAGS": "-race"}):
            env = build.go_environment({"go_toolchain": "go1.27.3"})
            for key in ("GOOS", "GOARCH", "GOFLAGS"):
                self.assertNotIn(key, env)
            target = build.go_environment({"go_toolchain": "go1.27.3"}, "linux/amd64")
            self.assertEqual((target["GOOS"], target["GOARCH"], target["CGO_ENABLED"]), ("linux", "amd64", "0"))

    def test_prepare_rejects_wrong_upstream_before_applying_patch(self):
        release = build.load_release()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(build, "ROOT", Path(folder)), patch.object(build, "run") as run:
                run.return_value = "0" * 40
                with self.assertRaisesRegex(ValueError, "база"):
                    build.prepare(release, Path(folder) / "cache")
                self.assertFalse(any("apply" in call.args[0] for call in run.call_args_list))


if __name__ == "__main__":
    unittest.main()
