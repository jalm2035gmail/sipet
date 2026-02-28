from html import escape
from io import StringIO
from pathlib import Path
import unicodedata
import re
import json

import pandas as pd
from fastapi import APIRouter, Request, UploadFile, File, Body
from fastapi.responses import HTMLResponse, Response, JSONResponse

from fastapi_modulo.login_utils import get_login_identity_context

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRESUPUESTO_TXT_PATH = PROJECT_ROOT / "presupuesto.txt"
CONTROL_MENSUAL_STORE_PATH = PROJECT_ROOT / "fastapi_modulo" / "modulos" / "presupuesto" / "control_mensual_store.json"


def _normalize_rubro_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    text = " ".join(text.replace(".", " ").replace(",", " ").split())
    return text


def _normalize_import_col(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


RUBRO_TIPO_MAP = {
    _normalize_rubro_key("INT NORMAL VIGENTE"): "Ingreso",
    _normalize_rubro_key("INT NORMAL VENCIDO"): "Ingreso",
    _normalize_rubro_key("GASTOS POR INTERESES"): "Egreso",
    _normalize_rubro_key("ESTIMACION PREV. P."): "Egreso",
    _normalize_rubro_key("OTROS INGRESOS"): "Ingreso",
    _normalize_rubro_key("INT MORATORIO VIGENTE"): "Ingreso",
    _normalize_rubro_key("INT MORATORIO VENCIDO"): "Ingreso",
    _normalize_rubro_key("INTERESES DE DISPONIBILIDADES"): "Ingreso",
    _normalize_rubro_key("INTERESES DE INVERSIONES"): "Ingreso",
    _normalize_rubro_key("OTROS PRODUCTOS"): "Ingreso",
    _normalize_rubro_key("COMISIONES Y TARIFAS COBRADAS"): "Ingreso",
    _normalize_rubro_key("COMISIONES Y TARIFAS PAGADAS"): "Egreso",
    _normalize_rubro_key("SALARIOS"): "Egreso",
    _normalize_rubro_key("AGUINALDO"): "Egreso",
    _normalize_rubro_key("GRATIFICACIONES"): "Egreso",
    _normalize_rubro_key("PRESTACIONES"): "Egreso",
    _normalize_rubro_key("HONORARIOS"): "Egreso",
    _normalize_rubro_key("GASTOS DE PROMOCION Y PUBLICIDAD"): "Egreso",
    _normalize_rubro_key("APORTACIONES AL FONDO DE PROTECCION"): "Egreso",
    _normalize_rubro_key("IMPUESTOS Y DERECHOS DIVERSOS"): "Egreso",
    _normalize_rubro_key("GASTOS NO DEDUCIBLES"): "Egreso",
    _normalize_rubro_key("GASTOS EN TECNOLOGIA"): "Egreso",
    _normalize_rubro_key("DEPRECIACIONES"): "Egreso",
    _normalize_rubro_key("AMORTIZACIONES"): "Egreso",
    _normalize_rubro_key("COSTO NETO DEL PERIODO"): "Egreso",
    _normalize_rubro_key("OTROS GASTOS DE ADMINISTRACION Y PROMOCION"): "Egreso",
    _normalize_rubro_key("OPERACIONES DISCONTINUAS"): "Egreso",
    _normalize_rubro_key("UTILIDAD O PERDIDA"): "",
}


def _resolve_tipo(rubro: str) -> str:
    return RUBRO_TIPO_MAP.get(_normalize_rubro_key(rubro), "")


def _get_colores_context() -> dict:
    from fastapi_modulo.main import get_colores_context
    return get_colores_context()


def _load_presupuesto_dataframe() -> pd.DataFrame:
    if not PRESUPUESTO_TXT_PATH.exists():
        return pd.DataFrame(columns=["cod", "tipo", "rubro", "monto", "mensual"])
    df = pd.read_csv(
        PRESUPUESTO_TXT_PATH,
        sep="\t",
        header=None,
        names=["cod", "rubro", "monto"],
        dtype=str,
        engine="python",
        keep_default_na=False,
        on_bad_lines="skip",
    )
    for col in ["cod", "rubro", "monto"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df = df[(df["cod"] != "") | (df["rubro"] != "") | (df["monto"] != "")].copy()
    df["tipo"] = df["rubro"].map(_resolve_tipo)
    df["rubro"] = df["rubro"].str.capitalize()
    monto_num = pd.to_numeric(df["monto"].str.replace(",", "", regex=False), errors="coerce")
    df["monto"] = monto_num.map(lambda val: f"{int(round(val)):,}" if pd.notna(val) else "").where(
        monto_num.notna(), df["monto"]
    )
    df["mensual"] = monto_num.div(12).map(lambda val: f"{int(round(val)):,}" if pd.notna(val) else "")
    return df[["cod", "tipo", "rubro", "monto", "mensual"]]


def _control_mensual_header_html() -> str:
    meses = [
        ("01", "Ene"),
        ("02", "Feb"),
        ("03", "Mar"),
        ("04", "Abr"),
        ("05", "May"),
        ("06", "Jun"),
        ("07", "Jul"),
        ("08", "Ago"),
        ("09", "Sep"),
        ("10", "Oct"),
        ("11", "Nov"),
        ("12", "Dic"),
    ]
    top = "".join(
        (
            f'<th colspan="3" class="month-group-head month-{numero}">'
            f'<button type="button" class="month-toggle-btn" data-month-toggle="{numero}" aria-label="Mostrar u ocultar {nombre}">▾</button>'
            f"{nombre}<span hidden class=\"mes-num-hidden\">{numero}</span></th>"
        )
        for numero, nombre in meses
    )
    bottom = "".join(
        (
            f'<th class="tabla-oficial-num month-col month-{numero}" data-month-col="{numero}">Proyectado</th>'
            f'<th class="tabla-oficial-num month-col month-{numero}" data-month-col="{numero}">Realizado</th>'
            f'<th class="tabla-oficial-num month-col month-{numero} month-percent-col" data-month-col="{numero}">%</th>'
        )
        for numero, _ in meses
    )
    return top, bottom


def _control_mensual_rows_html(df: pd.DataFrame) -> str:
    meses = [f"{i:02d}" for i in range(1, 13)]
    rows = []
    for idx, row in enumerate(df.itertuples(index=False), start=1):
        rubro = escape(str(getattr(row, "rubro", "") or ""))
        celdas = []
        for mes in meses:
            celdas.append(
                f'<td class="tabla-oficial-num month-col month-{mes}" data-month-col="{mes}"><input class="tabla-oficial-input num" type="text" name="cm_{idx}_{mes}_proyectado" value="0" inputmode="numeric"></td>'
            )
            celdas.append(
                f'<td class="tabla-oficial-num month-col month-{mes}" data-month-col="{mes}"><input class="tabla-oficial-input num" type="text" name="cm_{idx}_{mes}_realizado" value="0" inputmode="numeric"></td>'
            )
            celdas.append(
                f'<td class="tabla-oficial-num month-col month-{mes} month-percent-col" data-month-col="{mes}"><input class="tabla-oficial-input num cm-percent-input" type="text" name="cm_{idx}_{mes}_percent" value="0%" inputmode="numeric" readonly></td>'
            )
        rows.append(f"<tr><td>{rubro}</td>{''.join(celdas)}</tr>")
    return "".join(rows)


def _build_presupuesto_csv_response() -> Response:
    df = _load_presupuesto_dataframe()
    rubros = [
        str(getattr(row, "rubro", "") or "").strip()
        for row in df.itertuples(index=False)
        if str(getattr(row, "rubro", "") or "").strip()
    ]
    if not rubros:
        rubros = ["Ejemplo rubro"]
    rows = []
    for rubro in rubros:
        item = {"Rubro": rubro}
        for mes in range(0, 13):
            item[f"mes {mes}"] = 0
        rows.append(item)
    export_df = pd.DataFrame(rows)
    stream = StringIO()
    export_df.to_csv(stream, index=False)
    content = stream.getvalue()
    headers = {"Content-Disposition": "attachment; filename=plantilla_real_mensual_presupuesto.csv"}
    return Response(content, media_type="text/csv; charset=utf-8", headers=headers)


def _build_presupuesto_control_template_csv_response() -> Response:
    # Mismo formato oficial de "Descargar CSV" para evitar dos plantillas distintas.
    return _build_presupuesto_csv_response()


def _read_import_dataframe(upload: UploadFile) -> pd.DataFrame:
    filename = (upload.filename or "").strip().lower()
    if filename.endswith(".csv"):
        return pd.read_csv(upload.file, dtype=str, keep_default_na=False)
    if filename.endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        return pd.read_excel(upload.file, dtype=str).fillna("")
    raise ValueError("Formato no soportado. Usa CSV o Excel.")


def _to_int_or_none(value) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = raw.replace(",", "").replace(" ", "")
    try:
        numeric = float(normalized)
    except ValueError:
        return None
    if not pd.notna(numeric):
        return None
    return int(round(numeric))


def _load_control_mensual_store() -> dict:
    if not CONTROL_MENSUAL_STORE_PATH.exists():
        return {"rows": [], "updated_at": ""}
    try:
        raw = json.loads(CONTROL_MENSUAL_STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"rows": [], "updated_at": ""}
    if not isinstance(raw, dict):
        return {"rows": [], "updated_at": ""}
    rows = raw.get("rows")
    if not isinstance(rows, list):
        rows = []
    return {
        "rows": rows,
        "updated_at": str(raw.get("updated_at") or ""),
    }


def _save_control_mensual_store(payload: dict) -> None:
    CONTROL_MENSUAL_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTROL_MENSUAL_STORE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/descargar-csv-presupuesto", tags=["presupuesto"])
async def descargar_csv_presupuesto():
    """Descargar CSV del presupuesto anual actual."""
    return _build_presupuesto_csv_response()


@router.get("/descargar-plantilla-presupuesto", tags=["presupuesto"])
async def descargar_plantilla_presupuesto():
    """Plantilla para importar datos mensuales (con número de mes)."""
    return _build_presupuesto_control_template_csv_response()


@router.post("/importar-control-mensual", tags=["presupuesto"])
async def importar_control_mensual(file: UploadFile = File(...)):
    try:
        df = _read_import_dataframe(file)
    except ValueError as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    except Exception:
        return JSONResponse({"success": False, "error": "No se pudo leer el archivo"}, status_code=400)

    if df.empty:
        return JSONResponse({"success": False, "error": "El archivo está vacío"}, status_code=400)

    original_cols = list(df.columns)
    normalized_cols = {_normalize_import_col(col): col for col in original_cols}

    rubro_col = next((normalized_cols.get(key) for key in ("rubro", "nombre_rubro", "concepto")), None)
    month_col = next((normalized_cols.get(key) for key in ("mes_numero", "mes", "month", "numero_mes")), None)
    proyectado_col = next((normalized_cols.get(key) for key in ("proyectado", "monto_proyectado", "proyectado_mensual")), None)
    realizado_col = next((normalized_cols.get(key) for key in ("realizado", "monto_realizado", "realizado_mensual")), None)
    wide_month_cols: Dict[int, str] = {}
    for normalized, original in normalized_cols.items():
        # Acepta: mes_0, mes0, month_0 ... mes_12
        match = re.match(r"^(?:mes|month)_?([0-9]{1,2})$", normalized)
        if not match:
            continue
        month_idx = int(match.group(1))
        if month_idx < 0 or month_idx > 12:
            continue
        wide_month_cols[month_idx] = original

    is_wide_format = bool(rubro_col and wide_month_cols)
    if not rubro_col and not is_wide_format:
        return JSONResponse(
            {
                "success": False,
                "error": "Columnas obligatorias: Rubro y meses (mes 0..mes 12) o formato largo con mes_numero.",
                "columns_detected": original_cols,
            },
            status_code=400,
        )
    if not is_wide_format and (not month_col):
        return JSONResponse(
            {
                "success": False,
                "error": "En formato largo debes incluir columna mes_numero (1-12).",
                "columns_detected": original_cols,
            },
            status_code=400,
        )
    if not is_wide_format and (not proyectado_col and not realizado_col):
        return JSONResponse(
            {
                "success": False,
                "error": "Debes incluir al menos una columna de valores: proyectado o realizado.",
                "columns_detected": original_cols,
            },
            status_code=400,
        )

    entries = []
    row_errors = []
    duplicate_keys = set()
    seen_keys = set()
    initial_data_rows = 0
    if is_wide_format:
        for idx, row in df.iterrows():
            line_no = int(idx) + 2
            rubro = str(row.get(rubro_col, "") or "").strip()
            if not rubro:
                row_errors.append(f"Línea {line_no}: rubro vacío.")
                continue
            initial_value = _to_int_or_none(row.get(wide_month_cols.get(0, ""), "")) if wide_month_cols.get(0) else None
            if initial_value not in (None, 0):
                initial_data_rows += 1
            for mes_int in range(1, 13):
                month_column = wide_month_cols.get(mes_int)
                if not month_column:
                    continue
                realizado = _to_int_or_none(row.get(month_column, ""))
                if realizado is None:
                    continue
                mes = f"{mes_int:02d}"
                key = (_normalize_rubro_key(rubro), mes)
                if key in seen_keys:
                    duplicate_keys.add(key)
                seen_keys.add(key)
                entries.append(
                    {
                        "line": line_no,
                        "rubro": rubro,
                        "rubro_key": key[0],
                        "mes_numero": mes_int,
                        "mes": mes,
                        "proyectado": None,
                        "realizado": realizado,
                    }
                )
    else:
        for idx, row in df.iterrows():
            line_no = int(idx) + 2
            rubro = str(row.get(rubro_col, "") or "").strip()
            mes_raw = row.get(month_col, "")
            mes_int = _to_int_or_none(mes_raw)
            proyectado = _to_int_or_none(row.get(proyectado_col, "")) if proyectado_col else None
            realizado = _to_int_or_none(row.get(realizado_col, "")) if realizado_col else None

            if not rubro:
                row_errors.append(f"Línea {line_no}: rubro vacío.")
                continue
            if not mes_int or mes_int < 1 or mes_int > 12:
                row_errors.append(f"Línea {line_no}: mes_numero inválido ({mes_raw}). Debe ser 1-12.")
                continue
            if proyectado is None and realizado is None:
                row_errors.append(f"Línea {line_no}: sin valores en proyectado/realizado.")
                continue

            mes = f"{mes_int:02d}"
            key = (_normalize_rubro_key(rubro), mes)
            if key in seen_keys:
                duplicate_keys.add(key)
            seen_keys.add(key)
            entries.append(
                {
                    "line": line_no,
                    "rubro": rubro,
                    "rubro_key": key[0],
                    "mes_numero": mes_int,
                    "mes": mes,
                    "proyectado": proyectado,
                    "realizado": realizado,
                }
            )

    if row_errors:
        return JSONResponse(
            {
                "success": False,
                "error": "Se detectaron errores en el archivo.",
                "details": row_errors[:50],
            },
            status_code=400,
        )

    return JSONResponse(
        {
            "success": True,
            "entries": entries,
            "summary": {
                "rows": len(entries),
                "duplicates_in_file": len(duplicate_keys),
                "initial_data_rows": int(initial_data_rows),
                "format": "wide_real_only" if is_wide_format else "long",
            },
        }
    )


@router.get("/control-mensual-datos", tags=["presupuesto"])
async def obtener_control_mensual_datos():
    store = _load_control_mensual_store()
    # Compatibilidad con frontend legado y nuevo:
    # - rows/updated_at en raíz
    # - data con el objeto completo
    return JSONResponse(
        {
            "success": True,
            "rows": store.get("rows", []),
            "updated_at": store.get("updated_at", ""),
            "data": store,
        }
    )


@router.post("/guardar-control-mensual", tags=["presupuesto"])
async def guardar_control_mensual(data: dict = Body(default={})):
    rows = data.get("rows")
    if not isinstance(rows, list):
        return JSONResponse({"success": False, "error": "rows debe ser una lista"}, status_code=400)
    sanitized = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        rubro = str(item.get("rubro") or "").strip()
        if not rubro:
            continue
        months = item.get("months")
        if not isinstance(months, dict):
            continue
        row_months = {}
        for mes in range(1, 13):
            key = f"{mes:02d}"
            payload = months.get(key)
            if not isinstance(payload, dict):
                payload = {}
            proyectado = _to_int_or_none(payload.get("proyectado"))
            realizado = _to_int_or_none(payload.get("realizado"))
            row_months[key] = {
                "proyectado": int(proyectado or 0),
                "realizado": int(realizado or 0),
            }
        sanitized.append({"rubro": rubro, "months": row_months})
    store_payload = {
        "rows": sanitized,
        "updated_at": pd.Timestamp.utcnow().isoformat(),
    }
    _save_control_mensual_store(store_payload)
    return JSONResponse({"success": True, "saved_rows": len(sanitized)})


@router.get("/presupuesto", response_class=HTMLResponse)
def proyectando_presupuesto_page(request: Request):
    """Página de proyección de presupuesto con shell oficial."""
    login_identity = get_login_identity_context()
    logo_url = escape((login_identity.get("login_logo_url") or "").strip())
    logo_html = (
        f'<img src="{logo_url}" alt="Logo de la empresa" '
        'style="width:min(88px, 14vw); max-width:100%; height:auto; object-fit:contain;">'
        if logo_url else ""
    )
    df = _load_presupuesto_dataframe()
    control_header_top, control_header_bottom = _control_mensual_header_html()
    control_rows = _control_mensual_rows_html(df)

    presupuesto_table_rows = "".join(
        ('<tr class="presupuesto-zebra">' if i % 2 == 1 else "<tr>")
        + (
            f'<td class="cod-col" style="display:none;">{escape(row.cod)}</td>'
            f'<td class="tipo-col" style="display:none;">{escape(row.tipo)}</td>'
            f'<td class="rubro-col">{escape(row.rubro)}</td>'
            f'<td class="tabla-oficial-num"><input class="tabla-oficial-input num presupuesto-num-input" type="text" value="{escape(row.monto)}" inputmode="numeric" placeholder="0"></td>'
            f'<td class="tabla-oficial-num presupuesto-mensual">{escape(row.mensual)}</td></tr>'
        )
        for i, row in enumerate(df.itertuples(index=False))
    )

    content_template = request.app.state.templates.env.get_template("modulos/presupuesto/presupuesto.html")
    content = content_template.render(
        logo_html=logo_html,
        presupuesto_table_rows=presupuesto_table_rows,
        control_mensual_header_top=control_header_top,
        control_mensual_header_bottom=control_header_bottom,
        control_mensual_rows=control_rows,
    )

    return request.app.state.templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "Fase 9: Presupuesto",
            "description": "Gestiona el presupuesto anual y su carga de datos.",
            "page_title": "Fase 9: Presupuesto",
            "page_description": "Gestiona el presupuesto anual y su carga de datos.",
            "section_label": "",
            "section_title": "",
            "content": content,
            "floating_actions_html": "",
            "hide_floating_actions": True,
            "show_page_header": True,
            "colores": _get_colores_context(),
        },
    )
