from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from fastapi_modulo.core.db import MAIN


class IntelicoopSocio(MAIN):
    __tablename__ = "intelicoop_socios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    telefono = Column(String(30), nullable=False, default="")
    direccion = Column(String(255), nullable=False, default="")
    segmento = Column(String(30), nullable=False, default="inactivo")
    fecha_nacimiento = Column(DateTime, nullable=True, default=None)
    genero = Column(String(20), nullable=False, default="")
    estado_civil = Column(String(30), nullable=False, default="")
    nivel_educativo = Column(String(60), nullable=False, default="")
    ocupacion = Column(String(120), nullable=False, default="")
    sector_economico = Column(String(120), nullable=False, default="")
    ubicacion_estado = Column(String(120), nullable=False, default="")
    ubicacion_municipio = Column(String(120), nullable=False, default="")
    tipo_socio = Column(String(30), nullable=False, default="activo")
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopCredito(MAIN):
    __tablename__ = "intelicoop_creditos"

    id = Column(Integer, primary_key=True, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    monto = Column(Float, nullable=False, default=0)
    plazo = Column(Integer, nullable=False, default=1)
    numero_abonos = Column(Integer, nullable=False, default=1)
    periodicidad = Column(String(20), nullable=False, default="mensual")
    ingreso_mensual = Column(Float, nullable=False, default=0)
    deuda_actual = Column(Float, nullable=False, default=0)
    antiguedad_meses = Column(Integer, nullable=False, default=0)
    tasa = Column(Float, nullable=False, default=0)
    estado = Column(String(20), nullable=False, default="solicitado")
    dias_mora_actual = Column(Integer, nullable=False, default=0)
    max_dias_mora = Column(Integer, nullable=False, default=0)
    num_reestructuras = Column(Integer, nullable=False, default=0)
    fecha_desembolso = Column(DateTime, nullable=True, default=None)
    fecha_vencimiento = Column(DateTime, nullable=True, default=None)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopHistorialPago(MAIN):
    __tablename__ = "intelicoop_historial_pagos"

    id = Column(Integer, primary_key=True, index=True)
    credito_id = Column(Integer, ForeignKey("intelicoop_creditos.id"), nullable=False, index=True)
    monto = Column(Float, nullable=False, default=0)
    pago_puntual = Column(Integer, nullable=False, default=1)
    dias_atraso = Column(Integer, nullable=False, default=0)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopCuenta(MAIN):
    __tablename__ = "intelicoop_cuentas"

    id = Column(Integer, primary_key=True, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False, default="ahorro")
    saldo = Column(Float, nullable=False, default=0)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopTransaccion(MAIN):
    __tablename__ = "intelicoop_transacciones"

    id = Column(Integer, primary_key=True, index=True)
    cuenta_id = Column(Integer, ForeignKey("intelicoop_cuentas.id"), nullable=False, index=True)
    monto = Column(Float, nullable=False, default=0)
    tipo = Column(String(20), nullable=False, default="deposito")
    canal = Column(String(30), nullable=False, default="")
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopCampania(MAIN):
    __tablename__ = "intelicoop_campanas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    tipo = Column(String(100), nullable=False)
    fecha_inicio = Column(DateTime, nullable=True, default=None)
    fecha_fin = Column(DateTime, nullable=True, default=None)
    estado = Column(String(20), nullable=False, default="borrador")
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopProspecto(MAIN):
    __tablename__ = "intelicoop_prospectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    telefono = Column(String(30), nullable=False, default="")
    direccion = Column(String(255), nullable=False, default="")
    fuente = Column(String(100), nullable=False, default="")
    score_propension = Column(Float, nullable=False, default=0)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopContactoCampania(MAIN):
    __tablename__ = "intelicoop_contactos_campania"

    id = Column(Integer, primary_key=True, index=True)
    campania_id = Column(Integer, ForeignKey("intelicoop_campanas.id"), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    ejecutivo_id = Column(String(60), nullable=False, default="ejecutivo_general")
    canal = Column(String(30), nullable=False, default="telefono")
    estado_contacto = Column(String(20), nullable=False, default="pendiente")
    fecha_contacto = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopSeguimientoCampania(MAIN):
    __tablename__ = "intelicoop_seguimiento_campania"

    id = Column(Integer, primary_key=True, index=True)
    campania_id = Column(Integer, ForeignKey("intelicoop_campanas.id"), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    lista = Column(String(30), nullable=False, default="general")
    etapa = Column(String(30), nullable=False, default="contactado")
    conversion = Column(Integer, nullable=False, default=0)
    monto_colocado = Column(Float, nullable=False, default=0)
    fecha_evento = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopScoringResult(MAIN):
    __tablename__ = "intelicoop_scoring_results"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(String(120), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=True, index=True)
    credito_id = Column(Integer, ForeignKey("intelicoop_creditos.id"), nullable=True, index=True)
    ingreso_mensual = Column(Float, nullable=False, default=0)
    deuda_actual = Column(Float, nullable=False, default=0)
    antiguedad_meses = Column(Integer, nullable=False, default=0)
    score = Column(Float, nullable=False, default=0)
    recomendacion = Column(String(30), nullable=False, default="evaluar")
    riesgo = Column(String(10), nullable=False, default="medio")
    model_version = Column(String(60), nullable=False, default="intelicoop_scoring_v1")
    confianza = Column(Float, nullable=True, default=None)
    motor = Column(String(20), nullable=False, default="reglas")
    explicacion_json = Column(Text, nullable=False, default="{}")
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopScoringTraza(MAIN):
    __tablename__ = "intelicoop_scoring_trazas"

    id = Column(Integer, primary_key=True, index=True)
    scoring_result_id = Column(Integer, ForeignKey("intelicoop_scoring_results.id"), nullable=True, index=True)
    solicitud_id = Column(String(120), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=True, index=True)
    credito_id = Column(Integer, ForeignKey("intelicoop_creditos.id"), nullable=True, index=True)
    inputs_json = Column(Text, nullable=False, default="{}")
    features_calculados_json = Column(Text, nullable=False, default="{}")
    outputs_json = Column(Text, nullable=False, default="{}")
    razones_json = Column(Text, nullable=False, default="[]")
    reglas_aplicadas_json = Column(Text, nullable=False, default="[]")
    confianza = Column(Float, nullable=False, default=0)
    tiempo_ms = Column(Integer, nullable=False, default=0)
    motor = Column(String(20), nullable=False, default="reglas")
    model_version = Column(String(60), nullable=False, default="intelicoop_scoring_v1")
    traza_version = Column(String(40), nullable=False, default="intelicoop_traza_v1")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopModelVersionRegistry(MAIN):
    __tablename__ = "intelicoop_model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_key = Column(String(60), nullable=False, unique=True, index=True)
    algoritmo = Column(String(80), nullable=False, default="reglas")
    descripcion = Column(Text, nullable=False, default="")
    features_json = Column(Text, nullable=False, default="[]")
    umbrales_json = Column(Text, nullable=False, default="{}")
    metricas_json = Column(Text, nullable=False, default="{}")
    activo = Column(Integer, nullable=False, default=1)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_deprecado = Column(DateTime, nullable=True, default=None)


class IntelicoopAnalyticCut(MAIN):
    __tablename__ = "intelicoop_analytic_cuts"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, unique=True, index=True)
    cut_type = Column(String(20), nullable=False, default="daily_close")
    cut_date = Column(DateTime, nullable=False, index=True)
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False, index=True)
    transactional_tables_json = Column(Text, nullable=False, default="[]")
    analytical_tables_json = Column(Text, nullable=False, default="[]")
    bronze_manifest_json = Column(Text, nullable=False, default="{}")
    silver_manifest_json = Column(Text, nullable=False, default="{}")
    gold_manifest_json = Column(Text, nullable=False, default="{}")
    ml_manifest_json = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="ready")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopDataQualitySnapshot(MAIN):
    __tablename__ = "intelicoop_data_quality_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    scope = Column(String(60), nullable=False, index=True)
    rule_key = Column(String(120), nullable=False, index=True)
    total_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pass", index=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopSocioFeatureSnapshot(MAIN):
    __tablename__ = "intelicoop_socio_feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    socio_nombre = Column(String(150), nullable=False, default="")
    segmento_actual = Column(String(30), nullable=False, default="inactivo")
    # créditos
    creditos_total = Column(Integer, nullable=False, default=0)
    creditos_activos = Column(Integer, nullable=False, default=0)
    creditos_mora = Column(Integer, nullable=False, default=0)
    monto_creditos_total = Column(Float, nullable=False, default=0)
    pagos_total = Column(Float, nullable=False, default=0)
    tasa_cumplimiento_pagos = Column(Float, nullable=False, default=0)
    ratio_deuda_ingreso = Column(Float, nullable=False, default=0)
    # cuentas / ahorros
    cuentas_total = Column(Integer, nullable=False, default=0)
    saldo_cuentas_total = Column(Float, nullable=False, default=0)
    transacciones_total = Column(Integer, nullable=False, default=0)
    # campañas
    campanas_participadas = Column(Integer, nullable=False, default=0)
    campanas_convertidas = Column(Integer, nullable=False, default=0)
    respuesta_por_canal_json = Column(Text, nullable=False, default="{}")
    dias_desde_ultimo_contacto = Column(Integer, nullable=False, default=0)
    # perfil
    dias_como_socio = Column(Integer, nullable=False, default=0)
    edad = Column(Integer, nullable=False, default=0)
    num_productos = Column(Integer, nullable=False, default=0)
    diversificacion = Column(Float, nullable=False, default=0)
    profundidad_relacion = Column(Float, nullable=False, default=0)
    # scoring
    score_propension_referencia = Column(Float, nullable=False, default=0)
    score_abandono = Column(Float, nullable=False, default=0)
    score_fidelidad = Column(Float, nullable=False, default=0)
    score_scoring_reciente = Column(Float, nullable=False, default=0)
    riesgo_scoring_reciente = Column(String(10), nullable=False, default="sin_dato")
    estabilidad_financiera = Column(Float, nullable=False, default=0)
    tasa_respuesta = Column(Float, nullable=False, default=0)
    canal_preferido = Column(String(30), nullable=False, default="")
    sensibilidad_comercial = Column(Float, nullable=False, default=0)
    numero_alertas = Column(Integer, nullable=False, default=0)
    tendencia_riesgo = Column(String(20), nullable=False, default="estable")
    reincidencia = Column(Integer, nullable=False, default=0)
    abandono_90_dias = Column(Integer, nullable=False, default=0)
    responde_campania = Column(Integer, nullable=False, default=0)
    up_sell_exitoso = Column(Integer, nullable=False, default=0)
    recompra_credito = Column(Integer, nullable=False, default=0)
    feature_version = Column(String(40), nullable=False, default="intelicoop_features_v1")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopCreditoFeatureSnapshot(MAIN):
    __tablename__ = "intelicoop_credito_feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    credito_id = Column(Integer, ForeignKey("intelicoop_creditos.id"), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    monto = Column(Float, nullable=False, default=0)
    plazo = Column(Integer, nullable=False, default=0)
    numero_abonos = Column(Integer, nullable=False, default=0)
    periodicidad = Column(String(20), nullable=False, default="mensual")
    estado = Column(String(20), nullable=False, default="solicitado")
    num_pagos = Column(Integer, nullable=False, default=0)
    monto_pagado = Column(Float, nullable=False, default=0)
    saldo_pendiente = Column(Float, nullable=False, default=0)
    porcentaje_pagado = Column(Float, nullable=False, default=0)
    ratio_pagado = Column(Float, nullable=False, default=0)
    tasa_cumplimiento = Column(Float, nullable=False, default=0)
    ratio_deuda_ingreso = Column(Float, nullable=False, default=0)
    creditos_activos = Column(Integer, nullable=False, default=0)
    creditos_en_mora = Column(Integer, nullable=False, default=0)
    cumplimiento_pagos = Column(Float, nullable=False, default=0)
    exposicion_total = Column(Float, nullable=False, default=0)
    en_mora = Column(Integer, nullable=False, default=0)
    dias_desde_desembolso = Column(Integer, nullable=True, default=None)
    dias_hasta_vencimiento = Column(Integer, nullable=True, default=None)
    default_30 = Column(Integer, nullable=False, default=0)
    default_60 = Column(Integer, nullable=False, default=0)
    default_90 = Column(Integer, nullable=False, default=0)
    convirtio_credito = Column(Integer, nullable=False, default=0)
    up_sell_exitoso = Column(Integer, nullable=False, default=0)
    recompra_credito = Column(Integer, nullable=False, default=0)
    feature_version = Column(String(40), nullable=False, default="intelicoop_features_v1")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopAhorroFeatureSnapshot(MAIN):
    __tablename__ = "intelicoop_ahorro_feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    cuenta_id = Column(Integer, ForeignKey("intelicoop_cuentas.id"), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("intelicoop_socios.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False, default="ahorro")
    saldo_actual = Column(Float, nullable=False, default=0)
    num_transacciones = Column(Integer, nullable=False, default=0)
    monto_depositos = Column(Float, nullable=False, default=0)
    monto_retiros = Column(Float, nullable=False, default=0)
    promedio_deposito = Column(Float, nullable=False, default=0)
    promedio_retiro = Column(Float, nullable=False, default=0)
    saldo_promedio_30d = Column(Float, nullable=False, default=0)
    saldo_promedio_60d = Column(Float, nullable=False, default=0)
    saldo_promedio_90d = Column(Float, nullable=False, default=0)
    frecuencia_transaccional = Column(Float, nullable=False, default=0)
    captacion_neta_mensual = Column(Float, nullable=False, default=0)
    volatilidad_saldo = Column(Float, nullable=False, default=0)
    estacionalidad_ahorro = Column(String(20), nullable=False, default="estable")
    dias_sin_movimiento = Column(Integer, nullable=False, default=0)
    tendencia_saldo = Column(String(20), nullable=False, default="estable")
    feature_version = Column(String(40), nullable=False, default="intelicoop_features_v1")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopCampaniaFeatureSnapshot(MAIN):
    __tablename__ = "intelicoop_campania_feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    campania_id = Column(Integer, ForeignKey("intelicoop_campanas.id"), nullable=False, index=True)
    estado = Column(String(20), nullable=False, default="borrador")
    total_contactos = Column(Integer, nullable=False, default=0)
    total_seguimientos = Column(Integer, nullable=False, default=0)
    conversiones = Column(Integer, nullable=False, default=0)
    tasa_conversion = Column(Float, nullable=False, default=0)
    monto_colocado = Column(Float, nullable=False, default=0)
    duracion_dias = Column(Integer, nullable=True, default=None)
    feature_version = Column(String(40), nullable=False, default="intelicoop_features_v1")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopProspectoFeatureSnapshot(MAIN):
    __tablename__ = "intelicoop_prospecto_feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    prospecto_id = Column(Integer, ForeignKey("intelicoop_prospectos.id"), nullable=False, index=True)
    score_propension = Column(Float, nullable=False, default=0)
    fuente = Column(String(100), nullable=False, default="")
    dias_como_prospecto = Column(Integer, nullable=False, default=0)
    en_campana = Column(Integer, nullable=False, default=0)
    convirtio_credito = Column(Integer, nullable=False, default=0)
    responde_campania = Column(Integer, nullable=False, default=0)
    feature_version = Column(String(40), nullable=False, default="intelicoop_features_v1")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopKpiSnapshot(MAIN):
    __tablename__ = "intelicoop_kpi_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    kpi_key = Column(String(120), nullable=False, index=True)
    metric_group = Column(String(60), nullable=False, default="general", index=True)
    metric_value = Column(Float, nullable=False, default=0)
    metric_label = Column(String(160), nullable=False, default="")
    metric_type = Column(String(20), nullable=False, default="observado")
    semaforo = Column(String(20), nullable=False, default="sin_umbral")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopCohorteSnapshot(MAIN):
    __tablename__ = "intelicoop_cohorte_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=False, index=True)
    cut_date = Column(DateTime, nullable=False, index=True)
    dimension = Column(String(60), nullable=False, index=True)
    bucket = Column(String(40), nullable=False, index=True)
    metric_key = Column(String(80), nullable=False, index=True)
    metric_value = Column(Float, nullable=False, default=0)
    n_records = Column(Integer, nullable=False, default=0)
    metric_type = Column(String(20), nullable=False, default="observado")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopBatchJobState(MAIN):
    __tablename__ = "intelicoop_batch_job_states"

    id = Column(Integer, primary_key=True, index=True)
    job_key = Column(String(80), nullable=False, unique=True, index=True)
    job_label = Column(String(160), nullable=False, default="")
    cadence_minutes = Column(Integer, nullable=False, default=1440)
    enabled = Column(Integer, nullable=False, default=1)
    last_run_at = Column(DateTime, nullable=True, default=None)
    next_run_at = Column(DateTime, nullable=True, default=None)
    last_status = Column(String(20), nullable=False, default="pending")
    config_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopBatchRun(MAIN):
    __tablename__ = "intelicoop_batch_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_key = Column(String(120), nullable=False, unique=True, index=True)
    job_key = Column(String(80), nullable=False, index=True)
    trigger_type = Column(String(20), nullable=False, default="manual")
    cut_key = Column(String(40), nullable=True, index=True, default=None)
    status = Column(String(20), nullable=False, default="running")
    quality_status = Column(String(20), nullable=False, default="pending")
    records_processed = Column(Integer, nullable=False, default=0)
    records_created = Column(Integer, nullable=False, default=0)
    metrics_json = Column(Text, nullable=False, default="{}")
    quality_summary_json = Column(Text, nullable=False, default="{}")
    error_message = Column(Text, nullable=False, default="")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True, default=None)


class IntelicoopBatchAlert(MAIN):
    __tablename__ = "intelicoop_batch_alerts"

    id = Column(Integer, primary_key=True, index=True)
    batch_run_id = Column(Integer, ForeignKey("intelicoop_batch_runs.id"), nullable=True, index=True)
    cut_key = Column(String(40), nullable=True, index=True, default=None)
    alert_type = Column(String(80), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="media", index=True)
    entity_type = Column(String(40), nullable=False, default="socio", index=True)
    entity_id = Column(Integer, nullable=True, index=True, default=None)
    entity_label = Column(String(160), nullable=False, default="")
    score = Column(Float, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="open", index=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopGovernanceSnapshot(MAIN):
    __tablename__ = "intelicoop_governance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=True, index=True, default=None)
    model_version = Column(String(60), nullable=False, default="intelicoop_scoring_v1", index=True)
    monitoring_json = Column(Text, nullable=False, default="{}")
    drift_json = Column(Text, nullable=False, default="{}")
    explainability_json = Column(Text, nullable=False, default="{}")
    governance_status = Column(String(20), nullable=False, default="pass", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopModelDriftSnapshot(MAIN):
    __tablename__ = "intelicoop_model_drift_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    cut_key = Column(String(40), nullable=True, index=True, default=None)
    model_version = Column(String(60), nullable=False, default="intelicoop_scoring_v1", index=True)
    feature_key = Column(String(80), nullable=False, index=True)
    baseline_value = Column(Float, nullable=False, default=0)
    current_value = Column(Float, nullable=False, default=0)
    drift_score = Column(Float, nullable=False, default=0)
    drift_level = Column(String(20), nullable=False, default="bajo", index=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopModelRecalibration(MAIN):
    __tablename__ = "intelicoop_model_recalibrations"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(60), nullable=False, default="intelicoop_scoring_v1", index=True)
    trigger_reason = Column(String(120), nullable=False, default="manual", index=True)
    status = Column(String(20), nullable=False, default="proposed", index=True)
    notes = Column(Text, nullable=False, default="")
    before_metrics_json = Column(Text, nullable=False, default="{}")
    after_metrics_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopAuditLog(MAIN):
    __tablename__ = "intelicoop_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(60), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True, default=None)
    actor = Column(String(120), nullable=False, default="system", index=True)
    model_version = Column(String(60), nullable=False, default="", index=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntelicoopBusinessRule(MAIN):
    __tablename__ = "intelicoop_business_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String(80), nullable=False, unique=True, index=True)
    rule_label = Column(String(160), nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    severity = Column(String(20), nullable=False, default="media", index=True)
    enabled = Column(Integer, nullable=False, default=1)
    threshold_value = Column(Float, nullable=True, default=None)
    config_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
