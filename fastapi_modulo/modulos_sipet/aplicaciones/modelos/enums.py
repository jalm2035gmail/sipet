from enum import Enum


class ProtocolStatus(str, Enum):
    OK = "ok"
    MISSING = "missing"


__all__ = ["ProtocolStatus"]
