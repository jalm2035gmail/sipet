from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_MANIFEST_KEYS = (
    "name",
    "label",
    "summary",
    "version",
    "depends",
    "route",
    "installable",
    "application",
)
TAILWIND_DYNAMIC_PATTERN = re.compile(r"(?:text|bg|border|alert|btn)-\{\{", re.IGNORECASE)
TAILWIND_CDN_PATTERN = re.compile(r"cdn\.tailwindcss\.com", re.IGNORECASE)


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str = ""


@dataclass
class ValidationResult:
    module_path: str
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, code: str, message: str, path: Path | None = None) -> None:
        self.errors.append(Finding("ERROR", code, message, str(path) if path else ""))

    def add_warning(self, code: str, message: str, path: Path | None = None) -> None:
        self.warnings.append(Finding("WARN", code, message, str(path) if path else ""))


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    tree = ast.parse(manifest_path.read_text(encoding="utf-8"), filename=str(manifest_path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "MANIFEST":
                    return ast.literal_eval(node.value)
    raise ValueError("No se encontro la variable MANIFEST")


def _iter_files(module_path: Path, suffixes: tuple[str, ...]) -> list[Path]:
    return [
        path
        for path in module_path.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes and ".venv" not in path.parts
    ]


def _check_manifest(module_path: Path, result: ValidationResult) -> dict[str, Any] | None:
    manifest_path = module_path / "__manifest__.py"
    if not manifest_path.exists():
        result.add_error("manifest.missing", "Falta __manifest__.py", manifest_path)
        return None
    try:
        manifest = _load_manifest(manifest_path)
    except Exception as exc:
        result.add_error("manifest.invalid", f"No se pudo leer MANIFEST: {exc}", manifest_path)
        return None

    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            result.add_error("manifest.required_key", f"Falta la clave requerida '{key}'", manifest_path)

    structure = manifest.get("structure") or {}
    if isinstance(structure, dict):
        for _, rel_paths in structure.items():
            if not isinstance(rel_paths, list):
                continue
            for rel_path in rel_paths:
                current = module_path / str(rel_path)
                if not current.exists():
                    result.add_error("manifest.structure_missing", f"No existe la ruta declarada '{rel_path}'", current)

    assets = manifest.get("assets") or {}
    if isinstance(assets, dict):
        for _, rel_paths in assets.items():
            if not isinstance(rel_paths, list):
                continue
            for rel_path in rel_paths:
                current = module_path / str(rel_path)
                if not current.exists():
                    result.add_error("manifest.asset_missing", f"No existe el asset declarado '{rel_path}'", current)
    return manifest


class _PythonArchitectureVisitor(ast.NodeVisitor):
    def __init__(self, result: ValidationResult, path: Path):
        self.result = result
        self.path = path
        self.imported_names: dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_names[name] = f"{module}.{alias.name}".strip(".")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.imported_names[name] = alias.name
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        dotted = self._call_name(node.func)
        if dotted in {"create_engine", "sqlalchemy.create_engine", "sessionmaker", "sqlalchemy.orm.sessionmaker"}:
            self.result.add_error(
                "db.raw_engine",
                f"Uso prohibido de '{dotted}' en codigo de modulo; debe usar el core de BD.",
                self.path,
            )
        if dotted.endswith("get_session_factory_for_host") or dotted.endswith("get_engine_for_host") or dotted.endswith("get_current_database_info"):
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "":
                self.result.add_error(
                    "db.implicit_admin",
                    "No usar host vacio para acceder a la BD global; use la API admin explicita.",
                    self.path,
                )
        self.generic_visit(node)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return self.imported_names.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            root = self._call_name(node.value)
            return f"{root}.{node.attr}" if root else node.attr
        return ""


def _check_python_sources(module_path: Path, result: ValidationResult) -> None:
    for path in _iter_files(module_path, (".py",)):
        if "tests" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            result.add_error("python.syntax", f"Archivo Python invalido: {exc}", path)
            continue
        _PythonArchitectureVisitor(result, path).visit(tree)


def _check_templates(module_path: Path, result: ValidationResult) -> None:
    for path in _iter_files(module_path, (".html", ".jinja", ".j2")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if TAILWIND_CDN_PATTERN.search(text):
            result.add_error("styles.tailwind_cdn", "No usar Tailwind CDN dentro del modulo.", path)
        if TAILWIND_DYNAMIC_PATTERN.search(text):
            result.add_error("styles.dynamic_tailwind", "No usar clases Tailwind dinamicas en templates.", path)


def _check_static_assets(module_path: Path, manifest: dict[str, Any] | None, result: ValidationResult) -> None:
    static_css = [path for path in _iter_files(module_path, (".css",)) if "static" in path.parts]
    static_js = [path for path in _iter_files(module_path, (".js",)) if "static" in path.parts]
    assets = manifest.get("assets") if isinstance(manifest, dict) else {}
    declared_css = set((assets or {}).get("css") or [])
    declared_js = set((assets or {}).get("js") or [])

    undeclared_css = [path for path in static_css if str(path.relative_to(module_path)).replace("\\", "/") not in declared_css]
    undeclared_js = [path for path in static_js if str(path.relative_to(module_path)).replace("\\", "/") not in declared_js]
    if undeclared_css:
        result.add_warning("assets.css_undeclared", "Hay archivos CSS del modulo no declarados en MANIFEST assets.css.", undeclared_css[0])
    if undeclared_js:
        result.add_warning("assets.js_undeclared", "Hay archivos JS del modulo no declarados en MANIFEST assets.js.", undeclared_js[0])


def _check_tests(module_path: Path, result: ValidationResult) -> None:
    test_files = [path for path in module_path.rglob("test_*.py") if path.is_file()]
    if not test_files:
        result.add_warning("tests.missing", "El modulo no declara tests propios.", module_path)


def validate_module(module_path: Path) -> ValidationResult:
    module_path = module_path.resolve()
    result = ValidationResult(module_path=str(module_path))
    manifest = _check_manifest(module_path, result)
    _check_python_sources(module_path, result)
    _check_templates(module_path, result)
    _check_static_assets(module_path, manifest, result)
    _check_tests(module_path, result)
    return result


def _print_human(result: ValidationResult) -> None:
    print(f"Modulo: {result.module_path}")
    print(f"Estado: {'OK' if result.ok else 'ERROR'}")
    for finding in result.errors + result.warnings:
        location = f" [{finding.path}]" if finding.path else ""
        print(f"{finding.level} {finding.code}: {finding.message}{location}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida reglas de arquitectura para un modulo SIPET.")
    parser.add_argument("module_path", help="Ruta al directorio del modulo")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Imprime salida JSON")
    args = parser.parse_args()

    result = validate_module(Path(args.module_path))
    if args.as_json:
        print(json.dumps(asdict(result), ensure_ascii=True, indent=2))
    else:
        _print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
