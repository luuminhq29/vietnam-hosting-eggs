"""Vietnam Hosting Universal Egg CLI (`vnh-egg`).

Commands:
  list, create, generate, validate, build, test, export, update, doctor, package
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from generator import __version__
from generator.dockerfile_gen import generate_all_dockerfiles
from generator.models import (
    GHCR_NAMESPACE,
    REPO_ROOT,
    VALID_ARCHITECTURES,
    VALID_CATEGORIES,
    VALID_STATUSES,
)
from generator.renderer import build_catalog_and_compatibility, render_egg
from generator.specs.loader import load_all_specs
from generator.validator import validate_repository


def cmd_list(args: argparse.Namespace) -> int:
    specs = load_all_specs(category=args.category)
    if args.arch:
        specs = [s for s in specs if args.arch in s.supported_architectures]
    if args.status:
        specs = [s for s in specs if s.status.lower() == args.status.lower()]

    if args.format == "json":
        payload = [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "architectures": s.supported_architectures,
                "status": s.status,
                "versions": s.supported_versions,
            }
            for s in specs
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"{'CATEGORY':<20} {'ID':<26} {'ARCH':<12} {'STATUS':<12} NAME")
    print("-" * 100)
    for s in specs:
        arch_str = ",".join(s.supported_architectures)
        print(f"{s.category:<20} {s.id:<26} {arch_str:<12} {s.status:<12} {s.name}")
    print("-" * 100)
    print(f"Total: {len(specs)} egg(s)")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    egg_id = args.id.strip().lower()
    if args.category not in VALID_CATEGORIES:
        print(f"[ERROR] Invalid category '{args.category}'. Valid: {', '.join(VALID_CATEGORIES)}", file=sys.stderr)
        return 2
    custom_dir = REPO_ROOT / "generator" / "specs" / "custom"
    target = custom_dir / f"{egg_id}.json"
    if target.exists() and not args.force:
        print(f"[ERROR] Custom spec already exists: {target}. Use --force to overwrite.", file=sys.stderr)
        return 1

    arches = [a.strip().lower() for a in args.arch.split(",") if a.strip()]
    for a in arches:
        if a not in VALID_ARCHITECTURES:
            print(f"[ERROR] Invalid architecture '{a}'.", file=sys.stderr)
            return 2

    spec_payload: dict[str, Any] = {
        "id": egg_id,
        "name": args.name or f"Vietnam Hosting — {egg_id.replace('-', ' ').title()}",
        "category": args.category,
        "description": args.description or f"Custom Vietnam Hosting Pterodactyl Egg for {egg_id}.",
        "icon": args.icon or egg_id,
        "supported_versions": [args.runtime_version or "1.0"],
        "supported_architectures": arches,
        "minimum_ram_mb": args.min_ram,
        "recommended_ram_mb": max(args.min_ram * 2, 512),
        "minimum_disk_mb": 1024,
        "docker_images": {"Default": args.image},
        "custom_docker_images": {"Default": f"{GHCR_NAMESPACE}:{egg_id}"},
        "image_source": "upstream_official_yolk" if not args.image.startswith(GHCR_NAMESPACE) else "requires_ghcr_build",
        "startup": args.startup,
        "stop": "^C",
        "startup_done": "READY",
        "install_body": 'echo "[VNH][INSTALL] Custom runtime initialized in /mnt/server."',
        "variables": [
            {
                "name": "Application Entrypoint",
                "description": "Main script or binary inside /home/container.",
                "env_variable": "APP_FILE",
                "default_value": "main.sh",
                "user_viewable": True,
                "user_editable": True,
                "rules": "required|string|max:128",
                "field_type": "text",
            }
        ],
        "upstream_license": "MIT",
        "upstream_url": "https://vietnam-hosting.net",
    }

    if args.dry_run:
        print(f"[DRY-RUN] Would create custom spec at {target}:")
        print(json.dumps(spec_payload, indent=2, ensure_ascii=False))
        return 0

    custom_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Created extensible custom egg spec: {target}")
    print("Run `vnh-egg generate` to render egg.json, install.sh, README.md, metadata.json, and catalog.json.")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    specs = load_all_specs(category=args.category, only_id=args.only)
    if not specs:
        print("[ERROR] No matching egg specifications found.", file=sys.stderr)
        return 1

    if not args.skip_dockerfiles and not args.only and not args.category:
        dfs = generate_all_dockerfiles(dry_run=args.dry_run)
        prefix = "[DRY-RUN] Would generate" if args.dry_run else "[OK] Generated"
        print(f"{prefix} {len(dfs)} Dockerfile(s) from versions.json.")

    for spec in specs:
        egg_dir = render_egg(spec, registry_mode=args.registry, dry_run=args.dry_run)
        if args.verbose:
            action = "[DRY-RUN]" if args.dry_run else "[GEN]"
            print(f"{action} {egg_dir.relative_to(REPO_ROOT)}")

    if not args.only and not args.category:
        all_specs = load_all_specs()
        catalog, compat = build_catalog_and_compatibility(all_specs, registry_mode=args.registry, dry_run=args.dry_run)
        prefix = "[DRY-RUN] Would update" if args.dry_run else "[OK] Updated"
        print(
            f"{prefix} catalog.json ({catalog['total_eggs']} eggs), compatibility.json "
            f"(amd64={compat['summary']['amd64_supported']}, arm64={compat['summary']['arm64_supported']}), "
            "and docs/catalog-api/."
        )
    else:
        prefix = "[DRY-RUN] Would generate" if args.dry_run else "[OK] Generated"
        print(f"{prefix} {len(specs)} egg(s).")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    report = validate_repository(only_id=args.only)
    if args.json:
        payload = {
            "ok": report.ok,
            "checked_eggs": report.checked_eggs,
            "checked_dockerfiles": report.checked_dockerfiles,
            "error_count": len(report.errors),
            "warning_count": len(report.warnings),
            "issues": [
                {"severity": i.severity, "target": i.target, "code": i.code, "message": i.message}
                for i in report.issues
            ],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for issue in report.issues:
            print(f"[{issue.severity}] {issue.target} ({issue.code}): {issue.message}")
        print(
            f"Validation Summary: eggs={report.checked_eggs}, dockerfiles={report.checked_dockerfiles}, "
            f"errors={len(report.errors)}, warnings={len(report.warnings)}"
        )

    if not report.ok:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    versions_file = REPO_ROOT / "versions.json"
    if not versions_file.exists():
        print("[ERROR] versions.json not found.", file=sys.stderr)
        return 1

    if args.push and not args.confirm_publish:
        print(
            "[BLOCKED] Publishing images to GHCR modifies external registry resources and requires "
            "explicit administrator approval (`--confirm-publish`).",
            file=sys.stderr,
        )
        return 2

    versions = json.loads(versions_file.read_text(encoding="utf-8"))
    images = versions.get("docker_images", [])
    if args.only:
        images = [i for i in images if i["tag"] == args.only or i["id"] == args.only]
    if not images:
        print("[ERROR] No matching Docker images in versions.json.", file=sys.stderr)
        return 1

    docker_bin = shutil.which("docker")
    if not docker_bin and not args.dry_run:
        print("[ERROR] `docker` binary not found on this host. Use `--dry-run` or run via GitHub Actions `build-images.yml`.", file=sys.stderr)
        return 1

    for img in images:
        platforms = args.platform or ",".join(f"linux/{a}" for a in img.get("architectures", ["amd64"]))
        full_tag = f"{GHCR_NAMESPACE}:{img['tag']}"
        cmd = [
            "docker",
            "buildx",
            "build",
            "--platform",
            platforms,
            "-f",
            img["dockerfile"],
            "-t",
            full_tag,
        ]
        if args.push:
            cmd.append("--push")
        else:
            cmd.append("--load" if "," not in platforms else "--output=type=image,push=false")
        cmd.append(".")

        if args.dry_run:
            print(f"[DRY-RUN] {' '.join(cmd)}")
        else:
            print(f"[BUILD] {' '.join(cmd)}")
            proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
            if proc.returncode != 0:
                print(f"[ERROR] Build failed for {full_tag} (exit {proc.returncode}).", file=sys.stderr)
                return proc.returncode
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    report = validate_repository(only_id=args.only)
    specs = load_all_specs(category=args.category, only_id=args.only)
    docker_avail = shutil.which("docker") is not None

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host_os": platform.platform(),
        "docker_available": docker_avail,
        "pterodactyl_live_environment": False,
        "static_validation": {
            "status": "PASS" if report.ok else "FAIL",
            "checked_eggs": report.checked_eggs,
            "checked_dockerfiles": report.checked_dockerfiles,
            "errors": len(report.errors),
            "warnings": len(report.warnings),
        },
        "runtime_integration_tests": {
            "status": "UNVERIFIED",
            "reason": "No live Pterodactyl Panel/Wings + Docker runtime attached to local test host.",
        },
        "eggs_tested": len(specs),
    }

    if args.report:
        out_path = Path(args.report)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[OK] Wrote test report to {out_path}")

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if report.ok else 1


def cmd_export(args: argparse.Namespace) -> int:
    out_dir = Path(args.output)
    specs = load_all_specs(category=args.category)
    if not specs:
        print("[ERROR] No eggs found to export.", file=sys.stderr)
        return 1

    formats = ("ptdl_v2", "ptdl_v1") if args.format == "both" else (args.format,)
    exported = 0
    for spec in specs:
        for fmt in formats:
            src_name = "egg.json" if fmt == "ptdl_v2" else "egg-ptdl-v1.json"
            dst_name = f"egg-vnh-{spec.id}.json" if fmt == "ptdl_v2" else f"egg-vnh-{spec.id}-v1.json"
            src = REPO_ROOT / "eggs" / spec.category / spec.id / src_name
            if not src.exists():
                print(f"[WARN] Missing generated {src_name} for {spec.id}; run `vnh-egg generate` first.")
                continue
            dest_cat = out_dir / fmt / spec.category
            dest_file = dest_cat / dst_name
            if args.dry_run:
                print(f"[DRY-RUN] {src.relative_to(REPO_ROOT)} -> {dest_file}")
            else:
                dest_cat.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest_file)
            exported += 1

    prefix = "[DRY-RUN] Would export" if args.dry_run else "[OK] Exported"
    print(f"{prefix} {exported} import-ready Egg JSON file(s) ({'+'.join(formats)}) to {out_dir}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    versions_file = REPO_ROOT / "versions.json"
    if not versions_file.exists():
        print("[ERROR] versions.json not found.", file=sys.stderr)
        return 1
    versions = json.loads(versions_file.read_text(encoding="utf-8"))
    today = date.today()
    eol_warnings: list[dict[str, str]] = []

    for item in versions.get("runtime_lifecycle", []):
        eol_raw = item.get("eol_date")
        if not eol_raw:
            continue
        try:
            eol_dt = date.fromisoformat(eol_raw)
        except ValueError:
            continue
        if eol_dt <= today:
            eol_warnings.append(
                {
                    "runtime": item["runtime"],
                    "version": item["version"],
                    "eol_date": eol_raw,
                    "status": "EOL_REACHED",
                    "recommendation": item.get("upgrade_target", "Upgrade to active LTS"),
                }
            )
        elif (eol_dt - today).days <= 120:
            eol_warnings.append(
                {
                    "runtime": item["runtime"],
                    "version": item["version"],
                    "eol_date": eol_raw,
                    "status": "APPROACHING_EOL",
                    "recommendation": item.get("upgrade_target", "Plan upgrade to active LTS"),
                }
            )

    summary = {
        "checked_on": today.isoformat(),
        "dry_run": args.dry_run,
        "tracked_runtimes": len(versions.get("runtime_lifecycle", [])),
        "tracked_docker_images": len(versions.get("docker_images", [])),
        "lifecycle_alerts": eol_warnings,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    tools = ("python", "python3", "git", "docker", "shellcheck", "hadolint", "trivy", "jq")
    print("=== Vietnam Hosting Universal Egg System — Doctor ===")
    print(f"CLI Version:   {__version__}")
    print(f"Repository:    {REPO_ROOT}")
    print(f"Platform:      {platform.platform()}")
    print("\nTool Availability:")
    for tool in tools:
        loc = shutil.which(tool)
        status = f"OK ({loc})" if loc else "MISSING (optional locally; runs in CI)"
        print(f"  - {tool:<12}: {status}")

    required_paths = [
        "core/entrypoint.sh",
        "core/startup.sh",
        "core/installer.sh",
        "core/healthcheck.sh",
        "core/environment.sh",
        "core/nat-ssh.sh",
        "schemas/ptdl_v1.schema.json",
        "schemas/ptdl_v2.schema.json",
        "schemas/metadata.schema.json",
        "schemas/catalog.schema.json",
        "versions.json",
        "catalog.json",
        "compatibility.json",
    ]
    print("\nCore Assets:")
    missing_core = 0
    for rel in required_paths:
        exists = (REPO_ROOT / rel).exists()
        if not exists:
            missing_core += 1
        print(f"  - {rel:<32}: {'OK' if exists else 'MISSING'}")

    report = validate_repository()
    print(
        f"\nRepository Validation: {'PASS' if report.ok else 'FAIL'} "
        f"(eggs={report.checked_eggs}, dockerfiles={report.checked_dockerfiles}, "
        f"errors={len(report.errors)}, warnings={len(report.warnings)})"
    )
    return 0 if (missing_core == 0 and report.ok) else 1


def cmd_package(args: argparse.Namespace) -> int:
    out_zip = Path(args.output)
    if not out_zip.is_absolute():
        out_zip = REPO_ROOT / out_zip

    include_roots = [
        "eggs",
        "docker",
        "core",
        "generator",
        "templates",
        "schemas",
        "scripts",
        "security",
        "tests",
        "docs",
        ".github",
        "catalog.json",
        "versions.json",
        "compatibility.json",
        "Makefile",
        "pyproject.toml",
        "bin",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE",
        "README.md",
        "BUILD_STATUS.md",
    ]

    files_to_pack: list[Path] = []
    for item in include_roots:
        p = REPO_ROOT / item
        if not p.exists():
            continue
        if p.is_file():
            files_to_pack.append(p)
        else:
            for sub in sorted(p.rglob("*")):
                if sub.is_file() and "__pycache__" not in sub.parts and not sub.name.endswith(".pyc"):
                    files_to_pack.append(sub)

    if args.dry_run:
        print(f"[DRY-RUN] Would package {len(files_to_pack)} files into {out_zip}")
        return 0

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file_path in files_to_pack:
            arcname = f"vietnam-hosting-eggs/{file_path.relative_to(REPO_ROOT).as_posix()}"
            zf.write(file_path, arcname=arcname)

    sha256_hash = hashlib.sha256(out_zip.read_bytes()).hexdigest()
    sha_file = out_zip.with_suffix(out_zip.suffix + ".sha256")
    sha_file.write_text(f"{sha256_hash}  {out_zip.name}\n", encoding="utf-8")

    manifest = {
        "package": out_zip.name,
        "version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files_to_pack),
        "size_bytes": out_zip.stat().st_size,
        "sha256": sha256_hash,
    }
    manifest_file = out_zip.parent / "package-manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] Packaged {len(files_to_pack)} files -> {out_zip} ({out_zip.stat().st_size:,} bytes)")
    print(f"[OK] SHA256: {sha256_hash} ({sha_file.name})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vnh-egg",
        description="Vietnam Hosting — Universal Pterodactyl Egg Management CLI",
    )
    parser.add_argument("--version", action="version", version=f"vnh-egg {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List available eggs")
    p_list.add_argument("--category", choices=VALID_CATEGORIES)
    p_list.add_argument("--arch", choices=VALID_ARCHITECTURES)
    p_list.add_argument("--status", choices=VALID_STATUSES)
    p_list.add_argument("--format", choices=("table", "json"), default="table")
    p_list.set_defaults(func=cmd_list)

    # create
    p_create = sub.add_parser("create", help="Create a new extensible custom egg specification")
    p_create.add_argument("id", help="Egg slug ID (lowercase alphanumeric with hyphens)")
    p_create.add_argument("--category", required=True, choices=VALID_CATEGORIES)
    p_create.add_argument("--name", help="Display name")
    p_create.add_argument("--description", help="Short description")
    p_create.add_argument("--icon", help="Icon slug")
    p_create.add_argument("--image", default="ghcr.io/pterodactyl/yolks:debian", help="Docker image")
    p_create.add_argument("--startup", default="/bin/bash {{APP_FILE}}", help="Startup command")
    p_create.add_argument("--arch", default="amd64,arm64", help="Comma-separated architectures")
    p_create.add_argument("--runtime-version", default="1.0", help="Supported version string")
    p_create.add_argument("--min-ram", type=int, default=256, help="Minimum RAM in MiB")
    p_create.add_argument("--force", action="store_true")
    p_create.add_argument("--dry-run", action="store_true")
    p_create.set_defaults(func=cmd_create)

    # generate
    p_gen = sub.add_parser("generate", help="Generate Egg JSONs, scripts, READMEs, Dockerfiles, and Catalog")
    p_gen.add_argument("--category", choices=VALID_CATEGORIES)
    p_gen.add_argument("--only", help="Generate only a single egg ID")
    p_gen.add_argument("--registry", choices=("default", "ghcr"), default="default")
    p_gen.add_argument("--skip-dockerfiles", action="store_true")
    p_gen.add_argument("--dry-run", action="store_true")
    p_gen.add_argument("--verbose", "-v", action="store_true")
    p_gen.set_defaults(func=cmd_generate)

    # validate
    p_val = sub.add_parser("validate", help="Validate Egg JSON schemas, variables, scripts, and Dockerfiles")
    p_val.add_argument("--only", help="Validate only a single egg ID")
    p_val.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    p_val.add_argument("--json", action="store_true", help="Output JSON report")
    p_val.set_defaults(func=cmd_validate)

    # build
    p_build = sub.add_parser("build", help="Build Docker images using Buildx")
    p_build.add_argument("--only", help="Build a single image ID/tag from versions.json")
    p_build.add_argument("--platform", help="Override platform list (e.g. linux/amd64,linux/arm64)")
    p_build.add_argument("--push", action="store_true", help="Push built images to GHCR")
    p_build.add_argument("--confirm-publish", action="store_true", help="Required administrator confirmation for --push")
    p_build.add_argument("--dry-run", action="store_true")
    p_build.set_defaults(func=cmd_build)

    # test
    p_test = sub.add_parser("test", help="Run static validation and report integration test status")
    p_test.add_argument("--category", choices=VALID_CATEGORIES)
    p_test.add_argument("--only", help="Test a single egg ID")
    p_test.add_argument("--report", help="Write JSON test report to path")
    p_test.set_defaults(func=cmd_test)

    # export
    p_exp = sub.add_parser("export", help="Export clean import-ready PTDL_v1 & PTDL_v2 Egg JSON files")
    p_exp.add_argument("--output", default="dist/eggs", help="Destination folder")
    p_exp.add_argument("--category", choices=VALID_CATEGORIES)
    p_exp.add_argument("--format", choices=("both", "ptdl_v2", "ptdl_v1"), default="both", help="Egg schema format to export")
    p_exp.add_argument("--dry-run", action="store_true")
    p_exp.set_defaults(func=cmd_export)

    # update
    p_upd = sub.add_parser("update", help="Check runtime lifecycle and EOL status in versions.json")
    p_upd.add_argument("--dry-run", action="store_true")
    p_upd.add_argument("--check-eol", action="store_true", default=True)
    p_upd.set_defaults(func=cmd_update)

    # doctor
    p_doc = sub.add_parser("doctor", help="Inspect host tools, repository assets, and validation health")
    p_doc.set_defaults(func=cmd_doctor)

    # package
    p_pkg = sub.add_parser("package", help="Package the entire Egg suite into a release ZIP with SHA256")
    p_pkg.add_argument("--output", default="dist/vietnam-hosting-universal-eggs.zip", help="Output ZIP path")
    p_pkg.add_argument("--dry-run", action="store_true")
    p_pkg.set_defaults(func=cmd_package)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
