"""Controladores del backend web.

Este paquete no debe importar routers en tiempo de carga para evitar ciclos
entre auth, backend_auth y shell durante el arranque.
"""

__all__: list[str] = []
