"""
validacion/antiabuso.py
-----------------------
Detecta patrones sospechosos de uso de cupones y puntos.
Opera a nivel de tenant (fraude interno) y entre tenants (fraude cruzado).
"""

from datetime import datetime, timedelta
from typing import List, Optional

from cupones_fidelizacion.cupones.validador import RegistroUsoRepositorio
from cupones_fidelizacion.excepciones import SospechaDeFraude


class ConfiguracionAntiabuso:
    """Umbrales configurables por tenant."""
    max_usos_por_cliente_por_hora: int = 3
    max_usos_globales_por_minuto: int = 50
    max_cupones_distintos_por_cliente_por_dia: int = 10
    habilitar_deteccion_cruzada: bool = True


class AntiAbusoService:
    """
    Analiza el historial de usos para detectar comportamientos anómalos.
    Puede bloquear preventivamente o solo emitir alertas.
    """

    def __init__(
        self,
        uso_repo: Optional[RegistroUsoRepositorio] = None,
        config: Optional[ConfiguracionAntiabuso] = None,
    ):
        self._uso_repo = uso_repo or RegistroUsoRepositorio()
        self._config = config or ConfiguracionAntiabuso()
        self._alertas: List[dict] = []  # En prod: persistir en BD o enviar a monitoreo

    # ------------------------------------------------------------------
    # Verificaciones preventivas (llamar antes de aplicar cupón)
    # ------------------------------------------------------------------

    def verificar_cliente(
        self,
        tenant_id: str,
        cliente_id: str,
        cupon_id: str,
        ahora: Optional[datetime] = None,
        bloquear: bool = True,
    ) -> None:
        """
        Verifica si el cliente supera los umbrales de uso.
        Si bloquear=True lanza SospechaDeFraude, si no solo registra alerta.
        """
        ahora = ahora or datetime.utcnow()
        alertas = []

        # Usos del cliente en la última hora
        hace_una_hora = ahora - timedelta(hours=1)
        usos_recientes = [
            u for u in self._uso_repo.filtrar(tenant_id=tenant_id, cliente_id=cliente_id)
            if u.creado_en >= hace_una_hora
        ]
        if len(usos_recientes) >= self._config.max_usos_por_cliente_por_hora:
            alertas.append(
                f"Cliente '{cliente_id}' ha usado {len(usos_recientes)} cupones "
                f"en la última hora (límite: {self._config.max_usos_por_cliente_por_hora})."
            )

        # Cupones distintos usados hoy
        inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        usos_hoy = [
            u for u in self._uso_repo.filtrar(tenant_id=tenant_id, cliente_id=cliente_id)
            if u.creado_en >= inicio_dia
        ]
        cupones_distintos = {u.cupon_id for u in usos_hoy}
        if len(cupones_distintos) >= self._config.max_cupones_distintos_por_cliente_por_dia:
            alertas.append(
                f"Cliente '{cliente_id}' ha usado {len(cupones_distintos)} cupones distintos hoy."
            )

        if alertas:
            self._registrar_alerta(tenant_id, cliente_id, alertas)
            if bloquear:
                raise SospechaDeFraude(
                    f"Actividad sospechosa detectada: {'; '.join(alertas)}"
                )

    def verificar_volumen_global(
        self,
        tenant_id: str,
        ahora: Optional[datetime] = None,
    ) -> None:
        """
        Detecta un spike anormal de usos de cupones a nivel de tienda.
        Útil para detectar bots o campañas de abuso masivo.
        """
        ahora = ahora or datetime.utcnow()
        hace_un_minuto = ahora - timedelta(minutes=1)

        usos_recientes = [
            u for u in self._uso_repo.filtrar(tenant_id=tenant_id)
            if u.creado_en >= hace_un_minuto
        ]

        if len(usos_recientes) >= self._config.max_usos_globales_por_minuto:
            msg = (
                f"Volumen anormal: {len(usos_recientes)} usos de cupones "
                f"en el último minuto en la tienda '{tenant_id}'."
            )
            self._registrar_alerta(tenant_id, "SISTEMA", [msg])
            raise SospechaDeFraude(msg)

    def detectar_cliente_multi_tenant(
        self,
        cliente_id: str,
        ahora: Optional[datetime] = None,
    ) -> Optional[dict]:
        """
        Detección cruzada: identifica un cliente que abusa de cupones
        de 'primera compra' en múltiples tiendas.
        Solo ejecutar si habilitar_deteccion_cruzada=True.
        """
        if not self._config.habilitar_deteccion_cruzada:
            return None

        ahora = ahora or datetime.utcnow()
        hace_7_dias = ahora - timedelta(days=7)

        todos_usos = [
            u for u in self._uso_repo.listar_todos()
            if u.cliente_id == cliente_id and u.creado_en >= hace_7_dias
        ]

        tenants_usados = {u.tenant_id for u in todos_usos}

        if len(tenants_usados) >= 5:
            alerta = {
                "cliente_id": cliente_id,
                "tenants_involucrados": list(tenants_usados),
                "usos_totales": len(todos_usos),
                "periodo_dias": 7,
                "tipo": "abuso_multi_tienda",
            }
            self._alertas.append(alerta)
            return alerta

        return None

    # ------------------------------------------------------------------
    # Consulta de alertas
    # ------------------------------------------------------------------

    def obtener_alertas(self, tenant_id: Optional[str] = None) -> List[dict]:
        if tenant_id:
            return [a for a in self._alertas if a.get("tenant_id") == tenant_id]
        return list(self._alertas)

    def limpiar_alertas(self) -> None:
        self._alertas.clear()

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _registrar_alerta(
        self, tenant_id: str, cliente_id: str, mensajes: List[str]
    ) -> None:
        self._alertas.append({
            "tenant_id": tenant_id,
            "cliente_id": cliente_id,
            "mensajes": mensajes,
            "timestamp": datetime.utcnow().isoformat(),
        })
