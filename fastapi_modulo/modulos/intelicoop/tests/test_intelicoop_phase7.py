from __future__ import annotations

import io
import zipfile
from datetime import datetime, timedelta

import pytest
pytestmark = pytest.mark.filterwarnings("ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning")


from fastapi_modulo.core.db import MAIN, engine
from sqlalchemy.orm import sessionmaker

import fastapi_modulo.modulos.intelicoop.controladores.intelicoop as intelicoop_controller
from fastapi_modulo.modulos.intelicoop.modelos.intelicoop_db_models import (
    IntelicoopCampania,
    IntelicoopContactoCampania,
    IntelicoopCredito,
    IntelicoopCuenta,
    IntelicoopHistorialPago,
    IntelicoopModelVersionRegistry,
    IntelicoopProspecto,
    IntelicoopScoringResult,
    IntelicoopScoringTraza,
    IntelicoopSeguimientoCampania,
    IntelicoopSocio,
    IntelicoopTransaccion,
)


INTELICOOP_TABLES = [
    IntelicoopSocio.__table__,
    IntelicoopCredito.__table__,
    IntelicoopHistorialPago.__table__,
    IntelicoopCuenta.__table__,
    IntelicoopTransaccion.__table__,
    IntelicoopCampania.__table__,
    IntelicoopProspecto.__table__,
    IntelicoopContactoCampania.__table__,
    IntelicoopSeguimientoCampania.__table__,
    IntelicoopScoringResult.__table__,
    IntelicoopScoringTraza.__table__,
    IntelicoopModelVersionRegistry.__table__,
]


@pytest.fixture(autouse=True)
def _reset_phase7_tables(reset_tables) -> None:
    reset_tables(INTELICOOP_TABLES)


def test_intelicoop_html_requires_access(build_client, strict_intelicoop_access) -> None:
    client = build_client(strict_intelicoop_access)

    response = client.get("/inicio/intelicoop")

    assert response.status_code == 403
    assert response.json()["detail"] == "Acceso restringido a Intelicoop"


def test_intelicoop_html_renders_with_access(monkeypatch: pytest.MonkeyPatch, build_client, strict_intelicoop_access, auth_headers, fake_render_backend_page) -> None:
    client = build_client(strict_intelicoop_access)
    monkeypatch.setattr(intelicoop_controller, "render_backend_page_html", fake_render_backend_page)

    response = client.get("/inicio/intelicoop", headers=auth_headers("Intelicoop", role="admin"))

    assert response.status_code == 200
    assert "Intelicoop" in response.text
    assert "intelicoop-root" in response.text


def test_intelicoop_api_blocks_without_access(build_client, strict_intelicoop_access) -> None:
    client = build_client(strict_intelicoop_access)

    response = client.get("/api/intelicoop/socios")

    assert response.status_code == 403
    assert response.json()["detail"] == "Acceso restringido a Intelicoop"


def test_intelicoop_core_flow_persists_data_and_scoring(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="usuario", user="intelicoop.test")

    socio_response = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Ana Perez",
            "email": "ana@example.com",
            "telefono": "555-0101",
            "direccion": "Zona 1",
            "fecha_nacimiento": "1990-03-20",
            "genero": "femenino",
            "estado_civil": "casada",
            "nivel_educativo": "universitario",
            "ocupacion": "contadora",
            "sector_economico": "servicios",
            "ubicacion_estado": "Guatemala",
            "ubicacion_municipio": "Guatemala",
            "tipo_socio": "individual",
            "segmento": "hormiga",
        },
    )
    assert socio_response.status_code == 201
    socio_payload = socio_response.json()
    socio_id = socio_payload["id"]
    assert socio_payload["fecha_nacimiento"] == "1990-03-20"
    assert socio_payload["edad"] == 36
    assert socio_payload["ocupacion"] == "contadora"
    assert socio_payload["tipo_socio"] == "individual"

    credito_response = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 1500,
            "numero_abonos": 12,
            "periodicidad": "mensual",
            "ingreso_mensual": 5000,
            "deuda_actual": 800,
            "antiguedad_meses": 24,
            "tasa": 18.5,
            "dias_mora_actual": 7,
            "max_dias_mora": 21,
            "num_reestructuras": 1,
            "estado": "solicitado",
        },
    )
    assert credito_response.status_code == 201
    credito_payload = credito_response.json()
    credito_id = credito_payload["credito"]["id"]
    assert credito_payload["credito"]["numero_abonos"] == 12
    assert credito_payload["credito"]["periodicidad"] == "mensual"
    assert credito_payload["credito"]["tasa"] == 18.5
    assert credito_payload["credito"]["dias_mora_actual"] == 7
    assert credito_payload["credito"]["max_dias_mora"] == 21
    assert credito_payload["credito"]["num_reestructuras"] == 1
    scoring = credito_payload["scoring"]
    assert scoring["credito_id"] == credito_id
    assert scoring["model_version"] == "intelicoop_scoring_v1"
    assert scoring["confianza"] is not None
    assert scoring["motor"] in {"reglas", "modelo_ml"}
    assert scoring["traza_id"] is not None
    assert scoring["traza_version"] == "intelicoop_traza_v1"
    assert scoring["explicacion_json"]["razones"]
    assert scoring["explicacion_json"]["reglas_aplicadas"]
    assert "historial_pagos" in scoring["explicacion_json"]["reglas_aplicadas"][0]["regla"] or scoring["explicacion_json"]["reglas_aplicadas"]

    traza_response = client.get(f"/api/intelicoop/scoring/{scoring['id']}/traza", headers=headers)
    assert traza_response.status_code == 200
    traza = traza_response.json()
    assert traza["scoring_result_id"] == scoring["id"]
    assert traza["inputs"]["ingreso_mensual"] == 5000.0
    assert traza["outputs"]["score"] == scoring["score"]
    assert traza["razones"]
    assert traza["reglas_aplicadas"]

    pago_response = client.post(
        "/api/intelicoop/creditos/pagos",
        headers=headers,
        json={"credito_id": credito_id, "monto": 250, "pago_puntual": False, "dias_atraso": 4},
    )
    assert pago_response.status_code == 201
    assert pago_response.json()["pago_puntual"] is False
    assert pago_response.json()["dias_atraso"] == 4

    detalle_response = client.get(f"/api/intelicoop/creditos/{credito_id}/detalle", headers=headers)
    assert detalle_response.status_code == 200
    detalle = detalle_response.json()
    assert detalle["id"] == credito_id
    assert detalle["numero_abonos"] == 12
    assert detalle["periodicidad"] == "mensual"
    assert detalle["tasa"] == 18.5
    assert detalle["dias_mora_actual"] == 7
    assert detalle["resumen_pagos"]["monto_pagado"] == 250.0
    assert detalle["historial_pagos"][0]["pago_puntual"] is False
    assert detalle["historial_pagos"][0]["dias_atraso"] == 4

    cuenta_response = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_id, "tipo": "ahorro", "saldo": 1000},
    )
    assert cuenta_response.status_code == 201
    cuenta_id = cuenta_response.json()["id"]

    tx_response = client.post(
        "/api/intelicoop/ahorros/transacciones",
        headers=headers,
        json={"cuenta_id": cuenta_id, "tipo": "deposito", "monto": 300, "canal": "app"},
    )
    assert tx_response.status_code == 201
    assert tx_response.json()["canal"] == "app"

    campana_response = client.post(
        "/api/intelicoop/campanas",
        headers=headers,
        json={
            "nombre": "Campana Primavera",
            "tipo": "Colocacion",
            "fecha_inicio": "2026-03-01T00:00:00",
            "fecha_fin": "2026-03-31T00:00:00",
            "estado": "activa",
        },
    )
    assert campana_response.status_code == 201

    prospecto_response = client.post(
        "/api/intelicoop/prospectos",
        headers=headers,
        json={
            "nombre": "Carlos Ruiz",
            "telefono": "555-0202",
            "direccion": "Zona 4",
            "fuente": "referido",
            "score_propension": 0.7,
        },
    )
    assert prospecto_response.status_code == 201

    resumen_response = client.get("/api/intelicoop/scoring/resumen", headers=headers)
    assert resumen_response.status_code == 200
    resumen = resumen_response.json()
    assert resumen["total_inferencias"] >= 1
    assert resumen["recientes"][0]["model_version"] == "intelicoop_scoring_v1"

    materialize_response = client.post("/api/intelicoop/fundamentos/materializar", headers=headers, json={"cut_type": "daily_close"})
    assert materialize_response.status_code == 201
    scoring_batch_response = client.post("/api/intelicoop/batch/ejecutar", headers=headers, json={"job_key": "scoring_refresh"})
    assert scoring_batch_response.status_code == 201

    dashboard_response = client.get("/api/intelicoop/dashboard/resumen", headers=headers)
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["mode"] == "cut_driven"
    assert dashboard["cut_key"] == materialize_response.json()["cut_key"]
    assert dashboard["socios"] == 1
    assert dashboard["creditos"] == 1
    assert dashboard["campanas"] == 1
    assert dashboard["prospectos"] == 1
    assert dashboard["scoring_total"] >= 1


def test_admin_can_access_intelicoop_without_checkbox(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)

    response = client.get("/api/intelicoop/socios", headers=auth_headers(role="admin"))

    assert response.status_code == 200
    assert response.json() == []


def test_credito_estado_catalog_and_validation_are_normalized(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    socio = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Estado",
            "email": "estado@example.com",
            "telefono": "555-0199",
            "direccion": "Zona 5",
            "segmento": "hormiga",
        },
    )
    assert socio.status_code == 201
    socio_id = socio.json()["id"]

    catalogos = client.get("/api/intelicoop/catalogos/basicos", headers=headers)
    assert catalogos.status_code == 200
    estados = {row["value"] for row in catalogos.json()["estados_credito"]}
    assert {"solicitado", "aprobado", "vigente", "liquidado", "rechazado", "mora", "reestructurado"}.issubset(estados)

    credito = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 1800,
            "numero_abonos": 12,
            "periodicidad": "mensual",
            "ingreso_mensual": 7000,
            "deuda_actual": 1200,
            "antiguedad_meses": 20,
            "estado": "REESTRUCTURADO",
        },
    )
    assert credito.status_code == 201
    assert credito.json()["credito"]["estado"] == "reestructurado"

    invalido = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_id,
            "monto": 1800,
            "numero_abonos": 12,
            "periodicidad": "mensual",
            "ingreso_mensual": 7000,
            "deuda_actual": 1200,
            "antiguedad_meses": 20,
            "estado": "cerrado_manual",
        },
    )
    assert invalido.status_code == 422


def test_scoring_evaluar_persists_version_and_trace(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    response = client.post(
        "/api/intelicoop/scoring/evaluar",
        headers=headers,
        json={
            "solicitud_id": "sol-operativa-001",
            "ingreso_mensual": 6200,
            "deuda_actual": 900,
            "antiguedad_meses": 30,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["solicitud_id"] == "sol-operativa-001"
    assert body["model_version"] == "intelicoop_scoring_v1"
    assert body["confianza"] is not None
    assert body["motor"] in {"reglas", "modelo_ml"}
    assert body["traza_id"] is not None
    assert body["explicacion_json"]["inputs"]["ingreso_mensual"] == 6200.0
    assert "score_reglas_enriquecidas" in body["explicacion_json"]["features_calculados"]
    assert "historial_pagos" in body["explicacion_json"]["features_calculados"]
    assert "frecuencia_depositos" in body["explicacion_json"]["features_calculados"]
    assert "numero_productos" in body["explicacion_json"]["features_calculados"]
    assert "probabilidad_calibrada" in body["explicacion_json"]["features_calculados"]
    assert "completitud_datos" in body["explicacion_json"]["features_calculados"]
    assert "threshold_segmento" in body["explicacion_json"]["features_calculados"]
    assert body["explicacion_json"]["explainability"]["importancia_variables"]
    assert body["explicacion_json"]["explainability"]["shap_values"]
    assert body["explicacion_json"]["explainability"]["top_factores_por_score"]
    assert body["explicacion_json"]["explainability"]["explicacion_local_socio"]

    traza_response = client.get(f"/api/intelicoop/scoring/{body['id']}/traza", headers=headers)
    assert traza_response.status_code == 200
    traza = traza_response.json()
    assert traza["model_version"] == "intelicoop_scoring_v1"
    assert traza["traza_version"] == "intelicoop_traza_v1"
    assert traza["inputs"]["deuda_actual"] == 900.0
    assert traza["outputs"]["recomendacion"] == body["recomendacion"]
    assert "score_reglas_enriquecidas" in traza["features_calculados"]
    assert "psi" in traza["features_calculados"]
    assert "csi" in traza["features_calculados"]
    assert traza["explainability"]["importancia_variables"]
    assert traza["explainability"]["shap_values"]


def test_scoring_explainability_endpoint_exposes_global_and_local_views(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    socio_a = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Explain A",
            "email": "explain.a@example.com",
            "telefono": "555-5100",
            "direccion": "Centro",
            "segmento": "gran_ahorrador",
        },
    )
    assert socio_a.status_code == 201
    socio_a_id = socio_a.json()["id"]

    socio_b = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Explain B",
            "email": "explain.b@example.com",
            "telefono": "555-5200",
            "direccion": "Norte",
            "segmento": "inactivo",
        },
    )
    assert socio_b.status_code == 201
    socio_b_id = socio_b.json()["id"]

    for payload in (
        {"solicitud_id": "exp-a-1", "socio_id": socio_a_id, "ingreso_mensual": 8800, "deuda_actual": 700, "antiguedad_meses": 40},
        {"solicitud_id": "exp-a-2", "socio_id": socio_a_id, "ingreso_mensual": 7600, "deuda_actual": 1200, "antiguedad_meses": 28},
        {"solicitud_id": "exp-b-1", "socio_id": socio_b_id, "ingreso_mensual": 2600, "deuda_actual": 2100, "antiguedad_meses": 5},
    ):
        response = client.post("/api/intelicoop/scoring/evaluar", headers=headers, json=payload)
        assert response.status_code == 201

    global_response = client.get("/api/intelicoop/scoring/explicabilidad", headers=headers)
    assert global_response.status_code == 200
    global_body = global_response.json()
    assert global_body["importancia_variables"]
    assert global_body["shap_values_promedio"]
    assert global_body["top_factores_por_score"]["alto"] or global_body["top_factores_por_score"]["medio"] or global_body["top_factores_por_score"]["bajo"]
    assert global_body["explicacion_agregada_segmento"]

    local_response = client.get(f"/api/intelicoop/scoring/explicabilidad?socio_id={socio_a_id}", headers=headers)
    assert local_response.status_code == 200
    local_body = local_response.json()
    assert local_body["socio_id"] == socio_a_id
    assert local_body["explicacion_local_socio"]["socio_id"] == socio_a_id
    assert local_body["explicacion_local_socio"]["factores_clave"]
    assert local_body["importancia_variables"]


def test_creditos_import_template_and_csv_import(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    socio = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Importacion",
            "email": "importacion@example.com",
            "telefono": "555-6100",
            "direccion": "Centro",
            "segmento": "hormiga",
        },
    )
    assert socio.status_code == 201
    socio_id = socio.json()["id"]

    template_response = client.get("/api/intelicoop/creditos/importacion/plantilla", headers=headers)
    assert template_response.status_code == 200
    assert "socio_id" in template_response.text
    assert "socio_email" in template_response.text
    assert "attachment;" in template_response.headers["content-disposition"]

    csv_content = (
        "socio_id,socio_email,monto,numero_abonos,periodicidad,ingreso_mensual,deuda_actual,antiguedad_meses,estado,fecha_desembolso,fecha_vencimiento\n"
        f"{socio_id},,1500,12,mensual,5000,700,24,solicitado,2026-03-23,2027-03-23\n"
        ",importacion@example.com,2200,18,quincenal,6500,900,30,aprobado,2026-03-23,2027-09-23\n"
    )
    import_response = client.post(
        "/api/intelicoop/creditos/importacion",
        headers=headers,
        files={"file": ("creditos.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert import_response.status_code == 201
    body = import_response.json()
    assert body["total_filas"] == 2
    assert body["importados"] == 2
    assert body["errores"] == []
    assert len(body["registros"]) == 2

    creditos_response = client.get("/api/intelicoop/creditos", headers=headers)
    assert creditos_response.status_code == 200
    assert len(creditos_response.json()) == 2

    scoring_response = client.get("/api/intelicoop/scoring/resumen", headers=headers)
    assert scoring_response.status_code == 200
    assert scoring_response.json()["total_inferencias"] >= 2


def test_importacion_masiva_templates_zip_and_entity_imports(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    zip_response = client.get("/api/intelicoop/importacion/plantillas", headers=headers)
    assert zip_response.status_code == 200
    assert zip_response.headers["content-disposition"].endswith('filename="intelicoop_plantillas_importacion.zip"')
    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as archive:
        names = set(archive.namelist())
    assert {
        "intelicoop_socios_plantilla.csv",
        "intelicoop_creditos_plantilla.csv",
        "intelicoop_cuentas_plantilla.csv",
        "intelicoop_transacciones_plantilla.csv",
        "intelicoop_campanas_plantilla.csv",
        "intelicoop_contactos_plantilla.csv",
        "intelicoop_seguimientos_plantilla.csv",
        "intelicoop_prospectos_plantilla.csv",
        "intelicoop_pagos_plantilla.csv",
    }.issubset(names)

    socios_csv = (
        "nombre,email,telefono,direccion,segmento,fecha_nacimiento,genero,estado_civil,nivel_educativo,ocupacion,sector_economico,ubicacion_estado,ubicacion_municipio,tipo_socio\n"
        "Ana Import,ana.import@example.com,555-7001,Zona 1,hormiga,1992-01-02,femenino,soltera,universitario,analista,servicios,Guatemala,Guatemala,individual\n"
        "Luis Import,luis.import@example.com,555-7002,Zona 2,gran_ahorrador,1987-04-10,masculino,casado,maestria,gerente,comercio,Sacatepequez,Antigua,empresarial\n"
    )
    socios_response = client.post(
        "/api/intelicoop/socios/importacion",
        headers=headers,
        files={"file": ("socios.csv", socios_csv.encode("utf-8"), "text/csv")},
    )
    assert socios_response.status_code == 201
    socios_body = socios_response.json()
    assert socios_body["importados"] == 2
    assert socios_body["errores"] == []

    cuentas_csv = (
        "socio_id,socio_email,tipo,saldo\n"
        ",ana.import@example.com,ahorro,2500\n"
        ",luis.import@example.com,aportacion,5200\n"
    )
    cuentas_response = client.post(
        "/api/intelicoop/ahorros/cuentas/importacion",
        headers=headers,
        files={"file": ("cuentas.csv", cuentas_csv.encode("utf-8"), "text/csv")},
    )
    assert cuentas_response.status_code == 201
    assert cuentas_response.json()["importados"] == 2

    cuentas = client.get("/api/intelicoop/ahorros/cuentas", headers=headers)
    assert cuentas.status_code == 200
    cuenta_ids = [row["id"] for row in cuentas.json()]
    assert len(cuenta_ids) == 2

    transacciones_csv = (
        "cuenta_id,monto,tipo,canal\n"
        f"{cuenta_ids[0]},400,deposito,app\n"
        f"{cuenta_ids[1]},125,retiro,ventanilla\n"
    )
    transacciones_response = client.post(
        "/api/intelicoop/ahorros/transacciones/importacion",
        headers=headers,
        files={"file": ("transacciones.csv", transacciones_csv.encode("utf-8"), "text/csv")},
    )
    assert transacciones_response.status_code == 201
    assert transacciones_response.json()["importados"] == 2

    creditos_csv = (
        "socio_id,socio_email,monto,numero_abonos,periodicidad,ingreso_mensual,deuda_actual,antiguedad_meses,tasa,estado,dias_mora_actual,max_dias_mora,num_reestructuras,fecha_desembolso,fecha_vencimiento\n"
        ",ana.import@example.com,8000,18,mensual,9500,1200,30,19.5,aprobado,0,12,0,2026-03-23,2027-09-23\n"
        ",luis.import@example.com,15000,24,quincenal,18000,3500,48,16.0,solicitado,2,15,1,2026-03-23,2028-03-23\n"
    )
    creditos_response = client.post(
        "/api/intelicoop/creditos/importacion",
        headers=headers,
        files={"file": ("creditos.csv", creditos_csv.encode("utf-8"), "text/csv")},
    )
    assert creditos_response.status_code == 201
    assert creditos_response.json()["importados"] == 2

    creditos = client.get("/api/intelicoop/creditos", headers=headers)
    assert creditos.status_code == 200
    credito_ids = [row["id"] for row in creditos.json()]
    assert len(credito_ids) == 2

    pagos_csv = (
        "credito_id,monto,pago_puntual,dias_atraso\n"
        f"{credito_ids[0]},900,1,0\n"
        f"{credito_ids[1]},850,0,5\n"
    )
    pagos_response = client.post(
        "/api/intelicoop/creditos/pagos/importacion",
        headers=headers,
        files={"file": ("pagos.csv", pagos_csv.encode("utf-8"), "text/csv")},
    )
    assert pagos_response.status_code == 201
    assert pagos_response.json()["importados"] == 2

    campanas_csv = (
        "nombre,tipo,fecha_inicio,fecha_fin,estado\n"
        "Campana Masiva,Colocacion,2026-03-01T00:00:00,2026-03-31T00:00:00,activa\n"
    )
    campanas_response = client.post(
        "/api/intelicoop/campanas/importacion",
        headers=headers,
        files={"file": ("campanas.csv", campanas_csv.encode("utf-8"), "text/csv")},
    )
    assert campanas_response.status_code == 201
    assert campanas_response.json()["importados"] == 1

    contactos_csv = (
        "campania_id,campania_nombre,socio_id,socio_email,ejecutivo_id,canal,estado_contacto\n"
        ",Campana Masiva,,ana.import@example.com,ejecutivo_1,whatsapp,contactado\n"
    )
    contactos_response = client.post(
        "/api/intelicoop/campanas/contactos/importacion",
        headers=headers,
        files={"file": ("contactos.csv", contactos_csv.encode("utf-8"), "text/csv")},
    )
    assert contactos_response.status_code == 201
    assert contactos_response.json()["importados"] == 1

    seguimientos_csv = (
        "campania_id,campania_nombre,socio_id,socio_email,lista,etapa,conversion,monto_colocado\n"
        ",Campana Masiva,,ana.import@example.com,preferente,convertido,1,5000\n"
    )
    seguimientos_response = client.post(
        "/api/intelicoop/campanas/seguimientos/importacion",
        headers=headers,
        files={"file": ("seguimientos.csv", seguimientos_csv.encode("utf-8"), "text/csv")},
    )
    assert seguimientos_response.status_code == 201
    assert seguimientos_response.json()["importados"] == 1

    prospectos_csv = (
        "nombre,telefono,direccion,fuente,score_propension\n"
        "Prospecto Masivo,555-7999,Zona 9,web,0.66\n"
    )
    prospectos_response = client.post(
        "/api/intelicoop/prospectos/importacion",
        headers=headers,
        files={"file": ("prospectos.csv", prospectos_csv.encode("utf-8"), "text/csv")},
    )
    assert prospectos_response.status_code == 201
    assert prospectos_response.json()["importados"] == 1

    assert client.get("/api/intelicoop/campanas/contactos", headers=headers).status_code == 200
    assert len(client.get("/api/intelicoop/campanas/contactos", headers=headers).json()) == 1
    assert len(client.get("/api/intelicoop/campanas/seguimientos", headers=headers).json()) == 1
    assert len(client.get("/api/intelicoop/prospectos", headers=headers).json()) == 1


def test_segmentacion_resumen_calculates_segments_and_propensities(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    socio_a = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Integral",
            "email": "integral@example.com",
            "telefono": "555-1000",
            "direccion": "Centro",
            "segmento": "gran_ahorrador",
        },
    )
    assert socio_a.status_code == 201
    socio_a_id = socio_a.json()["id"]

    socio_b = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Riesgo",
            "email": "riesgo@example.com",
            "telefono": "555-2000",
            "direccion": "Norte",
            "segmento": "inactivo",
        },
    )
    assert socio_b.status_code == 201
    socio_b_id = socio_b.json()["id"]

    cuenta_a = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_a_id, "tipo": "ahorro", "saldo": 6500},
    )
    assert cuenta_a.status_code == 201
    cuenta_a_id = cuenta_a.json()["id"]

    movimiento_a = client.post(
        "/api/intelicoop/ahorros/transacciones",
        headers=headers,
        json={"cuenta_id": cuenta_a_id, "tipo": "deposito", "monto": 1200},
    )
    assert movimiento_a.status_code == 201

    credito_a = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_a_id,
            "monto": 3000,
            "numero_abonos": 12,
            "periodicidad": "mensual",
            "ingreso_mensual": 9000,
            "deuda_actual": 900,
            "antiguedad_meses": 36,
            "estado": "aprobado",
        },
    )
    assert credito_a.status_code == 201

    campana = client.post(
        "/api/intelicoop/campanas",
        headers=headers,
        json={
            "nombre": "Campana Elite",
            "tipo": "Upsell",
            "fecha_inicio": "2026-03-01T00:00:00",
            "fecha_fin": "2026-03-31T00:00:00",
            "estado": "activa",
        },
    )
    assert campana.status_code == 201
    campana_id = campana.json()["id"]

    contacto_a = client.post(
        "/api/intelicoop/campanas/contactos",
        headers=headers,
        json={
            "campania_id": campana_id,
            "socio_id": socio_a_id,
            "ejecutivo_id": "ejecutivo_1",
            "canal": "whatsapp",
            "estado_contacto": "contactado",
        },
    )
    assert contacto_a.status_code == 201

    seguimiento_a = client.post(
        "/api/intelicoop/campanas/seguimientos",
        headers=headers,
        json={
            "campania_id": campana_id,
            "socio_id": socio_a_id,
            "lista": "premium",
            "etapa": "cerrado",
            "conversion": True,
            "monto_colocado": 1800,
        },
    )
    assert seguimiento_a.status_code == 201

    credito_b = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_b_id,
            "monto": 2500,
            "numero_abonos": 10,
            "periodicidad": "mensual",
            "ingreso_mensual": 3200,
            "deuda_actual": 2400,
            "antiguedad_meses": 4,
            "estado": "mora",
        },
    )
    assert credito_b.status_code == 201

    prospecto = client.post(
        "/api/intelicoop/prospectos",
        headers=headers,
        json={
            "nombre": "Prospecto Alto",
            "telefono": "555-3000",
            "direccion": "Sur",
            "fuente": "referido",
            "score_propension": 0.91,
        },
    )
    assert prospecto.status_code == 201

    materialize = client.post("/api/intelicoop/fundamentos/materializar", headers=headers, json={"cut_type": "daily_close"})
    assert materialize.status_code == 201

    response = client.get("/api/intelicoop/segmentacion/resumen", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["resumen"]["total_socios"] == 2
    assert body["mode"] == "cut_driven"
    assert body["cut_key"] == materialize.json()["cut_key"]
    assert body["segmentos"]
    assert body["segmentos_analiticos"]
    assert body["clusters_financieros"]
    assert body["top_oportunidades"]
    assert body["alertas_tempranas"]
    assert body["prospectos"][0]["score_propension"] == 0.91

    socios = {row["socio_nombre"]: row for row in body["socios"]}
    assert socios["Socio Integral"]["segmento_automatico"] in {"integral_fiel", "crecimiento"}
    assert socios["Socio Integral"]["rfm_segmento"]
    assert socios["Socio Integral"]["cluster_label"]
    assert socios["Socio Integral"]["comercial_score"] > socios["Socio Riesgo"]["comercial_score"]
    assert socios["Socio Riesgo"]["segmento_automatico"] == "alerta_temprana"
    assert socios["Socio Riesgo"]["riesgo_temprano_score"] >= 0.5


def test_analitica_patrones_exposes_rules_anomalies_series_baskets_and_sequences(build_client, strict_intelicoop_access, auth_headers) -> None:
    client = build_client(strict_intelicoop_access)
    headers = auth_headers("Intelicoop", role="admin")

    socio_a = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Patron A",
            "email": "patron.a@example.com",
            "telefono": "555-4100",
            "direccion": "Centro",
            "segmento": "gran_ahorrador",
        },
    )
    assert socio_a.status_code == 201
    socio_a_id = socio_a.json()["id"]

    socio_b = client.post(
        "/api/intelicoop/socios",
        headers=headers,
        json={
            "nombre": "Socio Patron B",
            "email": "patron.b@example.com",
            "telefono": "555-4200",
            "direccion": "Sur",
            "segmento": "inactivo",
        },
    )
    assert socio_b.status_code == 201
    socio_b_id = socio_b.json()["id"]

    cuenta_a1 = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_a_id, "tipo": "ahorro", "saldo": 1800},
    )
    assert cuenta_a1.status_code == 201
    cuenta_a1_id = cuenta_a1.json()["id"]

    cuenta_a2 = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_a_id, "tipo": "aportacion", "saldo": 900},
    )
    assert cuenta_a2.status_code == 201

    cuenta_b = client.post(
        "/api/intelicoop/ahorros/cuentas",
        headers=headers,
        json={"socio_id": socio_b_id, "tipo": "ahorro", "saldo": 500},
    )
    assert cuenta_b.status_code == 201
    cuenta_b_id = cuenta_b.json()["id"]

    tx_ids = []
    for payload in (
        {"cuenta_id": cuenta_a1_id, "tipo": "deposito", "monto": 120},
        {"cuenta_id": cuenta_a1_id, "tipo": "deposito", "monto": 150},
        {"cuenta_id": cuenta_a1_id, "tipo": "deposito", "monto": 200},
        {"cuenta_id": cuenta_a1_id, "tipo": "deposito", "monto": 3200},
        {"cuenta_id": cuenta_b_id, "tipo": "deposito", "monto": 100},
        {"cuenta_id": cuenta_b_id, "tipo": "retiro", "monto": 300},
        {"cuenta_id": cuenta_b_id, "tipo": "retiro", "monto": 200},
    ):
        response = client.post("/api/intelicoop/ahorros/transacciones", headers=headers, json=payload)
        assert response.status_code == 201
        tx_ids.append(response.json()["id"])

    campana = client.post(
        "/api/intelicoop/campanas",
        headers=headers,
        json={
            "nombre": "Campana Patrones",
            "tipo": "Cross Sell",
            "fecha_inicio": "2026-01-01T00:00:00",
            "fecha_fin": "2026-03-31T00:00:00",
            "estado": "activa",
        },
    )
    assert campana.status_code == 201
    campana_id = campana.json()["id"]

    contacto = client.post(
        "/api/intelicoop/campanas/contactos",
        headers=headers,
        json={
            "campania_id": campana_id,
            "socio_id": socio_b_id,
            "ejecutivo_id": "ejecutivo_patrones",
            "canal": "telefono",
            "estado_contacto": "contactado",
        },
    )
    assert contacto.status_code == 201
    contacto_id = contacto.json()["id"]

    seguimiento = client.post(
        "/api/intelicoop/campanas/seguimientos",
        headers=headers,
        json={
            "campania_id": campana_id,
            "socio_id": socio_a_id,
            "lista": "premium",
            "etapa": "cerrado",
            "conversion": True,
            "monto_colocado": 900,
        },
    )
    assert seguimiento.status_code == 201

    credito_a = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_a_id,
            "monto": 2200,
            "numero_abonos": 10,
            "periodicidad": "mensual",
            "ingreso_mensual": 9000,
            "deuda_actual": 800,
            "antiguedad_meses": 24,
            "estado": "aprobado",
        },
    )
    assert credito_a.status_code == 201

    credito_b = client.post(
        "/api/intelicoop/creditos",
        headers=headers,
        json={
            "socio_id": socio_b_id,
            "monto": 2600,
            "numero_abonos": 8,
            "periodicidad": "mensual",
            "ingreso_mensual": 3000,
            "deuda_actual": 2100,
            "antiguedad_meses": 6,
            "estado": "mora",
        },
    )
    assert credito_b.status_code == 201
    credito_b_id = credito_b.json()["credito"]["id"]

    pago_b = client.post(
        "/api/intelicoop/creditos/pagos",
        headers=headers,
        json={"credito_id": credito_b_id, "monto": 300},
    )
    assert pago_b.status_code == 201
    pago_b_id = pago_b.json()["id"]

    now = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        dated_txs = (
            db.query(IntelicoopTransaccion)
            .filter(IntelicoopTransaccion.id.in_(tx_ids))
            .order_by(IntelicoopTransaccion.id.asc())
            .all()
        )
        tx_dates = [
            now - timedelta(days=88),
            now - timedelta(days=63),
            now - timedelta(days=35),
            now - timedelta(days=5),
            now - timedelta(days=70),
            now - timedelta(days=55),
            now - timedelta(days=40),
        ]
        for row, tx_date in zip(dated_txs, tx_dates):
            row.fecha = tx_date

        db.query(IntelicoopContactoCampania).filter(IntelicoopContactoCampania.id == contacto_id).update(
            {"fecha_contacto": now - timedelta(days=20)},
            synchronize_session=False,
        )
        db.query(IntelicoopSeguimientoCampania).filter(IntelicoopSeguimientoCampania.socio_id == socio_a_id).update(
            {"fecha_evento": now - timedelta(days=15)},
            synchronize_session=False,
        )
        db.query(IntelicoopCredito).filter(IntelicoopCredito.id == credito_b_id).update(
            {
                "fecha_creacion": now - timedelta(days=25),
                "fecha_desembolso": now - timedelta(days=120),
                "fecha_vencimiento": now - timedelta(days=45),
            },
            synchronize_session=False,
        )
        db.query(IntelicoopCredito).filter(IntelicoopCredito.socio_id == socio_a_id).update(
            {"fecha_creacion": now - timedelta(days=80)},
            synchronize_session=False,
        )
        db.query(IntelicoopHistorialPago).filter(IntelicoopHistorialPago.id == pago_b_id).update(
            {"fecha": now - timedelta(days=50)},
            synchronize_session=False,
        )
        db.commit()
    finally:
        db.close()

    materialize = client.post("/api/intelicoop/fundamentos/materializar", headers=headers, json={"cut_type": "daily_close"})
    assert materialize.status_code == 201

    response = client.get("/api/intelicoop/analitica/patrones", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "cut_driven"
    assert body["cut_key"] == materialize.json()["cut_key"]
    assert body["reglas_asociacion_productos"]
    assert body["anomalias_transacciones"]
    assert len(body["series_tiempo_captacion_cartera"]) >= 2
    assert body["canastas_productos_frecuentes"]
    assert body["secuencias_previas_mora"]

    association_pairs = {
        (row["antecedente"], row["consecuente"])
        for row in body["reglas_asociacion_productos"]
    }
    assert ("credito", "credito_activo") in association_pairs or ("credito_activo", "cuenta_ahorro") in association_pairs

    anomalies = {row["transaccion_id"]: row for row in body["anomalias_transacciones"]}
    assert tx_ids[3] in anomalies
    assert anomalies[tx_ids[3]]["score_anomalia"] > 0

    month_series = {row["periodo"]: row for row in body["series_tiempo_captacion_cartera"]}
    assert any(row["captacion_neta"] != 0 for row in month_series.values())
    assert any(row["cartera_total"] > 0 for row in month_series.values())

    top_basket = body["canastas_productos_frecuentes"][0]["canasta"]
    assert "cuenta_ahorro" in top_basket
    assert "credito" in top_basket

    sequences = [" > ".join(row["secuencia"]) for row in body["secuencias_previas_mora"]]
    assert any("mora" in row for row in sequences)
    assert any("contacto_sin_conversion" in row or "porcentaje_pagado_bajo" in row for row in sequences)
