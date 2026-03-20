from enum import Enum


class DashboardLayout(str, Enum):
    GRID = "grid"
    LIST = "list"


class DashboardTheme(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"
