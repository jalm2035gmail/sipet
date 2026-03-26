from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import HTTPException, UploadFile
from fastapi_modulo.core.module_registry import MODULES_BY_KEY
from scripts.validate_module_architecture import validate_module

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
IMPORTABLE_MODULES_ROOT = os.path.realpath(os.path.join(PROJECT_ROOT, "fastapi_modulo", "modulos"))
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_FILE_COUNT = 500
MAX_TOTAL_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_SINGLE_MEMBER_BYTES = 20 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
ZIP_CONTENT_TYPES = {
    "application/octet-stream",
    "application/x-zip",
    "application/x-zip-compressed",
    "application/zip",
    "multipart/x-zip",
}
DISALLOWED_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".msi",
    ".ps1",
    ".scr",
    ".sh",
    ".so",
}


def _resolve_module_root_from_manifest(module_key: str) -> str | None:
    definition = MODULES_BY_KEY.get(str(module_key or "").strip())
    if definition is None:
        return None
    manifest_file = str(definition.manifest_file or "").strip()
    if manifest_file:
        manifest_path = os.path.abspath(os.path.join(PROJECT_ROOT, manifest_file))
        module_root = os.path.dirname(manifest_path)
        if os.path.isdir(module_root):
            return module_root
    return None


def _is_importable_module_root(target_root: str | None) -> bool:
    normalized_root = os.path.realpath(str(target_root or "").strip())
    if not normalized_root or not os.path.isdir(normalized_root):
        return False
    try:
        return os.path.commonpath([IMPORTABLE_MODULES_ROOT, normalized_root]) == IMPORTABLE_MODULES_ROOT
    except ValueError:
        return False


def _resolve_module_root_from_router(module_key: str) -> str | None:
    definition = MODULES_BY_KEY.get(str(module_key or "").strip())
    if definition is None:
        return None
    for spec in definition.router_specs:
        module_path = str(spec.module_path or "").strip()
        if not module_path:
            continue
        parts = module_path.split(".")
        if "modulos" in parts:
            idx = parts.index("modulos")
            if idx + 1 < len(parts):
                candidate = os.path.abspath(
                    os.path.join(PROJECT_ROOT, "fastapi_modulo", "modulos", parts[idx + 1])
                )
                if os.path.isdir(candidate):
                    return candidate
        candidate = os.path.abspath(os.path.join(PROJECT_ROOT, *parts[:-2])) if len(parts) >= 2 else ""
        if candidate and os.path.isdir(candidate):
            return candidate
    return None


def _resolve_module_root_from_key(module_key: str) -> str | None:
    normalized_key = str(module_key or "").strip()
    if not normalized_key:
        return None
    candidate = os.path.abspath(os.path.join(PROJECT_ROOT, "fastapi_modulo", "modulos", normalized_key))
    if os.path.isdir(candidate):
        return candidate
    return None


def get_module_upload_root(module_key: str) -> str | None:
    target_root = (
        _resolve_module_root_from_manifest(module_key)
        or _resolve_module_root_from_router(module_key)
        or _resolve_module_root_from_key(module_key)
    )
    if not _is_importable_module_root(target_root):
        return None
    return target_root


def get_module_image_path(module_key: str) -> str | None:
    target_root = get_module_upload_root(module_key)
    if not target_root:
        return None
    image_root = Path(target_root) / "imagenes"
    if not image_root.is_dir():
        return None
    preferred_stems = [str(module_key or "").strip().lower()]
    for candidate in image_root.iterdir():
        if candidate.is_file() and candidate.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}:
            if candidate.stem.strip().lower() in preferred_stems:
                return str(candidate)
    for candidate in sorted(image_root.iterdir()):
        if candidate.is_file() and candidate.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}:
            return str(candidate)
    return None


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    return ((info.external_attr >> 16) & 0o170000) == 0o120000


def _iter_zip_members(archive: zipfile.ZipFile, target_root: str, module_key: str = ""):
    target_dir_name = os.path.basename(os.path.normpath(target_root))
    normalized_module_key = str(module_key or "").strip()
    file_infos = [info for info in archive.infolist() if not info.is_dir()]
    file_infos = [info for info in file_infos if not PurePosixPath(info.filename.replace("\\", "/")).name.startswith(".DS_Store")]
    file_infos = [info for info in file_infos if not info.filename.replace("\\", "/").startswith("__MACOSX/")]
    if not file_infos:
        raise HTTPException(status_code=400, detail="El archivo ZIP no contiene archivos validos.")

    normalized_parts: list[tuple[zipfile.ZipInfo, tuple[str, ...]]] = []
    for info in file_infos:
        raw_name = info.filename.replace("\\", "/").lstrip("/")
        path = PurePosixPath(raw_name)
        if raw_name == "" or path.is_absolute() or ".." in path.parts:
            raise HTTPException(status_code=400, detail="El ZIP contiene rutas invalidas.")
        if _is_symlink(info):
            raise HTTPException(status_code=400, detail="El ZIP contiene enlaces simbolicos no permitidos.")
        normalized_parts.append((info, tuple(part for part in path.parts if part not in {"", "."})))

    first_parts = {parts[0] for _, parts in normalized_parts if parts}
    strip_first_segment = len(first_parts) == 1 and next(iter(first_parts)) in {
        target_dir_name,
        normalized_module_key,
        "src",
        "package",
    }

    for info, parts in normalized_parts:
        rel_parts = parts[1:] if strip_first_segment and len(parts) > 1 else parts
        if not rel_parts:
            continue
        destination = os.path.abspath(os.path.join(target_root, *rel_parts))
        if os.path.commonpath([target_root, destination]) != target_root:
            raise HTTPException(status_code=400, detail="El ZIP intenta escribir fuera del modulo.")
        yield info, "/".join(rel_parts), destination


def _archive_member_checksum(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    with archive.open(info, "r") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _file_checksum(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _extract_archive_to_staging(
    archive: zipfile.ZipFile,
    target_root: str,
    *,
    staging_root: str,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    members = list(_iter_zip_members(archive, target_root, module_key))
    if len(members) > MAX_ZIP_FILE_COUNT:
        raise HTTPException(status_code=400, detail="El ZIP contiene demasiados archivos.")

    total_uncompressed_size = 0
    new_files = 0
    changed_files = 0
    unchanged_files = 0
    preview_files: list[dict[str, str | int]] = []
    warnings: list[str] = []

    for info, rel_path, destination in members:
        if info.file_size > MAX_SINGLE_MEMBER_BYTES:
            raise HTTPException(status_code=400, detail=f"El archivo '{rel_path}' excede el tamano maximo permitido.")
        total_uncompressed_size += int(info.file_size)
        if total_uncompressed_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise HTTPException(status_code=400, detail="El ZIP expandido excede el tamano maximo permitido.")
        if info.compress_size > 0 and info.file_size > info.compress_size * MAX_COMPRESSION_RATIO:
            raise HTTPException(status_code=400, detail="El ZIP parece desproporcionado o potencialmente malicioso.")
        if PurePosixPath(rel_path).suffix.lower() in DISALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"El ZIP contiene un archivo no permitido: {rel_path}")

        staged_path = os.path.abspath(os.path.join(staging_root, rel_path))
        os.makedirs(os.path.dirname(staged_path), exist_ok=True)
        with archive.open(info, "r") as source, open(staged_path, "wb") as target:
            shutil.copyfileobj(source, target)

        staged_checksum = _file_checksum(staged_path)
        if not os.path.exists(destination):
            status = "new"
            new_files += 1
        else:
            status = "unchanged" if _file_checksum(destination) == staged_checksum else "changed"
            if status == "changed":
                changed_files += 1
            else:
                unchanged_files += 1
        if len(preview_files) < 25:
            preview_files.append({"path": rel_path, "status": status, "size": int(info.file_size)})
        entries.append(
            {
                "relative_path": rel_path,
                "destination": destination,
                "staged_path": staged_path,
                "file_size": int(info.file_size),
                "status": status,
            }
        )

    if not entries:
        raise HTTPException(status_code=400, detail="El ZIP no contiene archivos para actualizar.")
    if unchanged_files == len(entries):
        warnings.append("Todos los archivos del ZIP ya coinciden con el modulo actual.")

    return {
        "entries": entries,
        "total_files": len(entries),
        "total_uncompressed_size": total_uncompressed_size,
        "new_files": new_files,
        "changed_files": changed_files,
        "unchanged_files": unchanged_files,
        "preview_files": preview_files,
        "warnings": warnings,
    }


def _validate_staged_module_architecture(module_key: str, target_root: str, staging_root: str) -> None:
    validation_root = tempfile.mkdtemp(prefix=f"apps-validate-{str(module_key or '').strip()}-")
    try:
        if os.path.isdir(target_root):
            shutil.copytree(target_root, validation_root, dirs_exist_ok=True)
        if os.path.isdir(staging_root):
            shutil.copytree(staging_root, validation_root, dirs_exist_ok=True)
        result = validate_module(Path(validation_root))
        if result.errors:
            detail_lines = [
                f"{finding.code}: {finding.message}"
                for finding in result.errors
            ]
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "El modulo no cumple las reglas de arquitectura.",
                    "architecture_ok": False,
                    "architecture_errors": [
                        {"code": finding.code, "message": finding.message, "path": finding.path}
                        for finding in result.errors
                    ],
                    "architecture_warnings": [
                        {"code": finding.code, "message": finding.message, "path": finding.path}
                        for finding in result.warnings
                    ],
                    "summary": " | ".join(detail_lines[:8]),
                },
            )
    finally:
        shutil.rmtree(validation_root, ignore_errors=True)


def get_module_architecture_report(module_key: str, module_root: str | None = None) -> dict[str, Any]:
    target_root = module_root or get_module_upload_root(module_key)
    if not target_root or not os.path.isdir(target_root):
        return {
            "architecture_ok": True,
            "architecture_errors": [],
            "architecture_warnings": [],
        }
    result = validate_module(Path(target_root))
    return {
        "architecture_ok": result.ok,
        "architecture_errors": [
            {"code": finding.code, "message": finding.message, "path": finding.path}
            for finding in result.errors
        ],
        "architecture_warnings": [
            {"code": finding.code, "message": finding.message, "path": finding.path}
            for finding in result.warnings
        ],
    }


def inspect_module_zip(module_key: str, zip_path: str) -> dict[str, Any]:
    target_root = get_module_upload_root(module_key)
    if not target_root:
        raise HTTPException(status_code=400, detail="Este modulo todavia no admite actualizacion por ZIP.")
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            if archive.testzip() is not None:
                raise HTTPException(status_code=400, detail="El archivo ZIP esta corrupto.")
            staging_root = tempfile.mkdtemp(prefix=f"apps-stage-{str(module_key or '').strip()}-")
            staged = _extract_archive_to_staging(archive, target_root, staging_root=staging_root)
            _validate_staged_module_architecture(module_key, target_root, staging_root)
            return {
                "module_key": module_key,
                "target_root": target_root,
                "staging_root": staging_root,
                **staged,
                **get_module_architecture_report(module_key, staging_root),
            }
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="El archivo ZIP no es valido.") from exc


def apply_module_zip(_zip_path: str, inspection: dict[str, Any]) -> int:
    extracted_files = 0
    for entry in inspection["entries"]:
        destination = str(entry["destination"])
        staged_path = str(entry["staged_path"])
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(staged_path, destination)
        extracted_files += 1
    if extracted_files == 0:
        raise HTTPException(status_code=400, detail="El ZIP no contiene archivos para actualizar.")
    return extracted_files


def cleanup_staging_dir(staging_root: str) -> None:
    if staging_root and os.path.isdir(staging_root):
        shutil.rmtree(staging_root, ignore_errors=True)


def restore_module_snapshot(module_key: str, snapshot_path: str) -> int:
    target_root = get_module_upload_root(module_key)
    if not target_root:
        raise HTTPException(status_code=400, detail="Este modulo todavia no admite restauracion por backup.")
    if not snapshot_path or not os.path.isfile(snapshot_path):
        raise HTTPException(status_code=404, detail="No existe un snapshot valido para restaurar.")
    staging_root = ""
    try:
        with zipfile.ZipFile(snapshot_path, "r") as archive:
            staging_root = tempfile.mkdtemp(prefix=f"apps-restore-{str(module_key or '').strip()}-")
            staged = _extract_archive_to_staging(archive, target_root, staging_root=staging_root)
        for child in Path(target_root).iterdir():
            if child.name == "__pycache__":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        restored_files = 0
        for entry in staged["entries"]:
            destination = str(entry["destination"])
            staged_path = str(entry["staged_path"])
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(staged_path, destination)
            restored_files += 1
        return restored_files
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="El snapshot de backup no es valido.") from exc
    finally:
        cleanup_staging_dir(staging_root)


async def persist_upload_to_temp(package: UploadFile) -> tuple[str, dict[str, Any]]:
    digest = hashlib.sha256()
    file_size = 0
    first_bytes = b""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
        while True:
            chunk = await package.read(1024 * 1024)
            if not chunk:
                break
            if not first_bytes:
                first_bytes = chunk[:8]
            file_size += len(chunk)
            if file_size > MAX_UPLOAD_BYTES:
                temp_file.close()
                os.unlink(temp_file.name)
                raise HTTPException(status_code=400, detail="El ZIP excede el tamano maximo permitido.")
            digest.update(chunk)
            temp_file.write(chunk)
        return temp_file.name, {
            "checksum": digest.hexdigest(),
            "file_size": file_size,
            "has_zip_signature": first_bytes.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
        }


def validate_upload_metadata(*, filename: str, content_type: str, file_size: int, has_zip_signature: bool) -> None:
    if not str(filename or "").strip().lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Debes subir un archivo .zip.")
    if str(content_type or "").strip().lower() not in ZIP_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="El tipo MIME del archivo no corresponde a un ZIP permitido.")
    if file_size <= 0:
        raise HTTPException(status_code=400, detail="El archivo ZIP esta vacio.")
    if not has_zip_signature:
        raise HTTPException(status_code=400, detail="La firma binaria del archivo no corresponde a un ZIP.")


def validate_zip_file(path: str) -> None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            if archive.testzip() is not None:
                raise HTTPException(status_code=400, detail="El archivo ZIP esta corrupto.")
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="El archivo ZIP no es valido.") from exc


def uninstall_module_files(module_key: str) -> dict[str, Any]:
    target_root = get_module_upload_root(module_key)
    if not target_root or not os.path.isdir(target_root):
        raise HTTPException(status_code=404, detail="No existe un directorio instalado para este módulo.")
    real_target = os.path.realpath(target_root)
    safe_roots = (
        os.path.realpath(os.path.join(PROJECT_ROOT, "fastapi_modulo", "modulos_sipet")),
        os.path.realpath(os.path.join(PROJECT_ROOT, "fastapi_modulo", "modulos")),
    )
    if not any(real_target.startswith(root + os.sep) for root in safe_roots):
        raise HTTPException(status_code=400, detail="La ruta del módulo no es segura para desinstalar.")
    removed_files = 0
    for _root, _dirs, files in os.walk(real_target):
        removed_files += len(files)
    shutil.rmtree(real_target)
    return {
        "module_key": module_key,
        "status": "success",
        "removed_path": target_root,
        "removed_files": removed_files,
    }


__all__ = [
    "apply_module_zip",
    "cleanup_staging_dir",
    "get_module_image_path",
    "get_module_architecture_report",
    "get_module_upload_root",
    "inspect_module_zip",
    "persist_upload_to_temp",
    "restore_module_snapshot",
    "uninstall_module_files",
    "validate_upload_metadata",
    "validate_zip_file",
]
