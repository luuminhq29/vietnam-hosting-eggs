"""Comprehensive automated verification suite for Vietnam Hosting Universal Eggs."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from generator.specs.loader import load_all_specs
from generator.validator import validate_repository


class TestVietnamHostingUniversalEggs(unittest.TestCase):
    def test_exact_egg_inventory_count(self) -> None:
        specs = load_all_specs()
        counts: dict[str, int] = {}
        for s in specs:
            counts[s.category] = counts.get(s.category, 0) + 1

        expected = {
            "languages": 26,
            "operating-systems": 15,
            "discord-bots": 17,
            "web-hosting": 22,
            "databases": 14,
            "game-servers": 29,
            "applications": 19,
            "utilities": 5,
        }
        self.assertEqual(counts, expected)
        self.assertEqual(len(specs), 147)

    def test_strict_repository_validation_passes(self) -> None:
        report = validate_repository()
        self.assertEqual(report.checked_eggs, 147)
        self.assertGreaterEqual(report.checked_dockerfiles, 80)
        self.assertEqual(
            report.errors,
            [],
            msg="\n".join(f"{i.target} [{i.code}]: {i.message}" for i in report.errors),
        )
        self.assertEqual(
            report.warnings,
            [],
            msg="\n".join(f"{i.target} [{i.code}]: {i.message}" for i in report.warnings),
        )

    def test_architecture_honesty_for_amd64_only_workloads(self) -> None:
        amd64_only_ids = {
            "arch-linux",
            "minecraft-bedrock",
            "terraria",
            "tshock",
            "factorio",
            "valheim",
            "palworld",
            "rust-game",
            "ark",
            "cs2",
            "project-zomboid",
            "dont-starve-together",
            "tf2",
            "fivem",
            "mta-sa",
            "unturned",
        }
        for egg_id in amd64_only_ids:
            matches = list((REPO_ROOT / "eggs").rglob(f"{egg_id}/metadata.json"))
            self.assertEqual(len(matches), 1, f"Missing metadata.json for {egg_id}")
            meta = json.loads(matches[0].read_text(encoding="utf-8"))
            self.assertEqual(
                meta["supported_architectures"],
                ["amd64"],
                f"{egg_id} must NOT claim arm64 support without official upstream binary!",
            )

    def test_sqlite_workspace_not_network_db_server(self) -> None:
        meta = json.loads((REPO_ROOT / "eggs/databases/sqlite-workspace/metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(meta["requires_inbound_port"])
        self.assertIn("NOT a standalone", meta["description"])

    def test_linux_os_eggs_are_unprivileged(self) -> None:
        os_dir = REPO_ROOT / "eggs/operating-systems"
        os_metas = list(os_dir.glob("*/metadata.json"))
        self.assertEqual(len(os_metas), 15)
        for mf in os_metas:
            meta = json.loads(mf.read_text(encoding="utf-8"))
            priv = meta["privileged_requirements"]
            self.assertFalse(priv["requires_privileged"])
            self.assertFalse(priv["requires_docker_socket"])
            self.assertFalse(priv["requires_kernel_features"])
            inst = (mf.parent / "install.sh").read_text(encoding="utf-8")
            self.assertIn("SSH_USER: ubuntu", inst)
            self.assertIn("PASSWORD: vietnam999", inst)
            self.assertIn("/mnt/server/readme.md", inst)

    def test_catalog_and_compatibility_sync(self) -> None:
        catalog = json.loads((REPO_ROOT / "catalog.json").read_text(encoding="utf-8"))
        compat = json.loads((REPO_ROOT / "compatibility.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["total_eggs"], 147)
        self.assertEqual(len(catalog["eggs"]), 147)
        self.assertEqual(compat["summary"]["total"], 147)
        self.assertEqual(compat["summary"]["amd64_supported"], 147)
        self.assertEqual(compat["summary"]["arm64_supported"], 131)
        self.assertEqual(compat["summary"]["amd64_only"], 16)

    def test_cli_commands_dry_run(self) -> None:
        cmds = [
            [sys.executable, "-m", "generator", "list", "--category", "databases", "--format", "json"],
            [sys.executable, "-m", "generator", "validate", "--strict"],
            [sys.executable, "-m", "generator", "build", "--only", "python-3.13", "--dry-run"],
            [sys.executable, "-m", "generator", "update", "--dry-run"],
            [sys.executable, "-m", "generator", "create", "sample-runtime", "--category", "languages", "--dry-run"],
            [sys.executable, "-m", "generator", "export", "--category", "utilities", "--dry-run"],
            [sys.executable, "-m", "generator", "package", "--dry-run"],
        ]
        for cmd in cmds:
            proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, f"CLI failed: {cmd}\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")

    def test_dual_ptdl_v1_and_v2_structure(self) -> None:
        v1_files = list((REPO_ROOT / "eggs").rglob("egg-ptdl-v1.json"))
        v2_files = list((REPO_ROOT / "eggs").rglob("egg.json"))
        self.assertEqual(len(v1_files), 147)
        self.assertEqual(len(v2_files), 147)
        for v1_path in v1_files:
            v1 = json.loads(v1_path.read_text(encoding="utf-8"))
            v2 = json.loads((v1_path.parent / "egg.json").read_text(encoding="utf-8"))
            self.assertEqual(v1["meta"]["version"], "PTDL_v1")
            self.assertEqual(v2["meta"]["version"], "PTDL_v2")
            self.assertIn("images", v1)
            self.assertNotIn("docker_images", v1)
            self.assertNotIn("file_denylist", v1)
            self.assertIn("docker_images", v2)
            self.assertEqual(v1["images"], list(dict.fromkeys(v2["docker_images"].values())))
            for var in v1["variables"]:
                self.assertNotIn("field_type", var)

    def test_bash_syntax_all_scripts_and_startups(self) -> None:
        bash_candidates = [
            Path("/bin/bash"),
            Path("/usr/bin/bash"),
            Path(r"C:\Program Files\Git\bin\bash.exe"),
        ]
        bash_bin = next((str(p) for p in bash_candidates if p.exists()), None)
        if not bash_bin:
            self.skipTest("GNU bash binary not found on host")

        # 1. Core scripts & utility scripts
        script_files = list((REPO_ROOT / "core").glob("*.sh")) + list((REPO_ROOT / "scripts").glob("*.sh"))
        for sf in script_files:
            proc = subprocess.run([bash_bin, "-n", str(sf)], capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, f"bash -n failed for {sf}: {proc.stderr}")

        # 2. All 147 Egg startup commands (with sample Wings numeric placeholders substituted)
        failures: list[str] = []
        for egg_path in sorted((REPO_ROOT / "eggs").rglob("egg.json")):
            data = json.loads(egg_path.read_text(encoding="utf-8"))
            cmd = (
                data["startup"]
                .replace("{{SERVER_PORT}}", "8080")
                .replace("{{SERVER_MEMORY}}", "2048")
                .replace("{{SERVER_IP}}", "0.0.0.0")
            )
            proc = subprocess.run([bash_bin, "-n", "-c", cmd], capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                failures.append(f"{egg_path.relative_to(REPO_ROOT)}: {proc.stderr.strip()}")
        self.assertEqual(failures, [], msg="Startup bash syntax errors:\n" + "\n".join(failures))

    def test_publish_requires_admin_confirmation(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "generator", "build", "--only", "python-3.13", "--push"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--confirm-publish", proc.stderr)


if __name__ == "__main__":
    unittest.main()
