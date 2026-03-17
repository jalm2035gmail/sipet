# -*- coding: utf-8 -*-
"""
Utilidades para la identidad de login.
"""
from typing import Dict

from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import get_login_identity_context as _get_login_identity_context


def get_login_identity_context() -> Dict[str, str]:
    return _get_login_identity_context()
