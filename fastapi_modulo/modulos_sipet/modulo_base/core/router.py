from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, Response


class ModuleRouterBuilder:
    def __init__(
        self,
        *,
        access_dependency: Callable,
        init_module: Callable[[], None] | None = None,
    ) -> None:
        self.access_dependency = access_dependency
        self.init_module = init_module

    def build_root_router(self, routers: Sequence[APIRouter]) -> APIRouter:
        @asynccontextmanager
        async def lifespan(_: APIRouter):
            if self.init_module:
                self.init_module()
            yield

        router = APIRouter(
            dependencies=[Depends(self.access_dependency)],
            lifespan=lifespan,
        )
        for child in routers:
            router.include_router(child)
        return router

    @staticmethod
    def build_asset_router(
        *,
        css_endpoint: Callable[[], Response],
        js_endpoint: Callable[[], Response],
        assets_prefix: str,
        asset_basename: str,
    ) -> APIRouter:
        router = APIRouter()
        router.get(f"{assets_prefix}/{asset_basename}.css")(css_endpoint)
        router.get(f"{assets_prefix}/{asset_basename}.js")(js_endpoint)
        return router
