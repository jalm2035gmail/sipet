import json
import os
from typing import Dict, List

APP_ENV_DEFAULT = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
RUNTIME_STORE_DIR = (os.environ.get("RUNTIME_STORE_DIR") or f"fastapi_modulo/runtime_store/{APP_ENV_DEFAULT}").strip()
DATOS_PRELIMINARES_STORE_PATH = (
    os.environ.get("DATOS_PRELIMINARES_STORE_PATH")
    or os.path.join(RUNTIME_STORE_DIR, "datos_preliminares_store.json")
).strip()
SUCURSALES_STORE_PATH = (
    os.environ.get("SUCURSALES_STORE_PATH")
    or os.path.join(RUNTIME_STORE_DIR, "sucursales_store.json")
).strip()

DEFAULT_DATOS_GENERALES = {
    "responsable_general": "",
    "primer_anio_proyeccion": "",
    "anios_proyeccion": "3",
    "moneda": "$",
    "inflacion_estimada": "",
    "tasa_crecimiento": "",
    "observaciones": "",
    "sociedad": "",
    "figura_juridica": "",
    "calle": "",
    "numero_exterior": "",
    "numero_interior": "",
    "colonia": "",
    "ciudad": "",
    "municipio": "",
    "estado": "",
    "cp": "",
    "pais": "",
    "ifb_activos_m3": "",
    "ifb_activos_m2": "",
    "ifb_activos_m1": "",
    "ifb_pasivos_m3": "",
    "ifb_pasivos_m2": "",
    "ifb_pasivos_m1": "",
    "ifb_capital_m3": "",
    "ifb_capital_m2": "",
    "ifb_capital_m1": "",
    "ifb_ingresos_m3": "",
    "ifb_ingresos_m2": "",
    "ifb_ingresos_m1": "",
    "ifb_egresos_m3": "",
    "ifb_egresos_m2": "",
    "ifb_egresos_m1": "",
    "ifb_resultado_m3": "",
    "ifb_resultado_m2": "",
    "ifb_resultado_m1": "",
    "macro_inflacion_json": "",
    "macro_udi_json": "",
    "activo_fijo_json": "",
    "gastos_rows_json": "",
    "ifb_rows_json": "",
    "ifb_conceptos_json": "",
    "cg_activo_total_growth_json": "",
    "cg_activo_total_rows_json": "",
    "cg_financiamiento_rows_json": "",
}


def _ensure_store_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_datos_preliminares_store() -> Dict[str, str]:
    data = dict(DEFAULT_DATOS_GENERALES)
    if not os.path.exists(DATOS_PRELIMINARES_STORE_PATH):
        return data
    try:
        with open(DATOS_PRELIMINARES_STORE_PATH, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            for key in data.keys():
                if key in loaded and loaded[key] is not None:
                    data[key] = str(loaded[key]).strip()
    except (OSError, json.JSONDecodeError):
        pass
    return data


def save_datos_preliminares_store(data: Dict[str, str]) -> None:
    safe_payload: Dict[str, str] = {}
    for key, default_value in DEFAULT_DATOS_GENERALES.items():
        safe_payload[key] = str(data.get(key, default_value) or "").strip()
    _ensure_store_parent_dir(DATOS_PRELIMINARES_STORE_PATH)
    with open(DATOS_PRELIMINARES_STORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(safe_payload, fh, ensure_ascii=False, indent=2)


def load_sucursales_store() -> List[Dict[str, str]]:
    if not os.path.exists(SUCURSALES_STORE_PATH):
        return []
    try:
        with open(SUCURSALES_STORE_PATH, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(loaded, list):
        return []
    rows: List[Dict[str, str]] = []
    for item in loaded:
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("nombre") or "").strip()
        region = str(item.get("region") or "").strip()
        codigo = str(item.get("codigo") or "").strip()
        descripcion = str(item.get("descripcion") or "").strip()
        if not nombre and not region and not codigo and not descripcion:
            continue
        rows.append(
            {
                "nombre": nombre,
                "region": region,
                "codigo": codigo,
                "descripcion": descripcion,
            }
        )
    return rows


def save_sucursales_store(rows: List[Dict[str, str]]) -> None:
    safe_rows: List[Dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("nombre") or "").strip()
        region = str(item.get("region") or "").strip()
        codigo = str(item.get("codigo") or "").strip()
        descripcion = str(item.get("descripcion") or "").strip()
        if not nombre and not region and not codigo and not descripcion:
            continue
        safe_rows.append(
            {
                "nombre": nombre,
                "region": region,
                "codigo": codigo,
                "descripcion": descripcion,
            }
        )
    _ensure_store_parent_dir(SUCURSALES_STORE_PATH)
    with open(SUCURSALES_STORE_PATH, "w", encoding="utf-8") as fh:
        json.dump(safe_rows, fh, ensure_ascii=False, indent=2)
