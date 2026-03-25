from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fastapi import FastAPI
from sqlalchemy import bindparam, text

from fastapi_modulo.core.db import (
    TenantInstalledApp,
    ensure_tenant_admin_schema,
    get_admin_engine,
    get_admin_session_factory,
)
from fastapi_modulo.core.tenant_context import get_tenant_context


@dataclass
class RouterSpec:
    module_path: str
    attr_name: str = "router"
    include_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleDefinition:
    key: str
    label: str
    description: str
    route: str = ""
    icon: str = ""
    metadata_file: str = ""
    manifest_file: str = ""
    app_access_name: Optional[str] = None
    sidebar_visible: bool = True
    manageable: bool = True
    always_enabled: bool = False
    default_enabled: bool = True
    boot_strategy: str = "deferred_router"
    registration_phase: str = "startup"
    router_specs: List[RouterSpec] = field(default_factory=list)


LEGACY_MODULES_ENABLED = (os.environ.get("ENABLE_LEGACY_MODULES") or "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
LEGACY_RUNTIME_ALLOWLIST = {
    "multitienda",
    "intelicoop",
}


MODULE_DEFINITIONS: List[ModuleDefinition] = [
    ModuleDefinition(
        key="backend",
        label="Configuración",
        description="Módulo web principal — ajustes de sistema y configuración.",
        route="/ajustes/configuracion",
        icon="fa-solid fa-gear",
        manifest_file="fastapi_modulo/modulos_sipet/web/__manifest__.py",
        sidebar_visible=True,
        manageable=False,
        always_enabled=True,
    ),
    ModuleDefinition(
        key="instalacion_core",
        label="Instalación",
        description="Bootstrap inicial de SIPET para preparar la base y el archivo sipet.conf.",
        route="/instalacion",
        icon="fa-solid fa-screwdriver-wrench",
        manifest_file="fastapi_modulo/modulos_sipet/instalacion/__manifest__.py",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.instalacion.controladores.instalacion")],
    ),
    ModuleDefinition(
        key="modulo_base",
        label="Modulo base",
        description="Núcleo reusable interno para contratos, utilidades y servicios compartidos.",
        route="/modulo-base",
        icon="fa-solid fa-layer-group",
        manifest_file="fastapi_modulo/modulos_sipet/modulo_base/__manifest__.py",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        boot_strategy="builtin",
    ),
    ModuleDefinition(
        key="mi_tablero",
        label="Mi tablero",
        description="Vista personal y accesos rápidos del usuario.",
        route="/mi-tablero",
        icon="fa-solid fa-rectangle-list",
        manifest_file="fastapi_modulo/modulos/mi_tablero/__manifest__.py",
        app_access_name="Mi tablero",
        sidebar_visible=True,
        manageable=True,
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.mi_tablero.controladores.mi_tablero"),
        ],
    ),
    ModuleDefinition(
        key="conversaciones",
        label="Conversaciones",
        description="Notificaciones internas y mensajería.",
        route="/notificaciones",
        icon="fa-regular fa-envelope",
        metadata_file="fastapi_modulo/modulos/notificaciones/modulo.json",
        app_access_name="Conversaciones",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.notificaciones.controladores.notificaciones")],
    ),
    ModuleDefinition(
        key="organizacion",
        label="Organización",
        description="Usuarios, empleados, regiones y departamentos.",
        route="/inicio/departamentos",
        icon="fa-solid fa-sitemap",
        manifest_file="fastapi_modulo/modulos/empleados/__manifest__.py",
        app_access_name="Organización",
        sidebar_visible=True,
        manageable=True,
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.empleados.controladores.empleados"),
            RouterSpec("fastapi_modulo.modulos.empleados.controladores.regiones"),
            RouterSpec("fastapi_modulo.modulos.empleados.controladores.departamentos"),
        ],
    ),
    ModuleDefinition(
        key="estrategia_tactica",
        label="Estrategia y táctica",
        description="Planificación, POA, ciclo anual y tablero estratégico.",
        route="/planes",
        icon="fa-solid fa-chess-board",
        app_access_name="Estrategia y táctica",
        sidebar_visible=True,
        manageable=True,
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.planificacion.controladores.annual_cycle_service"),
            RouterSpec("fastapi_modulo.modulos.planificacion.controladores.plan_estrategico"),
            RouterSpec("fastapi_modulo.modulos.planificacion.controladores.poa"),
            RouterSpec("fastapi_modulo.modulos.planificacion.controladores.kpis"),
            RouterSpec("fastapi_modulo.modulos.planificacion.controladores.notificaciones"),
            RouterSpec("fastapi_modulo.modulos.planificacion.controladores.ejes_poa"),
        ],
    ),
    ModuleDefinition(
        key="datos_financieros",
        label="Datos financieros",
        description="Proyecciones y herramientas financieras.",
        route="/proyectando",
        icon="fa-solid fa-chart-column",
        app_access_name="Datos financieros",
        sidebar_visible=True,
        manageable=True,
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.proyectando.controladores.presupuesto", include_kwargs={"prefix": "/proyectando"}),
            RouterSpec("fastapi_modulo.modulos.proyectando.controladores.tablero"),
            RouterSpec("fastapi_modulo.modulos.proyectando.controladores.datos_preliminares"),
            RouterSpec("fastapi_modulo.modulos.proyectando.controladores.crecimiento_general"),
            RouterSpec("fastapi_modulo.modulos.proyectando.controladores.sucursales"),
            RouterSpec("fastapi_modulo.modulos.proyectando.controladores.no_acceso"),
        ],
    ),
    ModuleDefinition(
        key="cartera_prestamos",
        label="Cartera de préstamos",
        description="Resumen ejecutivo de cartera.",
        route="/resumen_ejecutivo",
        icon="fa-solid fa-hand-holding-dollar",
        manifest_file="fastapi_modulo/modulos/cartera_prestamos/__manifest__.py",
        app_access_name="Cartera de préstamos",
        sidebar_visible=True,
        manageable=True,
        boot_strategy="builtin",
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.cartera_prestamos.controladores.cartera_prestamos"),
        ],
    ),
    ModuleDefinition(
        key="pld",
        label="PLD",
        description="Prevención de lavado de dinero.",
        route="/pld",
        icon="fa-solid fa-shield-halved",
        app_access_name="PLD",
        sidebar_visible=True,
        manageable=True,
        boot_strategy="builtin",
        router_specs=[RouterSpec("fastapi_modulo.modulos.pld.controladores.pld")],
    ),
    ModuleDefinition(
        key="mkt",
        label="MKT",
        description="Marketing y comunicación.",
        route="/mkt/digital",
        icon="fa-solid fa-bullhorn",
        app_access_name="MKT",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.mkt.controladores.mkt")],
    ),
    ModuleDefinition(
        key="intelicoop",
        label="Intelicoop",
        description="Analítica e inteligencia institucional.",
        route="/inicio/intelicoop",
        icon="fa-solid fa-microchip",
        manifest_file="fastapi_modulo/modulos/intelicoop/__manifest__.py",
        app_access_name="Intelicoop",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.intelicoop.controladores.intelicoop")],
    ),
    ModuleDefinition(
        key="brujula",
        label="Brújula",
        description="Seguimiento visual de indicadores y objetivos.",
        route="/brujula",
        icon="fa-regular fa-compass",
        app_access_name="Brújula",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.brujula.controladores.brujula")],
    ),
    ModuleDefinition(
        key="crm",
        label="CRM",
        description="Gestión comercial y de relaciones.",
        route="/crm",
        icon="fa-solid fa-address-card",
        app_access_name="CRM",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.crm.controladores.crm")],
    ),
    ModuleDefinition(
        key="encuestas",
        label="Encuestas",
        description="Campañas, constructor, respuesta y resultados.",
        route="/encuestas",
        icon="fa fa-square-poll-vertical",
        metadata_file="fastapi_modulo/modulos/encuestas/modulo.json",
        app_access_name="Encuestas",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.encuestas.controladores.encuesta")],
    ),
    ModuleDefinition(
        key="auditoria",
        label="Auditoría",
        description="Hallazgos, seguimiento y control de auditoría.",
        route="/auditoria",
        icon="fa-solid fa-clipboard-check",
        app_access_name="Auditoria",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.auditoria.controladores.auditoria")],
    ),
    ModuleDefinition(
        key="activo_fijo",
        label="Gestión de Activo Fijo",
        description="Inventario y control de activos fijos.",
        route="/activo-fijo",
        icon="fa-solid fa-building-columns",
        app_access_name="ActivoFijo",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.activo_fijo.controladores.activo_fijo")],
    ),
    ModuleDefinition(
        key="bsc",
        label="BSC",
        description="Tablero principal institucional.",
        route="/inicio",
        icon="fa-regular fa-circle-dot",
        manifest_file="fastapi_modulo/modulos_sipet/aplicaciones/__manifest__.py",
        app_access_name="BSC",
        sidebar_visible=False,
        manageable=True,
        boot_strategy="builtin",
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.aplicaciones.controladores.pages")],
    ),
    ModuleDefinition(
        key="control_seguimiento",
        label="Control y seguimiento",
        description="Programa, evidencias, hallazgos y reportes.",
        route="/control-seguimiento",
        icon="fa-solid fa-list-check",
        manifest_file="fastapi_modulo/modulos/control_interno/__manifest__.py",
        app_access_name="Control y seguimiento",
        sidebar_visible=True,
        manageable=True,
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.control_interno.controladores.control"),
            RouterSpec("fastapi_modulo.modulos.control_interno.controladores.programa"),
            RouterSpec("fastapi_modulo.modulos.control_interno.controladores.evidencia"),
            RouterSpec("fastapi_modulo.modulos.control_interno.controladores.hallazgos"),
            RouterSpec("fastapi_modulo.modulos.control_interno.controladores.tablero"),
            RouterSpec("fastapi_modulo.modulos.control_interno.controladores.reportes_ci"),
        ],
    ),
    ModuleDefinition(
        key="kpis",
        label="KPIs",
        description="Indicadores clave y analítica resumida.",
        route="/kpis",
        icon="fa-solid fa-chart-line",
        app_access_name="KPIs",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.kpis.controladores.kpis")],
    ),
    ModuleDefinition(
        key="reportes",
        label="Reportes",
        description="Generación y consulta de reportes.",
        route="/reportes",
        icon="fa-regular fa-file-lines",
        app_access_name="Reportes",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.reportes.controladores.reportes")],
    ),
    ModuleDefinition(
        key="referidos",
        label="Referidos",
        description="Programa integral de referidos, incentivos y embajadores de marca.",
        route="/referidos",
        icon="fa-solid fa-users",
        manifest_file="fastapi_modulo/modulos/referidos/__manifest__.py",
        app_access_name="Referidos",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.referidos.controladores.referidos")],
    ),
    ModuleDefinition(
        key="multitienda",
        label="Multitienda",
        description="Marketplace multitienda integrado al runtime de SIPET.",
        route="/multitienda",
        icon="fa-solid fa-store",
        manifest_file="fastapi_modulo/modulos/multitienda/__manifest__.py",
        app_access_name="Multitienda",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.multitienda.controladores.multitienda")],
    ),
    ModuleDefinition(
        key="frontend",
        label="Frontend",
        description="Sitio backend y constructor frontend.",
        route="/web",
        icon="fa-solid fa-globe",
        manifest_file="fastapi_modulo/modulos_sipet/frontend/__manifest__.py",
        app_access_name="Frontend",
        sidebar_visible=True,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.frontend.controladores.frontend")],
    ),
    ModuleDefinition(
        key="empresa",
        label="Empresa",
        description="Configuración institucional y estructura MAIN.",
        route="/identidad-institucional",
        icon="fa-solid fa-building",
        manifest_file="fastapi_modulo/modulos/identidad_institucional/__manifest__.py",
        app_access_name="Empresa",
        sidebar_visible=True,
        manageable=False,
        always_enabled=True,
        boot_strategy="builtin",
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.identidad_institucional.controladores.identidad_institucional"),
        ],
    ),
    ModuleDefinition(
        key="capacitacion",
        label="Capacitación",
        description="Cursos, presentaciones y evaluaciones.",
        route="/capacitacion",
        icon="fa-solid fa-graduation-cap",
        metadata_file="fastapi_modulo/modulos/capacitacion/modulo.json",
        app_access_name="Capacitacion",
        sidebar_visible=True,
        manageable=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.capacitacion.controladores.capacitacion")],
    ),
    ModuleDefinition(
        key="multiempresa",
        label="Multiempresa",
        description="Gestión y aislamiento por empresa.",
        route="/multiempresa",
        icon="fa-solid fa-building-user",
        manifest_file="fastapi_modulo/modulos/multiempresa/__manifest__.py",
        app_access_name="Multiempresa",
        sidebar_visible=True,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.multiempresa.controladores.multiempresa")],
    ),
    ModuleDefinition(
        key="system_admin",
        label="Aplicaciones",
        description="Gestión centralizada de módulos y protocolo.",
        route="/aplicaciones",
        icon="fa-solid fa-cubes",
        manifest_file="fastapi_modulo/modulos_sipet/aplicaciones/__manifest__.py",
        sidebar_visible=True,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.aplicaciones.controladores.aplicaciones")],
    ),
    ModuleDefinition(
        key="personalizacion_core",
        label="Colores",
        description="Personalización de colores e identidad visual institucional.",
        route="/personalizar",
        icon="fa-solid fa-palette",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.personalizacion.controladores.personalizar")],
    ),
    ModuleDefinition(
        key="membresia_core",
        label="Membresía",
        description="Core de membresía.",
        route="/membresia",
        icon="fa-solid fa-id-card",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.aplicaciones.controladores.membresia", attr_name="membresia_router")],
    ),
    ModuleDefinition(
        key="roles_core",
        label="Roles",
        description="Core de roles y permisos.",
        route="/roles-permisos",
        icon="fa-solid fa-user-shield",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.personalizacion.controladores.roles")],
    ),
    ModuleDefinition(
        key="plantillas_core",
        label="Plantillas",
        description="Core de plantillas.",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.plantillas.controladores.plantillas_forms")],
    ),
    ModuleDefinition(
        key="diagnostico_core",
        label="Diagnóstico",
        description="Core de diagnóstico.",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos.diagnostico.controladores.diagnostico")],
    ),
    ModuleDefinition(
        key="ajustes_ia_core",
        label="IA",
        description="Configuración e inteligencia artificial del sistema.",
        route="/ajustes/ia",
        icon="fa-solid fa-robot",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.web.controladores.ajustes_ia")],
    ),
    ModuleDefinition(
        key="predictivo_core",
        label="Análisis predictivo",
        description="Análisis predictivo e inteligencia de datos.",
        route="/ia/predictivo",
        icon="fa-solid fa-chart-mixed",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
    ),
    ModuleDefinition(
        key="ajustes_core",
        label="Ajustes",
        description="Configuración general del sistema.",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[RouterSpec("fastapi_modulo.modulos_sipet.modulo_base.controladores.settings")],
    ),
    ModuleDefinition(
        key="ia_core",
        label="IA",
        description="Router agregado de IA.",
        sidebar_visible=False,
        manageable=False,
        always_enabled=True,
        router_specs=[
            RouterSpec("fastapi_modulo.modulos.ia.controladores.ia_router", attr_name="ia_router"),
            RouterSpec("fastapi_modulo.modulos.ia.controladores.predictivo"),
        ],
    ),
]

MODULES_BY_KEY = {module.key: module for module in MODULE_DEFINITIONS}
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_REPO_ROOT = os.path.abspath(os.path.join(_PROJECT_ROOT, ".."))


def _resolve_registry_path(path_value: str) -> str:
    normalized = str(path_value or "").strip()
    if not normalized:
        return ""
    candidates = [
        os.path.abspath(os.path.join(_PROJECT_ROOT, normalized)),
        os.path.abspath(os.path.join(_REPO_ROOT, normalized)),
    ]
    fastapi_prefix = "fastapi_modulo/"
    if normalized.startswith(fastapi_prefix):
        trimmed = normalized[len(fastapi_prefix) :]
        candidates.append(os.path.abspath(os.path.join(_PROJECT_ROOT, trimmed)))
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]
APP_ACCESS_TO_MODULE = {
    module.app_access_name: module
    for module in MODULE_DEFINITIONS
    if module.app_access_name
}


def _normalize_registry_relpath(path_value: str) -> str:
    normalized = str(path_value or "").strip()
    if not normalized:
        return ""
    resolved = _resolve_registry_path(normalized)
    try:
        return os.path.relpath(resolved, _REPO_ROOT).replace(os.sep, "/")
    except Exception:
        return normalized.replace(os.sep, "/")


def _iter_discoverable_manifest_files() -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    roots = (
        ("fastapi_modulo.modulos", Path(_PROJECT_ROOT) / "modulos"),
        ("fastapi_modulo.modulos_sipet", Path(_PROJECT_ROOT) / "modulos_sipet"),
    )
    for package_prefix, root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith(".") or child.name.startswith("__"):
                continue
            manifest_path = child / "__manifest__.py"
            if manifest_path.is_file():
                candidates.append((package_prefix, str(manifest_path)))
    return candidates


def _load_manifest_payload_from_path(module_key: str, manifest_path: str) -> dict[str, Any]:
    try:
        spec = spec_from_file_location(f"{module_key}__discovered_manifest__", manifest_path)
        if spec and spec.loader:
            manifest_module = module_from_spec(spec)
            spec.loader.exec_module(manifest_module)
            payload = getattr(manifest_module, "MANIFEST", {})
            if isinstance(payload, dict):
                return payload
    except Exception:
        return {}
    return {}


def _guess_router_specs_from_manifest(package_prefix: str, module_dir_name: str, manifest: dict[str, Any]) -> list[RouterSpec]:
    structure = manifest.get("structure") if isinstance(manifest, dict) else {}
    router_entries = structure.get("router") if isinstance(structure, dict) else None
    module_dir = Path(_PROJECT_ROOT) / package_prefix.split(".")[-1] / module_dir_name
    candidates: list[str] = []
    if isinstance(router_entries, list):
        for entry in router_entries:
            entry_value = str(entry or "").strip().replace("\\", "/")
            if entry_value.startswith("controladores/") and entry_value.endswith(".py"):
                candidates.append(Path(entry_value).stem)
    default_controller = module_dir / "controladores" / f"{module_dir_name}.py"
    if default_controller.is_file():
        candidates.append(module_dir_name)
    deduped: list[RouterSpec] = []
    seen: set[str] = set()
    for candidate in candidates:
        module_path = f"{package_prefix}.{module_dir_name}.controladores.{candidate}"
        if module_path in seen:
            continue
        seen.add(module_path)
        deduped.append(RouterSpec(module_path))
    return deduped


def _build_module_definition_from_manifest(package_prefix: str, manifest_path: str) -> ModuleDefinition | None:
    module_dir = Path(manifest_path).parent
    module_key = str(module_dir.name).strip()
    if not module_key:
        return None
    manifest = _load_manifest_payload_from_path(module_key, manifest_path)
    label = str(manifest.get("label") or manifest.get("name") or module_key.replace("_", " ").title()).strip()
    description = str(manifest.get("description") or manifest.get("summary") or "").strip()
    route = str(manifest.get("route") or "").strip()
    icon = str(manifest.get("icon") or manifest.get("fafa") or "").strip()
    relative_manifest_path = os.path.relpath(manifest_path, _REPO_ROOT).replace(os.sep, "/")
    return ModuleDefinition(
        key=module_key,
        label=label or module_key,
        description=description or f"Módulo detectado automáticamente desde {module_key}.",
        route=route,
        icon=icon,
        manifest_file=relative_manifest_path,
        app_access_name=label or module_key,
        sidebar_visible=bool(route),
        manageable=True,
        always_enabled=False,
        default_enabled=bool(manifest.get("installable", True)),
        router_specs=_guess_router_specs_from_manifest(package_prefix, module_dir.name, manifest),
    )


def refresh_module_registry_from_disk() -> list[str]:
    discovered_keys: list[str] = []
    known_manifest_paths = {
        _normalize_registry_relpath(module.manifest_file)
        for module in MODULE_DEFINITIONS
        if str(module.manifest_file or "").strip()
    }
    known_routes = {
        str(module.route or "").strip()
        for module in MODULE_DEFINITIONS
        if str(module.route or "").strip()
    }
    for package_prefix, manifest_path in _iter_discoverable_manifest_files():
        definition = _build_module_definition_from_manifest(package_prefix, manifest_path)
        normalized_manifest_path = _normalize_registry_relpath(manifest_path)
        if (
            definition is None
            or definition.key in MODULES_BY_KEY
            or normalized_manifest_path in known_manifest_paths
            or (definition.route and definition.route in known_routes)
        ):
            continue
        MODULE_DEFINITIONS.append(definition)
        MODULES_BY_KEY[definition.key] = definition
        if definition.app_access_name:
            APP_ACCESS_TO_MODULE[definition.app_access_name] = definition
        discovered_keys.append(definition.key)
        if normalized_manifest_path:
            known_manifest_paths.add(normalized_manifest_path)
        if definition.route:
            known_routes.add(definition.route)
    return discovered_keys


def is_legacy_module(module: ModuleDefinition) -> bool:
    if str(module.key or "").strip() in LEGACY_RUNTIME_ALLOWLIST:
        return False
    if str(module.manifest_file or "").startswith("fastapi_modulo/modulos/"):
        return True
    if str(module.metadata_file or "").startswith("fastapi_modulo/modulos/"):
        return True
    return any(str(spec.module_path or "").startswith("fastapi_modulo.modulos.") for spec in module.router_specs)


def is_supported_module(module: ModuleDefinition) -> bool:
    if LEGACY_MODULES_ENABLED:
        return True
    return not is_legacy_module(module)


def list_system_app_access_options() -> List[str]:
    return [
        module.app_access_name
        for module in MODULE_DEFINITIONS
        if module.app_access_name and is_supported_module(module)
    ]


def _unsupported_module_keys() -> list[str]:
    return [module.key for module in MODULE_DEFINITIONS if not is_supported_module(module)]


def _disable_unsupported_modules() -> None:
    unsupported_keys = _unsupported_module_keys()
    if not unsupported_keys:
        return
    with get_admin_engine().begin() as conn:
        conn.execute(
            text(
                """
                UPDATE system_module_settings
                SET enabled = 0,
                    updated_at = :updated_at
                WHERE module_key IN :module_keys
                """
            ).bindparams(bindparam("module_keys", expanding=True)),
            {
                "updated_at": datetime.utcnow(),
                "module_keys": unsupported_keys,
            },
        )
    session = get_admin_session_factory()()
    try:
        (
            session.query(TenantInstalledApp)
            .filter(TenantInstalledApp.app_key.in_(unsupported_keys))
            .update(
                {
                    TenantInstalledApp.is_enabled: 0,
                    TenantInstalledApp.install_status: "disabled",
                },
                synchronize_session=False,
            )
        )
        session.commit()
    finally:
        session.close()


def _ensure_module_settings_table() -> None:
    ensure_tenant_admin_schema(get_admin_engine())
    with get_admin_engine().begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS system_module_settings (
                    module_key VARCHAR(120) PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        for module in MODULE_DEFINITIONS:
            conn.execute(
                text(
                    """
                    INSERT INTO system_module_settings (module_key, enabled, updated_at)
                    SELECT :module_key, :enabled, :updated_at
                    WHERE NOT EXISTS (
                        SELECT 1 FROM system_module_settings WHERE module_key = :module_key
                    )
                    """
                ),
                {
                    "module_key": module.key,
                    "enabled": 1 if (module.default_enabled or module.always_enabled) else 0,
                    "updated_at": datetime.utcnow(),
                },
            )
    _disable_unsupported_modules()


def _read_module_state_map() -> Dict[str, bool]:
    _ensure_module_settings_table()
    with get_admin_engine().begin() as conn:
        rows = conn.execute(text("SELECT module_key, enabled FROM system_module_settings")).mappings().all()
    return {str(row["module_key"]): bool(row["enabled"]) for row in rows}


def _resolve_tenant_key(tenant_key: Optional[str] = None) -> str:
    if tenant_key:
        return str(tenant_key).strip()
    context = get_tenant_context()
    if context and context.tenant_key:
        return str(context.tenant_key).strip()
    return ""


def _read_installed_app_keys_for_tenant(tenant_key: str) -> Optional[set[str]]:
    resolved_tenant_key = str(tenant_key or "").strip()
    if not resolved_tenant_key:
        return None
    session = get_admin_session_factory()()
    try:
        rows = (
            session.query(TenantInstalledApp.app_key)
            .filter(
                TenantInstalledApp.tenant_key == resolved_tenant_key,
                TenantInstalledApp.is_enabled == 1,
                TenantInstalledApp.install_status == "installed",
            )
            .all()
        )
        installed = {str(row[0]).strip() for row in rows if str(row[0] or "").strip()}
        return installed
    finally:
        session.close()


def is_module_enabled(module_key: str, tenant_key: Optional[str] = None) -> bool:
    module = MODULES_BY_KEY.get(str(module_key or "").strip())
    if not module:
        return True
    if not is_supported_module(module):
        return False
    if module.always_enabled:
        return True
    installed_app_keys = _read_installed_app_keys_for_tenant(_resolve_tenant_key(tenant_key))
    if installed_app_keys is not None:
        if module.key in installed_app_keys:
            return True
        if module.app_access_name and module.app_access_name.lower().replace(" ", "_") in installed_app_keys:
            return True
        if module.manageable:
            return False

    states = _read_module_state_map()
    enabled = bool(states.get(module.key, module.default_enabled))
    if not enabled:
        return False
    if installed_app_keys is None:
        return True
    return enabled


def is_app_access_enabled(app_access_name: str, tenant_key: Optional[str] = None) -> bool:
    module = APP_ACCESS_TO_MODULE.get(str(app_access_name or "").strip())
    if not module:
        return True
    return is_module_enabled(module.key, tenant_key=tenant_key)


def get_active_module_keys(tenant_key: Optional[str] = None) -> List[str]:
    return [
        module.key
        for module in MODULE_DEFINITIONS
        if is_supported_module(module) and is_module_enabled(module.key, tenant_key=tenant_key)
    ]


def get_active_app_access_names(tenant_key: Optional[str] = None) -> List[str]:
    return [
        module.app_access_name
        for module in MODULE_DEFINITIONS
        if module.app_access_name and is_supported_module(module) and is_module_enabled(module.key, tenant_key=tenant_key)
    ]


def _load_module_metadata(module: ModuleDefinition) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}

    metadata_file = str(module.metadata_file or "").strip()
    if metadata_file:
        file_path = _resolve_registry_path(metadata_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    raw_payload = json.load(fh)
                if isinstance(raw_payload, dict):
                    payload.update(raw_payload)
            except Exception:
                pass

    manifest_file = str(module.manifest_file or "").strip()
    if not manifest_file:
        guessed_dirs: list[str] = []
        for spec in module.router_specs:
            parts = spec.module_path.split(".")
            if "modulos" not in parts:
                continue
            idx = parts.index("modulos")
            if idx + 1 < len(parts):
                guessed_dirs.append(parts[idx + 1])
        if guessed_dirs:
            candidate = os.path.join("fastapi_modulo", "modulos", guessed_dirs[0], "__manifest__.py")
            candidate_abs = _resolve_registry_path(candidate)
            if os.path.exists(candidate_abs):
                manifest_file = candidate
    if manifest_file:
        file_path = _resolve_registry_path(manifest_file)
        if os.path.exists(file_path):
            try:
                spec = spec_from_file_location(f"{module.key}__manifest__", file_path)
                if spec and spec.loader:
                    manifest_module = module_from_spec(spec)
                    spec.loader.exec_module(manifest_module)
                    manifest_payload = getattr(manifest_module, "MANIFEST", {})
                    if isinstance(manifest_payload, dict):
                        payload["manifest"] = manifest_payload
            except Exception:
                pass

    return payload


def _resolve_manifest_icon_url(metadata: Dict[str, Any]) -> str:
    manifest = metadata.get("manifest") if isinstance(metadata, dict) else {}
    if not isinstance(manifest, dict):
        return ""
    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        return ""
    static_base_url = str(assets.get("static_base_url") or "").strip().rstrip("/")
    if not static_base_url:
        return ""
    for key in ("img", "description"):
        entries = assets.get(key)
        if not isinstance(entries, list):
            continue
        for item in entries:
            path = str(item or "").strip().lstrip("/")
            if not path:
                continue
            if path.startswith("static/"):
                path = path[len("static/"):]
            return f"{static_base_url}/{path}"
    return ""


def _normalize_manifest_sequence(raw_value: Any, fallback_index: int) -> tuple[int, str]:
    value = str(raw_value or "").strip()
    if not value:
        return (fallback_index + 1000, "")
    try:
        return (int(value), value)
    except ValueError:
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return (int(digits), value)
        return (fallback_index + 1000, value)


def list_modules_payload(
    tenant_key: Optional[str] = None,
    *,
    refresh: bool = False,
    include_legacy: bool = False,
) -> List[Dict[str, Any]]:
    if refresh:
        refresh_module_registry_from_disk()
    states = _read_module_state_map()
    resolved_tenant_key = _resolve_tenant_key(tenant_key)
    payload: List[Dict[str, Any]] = []
    for index, module in enumerate(MODULE_DEFINITIONS):
        if not include_legacy and not is_supported_module(module):
            continue
        metadata = _load_module_metadata(module)
        manifest = metadata.get("manifest", {}) if isinstance(metadata.get("manifest"), dict) else {}
        sequence_value = manifest.get("sequence", "")
        sequence_sort, sequence_label = _normalize_manifest_sequence(sequence_value, index)
        payload.append(
            {
                "key": module.key,
                "label": str(metadata.get("label") or manifest.get("label") or module.label),
                "description": str(metadata.get("description") or manifest.get("description") or module.description),
                "route": str(metadata.get("route") or manifest.get("route") or module.route),
                "icon": str(
                    metadata.get("icon")
                    or metadata.get("fafa")
                    or manifest.get("icon")
                    or manifest.get("fafa")
                    or module.icon
                ),
                "icon_url": _resolve_manifest_icon_url(metadata),
                "sequence": sequence_label,
                "sequence_sort": sequence_sort,
                "app_access_name": module.app_access_name,
                "sidebar_visible": module.sidebar_visible,
                "manageable": module.manageable,
                "always_enabled": module.always_enabled,
                "default_enabled": module.default_enabled,
                "enabled": is_module_enabled(module.key, tenant_key=resolved_tenant_key),
                "boot_strategy": module.boot_strategy,
                "router_count": len(module.router_specs),
                "screen_access_levels": manifest.get("screen_access_levels") or {},
            }
        )
    payload.sort(key=lambda item: (int(item.get("sequence_sort", 10_000)), str(item.get("label") or "").lower(), str(item.get("key") or "")))
    return payload


def set_module_enabled(module_key: str, enabled: bool) -> Dict[str, Any]:
    module = MODULES_BY_KEY.get(str(module_key or "").strip())
    if not module:
        raise KeyError("Módulo no encontrado.")
    if not is_supported_module(module):
        raise ValueError("Este módulo legacy está deshabilitado hasta ser migrado a modulos_sipet.")
    if module.always_enabled or not module.manageable:
        raise ValueError("Este módulo no se puede desactivar.")
    _ensure_module_settings_table()
    with get_admin_engine().begin() as conn:
        update_result = conn.execute(
            text(
                """
                UPDATE system_module_settings
                SET enabled = :enabled,
                    updated_at = :updated_at
                WHERE module_key = :module_key
                """
            ),
            {
                "enabled": 1 if enabled else 0,
                "updated_at": datetime.utcnow(),
                "module_key": module.key,
            },
        )
        if update_result.rowcount == 0:
            conn.execute(
                text(
                    """
                    INSERT INTO system_module_settings (module_key, enabled, updated_at)
                    VALUES (:module_key, :enabled, :updated_at)
                    """
                ),
                {
                    "module_key": module.key,
                    "enabled": 1 if enabled else 0,
                    "updated_at": datetime.utcnow(),
                },
            )
    result = next(item for item in list_modules_payload() if item["key"] == module.key)
    result["restart_required"] = True
    return result


def register_enabled_routers(app: FastAPI, phase: str = "startup", tenant_key: Optional[str] = None) -> List[str]:
    _ensure_module_settings_table()
    registered: List[str] = []
    for module in MODULE_DEFINITIONS:
        if not is_supported_module(module):
            continue
        if module.registration_phase != phase:
            continue
        if not module.router_specs or not is_module_enabled(module.key, tenant_key=tenant_key):
            continue
        print(f"[startup] module {phase} {module.key} begin", flush=True)
        module_ok = True
        for spec in module.router_specs:
            print(f"[startup] import {spec.module_path}", flush=True)
            try:
                imported = import_module(spec.module_path)
            except (ModuleNotFoundError, ImportError, KeyError) as exc:
                print(
                    f"[startup] module {module.key} not installed or incomplete — skipped: {exc}",
                    flush=True,
                )
                module_ok = False
                break
            router = getattr(imported, spec.attr_name)
            app.include_router(router, **(spec.include_kwargs or {}))
            print(f"[startup] import {spec.module_path} done", flush=True)
        if module_ok:
            registered.append(module.key)
            print(f"[startup] module {phase} {module.key} done", flush=True)
    return registered


def iter_manageable_modules() -> Iterable[ModuleDefinition]:
    return (module for module in MODULE_DEFINITIONS if module.manageable and is_supported_module(module))
