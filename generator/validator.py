"""Strict PTDL_v2 Egg, Metadata, Script, and Dockerfile Validator."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from generator.models import (
    PTERODACTYL_BUILTIN_VARS,
    REPO_ROOT,
    VALID_ARCHITECTURES,
    VALID_CATEGORIES,
    VALID_PTDL_FEATURES,
)

# Forbidden patterns in scripts and startup commands (no eval on untrusted input, no weak default creds).
FORBIDDEN_EVAL_RE = re.compile(r"(^|[;&|\s])eval\s+", re.MULTILINE)
UNPINNED_LATEST_RE = re.compile(r"^FROM\s+[^\s]+:latest(\s|$)", re.IGNORECASE | re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_.-]+)\}\}")
WEAK_PASSWORD_RE = re.compile(
    r"(?i)(default_value[\"']?\s*[:=]\s*[\"'](admin|password|123456|root|changeme|qwerty)[\"'])"
)


@dataclass
class ValidationIssue:
    severity: str  # "ERROR" | "WARN"
    target: str
    code: str
    message: str


@dataclass
class ValidationReport:
    checked_eggs: int = 0
    checked_dockerfiles: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARN"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _validate_against_schema_builtin(
    instance: Any, schema: dict[str, Any], path: str = "$"
) -> list[str]:
    """Zero-dependency JSON Schema validator covering Draft 2020-12 subset used in schemas/."""
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None:
        allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
        type_ok = False
        for t in allowed_types:
            if t == "null" and instance is None:
                type_ok = True
            elif t == "boolean" and isinstance(instance, bool):
                type_ok = True
            elif t == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
                type_ok = True
            elif t == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool):
                type_ok = True
            elif t == "string" and isinstance(instance, str):
                type_ok = True
            elif t == "array" and isinstance(instance, list):
                type_ok = True
            elif t == "object" and isinstance(instance, dict):
                type_ok = True
        if not type_ok:
            errors.append(f"{path}: expected type {expected_type}, got {type(instance).__name__}")
            return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string length {len(instance)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: string length {len(instance)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: string {instance!r} does not match pattern {schema['pattern']!r}")

    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value {instance} < minimum {schema['minimum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: list length {len(instance)} < minItems {schema['minItems']}")
        if schema.get("uniqueItems") and len(instance) != len(set(json.dumps(x, sort_keys=True) for x in instance)):
            errors.append(f"{path}: list contains duplicate items")
        if "items" in schema:
            for idx, item in enumerate(instance):
                errors.extend(_validate_against_schema_builtin(item, schema["items"], f"{path}[{idx}]"))

    if isinstance(instance, dict):
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            errors.append(f"{path}: object has {len(instance)} properties < minProperties {schema['minProperties']}")
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required key {req!r}")
        props = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)
        for k, v in instance.items():
            if k in props:
                errors.extend(_validate_against_schema_builtin(v, props[k], f"{path}.{k}"))
            elif addl is False:
                errors.append(f"{path}: unexpected additional property {k!r}")
            elif isinstance(addl, dict):
                errors.extend(_validate_against_schema_builtin(v, addl, f"{path}.{k}"))

    return errors


def load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = REPO_ROOT / "schemas" / schema_name
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_egg_directory(
    egg_dir: Path,
    ptdl_v1_schema: dict[str, Any],
    ptdl_schema: dict[str, Any],
    meta_schema: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rel = str(egg_dir.relative_to(REPO_ROOT)).replace("\\", "/")

    egg_file = egg_dir / "egg.json"
    egg_v1_file = egg_dir / "egg-ptdl-v1.json"
    meta_file = egg_dir / "metadata.json"
    install_file = egg_dir / "install.sh"
    readme_file = egg_dir / "README.md"
    test_file = egg_dir / "test.config.json"

    for required_file in (egg_file, egg_v1_file, meta_file, install_file, readme_file, test_file):
        if not required_file.exists():
            issues.append(ValidationIssue("ERROR", rel, "MISSING_FILE", f"Missing required file: {required_file.name}"))

    if not egg_file.exists():
        return issues

    try:
        egg_data = json.loads(egg_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(ValidationIssue("ERROR", rel, "INVALID_JSON", f"egg.json parse error: {exc}"))
        return issues

    # 1. Strict PTDL_v2 Schema Check
    for err in _validate_against_schema_builtin(egg_data, ptdl_schema):
        issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "PTDL_V2_SCHEMA", err))

    # 1b. Strict PTDL_v1 Schema Check & Semantic Sync with PTDL_v2
    if egg_v1_file.exists():
        try:
            egg_v1_data = json.loads(egg_v1_file.read_text(encoding="utf-8"))
            for err in _validate_against_schema_builtin(egg_v1_data, ptdl_v1_schema):
                issues.append(ValidationIssue("ERROR", f"{rel}/egg-ptdl-v1.json", "PTDL_V1_SCHEMA", err))
            expected_v1_images = list(dict.fromkeys(egg_data.get("docker_images", {}).values()))
            if egg_v1_data.get("images") != expected_v1_images:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        f"{rel}/egg-ptdl-v1.json",
                        "PTDL_V1_IMAGES_DRIFT",
                        "egg-ptdl-v1.json images[] differ from egg.json docker_images values",
                    )
                )
            for sync_key in ("name", "author", "description", "features", "startup", "config", "scripts"):
                if egg_v1_data.get(sync_key) != egg_data.get(sync_key):
                    issues.append(
                        ValidationIssue(
                            "ERROR",
                            f"{rel}/egg-ptdl-v1.json",
                            "PTDL_V1_DRIFT",
                            f"egg-ptdl-v1.json field '{sync_key}' differs from egg.json (PTDL_v2)",
                        )
                    )
            for img in egg_v1_data.get("images", []):
                if img.endswith(":latest"):
                    issues.append(ValidationIssue("ERROR", f"{rel}/egg-ptdl-v1.json", "UNPINNED_IMAGE_TAG", f"PTDL_v1 image uses unpinned :latest ({img})"))
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue("ERROR", f"{rel}/egg-ptdl-v1.json", "INVALID_JSON", f"egg-ptdl-v1.json parse error: {exc}"))

    # 2. Check stringified JSON fields inside config
    cfg = egg_data.get("config", {})
    for cfg_key in ("files", "startup", "logs"):
        raw_val = cfg.get(cfg_key, "")
        try:
            parsed_cfg = json.loads(raw_val)
            if not isinstance(parsed_cfg, dict):
                issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "CONFIG_NOT_OBJECT", f"config.{cfg_key} must serialize a JSON object"))
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "CONFIG_INVALID_JSON", f"config.{cfg_key} is not valid JSON string: {exc}"))

    # 3. Check duplicate env_variable declarations & collect declared vars
    declared_vars: set[str] = set()
    for var in egg_data.get("variables", []):
        env_name = var.get("env_variable", "")
        if env_name in declared_vars:
            issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "DUPLICATE_ENV_VAR", f"Duplicate env_variable: {env_name}"))
        declared_vars.add(env_name)
        if env_name in PTERODACTYL_BUILTIN_VARS:
            issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "RESERVED_ENV_VAR", f"Overrides Pterodactyl built-in variable: {env_name}"))
        # Weak default password check on password variables
        if "PASS" in env_name and var.get("default_value", "").lower() in {"admin", "password", "123456", "root", "changeme", "secret"}:
            issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "WEAK_DEFAULT_PASSWORD", f"Weak default password in {env_name}"))

    # 4. Check undeclared {{VAR}} placeholders in startup
    startup_cmd = egg_data.get("startup", "")
    if FORBIDDEN_EVAL_RE.search(startup_cmd):
        issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "FORBIDDEN_EVAL", "startup command contains forbidden `eval`"))
    for match in PLACEHOLDER_RE.finditer(startup_cmd):
        token = match.group(1)
        if token not in declared_vars and token not in PTERODACTYL_BUILTIN_VARS:
            issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "UNDECLARED_STARTUP_VAR", f"Undeclared startup variable: {{{{{token}}}}}") )

    # 5. Check config.files placeholders (allow server.*, env.*, declared vars, builtins)
    try:
        cfg_files = json.loads(cfg.get("files", "{}"))
        cfg_files_text = json.dumps(cfg_files)
        for match in PLACEHOLDER_RE.finditer(cfg_files_text):
            token = match.group(1)
            if token.startswith("server."):
                continue
            if token.startswith("env."):
                env_ref = token[4:]
                if env_ref not in declared_vars and env_ref not in PTERODACTYL_BUILTIN_VARS:
                    issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "UNDECLARED_CONFIG_VAR", f"Undeclared config.files env variable: {{{{{token}}}}}") )
            elif token not in declared_vars and token not in PTERODACTYL_BUILTIN_VARS:
                issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "UNDECLARED_CONFIG_VAR", f"Undeclared config.files variable: {{{{{token}}}}}") )
    except json.JSONDecodeError:
        pass

    # 6. Check features validity
    features = egg_data.get("features")
    if isinstance(features, list):
        for f in features:
            if f not in VALID_PTDL_FEATURES:
                issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "INVALID_FEATURE", f"Unknown PTDL_v2 feature: {f}"))

    # 7. Check docker_images tags (no uncontrolled :latest)
    for label, img in egg_data.get("docker_images", {}).items():
        if img.endswith(":latest"):
            issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "UNPINNED_IMAGE_TAG", f"Docker image '{label}' uses unpinned :latest tag ({img})"))

    # 8. Check installation script safety and sync with install.sh
    inst_script = egg_data.get("scripts", {}).get("installation", {}).get("script", "")
    if not inst_script.startswith("#!"):
        issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "MISSING_SHEBANG", "Installation script must start with a shebang"))
    if "/mnt/server" not in inst_script:
        issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "MISSING_MNT_SERVER", "Installation script must target /mnt/server"))
    if FORBIDDEN_EVAL_RE.search(inst_script):
        issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "FORBIDDEN_EVAL", "Installation script contains forbidden `eval`"))
    if re.search(r"curl\s+[^|\n]*\|\s*(ba)?sh", inst_script):
        issues.append(ValidationIssue("ERROR", f"{rel}/egg.json", "UNVERIFIED_PIPE_TO_SH", "Installation script pipes curl output directly into sh/bash"))

    if install_file.exists():
        disk_script = install_file.read_text(encoding="utf-8").replace("\r\n", "\n")
        json_script = inst_script.replace("\r\n", "\n")
        if disk_script.strip() != json_script.strip():
            issues.append(ValidationIssue("ERROR", f"{rel}/install.sh", "INSTALL_SCRIPT_DRIFT", "install.sh differs from scripts.installation.script in egg.json"))

    # 9. Validate metadata.json & cross-check
    if meta_file.exists():
        try:
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
            for err in _validate_against_schema_builtin(meta_data, meta_schema):
                issues.append(ValidationIssue("ERROR", f"{rel}/metadata.json", "META_SCHEMA", err))
            if meta_data.get("docker_images") != egg_data.get("docker_images"):
                issues.append(ValidationIssue("ERROR", f"{rel}/metadata.json", "DOCKER_IMAGE_MISMATCH", "metadata.json docker_images differ from egg.json"))
            if meta_data.get("minimum_ram_mb", 0) > meta_data.get("recommended_ram_mb", 0):
                issues.append(ValidationIssue("ERROR", f"{rel}/metadata.json", "RAM_RANGE_INVALID", "minimum_ram_mb exceeds recommended_ram_mb"))
            for arch in meta_data.get("supported_architectures", []):
                if arch not in VALID_ARCHITECTURES:
                    issues.append(ValidationIssue("ERROR", f"{rel}/metadata.json", "INVALID_ARCH", f"Invalid architecture: {arch}"))
            df_path = meta_data.get("dockerfile_path")
            if df_path:
                resolved_df = REPO_ROOT / df_path
                if not resolved_df.exists():
                    issues.append(ValidationIssue("ERROR", f"{rel}/metadata.json", "MISSING_DOCKERFILE", f"Referenced Dockerfile does not exist: {df_path}"))
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue("ERROR", f"{rel}/metadata.json", "INVALID_JSON", f"metadata.json parse error: {exc}"))

    return issues


def validate_dockerfile(df_path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rel = str(df_path.relative_to(REPO_ROOT)).replace("\\", "/")
    content = df_path.read_text(encoding="utf-8")

    if UNPINNED_LATEST_RE.search(content):
        issues.append(ValidationIssue("ERROR", rel, "DOCKERFILE_LATEST_BASE", "Dockerfile uses unpinned :latest base image"))
    if "WORKDIR /home/container" not in content and "installers/" not in rel:
        issues.append(ValidationIssue("ERROR", rel, "DOCKERFILE_MISSING_WORKDIR", "Runtime Dockerfile must set WORKDIR /home/container"))
    if "USER container" not in content and "installers/" not in rel:
        issues.append(ValidationIssue("ERROR", rel, "DOCKERFILE_ROOT_RUNTIME", "Runtime Dockerfile must switch to unprivileged USER container"))
    if "ENTRYPOINT" not in content and "installers/" not in rel:
        issues.append(ValidationIssue("ERROR", rel, "DOCKERFILE_MISSING_ENTRYPOINT", "Runtime Dockerfile must declare ENTRYPOINT"))
    if FORBIDDEN_EVAL_RE.search(content):
        issues.append(ValidationIssue("ERROR", rel, "DOCKERFILE_EVAL", "Dockerfile contains forbidden eval"))

    return issues


def validate_repository(only_id: str | None = None) -> ValidationReport:
    report = ValidationReport()
    ptdl_v1_schema = load_schema("ptdl_v1.schema.json")
    ptdl_schema = load_schema("ptdl_v2.schema.json")
    meta_schema = load_schema("metadata.schema.json")
    catalog_schema = load_schema("catalog.schema.json")

    eggs_root = REPO_ROOT / "eggs"
    seen_ids: set[str] = set()

    if eggs_root.exists():
        for cat_dir in sorted(eggs_root.iterdir()):
            if not cat_dir.is_dir():
                continue
            if cat_dir.name not in VALID_CATEGORIES:
                report.issues.append(ValidationIssue("WARN", f"eggs/{cat_dir.name}", "UNKNOWN_CATEGORY", f"Unexpected category folder: {cat_dir.name}"))
            for egg_dir in sorted(cat_dir.iterdir()):
                if not egg_dir.is_dir():
                    continue
                if only_id and egg_dir.name != only_id:
                    continue
                if egg_dir.name in seen_ids:
                    report.issues.append(ValidationIssue("ERROR", f"eggs/{cat_dir.name}/{egg_dir.name}", "DUPLICATE_EGG_ID", f"Duplicate egg ID across categories: {egg_dir.name}"))
                seen_ids.add(egg_dir.name)
                report.checked_eggs += 1
                report.issues.extend(validate_egg_directory(egg_dir, ptdl_v1_schema, ptdl_schema, meta_schema))

    # Validate Dockerfiles
    docker_root = REPO_ROOT / "docker"
    if docker_root.exists() and not only_id:
        for df in sorted(docker_root.rglob("Dockerfile")):
            report.checked_dockerfiles += 1
            report.issues.extend(validate_dockerfile(df))

    # Validate core scripts for forbidden eval
    core_root = REPO_ROOT / "core"
    if core_root.exists() and not only_id:
        for sh in sorted(core_root.glob("*.sh")):
            content = sh.read_text(encoding="utf-8")
            if FORBIDDEN_EVAL_RE.search(content):
                report.issues.append(ValidationIssue("ERROR", f"core/{sh.name}", "CORE_FORBIDDEN_EVAL", f"core/{sh.name} contains forbidden eval"))

    # Validate catalog.json if present
    catalog_file = REPO_ROOT / "catalog.json"
    if catalog_file.exists() and not only_id:
        try:
            cat_data = json.loads(catalog_file.read_text(encoding="utf-8"))
            for err in _validate_against_schema_builtin(cat_data, catalog_schema):
                report.issues.append(ValidationIssue("ERROR", "catalog.json", "CATALOG_SCHEMA", err))
        except json.JSONDecodeError as exc:
            report.issues.append(ValidationIssue("ERROR", "catalog.json", "INVALID_JSON", f"catalog.json parse error: {exc}"))

    return report
