from __future__ import annotations

import os
from pathlib import Path
from pprint import pformat
from typing import Any

from fastapi_modulo.module_registry import MODULE_DEFINITIONS, MODULES_BY_KEY, ModuleDefinition

IGNORE_DIRS = {"__pycache__", "static", "templates"}
TECHNICAL_MODULES = {"main", "backend", "web", "modulo_base", "aplicaciones", "sistema"}
PROTOCOL_MODE_REPAIR = "repair_missing_only"
PROTOCOL_MODE_REBUILD = "rebuild_full"


def _resolve_project_root() -> Path:
    configured = (os.environ.get("SIPET_PROJECT_ROOT") or "").strip()
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[4]


PROJECT_ROOT = _resolve_project_root()


def _resolve_modules_dir() -> Path:
    configured = (os.environ.get("SIPET_MODULES_DIR") or os.environ.get("APP_MODULES_DIR") or "").strip()
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    return PROJECT_ROOT / "fastapi_modulo" / "modulos"


MODULOS_DIR = _resolve_modules_dir()


def _module_dir_name_from_spec(module_path: str) -> str | None:
    parts = module_path.split(".")
    if "modulos" not in parts:
        return None
    idx = parts.index("modulos")
    if idx + 1 >= len(parts):
        return None
    return parts[idx + 1]


def _manifest_module_dir(definition: ModuleDefinition) -> Path | None:
    manifest_file = str(definition.manifest_file or "").strip()
    if not manifest_file:
        return None
    manifest_path = (PROJECT_ROOT / manifest_file).resolve()
    if manifest_path.is_file():
        return manifest_path.parent
    return None


def _router_module_dir(definition: ModuleDefinition) -> Path | None:
    for spec in definition.router_specs:
        dir_name = _module_dir_name_from_spec(spec.module_path)
        if not dir_name:
            continue
        candidate = (MODULOS_DIR / dir_name).resolve()
        if candidate.is_dir():
            return candidate
    return None


def iter_module_dirs() -> list[Path]:
    discovered: dict[str, Path] = {}
    if MODULOS_DIR.is_dir():
        for path in sorted(MODULOS_DIR.iterdir()):
            if path.is_dir() and path.name not in IGNORE_DIRS:
                discovered[path.name] = path.resolve()
    for definition in MODULE_DEFINITIONS:
        candidate = _manifest_module_dir(definition) or _router_module_dir(definition)
        if candidate and candidate.name not in IGNORE_DIRS:
            discovered[candidate.name] = candidate
    return sorted(discovered.values(), key=lambda item: item.name)


def _definitions_by_dir() -> dict[str, list[ModuleDefinition]]:
    mapping: dict[str, list[ModuleDefinition]] = {}
    for definition in MODULE_DEFINITIONS:
        matched = False
        for spec in definition.router_specs:
            dir_name = _module_dir_name_from_spec(spec.module_path)
            if not dir_name:
                continue
            mapping.setdefault(dir_name, []).append(definition)
            matched = True
        if matched:
            continue
        manifest_dir = _manifest_module_dir(definition)
        if manifest_dir is not None:
            mapping.setdefault(manifest_dir.name, []).append(definition)
    return mapping


def _module_key_for_dir(module_dir: Path) -> str:
    definitions = _definitions_by_dir().get(module_dir.name, [])
    if definitions:
        return definitions[0].key
    if module_dir.name == "aplicaciones" and "system_admin" in MODULES_BY_KEY:
        return "system_admin"
    return module_dir.name


def _collect_rel_files(module_dir: Path, child: str, patterns: list[str]) -> list[str]:
    target = module_dir / child
    if not target.is_dir():
        return []
    found: list[str] = []
    for pattern in patterns:
        found.extend(
            str(path.relative_to(module_dir)).replace("\\", "/")
            for path in target.glob(pattern)
            if path.is_file()
        )
    return sorted(set(found))


def _collect_assets(module_dir: Path) -> dict[str, list[str]]:
    return {
        "css": _collect_rel_files(module_dir, "static/css", ["*.css"]),
        "js": _collect_rel_files(module_dir, "static/js", ["*.js", "*/*.js", "*/*/*.js"]),
        "description": _collect_rel_files(module_dir, "static/description", ["*.*"]),
        "img": _collect_rel_files(module_dir, "static/img", ["*.*"]),
    }


def _collect_structure(module_dir: Path) -> dict[str, list[str]]:
    structure: dict[str, list[str]] = {}
    mapping = {
        "router": ("controladores", ["*.py"]),
        "models": ("modelos", ["*.py"]),
        "repositories": ("repositorios", ["*.py"]),
        "services": ("servicios", ["*.py"]),
        "security": ("seguridad", ["*.json", "*.py"]),
        "views": ("vistas", ["*.html"]),
        "tests": ("tests", ["*.py"]),
    }
    for key, (child, patterns) in mapping.items():
        files = _collect_rel_files(module_dir, child, patterns)
        if files:
            structure[key] = files
    docs = [name for name in ("README.md", "modulo.json", "manifiesto.json") if (module_dir / name).is_file()]
    if docs:
        structure["docs"] = docs
    return structure


def _detect_depends(module_dir: Path) -> list[str]:
    if module_dir.name == "main":
        return []
    depends = ["main"]
    for path in module_dir.rglob("*.py"):
        if "fastapi_modulo.modulos.web" in path.read_text(encoding="utf-8", errors="ignore"):
            depends.append("web")
            break
    return depends


def build_manifest_payload(module_dir: Path) -> dict[str, Any]:
    definitions = _definitions_by_dir().get(module_dir.name, [])
    primary = definitions[0] if definitions else None
    return {
        "name": module_dir.name,
        "label": primary.label if primary else module_dir.name.replace("_", " ").title(),
        "summary": primary.description if primary else f"Modulo {module_dir.name} del sistema SIPET.",
        "description": primary.description if primary else f"Modulo {module_dir.name} del sistema SIPET.",
        "version": "1.0.0",
        "category": "Base" if module_dir.name in TECHNICAL_MODULES else "Operaciones",
        "author": "SIPET",
        "sequence": "",
        "website": "https://avancoop.org",
        "route": primary.route if primary and primary.route else f"/{module_dir.name.replace('_', '-')}",
        "icon": primary.icon if primary else "",
        "depends": _detect_depends(module_dir),
        "data": sorted(
            _collect_rel_files(module_dir, "vistas", ["*.html"])
            + _collect_rel_files(module_dir, "seguridad", ["*.json"])
        ),
        "assets": _collect_assets(module_dir),
        "structure": _collect_structure(module_dir),
        "installable": True,
        "application": module_dir.name not in TECHNICAL_MODULES,
        "auto_install": False,
    }


def _guess_router_import(module_dir: Path) -> str | None:
    definitions = _definitions_by_dir().get(module_dir.name, [])
    preferred: list[str] = []
    for definition in definitions:
        for spec in definition.router_specs:
            if f".modulos.{module_dir.name}." in spec.module_path:
                preferred.append(spec.module_path)
    if preferred:
        return preferred[0]
    controller_dir = module_dir / "controladores"
    if not controller_dir.is_dir():
        return None
    same_name = controller_dir / f"{module_dir.name}.py"
    if same_name.exists():
        return f"fastapi_modulo.modulos.{module_dir.name}.controladores.{module_dir.name}"
    candidates = sorted(path.stem for path in controller_dir.glob("*.py") if path.name != "__init__.py")
    if len(candidates) == 1:
        return f"fastapi_modulo.modulos.{module_dir.name}.controladores.{candidates[0]}"
    return None


def build_init_source(module_dir: Path) -> str:
    router_import = _guess_router_import(module_dir)
    if not router_import:
        return "__all__ = []\n"
    return f"from {router_import} import router\n\n__all__ = [\"router\"]\n"


def build_manifest_source(module_dir: Path) -> str:
    return f"MANIFEST = {pformat(build_manifest_payload(module_dir), width=100, sort_dicts=False)}\n\n__all__ = [\"MANIFEST\"]\n"


def _load_manifest_payload(module_dir: Path) -> dict[str, Any]:
    manifest_path = module_dir / "__manifest__.py"
    if not manifest_path.is_file():
        return {}
    namespace: dict[str, Any] = {}
    try:
        exec(manifest_path.read_text(encoding="utf-8"), namespace)
    except Exception:
        return {}
    payload = namespace.get("MANIFEST", {})
    return payload if isinstance(payload, dict) else {}


def _assets_declared_exist(module_dir: Path, manifest_payload: dict[str, Any]) -> bool:
    assets = manifest_payload.get("assets", {})
    if not isinstance(assets, dict):
        return True
    for entries in assets.values():
        if not isinstance(entries, list):
            continue
        for item in entries:
            relative_path = str(item or "").strip()
            if relative_path and not (module_dir / relative_path).exists():
                return False
    return True


def _route_valid(manifest_payload: dict[str, Any]) -> bool:
    route = str(manifest_payload.get("route") or "").strip()
    return not route or route.startswith("/")


def _icon_declared(manifest_payload: dict[str, Any], module_dir: Path, definitions: list[ModuleDefinition]) -> bool:
    icon = str(manifest_payload.get("icon") or "").strip()
    if icon:
        return True
    if any(str(definition.icon or "").strip() for definition in definitions):
        return True
    image_root = module_dir / "imagenes"
    return image_root.is_dir() and any(path.is_file() for path in image_root.iterdir())


def _depends_valid(manifest_payload: dict[str, Any]) -> bool:
    depends = manifest_payload.get("depends", [])
    if not isinstance(depends, list):
        return False
    known_module_names = {path.name for path in iter_module_dirs()}
    known_keys = set(MODULES_BY_KEY)
    for item in depends:
        value = str(item or "").strip()
        if not value:
            continue
        if value not in known_module_names and value not in known_keys:
            return False
    return True


def _routers_importable(module_dir: Path, definitions: list[ModuleDefinition]) -> bool:
    def _module_path_exists(module_path: str) -> bool:
        parts = [part for part in str(module_path or "").split(".") if part]
        if not parts:
            return False
        candidate_file = (PROJECT_ROOT / Path(*parts)).with_suffix(".py")
        if candidate_file.is_file():
            return True
        candidate_package = PROJECT_ROOT / Path(*parts) / "__init__.py"
        return candidate_package.is_file()

    if not definitions:
        guessed = _guess_router_import(module_dir)
        if not guessed:
            return False
        return _module_path_exists(guessed)
    for definition in definitions:
        for spec in definition.router_specs:
            if not _module_path_exists(spec.module_path):
                return False
    return True


def _protocol_status_for_module(module_dir: Path, definitions_map: dict[str, list[ModuleDefinition]]) -> dict[str, Any]:
    definitions = definitions_map.get(module_dir.name, [])
    manifest_payload = _load_manifest_payload(module_dir)
    has_init = (module_dir / "__init__.py").is_file()
    has_manifest = (module_dir / "__manifest__.py").is_file()
    has_readme = (module_dir / "README.md").is_file()
    has_controladores_dir = (module_dir / "controladores").is_dir()
    has_tests_dir = (module_dir / "tests").is_dir()
    route_valid = _route_valid(manifest_payload)
    icon_declared = _icon_declared(manifest_payload, module_dir, definitions)
    depends_valid = _depends_valid(manifest_payload)
    routers_importable = _routers_importable(module_dir, definitions)
    assets_declared_exist = _assets_declared_exist(module_dir, manifest_payload)
    missing = []
    if not has_init:
        missing.append("__init__.py")
    if not has_manifest:
        missing.append("__manifest__.py")
    if not has_readme:
        missing.append("README.md")
    if not has_controladores_dir:
        missing.append("controladores/")
    if not has_tests_dir:
        missing.append("tests/")
    issues = []
    if not route_valid:
        issues.append("route")
    if not icon_declared:
        issues.append("icon")
    if not depends_valid:
        issues.append("depends")
    if not routers_importable:
        issues.append("routers")
    if not assets_declared_exist:
        issues.append("assets")
    return {
        "module_key": _module_key_for_dir(module_dir),
        "module_dir": str(module_dir),
        "has_init": has_init,
        "has_manifest": has_manifest,
        "has_readme": has_readme,
        "has_controladores_dir": has_controladores_dir,
        "has_tests_dir": has_tests_dir,
        "route_valid": route_valid,
        "icon_declared": icon_declared,
        "depends_valid": depends_valid,
        "routers_importable": routers_importable,
        "assets_declared_exist": assets_declared_exist,
        "missing": missing,
        "issues": issues,
        "ok": not missing and not issues,
    }


def get_protocol_status_map() -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    definitions_map = _definitions_by_dir()
    for module_dir in iter_module_dirs():
        status[module_dir.name] = _protocol_status_for_module(module_dir, definitions_map)
    return status


def ensure_protocol_files(
    *,
    mode: str = PROTOCOL_MODE_REPAIR,
    overwrite_manifest: bool = False,
    overwrite_init: bool = False,
    module_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    selected_mode = mode if mode in {PROTOCOL_MODE_REPAIR, PROTOCOL_MODE_REBUILD} else PROTOCOL_MODE_REPAIR
    rebuild_full = selected_mode == PROTOCOL_MODE_REBUILD
    rewrite_init = overwrite_init or rebuild_full
    rewrite_manifest = overwrite_manifest or rebuild_full
    target_dirs = iter_module_dirs() if module_dirs is None else list(module_dirs)
    definitions_map = _definitions_by_dir()
    before = (
        get_protocol_status_map()
        if module_dirs is None
        else {module_dir.name: _protocol_status_for_module(module_dir, definitions_map) for module_dir in target_dirs}
    )
    created_init: list[str] = []
    created_manifest: list[str] = []
    updated_init: list[str] = []
    updated_manifest: list[str] = []
    for module_dir in target_dirs:
        init_path = module_dir / "__init__.py"
        manifest_path = module_dir / "__manifest__.py"
        if not init_path.exists():
            init_path.write_text(build_init_source(module_dir), encoding="utf-8")
            created_init.append(module_dir.name)
        elif rewrite_init:
            init_path.write_text(build_init_source(module_dir), encoding="utf-8")
            updated_init.append(module_dir.name)
        if not manifest_path.exists():
            manifest_path.write_text(build_manifest_source(module_dir), encoding="utf-8")
            created_manifest.append(module_dir.name)
        elif rewrite_manifest:
            manifest_path.write_text(build_manifest_source(module_dir), encoding="utf-8")
            updated_manifest.append(module_dir.name)
    return {
        "mode": selected_mode,
        "created_init": created_init,
        "created_manifest": created_manifest,
        "updated_init": updated_init,
        "updated_manifest": updated_manifest,
        "before": before,
        "after": (
            get_protocol_status_map()
            if module_dirs is None
            else {module_dir.name: _protocol_status_for_module(module_dir, definitions_map) for module_dir in target_dirs}
        ),
    }


__all__ = [
    "PROTOCOL_MODE_REBUILD",
    "PROTOCOL_MODE_REPAIR",
    "build_init_source",
    "build_manifest_payload",
    "build_manifest_source",
    "ensure_protocol_files",
    "get_protocol_status_map",
    "iter_module_dirs",
]
