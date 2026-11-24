"""Dynamic spec loader supporting built-in Python modules and custom JSON runtime specs."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Iterable

from generator.models import REPO_ROOT, EggSpec

BUILTIN_SPEC_MODULES = (
    "generator.specs.languages",
    "generator.specs.operating_systems",
    "generator.specs.discord_bots",
    "generator.specs.web_hosting",
    "generator.specs.databases",
    "generator.specs.game_servers",
    "generator.specs.applications",
    "generator.specs.utilities",
)


def load_all_specs(category: str | None = None, only_id: str | None = None) -> list[EggSpec]:
    specs: list[EggSpec] = []

    for mod_name in BUILTIN_SPEC_MODULES:
        try:
            mod = importlib.import_module(mod_name)
        except ModuleNotFoundError:
            continue
        get_specs = getattr(mod, "get_specs", None)
        if callable(get_specs):
            specs.extend(get_specs())

    # User-extensible custom JSON specs: add new runtimes without editing generator code!
    custom_dir = REPO_ROOT / "generator" / "specs" / "custom"
    if custom_dir.exists():
        for spec_file in sorted(custom_dir.glob("*.json")):
            raw = json.loads(spec_file.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                for item in raw:
                    specs.append(EggSpec.from_dict(item))
            elif isinstance(raw, dict):
                specs.append(EggSpec.from_dict(raw))

    filtered: list[EggSpec] = []
    for s in specs:
        if category and s.category != category:
            continue
        if only_id and s.id != only_id:
            continue
        filtered.append(s)

    return sorted(filtered, key=lambda s: (s.category, s.id))
