"""
repositorio.py
--------------
Repositorios en memoria que simulan la capa de persistencia.
En producción, reemplaza estos repositorios por implementaciones
que se conecten a tu base de datos (SQLAlchemy, MongoDB, etc.).
Todos los repositorios siguen la misma interfaz base.
"""

from typing import Dict, List, Optional, TypeVar, Generic
from dataclasses import asdict
import copy

T = TypeVar("T")


class RepositorioBase(Generic[T]):
    """Repositorio genérico en memoria."""

    def __init__(self):
        self._store: Dict[str, T] = {}

    def guardar(self, entidad: T) -> T:
        self._store[entidad.id] = copy.deepcopy(entidad)
        return entidad

    def obtener(self, id: str) -> Optional[T]:
        return copy.deepcopy(self._store.get(id))

    def eliminar(self, id: str) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False

    def listar_todos(self) -> List[T]:
        return [copy.deepcopy(v) for v in self._store.values()]

    def filtrar(self, **kwargs) -> List[T]:
        """Filtra entidades por atributos exactos."""
        resultado = []
        for entidad in self._store.values():
            if all(getattr(entidad, k, None) == v for k, v in kwargs.items()):
                resultado.append(copy.deepcopy(entidad))
        return resultado

    def actualizar(self, id: str, **campos) -> Optional[T]:
        entidad = self._store.get(id)
        if not entidad:
            return None
        for k, v in campos.items():
            if hasattr(entidad, k):
                setattr(entidad, k, v)
        self._store[id] = entidad
        return copy.deepcopy(entidad)

    def contar(self) -> int:
        return len(self._store)
