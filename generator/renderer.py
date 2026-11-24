"""Renderer for PTDL_v2 Eggs, scripts, metadata, README, catalog, and compatibility matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from generator.models import (
    DEFAULT_PANEL_VERSIONS,
    DEFAULT_WINGS_VERSIONS,
    EGG_AUTHOR_EMAIL,
    EXPORTED_AT_DEFAULT,
    LAST_UPDATED_DEFAULT,
    PROVIDER_NAME,
    PROVIDER_WEBSITE,
    REPO_ROOT,
    EggSpec,
)

RESOURCE_BASIS_VI = {
    "recommended_estimate": "giá trị khuyến nghị ước lượng cho vận hành sản xuất",
    "upstream_documented": "yêu cầu tài liệu chính thức từ nhà phát triển upstream",
    "benchmarked": "kết quả benchmark thực tế",
}

IMAGE_SOURCE_VI = {
    "upstream_official_yolk": "Official Pterodactyl/Community Yolks (đã xác minh nguồn công khai)",
    "hybrid_official_and_ghcr": "Official Yolks mặc định + Dockerfile GHCR Vietnam Hosting tùy chọn build",
    "requires_ghcr_build": "Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)",
}


def _render_install_script(spec: EggSpec) -> str:
    tmpl = (REPO_ROOT / "templates" / "install.sh.tmpl").read_text(encoding="utf-8")
    return (
        tmpl.replace("{{EGG_NAME}}", spec.name)
        .replace("{{EGG_ID}}", spec.id)
        .replace("{{EGG_VERSION}}", spec.version)
        .replace("{{INSTALL_BODY}}", spec.install_body.strip())
    )


def _select_images(spec: EggSpec, registry_mode: str) -> dict[str, str]:
    if registry_mode == "ghcr" and spec.custom_docker_images:
        return dict(spec.custom_docker_images)
    return dict(spec.docker_images)


def build_ptdl_v2_json(spec: EggSpec, registry_mode: str = "default") -> dict[str, Any]:
    install_script = _render_install_script(spec)
    images = _select_images(spec, registry_mode)
    return {
        "_comment": "DO NOT EDIT: FILE GENERATED AUTOMATICALLY BY VIETNAM HOSTING UNIVERSAL EGG SYSTEM (PTDL_v2)",
        "meta": {
            "version": "PTDL_v2",
            "update_url": None,
        },
        "exported_at": EXPORTED_AT_DEFAULT,
        "name": spec.name,
        "author": EGG_AUTHOR_EMAIL,
        "description": spec.description,
        "features": spec.features,
        "docker_images": images,
        "file_denylist": spec.file_denylist,
        "startup": spec.startup,
        "config": {
            "files": json.dumps(spec.config_files, indent=4) if spec.config_files else "{}",
            "startup": json.dumps({"done": spec.startup_done}),
            "logs": json.dumps(spec.config_logs) if spec.config_logs else "{}",
            "stop": spec.stop,
        },
        "scripts": {
            "installation": {
                "script": install_script,
                "container": spec.install_container,
                "entrypoint": spec.install_entrypoint,
            }
        },
        "variables": [v.to_ptdl_dict() for v in spec.variables],
    }


def build_ptdl_v1_json(spec: EggSpec, registry_mode: str = "default") -> dict[str, Any]:
    """Build authentic PTDL_v1 JSON (images[] array, no file_denylist, no variable field_type)."""
    install_script = _render_install_script(spec)
    images_map = _select_images(spec, registry_mode)
    unique_images: list[str] = list(dict.fromkeys(images_map.values()))
    return {
        "_comment": "DO NOT EDIT: FILE GENERATED AUTOMATICALLY BY VIETNAM HOSTING UNIVERSAL EGG SYSTEM (PTDL_v1)",
        "meta": {
            "version": "PTDL_v1",
            "update_url": None,
        },
        "exported_at": EXPORTED_AT_DEFAULT,
        "name": spec.name,
        "author": EGG_AUTHOR_EMAIL,
        "description": spec.description,
        "features": spec.features,
        "images": unique_images,
        "startup": spec.startup,
        "config": {
            "files": json.dumps(spec.config_files, indent=4) if spec.config_files else "{}",
            "startup": json.dumps({"done": spec.startup_done}),
            "logs": json.dumps(spec.config_logs) if spec.config_logs else "{}",
            "stop": spec.stop,
        },
        "scripts": {
            "installation": {
                "script": install_script,
                "container": spec.install_container,
                "entrypoint": spec.install_entrypoint,
            }
        },
        "variables": [v.to_ptdl_v1_dict() for v in spec.variables],
    }


def build_metadata_json(spec: EggSpec, registry_mode: str = "default") -> dict[str, Any]:
    images = _select_images(spec, registry_mode)
    return {
        "id": spec.id,
        "name": spec.name,
        "description": spec.description,
        "category": spec.category,
        "icon": spec.icon,
        "version": spec.version,
        "supported_versions": spec.supported_versions,
        "supported_architectures": spec.supported_architectures,
        "minimum_ram_mb": spec.minimum_ram_mb,
        "recommended_ram_mb": spec.recommended_ram_mb,
        "minimum_disk_mb": spec.minimum_disk_mb,
        "resource_basis": spec.resource_basis,
        "docker_images": images,
        "custom_docker_images": spec.custom_docker_images,
        "dockerfile_path": spec.dockerfile_path,
        "image_source": spec.image_source,
        "requires_inbound_port": spec.requires_inbound_port,
        "privileged_requirements": spec.privileged_requirements,
        "supported_panel_versions": DEFAULT_PANEL_VERSIONS,
        "supported_wings_versions": DEFAULT_WINGS_VERSIONS,
        "status": spec.status,
        "verification_status": "UNVERIFIED",
        "supported_schemas": ["PTDL_v1", "PTDL_v2"],
        "last_updated": LAST_UPDATED_DEFAULT,
        "upstream_license": spec.upstream_license,
        "upstream_url": spec.upstream_url,
        "eula_required": spec.eula_required,
        "steam_app_id": spec.steam_app_id,
        "notes": spec.notes,
    }


def build_test_config(spec: EggSpec) -> dict[str, Any]:
    return {
        "egg_id": spec.id,
        "category": spec.category,
        "schema_versions": ["PTDL_v1", "PTDL_v2"],
        "supported_architectures": spec.supported_architectures,
        "requires_inbound_port": spec.requires_inbound_port,
        "expected_startup_done": spec.startup_done,
        "stop_signal": spec.stop,
        "healthcheck": {
            "mode": spec.healthcheck_mode,
            "target": spec.healthcheck_target,
        },
        "checklist": {
            "ptdl_v1_schema_valid": "STATIC_VALIDATED",
            "ptdl_v2_schema_valid": "STATIC_VALIDATED",
            "panel_import": "UNVERIFIED",
            "install_script_execution": "UNVERIFIED",
            "docker_image_pull": "UNVERIFIED",
            "server_startup": "UNVERIFIED",
            "startup_detection": "UNVERIFIED",
            "console_io": "UNVERIFIED",
            "graceful_stop": "UNVERIFIED",
            "restart_data_persistence": "UNVERIFIED",
            "reinstall_behavior": "UNVERIFIED",
            "wings_sftp": "UNVERIFIED",
            "port_allocation": "UNVERIFIED" if spec.requires_inbound_port else "NOT_APPLICABLE",
            "ram_cpu_limits": "UNVERIFIED",
            "unprivileged_execution": "STATIC_VALIDATED",
            "secret_redaction": "STATIC_VALIDATED",
            "container_isolation": "UNVERIFIED",
            "backup_restore": "UNVERIFIED",
            "multi_arch_matrix": {arch: "UNVERIFIED" for arch in spec.supported_architectures},
        },
    }


def build_readme_vi(spec: EggSpec, registry_mode: str = "default") -> str:
    tmpl = (REPO_ROOT / "templates" / "README.md.tmpl").read_text(encoding="utf-8")
    images = _select_images(spec, registry_mode)

    img_lines = ["| Nhãn hiển thị | Docker Image |", "| :--- | :--- |"]
    for label, img in images.items():
        img_lines.append(f"| {label} | `{img}` |")
    img_table = "\n".join(img_lines)

    if spec.dockerfile_path:
        df_note = (
            f"> [!IMPORTANT]\n"
            f"> Dockerfile nguồn được cung cấp tại `{spec.dockerfile_path}`. "
            f"Image đích trên GHCR: `ghcr.io/luuminhq29/yolks:*` (build & publish qua `.github/workflows/build-images.yml` hoặc `vnh-egg build`)."
        )
    else:
        df_note = (
            "> [!TIP]\n"
            "> Egg sử dụng trực tiếp Official Pterodactyl / Community Yolks đã có sẵn. "
            "Có thể chuyển sang image nội bộ Vietnam Hosting bằng `vnh-egg generate --registry ghcr` sau khi publish GHCR."
        )

    if spec.variables:
        var_lines = [
            "| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |",
            "| :--- | :--- | :--- | :---: | :--- | :--- |",
        ]
        for v in spec.variables:
            default_disp = "`(trống)`" if not v.default_value else f"`{v.default_value}`"
            if any(k in v.env_variable for k in ("TOKEN", "PASSWORD", "SECRET", "KEY")):
                default_disp = "`(bí mật / để trống)`"
            editable = "Có" if v.user_editable else "Không"
            var_lines.append(
                f"| `{v.env_variable}` | {v.name} | {default_disp} | {editable} | `{v.rules}` | {v.description} |"
            )
        var_table = "\n".join(var_lines)
    else:
        var_table = "_Egg này không yêu cầu biến môi trường bổ sung ngoài biến hệ thống của Pterodactyl._"

    sec_notes = spec.security_notes_vi or (
        "- Chạy hoàn toàn trong không gian người dùng không đặc quyền (`container`).\n"
        "- Mọi token/mật khẩu phải truyền qua biến môi trường, tuyệt đối không commit vào Git hoặc in ra log."
    )
    if spec.eula_required:
        sec_notes += "\n- **Yêu cầu EULA:** Người dùng phải đồng ý điều khoản giấy phép (EULA) của nhà phát triển upstream trước khi vận hành."

    backup_notes = spec.backup_notes_vi or (
        "- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.\n"
        "- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu."
    )

    return (
        tmpl.replace("{{NAME}}", spec.name)
        .replace("{{ID}}", spec.id)
        .replace("{{CATEGORY}}", spec.category)
        .replace("{{VERSION}}", spec.version)
        .replace("{{STATUS}}", spec.status)
        .replace("{{VERIFICATION_STATUS}}", "UNVERIFIED (Static Validated)")
        .replace("{{DESCRIPTION}}", spec.description)
        .replace("{{SUPPORTED_VERSIONS}}", ", ".join(spec.supported_versions))
        .replace("{{SUPPORTED_ARCHITECTURES}}", ", ".join(a.upper() for a in spec.supported_architectures))
        .replace(
            "{{INBOUND_PORT_TEXT}}",
            "Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)" if spec.requires_inbound_port else "Không bắt buộc (ứng dụng kết nối outbound)",
        )
        .replace("{{IMAGE_SOURCE_TEXT}}", IMAGE_SOURCE_VI.get(spec.image_source, spec.image_source))
        .replace("{{UPSTREAM_URL}}", spec.upstream_url)
        .replace("{{UPSTREAM_LICENSE}}", spec.upstream_license)
        .replace("{{RESOURCE_BASIS_TEXT}}", RESOURCE_BASIS_VI.get(spec.resource_basis, spec.resource_basis))
        .replace("{{MINIMUM_RAM_MB}}", str(spec.minimum_ram_mb))
        .replace("{{RECOMMENDED_RAM_MB}}", str(spec.recommended_ram_mb))
        .replace("{{MINIMUM_DISK_MB}}", str(spec.minimum_disk_mb))
        .replace("{{RECOMMENDED_DISK_MB}}", str(max(spec.minimum_disk_mb * 2, 1024)))
        .replace("{{DOCKER_IMAGES_TABLE}}", img_table)
        .replace("{{DOCKERFILE_NOTE}}", df_note)
        .replace("{{VARIABLES_TABLE}}", var_table)
        .replace("{{STARTUP}}", spec.startup)
        .replace("{{STOP_COMMAND}}", spec.stop)
        .replace("{{STARTUP_DONE}}", spec.startup_done)
        .replace("{{SECURITY_NOTES}}", sec_notes)
        .replace("{{BACKUP_NOTES}}", backup_notes)
    )


def render_egg(spec: EggSpec, registry_mode: str = "default", dry_run: bool = False) -> Path:
    egg_dir = REPO_ROOT / "eggs" / spec.category / spec.id
    egg_json = build_ptdl_v2_json(spec, registry_mode=registry_mode)
    egg_v1_json = build_ptdl_v1_json(spec, registry_mode=registry_mode)
    meta_json = build_metadata_json(spec, registry_mode=registry_mode)
    test_json = build_test_config(spec)
    readme_md = build_readme_vi(spec, registry_mode=registry_mode)
    install_sh = egg_json["scripts"]["installation"]["script"]
    image_ref = {
        "egg_id": spec.id,
        "supported_schemas": ["PTDL_v1", "PTDL_v2"],
        "image_source": spec.image_source,
        "dockerfile_path": spec.dockerfile_path,
        "docker_images": egg_json["docker_images"],
        "ptdl_v1_images": egg_v1_json["images"],
        "custom_ghcr_targets": spec.custom_docker_images,
        "ghcr_published": False,
        "note": "Custom ghcr.io/luuminhq29/yolks:* images are built and published via .github/workflows/build-images.yml.",
    }

    if dry_run:
        return egg_dir

    egg_dir.mkdir(parents=True, exist_ok=True)
    (egg_dir / "egg.json").write_text(json.dumps(egg_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (egg_dir / "egg-ptdl-v1.json").write_text(json.dumps(egg_v1_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (egg_dir / "metadata.json").write_text(json.dumps(meta_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (egg_dir / "test.config.json").write_text(json.dumps(test_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (egg_dir / "image-ref.json").write_text(json.dumps(image_ref, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (egg_dir / "install.sh").write_text(install_sh.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    (egg_dir / "README.md").write_text(readme_md, encoding="utf-8", newline="\n")

    if spec.extra_entrypoint:
        (egg_dir / "entrypoint.sh").write_text(spec.extra_entrypoint.replace("\r\n", "\n"), encoding="utf-8", newline="\n")

    if spec.example_files:
        ex_dir = egg_dir / "example"
        ex_dir.mkdir(parents=True, exist_ok=True)
        for rel_file, content in spec.example_files.items():
            target = ex_dir / rel_file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")

    return egg_dir


def build_catalog_and_compatibility(specs: list[EggSpec], registry_mode: str = "default", dry_run: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    categories_count: dict[str, int] = {}
    catalog_entries: list[dict[str, Any]] = []
    compat_entries: list[dict[str, Any]] = []

    for spec in sorted(specs, key=lambda s: (s.category, s.id)):
        categories_count[spec.category] = categories_count.get(spec.category, 0) + 1
        images = _select_images(spec, registry_mode)
        rel_egg = f"eggs/{spec.category}/{spec.id}/egg.json"
        rel_egg_v1 = f"eggs/{spec.category}/{spec.id}/egg-ptdl-v1.json"
        rel_doc = f"eggs/{spec.category}/{spec.id}/README.md"

        catalog_entries.append(
            {
                "id": spec.id,
                "name": spec.name,
                "description": spec.description,
                "category": spec.category,
                "icon": spec.icon,
                "version": spec.version,
                "supported_versions": spec.supported_versions,
                "supported_architectures": spec.supported_architectures,
                "minimum_ram_mb": spec.minimum_ram_mb,
                "recommended_ram_mb": spec.recommended_ram_mb,
                "minimum_disk_mb": spec.minimum_disk_mb,
                "resource_basis": spec.resource_basis,
                "docker_images": images,
                "image_source": spec.image_source,
                "supported_schemas": ["PTDL_v1", "PTDL_v2"],
                "egg_download": rel_egg,
                "egg_download_v1": rel_egg_v1,
                "documentation_url": rel_doc,
                "supported_panel_versions": DEFAULT_PANEL_VERSIONS,
                "supported_wings_versions": DEFAULT_WINGS_VERSIONS,
                "status": spec.status,
                "verification_status": "UNVERIFIED",
                "last_updated": LAST_UPDATED_DEFAULT,
            }
        )

        compat_entries.append(
            {
                "id": spec.id,
                "name": spec.name,
                "category": spec.category,
                "amd64": "amd64" in spec.supported_architectures,
                "arm64": "arm64" in spec.supported_architectures,
                "panel_1x_ptdl_v1": True,
                "panel_1x_ptdl_v2": True,
                "wings_unprivileged": not spec.privileged_requirements.get("requires_privileged", False),
                "requires_inbound_port": spec.requires_inbound_port,
                "requires_docker_socket": spec.privileged_requirements.get("requires_docker_socket", False),
                "requires_gpu": spec.privileged_requirements.get("requires_gpu", False),
                "eula_required": spec.eula_required,
                "steam_app_id": spec.steam_app_id,
                "image_source": spec.image_source,
                "status": spec.status,
                "verification_status": "UNVERIFIED",
                "notes": spec.notes,
            }
        )

    catalog = {
        "schema_version": "1.0.0",
        "provider": PROVIDER_NAME,
        "website": PROVIDER_WEBSITE,
        "generated_at": EXPORTED_AT_DEFAULT,
        "total_eggs": len(catalog_entries),
        "categories": categories_count,
        "eggs": catalog_entries,
    }

    compatibility = {
        "schema_version": "1.0.0",
        "provider": PROVIDER_NAME,
        "generated_at": EXPORTED_AT_DEFAULT,
        "summary": {
            "total": len(compat_entries),
            "amd64_supported": sum(1 for e in compat_entries if e["amd64"]),
            "arm64_supported": sum(1 for e in compat_entries if e["arm64"]),
            "amd64_only": sum(1 for e in compat_entries if e["amd64"] and not e["arm64"]),
            "unprivileged_compatible": sum(1 for e in compat_entries if e["wings_unprivileged"]),
        },
        "matrix": compat_entries,
    }

    if not dry_run:
        (REPO_ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (REPO_ROOT / "compatibility.json").write_text(json.dumps(compatibility, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        # Generate Static Catalog API endpoints for Vietnam Hosting Admin Dashboard integration
        api_dir = REPO_ROOT / "docs" / "catalog-api"
        api_dir.mkdir(parents=True, exist_ok=True)
        (api_dir / "index.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        by_cat_dir = api_dir / "categories"
        by_cat_dir.mkdir(parents=True, exist_ok=True)
        for cat in categories_count:
            cat_eggs = [e for e in catalog_entries if e["category"] == cat]
            (by_cat_dir / f"{cat}.json").write_text(
                json.dumps({"category": cat, "count": len(cat_eggs), "eggs": cat_eggs}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        by_arch_dir = api_dir / "architectures"
        by_arch_dir.mkdir(parents=True, exist_ok=True)
        for arch in ("amd64", "arm64"):
            arch_eggs = [e for e in catalog_entries if arch in e["supported_architectures"]]
            (by_arch_dir / f"{arch}.json").write_text(
                json.dumps({"architecture": arch, "count": len(arch_eggs), "eggs": arch_eggs}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    return catalog, compatibility
