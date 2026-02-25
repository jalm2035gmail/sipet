from html import escape
from io import StringIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from fastapi_modulo.login_utils import get_login_identity_context

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRESUPUESTO_TXT_PATH = PROJECT_ROOT / "presupuesto.txt"


def _get_colores_context() -> dict:
    from fastapi_modulo.main import get_colores_context
    return get_colores_context()


def _load_presupuesto_dataframe() -> pd.DataFrame:
    if not PRESUPUESTO_TXT_PATH.exists():
        return pd.DataFrame(columns=["cod", "rubro", "monto", "mensual"])
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
    df["rubro"] = df["rubro"].str.capitalize()
    monto_num = pd.to_numeric(df["monto"].str.replace(",", "", regex=False), errors="coerce")
    df["monto"] = monto_num.map(lambda val: f"{int(round(val)):,}" if pd.notna(val) else "").where(
        monto_num.notna(), df["monto"]
    )
    df["mensual"] = monto_num.div(12).map(lambda val: f"{int(round(val)):,}" if pd.notna(val) else "")
    return df[["cod", "rubro", "monto", "mensual"]]


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
            f'<th class="tabla-oficial-num month-col month-{numero}" data-month-col="{numero}">%</th>'
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
                f'<td class="tabla-oficial-num month-col month-{mes}" data-month-col="{mes}"><input class="tabla-oficial-input num cm-percent-input" type="text" name="cm_{idx}_{mes}_percent" value="0%" inputmode="numeric" readonly></td>'
            )
        rows.append(f"<tr><td>{rubro}</td>{''.join(celdas)}</tr>")
    return "".join(rows)


def _build_presupuesto_csv_response() -> Response:
    df = _load_presupuesto_dataframe()
    export_df = df[["rubro", "monto", "mensual"]].rename(
        columns={"rubro": "Rubro", "monto": "Monto", "mensual": "Mensual"}
    )
    stream = StringIO()
    export_df.to_csv(stream, index=False)
    content = stream.getvalue()
    headers = {"Content-Disposition": "attachment; filename=presupuesto_anual.csv"}
    return Response(content, media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/descargar-csv-presupuesto", tags=["presupuesto"])
async def descargar_csv_presupuesto():
    """Descargar CSV del presupuesto anual actual."""
    return _build_presupuesto_csv_response()


@router.get("/descargar-plantilla-presupuesto", tags=["presupuesto"])
async def descargar_plantilla_presupuesto():
    """Compatibilidad con enlace anterior: descarga el CSV actual."""
    return _build_presupuesto_csv_response()


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
            f"<td>{escape(row.rubro)}</td>"
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
