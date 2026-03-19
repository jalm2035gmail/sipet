from __future__ import annotations

import configparser
import json
import os
import re
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP_ENV_DEFAULT = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
DOMAIN_CONFIG_DIR = Path(os.environ.get("DOMAIN_CONFIG_DIR") or os.path.join(PROJECT_ROOT, "config", "dominios"))
SIPET_CONFIG_PATH = Path(os.environ.get("SIPET_CONFIG") or os.path.join(PROJECT_ROOT, "sipet.conf"))
_REQUEST_HOST: ContextVar[str] = ContextVar("sipet_request_host", default="")


def _domain_config_files() -> list[Path]:
    if not DOMAIN_CONFIG_DIR.exists():
        return []
    return sorted(DOMAIN_CONFIG_DIR.glob("*.conf")) + sorted(DOMAIN_CONFIG_DIR.glob("*.ini"))


def normalize_host(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        raw = raw.split("://", 1)[1]
    raw = raw.split("/", 1)[0]
    raw = raw.split(",", 1)[0].strip()
    if ":" in raw and raw.count(":") == 1:
        raw = raw.split(":", 1)[0]
    return raw


def normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql://", 1)
    if raw_url.startswith("mysql://"):
        return raw_url.replace("mysql://", "mysql+pymysql://", 1)
    return raw_url


def normalize_database_name(value: str) -> str:
    raw = str(value or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
    return cleaned or "sipet"


def _coerce_bool(value: Any, default: bool = False) -> bool:
    raw = str(value if value is not None else "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on", "si", "sí"}


def resolve_sqlite_path(raw_path: str) -> str:
    candidate = (raw_path or "").strip()
    if not candidate:
        default_name = f"strategic_planning_{APP_ENV_DEFAULT}.db"
        return os.path.join(PROJECT_ROOT, default_name)
    if os.path.isabs(candidate):
        return candidate
    return os.path.abspath(os.path.join(PROJECT_ROOT, candidate))


def coerce_database_target_to_url(target: str) -> str:
    raw = (target or "").strip()
    if not raw:
        raise RuntimeError("Destino de base de datos vacío.")
    if "://" in raw:
        return normalize_database_url(raw)
    sqlite_path = resolve_sqlite_path(raw)
    return f"sqlite:///{sqlite_path}"


def is_writable_directory(path: str) -> bool:
    directory = (path or "").strip()
    if not directory:
        return False
    return os.path.isdir(directory) and os.access(directory, os.W_OK | os.X_OK)


def build_sqlite_fallback_path(original_path: str) -> str:
    fallback_dir = os.path.join("/tmp", "sipet_data")
    try:
        os.makedirs(fallback_dir, exist_ok=True)
    except OSError:
        pass
    return os.path.join(fallback_dir, os.path.basename(original_path))


def prepare_sqlite_directory(sqlite_path: str) -> str:
    normalized_path = os.path.abspath((sqlite_path or "").strip())
    directory = os.path.dirname(normalized_path) or "."
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as exc:
        fallback_path = build_sqlite_fallback_path(normalized_path)
        print(
            f"[db] No se pudo preparar directorio SQLite '{directory}': {exc}. "
            f"Usando fallback '{fallback_path}'."
        )
        return fallback_path

    if not is_writable_directory(directory):
        fallback_path = build_sqlite_fallback_path(normalized_path)
        print(
            f"[db] Directorio SQLite sin permisos de escritura '{directory}'. "
            f"Usando fallback '{fallback_path}'."
        )
        return fallback_path

    return normalized_path


def extract_sqlite_path(db_url: str) -> Optional[str]:
    if not db_url.startswith("sqlite:///"):
        return None
    return db_url.replace("sqlite:///", "", 1).split("?", 1)[0]


def normalize_sqlite_url_for_runtime(db_url: str) -> str:
    sqlite_path = extract_sqlite_path(db_url)
    if not sqlite_path:
        return db_url
    prepared_path = prepare_sqlite_directory(sqlite_path)
    if prepared_path == sqlite_path:
        return db_url
    return f"sqlite:///{prepared_path}"


def _load_conf_options(file_path: Path) -> Optional[configparser.SectionProxy]:
    if not file_path.exists():
        return None
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with file_path.open("r", encoding="utf-8") as fh:
            parser.read_file(fh)
    except OSError as exc:
        print(f"[db] No se pudo leer configuración '{file_path}': {exc}")
        return None
    if not parser.has_section("options"):
        return None
    return parser["options"]


def load_sipet_conf_options() -> Optional[configparser.SectionProxy]:
    return _load_conf_options(SIPET_CONFIG_PATH)


def read_conf_file(file_path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as fh:
            parser.read_file(fh)
    if not parser.has_section("options"):
        parser.add_section("options")
    return parser


def write_conf_file(file_path: Path, parser: configparser.ConfigParser) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as fh:
        parser.write(fh)


def get_sipet_conf_settings() -> Dict[str, Any]:
    options = load_sipet_conf_options()
    data = {
        "path": str(SIPET_CONFIG_PATH),
        "exists": SIPET_CONFIG_PATH.exists(),
        "show_db_path": False,
        "db_host": "",
        "db_port": "5432",
        "db_user": "",
        "db_name": "",
        "db_engine": "",
        "dbfilter": "",
        "domain": "",
        "admin_passwd": "",
        "list_db": False,
        "proxy_mode": False,
        "workers": "",
        "max_cron_threads": "",
        "log_level": "",
    }
    if options is None:
        return data
    data.update(
        {
            "show_db_path": _coerce_bool(options.get("show_db_path"), False),
            "db_host": str(options.get("db_host") or "").strip(),
            "db_port": str(options.get("db_port") or "5432").strip(),
            "db_user": str(options.get("db_user") or "").strip(),
            "db_name": str(options.get("db_name") or "").strip(),
            "db_engine": str(options.get("db_engine") or options.get("db_type") or "").strip().lower(),
            "dbfilter": str(options.get("dbfilter") or "").strip(),
            "domain": str(options.get("domain") or options.get("host") or "").strip(),
            "admin_passwd": str(options.get("admin_passwd") or "").strip(),
            "list_db": _coerce_bool(options.get("list_db"), False),
            "proxy_mode": _coerce_bool(options.get("proxy_mode"), False),
            "workers": str(options.get("workers") or "").strip(),
            "max_cron_threads": str(options.get("max_cron_threads") or "").strip(),
            "log_level": str(options.get("log_level") or "").strip(),
        }
    )
    return data


def has_explicit_database_config() -> bool:
    if SIPET_CONFIG_PATH.exists():
        return True
    if any(
        str(os.environ.get(key) or "").strip()
        for key in (
            "DATAMAIN_URL",
            "MYSQL_URL",
            "POSTGRES_URL",
            "POSTGRESQL_URL",
            "SQLITE_DB_PATH",
            "HOST_DATAMAIN_MAP",
            "HOST_DATAMAIN_MAP_JSON",
        )
    ):
        return True
    return bool(_domain_config_files())


def get_sipet_superadmin_settings() -> Dict[str, str]:
    parser = read_conf_file(SIPET_CONFIG_PATH)
    if not parser.has_section("superadmin"):
        return {
            "username": "",
            "password": "",
            "email": "",
        }
    section = parser["superadmin"]
    return {
        "username": str(section.get("superadmin_user") or section.get("username") or "").strip(),
        "password": str(section.get("superadmin_password") or section.get("password") or ""),
        "email": str(section.get("superadmin_email") or section.get("email") or "").strip(),
    }


def update_sipet_conf_settings(payload: Mapping[str, Any]) -> Dict[str, Any]:
    parser = read_conf_file(SIPET_CONFIG_PATH)
    options = parser["options"]
    for key in ("domain", "db_host", "db_port", "db_user", "db_password", "db_name", "db_engine", "dbfilter", "admin_passwd", "workers", "max_cron_threads", "log_level"):
        if key in payload:
            options[key] = str(payload.get(key) or "").strip()
    for key in ("list_db", "proxy_mode", "show_db_path"):
        if key in payload:
            options[key] = "True" if _coerce_bool(payload.get(key), False) else "False"
    write_conf_file(SIPET_CONFIG_PATH, parser)
    return get_sipet_conf_settings()


def get_show_db_path_enabled() -> bool:
    return bool(get_sipet_conf_settings().get("show_db_path"))


def _format_host_template(value: str, host: str) -> str:
    normalized_host = normalize_host(host)
    short_host = normalized_host.split(".", 1)[0] if normalized_host else ""
    database_host = normalize_database_name(normalized_host)
    return (
        str(value or "")
        .replace("%h", normalized_host)
        .replace("%d", short_host)
        .replace("%H", database_host)
    )


def _build_url_from_options(options: Mapping[str, str], host: str = "") -> Optional[str]:
    raw_url = str(
        options.get("db_url")
        or options.get("database_url")
        or options.get("datamain_url")
        or ""
    ).strip()
    if raw_url:
        return normalize_database_url(_format_host_template(raw_url, host))

    sqlite_path = str(
        options.get("sqlite_db_path")
        or options.get("db_path")
        or ""
    ).strip()
    if sqlite_path:
        return coerce_database_target_to_url(_format_host_template(sqlite_path, host))

    db_host = str(options.get("db_host") or "localhost").strip()
    db_port = str(options.get("db_port") or "5432").strip()
    db_user = str(options.get("db_user") or "").strip()
    db_password = str(options.get("db_password") or "").strip()
    db_engine = str(options.get("db_engine") or options.get("db_type") or "").strip().lower()
    db_name = _resolve_db_name_from_options(options, host)
    if not db_name:
        return None
    auth = ""
    if db_user:
        auth = db_user
        if db_password:
            auth = f"{auth}:{db_password}"
        auth = f"{auth}@"
    if db_engine == "mysql":
        return f"mysql+pymysql://{auth}{db_host}:{db_port}/{db_name}"
    return f"postgresql://{auth}{db_host}:{db_port}/{db_name}"


def _resolve_db_name_from_dbfilter(host: str, dbfilter: str) -> str:
    normalized_host = normalize_host(host)
    if not normalized_host:
        return ""
    pattern = str(dbfilter or "").strip()
    if not pattern:
        return ""
    candidate = pattern
    candidate = candidate.replace("^", "").replace("$", "")
    candidate = candidate.replace("%h", normalized_host)
    candidate = candidate.replace("%d", normalized_host.split(".", 1)[0])
    if re.search(r"[\[\]\(\)\|\+\*\?\\]", candidate):
        return normalize_database_name(normalized_host)
    return normalize_database_name(candidate)


def _resolve_db_name_from_options(options: Mapping[str, str], host: str = "") -> str:
    explicit_name = str(options.get("db_name") or options.get("database") or "").strip()
    if explicit_name:
        return normalize_database_name(_format_host_template(explicit_name, host))
    dbfilter = str(options.get("dbfilter") or "").strip()
    if dbfilter and host:
        return _resolve_db_name_from_dbfilter(host, dbfilter)
    return ""


def resolve_database_url_from_sipet_conf(host: Optional[str] = None) -> Optional[str]:
    options = load_sipet_conf_options()
    if options is None:
        return None
    normalized_host = normalize_host(host) or normalize_host(
        str(options.get("domain") or options.get("host") or options.get("server_name") or "")
    )
    dbfilter = str(options.get("dbfilter") or "").strip()
    if dbfilter and not normalized_host:
        return None
    return _build_url_from_options(options, normalized_host)


def load_host_database_map() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    raw_json = (os.environ.get("HOST_DATAMAIN_MAP_JSON") or "").strip()
    if raw_json:
        try:
            data = json.loads(raw_json)
            if isinstance(data, dict):
                for host, target in data.items():
                    normalized_host = normalize_host(str(host))
                    normalized_target = str(target or "").strip()
                    if normalized_host and normalized_target:
                        mapping[normalized_host] = normalized_target
        except Exception as exc:
            print(f"[db] No se pudo leer HOST_DATAMAIN_MAP_JSON: {exc}")

    raw_pairs = (os.environ.get("HOST_DATAMAIN_MAP") or "").strip()
    if raw_pairs:
        for chunk in raw_pairs.split(","):
            host, separator, target = chunk.partition("=")
            if not separator:
                continue
            normalized_host = normalize_host(host)
            normalized_target = str(target or "").strip()
            if normalized_host and normalized_target:
                mapping[normalized_host] = normalized_target

    for host, target in load_domain_database_map().items():
        mapping[host] = target
    return mapping


def _build_postgresql_url_from_options(options: configparser.SectionProxy) -> str:
    db_name = _resolve_db_name_from_options(options)
    if not db_name:
        raise RuntimeError("Falta 'db_name' en el archivo de dominio.")
    db_host = str(options.get("db_host") or "localhost").strip()
    db_port = str(options.get("db_port") or "5432").strip()
    db_user = str(options.get("db_user") or "").strip()
    db_password = str(options.get("db_password") or "").strip()
    auth = ""
    if db_user:
        auth = db_user
        if db_password:
            auth = f"{auth}:{db_password}"
        auth = f"{auth}@"
    return f"postgresql://{auth}{db_host}:{db_port}/{db_name}"


def _build_database_url_from_options(options: Mapping[str, str]) -> str:
    db_engine = str(options.get("db_engine") or options.get("db_type") or "").strip().lower()
    if db_engine == "mysql":
        db_name = _resolve_db_name_from_options(options)
        if not db_name:
            raise RuntimeError("Falta 'db_name' en el archivo de dominio.")
        db_host = str(options.get("db_host") or "localhost").strip()
        db_port = str(options.get("db_port") or "3306").strip()
        db_user = str(options.get("db_user") or "").strip()
        db_password = str(options.get("db_password") or "").strip()
        auth = ""
        if db_user:
            auth = db_user
            if db_password:
                auth = f"{auth}:{db_password}"
            auth = f"{auth}@"
        return f"mysql+pymysql://{auth}{db_host}:{db_port}/{db_name}"
    return _build_postgresql_url_from_options(options)


def domain_config_path(domain: str) -> Path:
    normalized = normalize_host(domain)
    slug = normalized or "default"
    return DOMAIN_CONFIG_DIR / f"{slug}.conf"


def _serialize_domain_options(file_path: Path, options: Mapping[str, str]) -> Dict[str, Any]:
    domain = normalize_host(str(options.get("domain") or options.get("host") or file_path.stem))
    db_url = _build_url_from_options(options, domain) or ""
    sqlite_path = extract_sqlite_path(db_url or "")
    db_engine = str(options.get("db_engine") or options.get("db_type") or "").strip().lower()
    if sqlite_path:
        engine_name = "sqlite"
    elif db_engine == "mysql" or db_url.startswith("mysql+pymysql://"):
        engine_name = "mysql"
    else:
        engine_name = "postgresql"
    return {
        "domain": domain,
        "file_path": str(file_path),
        "db_host": str(options.get("db_host") or "").strip(),
        "db_port": str(options.get("db_port") or "5432").strip(),
        "db_user": str(options.get("db_user") or "").strip(),
        "db_password": str(options.get("db_password") or "").strip(),
        "db_name": str(options.get("db_name") or "").strip(),
        "db_engine": engine_name,
        "dbfilter": str(options.get("dbfilter") or "").strip(),
        "db_url": db_url,
        "sqlite_path": sqlite_path or "",
        "show_path": get_show_db_path_enabled(),
        "enabled": _coerce_bool(options.get("enabled"), True),
    }


def list_domain_conf_entries() -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for file_path in _domain_config_files():
        options = _load_conf_options(file_path)
        if options is None:
            continue
        entries.append(_serialize_domain_options(file_path, options))
    if entries:
        return entries

    raw_url = (
        os.environ.get("DATAMAIN_URL")
        or os.environ.get("MYSQL_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRESQL_URL")
        or ""
    ).strip()
    sqlite_path = (os.environ.get("SQLITE_DB_PATH") or "").strip()
    if not raw_url and not sqlite_path:
        return entries

    db_url = normalize_database_url(raw_url) if raw_url else coerce_database_target_to_url(sqlite_path)
    parsed = make_url(db_url)
    host = normalize_host(
        os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        or os.environ.get("PUBLIC_DOMAIN")
        or os.environ.get("APP_DOMAIN")
        or get_sipet_conf_settings().get("domain")
        or "default"
    )
    engine_name = "sqlite" if db_url.startswith("sqlite:///") else ("mysql" if parsed.drivername.startswith("mysql") else "postgresql")
    entries.append(
        {
            "domain": host or "default",
            "file_path": "",
            "db_host": "" if engine_name == "sqlite" else str(parsed.host or "").strip(),
            "db_port": "" if engine_name == "sqlite" else str(parsed.port or ""),
            "db_user": "" if engine_name == "sqlite" else str(parsed.username or "").strip(),
            "db_password": "",
            "db_name": "" if engine_name == "sqlite" else str(parsed.database or "").strip(),
            "db_engine": engine_name,
            "dbfilter": "",
            "db_url": db_url,
            "sqlite_path": extract_sqlite_path(db_url) or "",
            "show_path": get_show_db_path_enabled(),
            "enabled": True,
            "is_runtime_entry": True,
        }
    )
    return entries


def save_domain_conf_entry(payload: Mapping[str, Any]) -> Dict[str, Any]:
    domain = normalize_host(str(payload.get("domain") or payload.get("host") or ""))
    if not domain:
        raise ValueError("domain es obligatorio")
    file_path = domain_config_path(domain)
    parser = read_conf_file(file_path)
    options = parser["options"]
    options["domain"] = domain
    for key in ("db_host", "db_port", "db_user", "db_password", "db_name", "db_engine", "db_type", "dbfilter", "db_url", "database_url", "datamain_url", "sqlite_db_path", "db_path"):
        if key in payload:
            value = str(payload.get(key) or "").strip()
            if value:
                options[key] = value
            elif key in options:
                options.pop(key, None)
    options["enabled"] = "True" if _coerce_bool(payload.get("enabled"), True) else "False"
    write_conf_file(file_path, parser)
    return _serialize_domain_options(file_path, options)


def delete_domain_conf_entry(domain: str) -> bool:
    file_path = domain_config_path(domain)
    if not file_path.exists():
        return False
    file_path.unlink()
    return True


def export_domain_conf_text(domain: str) -> str:
    file_path = domain_config_path(domain)
    if not file_path.exists():
        raise FileNotFoundError(domain)
    return file_path.read_text(encoding="utf-8")


def import_domain_conf_text(filename: str, content: str) -> Dict[str, Any]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(content)
    if not parser.has_section("options"):
        raise ValueError("Archivo sin sección [options]")
    options = parser["options"]
    domain = normalize_host(str(options.get("domain") or options.get("host") or Path(filename).stem))
    if not domain:
        raise ValueError("No se pudo resolver el dominio")
    file_path = domain_config_path(domain)
    write_conf_file(file_path, parser)
    return _serialize_domain_options(file_path, options)


def can_connect_database_url(db_url: str) -> tuple[bool, str]:
    normalized_url = normalize_sqlite_url_for_runtime(str(db_url or "").strip())
    if not normalized_url:
        return False, "URL de base de datos vacía"
    try:
        connect_args = {"check_same_thread": False} if normalized_url.startswith("sqlite:///") else {}
        probe_engine = create_engine(normalized_url, connect_args=connect_args, echo=False)
        try:
            with probe_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True, ""
        finally:
            probe_engine.dispose()
    except Exception as exc:
        return False, str(exc)


def can_connect_current_database(host: Optional[str] = None) -> tuple[bool, str]:
    target_url = resolve_database_url_from_sipet_conf(host) or ""
    if not target_url:
        return False, "Sin configuración de base de datos"
    return can_connect_database_url(target_url)


def initialize_database_from_sipet_conf(payload: Mapping[str, Any]) -> Dict[str, Any]:
    settings = update_sipet_conf_settings(payload)
    db_url = resolve_database_url_from_sipet_conf(settings.get("domain") or "") or resolve_database_url_from_sipet_conf()
    if not db_url:
        raise RuntimeError("No se pudo resolver la URL de base de datos desde sipet.conf")
    normalized_url = normalize_sqlite_url_for_runtime(db_url)
    sqlite_path = extract_sqlite_path(normalized_url)
    if sqlite_path:
        sqlite_file = Path(sqlite_path)
        sqlite_file.parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False}
        probe_engine = create_engine(normalized_url, connect_args=connect_args, echo=False)
        try:
            with probe_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        finally:
            probe_engine.dispose()
        ok, error = can_connect_database_url(normalized_url)
        return {"db_url": normalized_url, "sqlite_path": str(sqlite_file), "connected": ok, "error": error}

    parsed = make_url(normalized_url)
    database_name = str(parsed.database or "").strip()
    if not database_name:
        raise RuntimeError("No se pudo resolver el nombre de la base de datos")
    if parsed.drivername.startswith("mysql"):
        maintenance_name = str(payload.get("maintenance_db") or "mysql").strip() or "mysql"
        admin_url = parsed.set(database=maintenance_name)
        admin_engine = create_engine(str(admin_url), isolation_level="AUTOCOMMIT", echo=False)
        try:
            with admin_engine.connect() as connection:
                exists = connection.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :database_name"),
                    {"database_name": database_name},
                ).scalar()
                if not exists:
                    safe_name = database_name.replace("`", "``")
                    connection.execute(text(f"CREATE DATABASE `{safe_name}`"))
        finally:
            admin_engine.dispose()
    else:
        maintenance_name = str(payload.get("maintenance_db") or "postgres").strip() or "postgres"
        admin_url = parsed.set(database=maintenance_name)
        admin_engine = create_engine(str(admin_url), isolation_level="AUTOCOMMIT", echo=False)
        try:
            with admin_engine.connect() as connection:
                exists = connection.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                    {"database_name": database_name},
                ).scalar()
                if not exists:
                    safe_name = database_name.replace('"', '""')
                    connection.execute(text(f'CREATE DATABASE "{safe_name}"'))
        finally:
            admin_engine.dispose()
    ok, error = can_connect_database_url(normalized_url)
    return {"db_url": normalized_url, "sqlite_path": "", "connected": ok, "error": error}


def _coerce_domain_conf_to_target(file_path: Path) -> tuple[str, str] | None:
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with file_path.open("r", encoding="utf-8") as fh:
            parser.read_file(fh)
    except OSError as exc:
        print(f"[db] No se pudo leer configuración de dominio '{file_path}': {exc}")
        return None

    if not parser.has_section("options"):
        return None
    options = parser["options"]
    enabled = str(options.get("enabled") or "true").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        return None

    host = normalize_host(
        str(
            options.get("domain")
            or options.get("host")
            or options.get("server_name")
            or file_path.stem
        )
    )
    if not host:
        return None

    raw_url = str(
        options.get("db_url")
        or options.get("database_url")
        or options.get("datamain_url")
        or ""
    ).strip()
    if raw_url:
        return host, normalize_database_url(raw_url)

    sqlite_path = str(
        options.get("sqlite_db_path")
        or options.get("db_path")
        or ""
    ).strip()
    if sqlite_path:
        return host, coerce_database_target_to_url(sqlite_path)

    try:
        return host, _build_database_url_from_options(options)
    except Exception as exc:
        print(f"[db] Configuración de dominio inválida '{file_path}': {exc}")
        return None


def load_domain_database_map() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not DOMAIN_CONFIG_DIR.exists():
        return mapping
    for file_path in sorted(DOMAIN_CONFIG_DIR.glob("*.conf")) + sorted(DOMAIN_CONFIG_DIR.glob("*.ini")):
        entry = _coerce_domain_conf_to_target(file_path)
        if entry is None:
            continue
        host, target = entry
        mapping[host] = target
        if host.startswith("www."):
            mapping[host[4:]] = target
        else:
            mapping[f"www.{host}"] = target
    return mapping


def resolve_default_database_url() -> str:
    conf_url = resolve_database_url_from_sipet_conf()
    if conf_url:
        return conf_url

    raw_url = (
        os.environ.get("DATAMAIN_URL")
        or os.environ.get("MYSQL_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRESQL_URL")
        or ""
    ).strip()
    if raw_url:
        return normalize_database_url(raw_url)

    sqlite_db_path = (os.environ.get("SQLITE_DB_PATH") or "").strip()
    if sqlite_db_path:
        return coerce_database_target_to_url(sqlite_db_path)

    is_railway = any(str(value or "").strip() for key, value in os.environ.items() if key.startswith("RAILWAY_"))
    is_prod_like = APP_ENV_DEFAULT in {"production", "prod"} or is_railway
    default_name = f"strategic_planning_{APP_ENV_DEFAULT}.db"
    if is_prod_like:
        fallback_path = os.path.join("/tmp", default_name)
        print(
            "[db] DATAMAIN_URL no configurada en producción/Railway; "
            f"usando fallback SQLite temporal en {fallback_path}."
        )
        return f"sqlite:///{fallback_path}"

    return f"sqlite:///{os.path.join(PROJECT_ROOT, default_name)}"


@dataclass(frozen=True)
class DatabaseTarget:
    host: str
    db_url: str
    engine_name: str
    path: str
    name: str


class DatabaseRouter:
    def __init__(self) -> None:
        self._engine_cache: Dict[str, Engine] = {}
        self._session_factory_cache: Dict[str, sessionmaker] = {}
        self._host_database_map = load_host_database_map()
        self.default_database_url = resolve_default_database_url()

    def refresh_host_map(self) -> None:
        self._host_database_map = load_host_database_map()

    def refresh(self) -> None:
        for engine_instance in self._engine_cache.values():
            try:
                engine_instance.dispose()
            except Exception:
                pass
        self._engine_cache.clear()
        self._session_factory_cache.clear()
        self.refresh_host_map()
        self.default_database_url = resolve_default_database_url()

    def set_request_host(self, host: Optional[str]):
        return _REQUEST_HOST.set(normalize_host(host))

    def reset_request_host(self, token) -> None:
        _REQUEST_HOST.reset(token)

    def get_request_host(self) -> str:
        return _REQUEST_HOST.get("")

    def get_database_url_for_host(self, host: Optional[str] = None) -> str:
        normalized_host = normalize_host(host) or self.get_request_host()
        conf_url = resolve_database_url_from_sipet_conf(normalized_host)
        if conf_url:
            return conf_url
        if normalized_host and normalized_host in self._host_database_map:
            return coerce_database_target_to_url(self._host_database_map[normalized_host])
        return self.default_database_url

    def get_database_target(self, host: Optional[str] = None) -> DatabaseTarget:
        db_url = normalize_sqlite_url_for_runtime(self.get_database_url_for_host(host))
        sqlite_path = extract_sqlite_path(db_url)
        engine_name = "sqlite" if sqlite_path else ("mysql" if db_url.startswith("mysql+pymysql://") else "postgresql")
        return DatabaseTarget(
            host=normalize_host(host) or self.get_request_host() or "",
            db_url=db_url,
            engine_name=engine_name,
            path=sqlite_path or "",
            name=os.path.basename(sqlite_path) if sqlite_path else engine_name,
        )

    def get_engine(self, host: Optional[str] = None) -> Engine:
        target = self.get_database_target(host)
        engine_instance = self._engine_cache.get(target.db_url)
        if engine_instance is not None:
            return engine_instance
        connect_args = {"check_same_thread": False} if target.db_url.startswith("sqlite:///") else {}
        engine_instance = create_engine(target.db_url, connect_args=connect_args, echo=False)
        self._engine_cache[target.db_url] = engine_instance
        return engine_instance

    def get_session_factory(self, host: Optional[str] = None) -> sessionmaker:
        target = self.get_database_target(host)
        session_factory = self._session_factory_cache.get(target.db_url)
        if session_factory is not None:
            return session_factory
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.get_engine(host),
        )
        self._session_factory_cache[target.db_url] = session_factory
        return session_factory

    def dispose_engine(self, host: Optional[str] = None) -> None:
        target = self.get_database_target(host)
        engine_instance = self._engine_cache.pop(target.db_url, None)
        self._session_factory_cache.pop(target.db_url, None)
        if engine_instance is not None:
            engine_instance.dispose()


DEFAULT_DATABASE_ROUTER = DatabaseRouter()
