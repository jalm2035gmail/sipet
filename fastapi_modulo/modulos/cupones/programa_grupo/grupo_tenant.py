"""
programa_grupo/grupo_tenant.py
-------------------------------
Módulo OPT-IN: agrupa tiendas bajo un programa de puntos compartido.
Las tiendas que no se unen a ningún grupo no se ven afectadas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
import uuid

from cupones_fidelizacion.repositorio import RepositorioBase
from cupones_fidelizacion.multitienda.tenant import TenantService


@dataclass
class GrupoTenant:
    nombre: str
    tenant_ids: List[str] = field(default_factory=list)
    proporcion_puntos: Dict[str, float] = field(default_factory=dict)
    activo: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)


class GrupoRepositorio(RepositorioBase[GrupoTenant]):

    def obtener_por_tenant(self, tenant_id: str) -> Optional[GrupoTenant]:
        for grupo in self._store.values():
            if tenant_id in grupo.tenant_ids and grupo.activo:
                return grupo
        return None


class GrupoTenantService:
    """
    Crea y gestiona grupos de tiendas con programa de puntos compartido.
    """

    def __init__(
        self,
        tenant_service: TenantService,
        repo: Optional[GrupoRepositorio] = None,
    ):
        self._tenant_svc = tenant_service
        self._repo = repo or GrupoRepositorio()

    def crear_grupo(
        self,
        nombre: str,
        tenant_ids: List[str],
        proporcion_puntos: Optional[Dict[str, float]] = None,
    ) -> GrupoTenant:
        """
        Crea un grupo de tiendas.
        proporcion_puntos: dict {tenant_id: multiplicador}
        ej. {'tienda_a': 1.0, 'tienda_b': 0.5} → Tienda B da la mitad de puntos.
        """
        for tid in tenant_ids:
            self._tenant_svc.verificar_activa(tid)
            if self._repo.obtener_por_tenant(tid):
                raise ValueError(
                    f"La tienda '{tid}' ya pertenece a otro grupo."
                )

        proporciones = proporcion_puntos or {tid: 1.0 for tid in tenant_ids}

        grupo = GrupoTenant(
            nombre=nombre,
            tenant_ids=tenant_ids,
            proporcion_puntos=proporciones,
        )
        return self._repo.guardar(grupo)

    def agregar_tienda(
        self, grupo_id: str, tenant_id: str, proporcion: float = 1.0
    ) -> GrupoTenant:
        self._tenant_svc.verificar_activa(tenant_id)
        if self._repo.obtener_por_tenant(tenant_id):
            raise ValueError(f"La tienda '{tenant_id}' ya pertenece a un grupo.")
        grupo = self._repo.obtener(grupo_id)
        if not grupo:
            raise ValueError(f"Grupo '{grupo_id}' no encontrado.")
        grupo.tenant_ids.append(tenant_id)
        grupo.proporcion_puntos[tenant_id] = proporcion
        return self._repo.guardar(grupo)

    def remover_tienda(self, grupo_id: str, tenant_id: str) -> GrupoTenant:
        grupo = self._repo.obtener(grupo_id)
        if not grupo:
            raise ValueError(f"Grupo '{grupo_id}' no encontrado.")
        grupo.tenant_ids = [tid for tid in grupo.tenant_ids if tid != tenant_id]
        grupo.proporcion_puntos.pop(tenant_id, None)
        return self._repo.guardar(grupo)

    def obtener_grupo_de_tienda(self, tenant_id: str) -> Optional[GrupoTenant]:
        return self._repo.obtener_por_tenant(tenant_id)

    def listar_grupos(self) -> List[GrupoTenant]:
        return self._repo.listar_todos()

    def desactivar_grupo(self, grupo_id: str) -> GrupoTenant:
        grupo = self._repo.obtener(grupo_id)
        if not grupo:
            raise ValueError(f"Grupo '{grupo_id}' no encontrado.")
        return self._repo.actualizar(grupo_id, activo=False)
