from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


EmployeeListHandler = Callable[[Request], dict]
EmployeeCreateHandler = Callable[[Request], Awaitable[dict]]
EmployeeUpdateHandler = Callable[[int, Request], Awaitable[dict]]
EmployeeDeleteHandler = Callable[[int, Request], dict]
EmployeePasswordHandler = Callable[[int, Request], Awaitable[dict]]


def create_employees_router(
    *,
    list_employees: EmployeeListHandler,
    create_employee: EmployeeCreateHandler,
    update_employee: EmployeeUpdateHandler,
    delete_employee: EmployeeDeleteHandler,
    change_employee_password: EmployeePasswordHandler,
) -> APIRouter:
    router = APIRouter()

    @router.get("/multitienda/api/empleados", response_class=JSONResponse)
    def api_list_employees(request: Request):
        return list_employees(request)

    @router.post("/multitienda/api/empleados", response_class=JSONResponse)
    async def api_create_employee(request: Request):
        return await create_employee(request)

    @router.put("/multitienda/api/empleados/{employee_id}", response_class=JSONResponse)
    async def api_update_employee(employee_id: int, request: Request):
        return await update_employee(employee_id, request)

    @router.delete("/multitienda/api/empleados/{employee_id}", response_class=JSONResponse)
    def api_delete_employee(employee_id: int, request: Request):
        return delete_employee(employee_id, request)

    @router.post("/multitienda/api/empleados/{employee_id}/password", response_class=JSONResponse)
    async def api_change_employee_password(employee_id: int, request: Request):
        return await change_employee_password(employee_id, request)

    return router
