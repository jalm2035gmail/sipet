from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class ModuleConfig:
    key: str
    name: str
    base_path: Path
    route: str
    api_prefix: str
    uses_migrations: bool = True
    requires_data_bootstrap: bool = False
    requires_seeds: bool = False
    allow_create_all_in_dev: bool = True
    template_name: str = "base_page.html"
    navbar_name: str = "navbar.html"
    sidebar_name: str = "sidebar.html"
    assets_prefix: str = ""
    description: str = ""
    sections: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        assets_prefix = self.assets_prefix or f"{self.api_prefix}/assets"
        object.__setattr__(self, "assets_prefix", assets_prefix.rstrip("/"))
        object.__setattr__(self, "base_path", Path(self.base_path).resolve())

    @property
    def views_dir(self) -> Path:
        return self.base_path / "vistas"

    @property
    def static_dir(self) -> Path:
        return self.base_path / "static"

    @property
    def migrations_dir(self) -> Path:
        return self.base_path / "migrations"

    @property
    def migration_versions_dir(self) -> Path:
        return self.migrations_dir / "versions"

    @property
    def css_path(self) -> Path:
        return self.static_dir / "css" / f"{self.key}.css"

    @property
    def js_path(self) -> Path:
        return self.static_dir / "js" / f"{self.key}.js"


class BaseModule(ABC):
    def __init__(self, config: ModuleConfig, permissions: list[str] | None = None) -> None:
        self.config = config
        self.name = config.name
        self.route = config.route
        self.permissions = list(permissions or [])
        self.uses_migrations = config.uses_migrations
        self.requires_data_bootstrap = config.requires_data_bootstrap
        self.requires_seeds = config.requires_seeds

    @abstractmethod
    def init(self) -> None:
        ...

    @abstractmethod
    def register_routes(self, app: Any) -> None:
        ...

    @abstractmethod
    def register_assets(self) -> None:
        ...
