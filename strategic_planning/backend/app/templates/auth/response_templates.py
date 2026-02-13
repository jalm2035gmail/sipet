from typing import Any, Dict

from app.templates.api import ApiResponseTemplate
from app.templates.components.buttons import ButtonTemplate
from app.templates.components.cards import CardTemplate


class AuthResponseTemplates:
    """Templates para respuestas de autenticación"""

    @staticmethod
    def login_success(user_data: Dict[str, Any], tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Template para respuesta de login exitoso"""
        return ApiResponseTemplate.success(
            data={"user": user_data, "tokens": tokens},
            message="Inicio de sesión exitoso",
            metadata={
                "next_actions": [
                    ButtonTemplate.primary("Ir al Dashboard", url="/dashboard"),
                    ButtonTemplate.secondary("Ver Perfil", url="/profile"),
                ],
                "security_notes": [
                    "Guarda tus tokens en un lugar seguro",
                    "El access token expira en 30 minutos",
                    "Usa el refresh token para obtener nuevos tokens",
                ],
            },
        )

    @staticmethod
    def registration_success(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template para respuesta de registro exitoso"""
        return ApiResponseTemplate.success(
            data=user_data,
            message="Registro exitoso. Por favor verifica tu email.",
            status_code=201,
            metadata={
                "requires_verification": True,
                "next_steps": [
                    "Revisa tu bandeja de entrada",
                    "Haz clic en el enlace de verificación",
                    "Inicia sesión con tus credenciales",
                ],
                "actions": [
                    ButtonTemplate.primary("Reenviar email de verificación", action="resend_verification"),
                    ButtonTemplate.secondary("Contactar soporte", url="/support"),
                ],
            },
        )

    @staticmethod
    def password_reset_success() -> Dict[str, Any]:
        """Template para respuesta de reset de contraseña exitoso"""
        return ApiResponseTemplate.success(
            message="Contraseña actualizada exitosamente",
            metadata={
                "next_actions": [
                    ButtonTemplate.primary("Iniciar Sesión", url="/auth/login"),
                    ButtonTemplate.secondary("Ir al Inicio", url="/"),
                ],
                "security_notes": [
                    "Se han cerrado todas las otras sesiones por seguridad",
                    "Considera habilitar autenticación de dos factores",
                ],
            },
        )

    @staticmethod
    def user_profile_card(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template para tarjeta de perfil de usuario"""
        return CardTemplate.basic(
            title=user_data.get("full_name", "Usuario"),
            subtitle=user_data.get("email", ""),
            content={
                "role": {
                    "value": user_data.get("role"),
                    "display": user_data.get("role").replace("_", " ").title() if user_data.get("role") else "Sin rol",
                },
                "status": {
                    "value": user_data.get("status"),
                    "display": "Activo" if user_data.get("status") == "active" else "Inactivo",
                    "color": "success" if user_data.get("status") == "active" else "warning",
                },
                "verified": {
                    "value": user_data.get("is_verified"),
                    "display": "Verificado" if user_data.get("is_verified") else "No verificado",
                    "color": "success" if user_data.get("is_verified") else "warning",
                },
                "department": user_data.get("department_name", "Sin departamento"),
                "member_since": user_data.get("created_at").strftime("%d/%m/%Y")
                if user_data.get("created_at")
                else "Sin fecha",
            },
            actions=[
                ButtonTemplate.primary("Editar Perfil", url="/profile/edit"),
                ButtonTemplate.secondary("Cambiar Contraseña", action="change_password"),
                ButtonTemplate.danger("Cerrar Sesión", action="logout", confirmation=True),
            ],
            badges=[{"text": user_data.get("role", "").upper(), "color": "primary"}],
        )


class UserResponseTemplates:
    """Templates para respuestas de gestión de usuarios"""

    @staticmethod
    def user_list_response(users: list, total: int, filters: dict = None) -> Dict[str, Any]:
        """Template para listado de usuarios"""
        user_cards = []
        for user in users:
            user_cards.append(
                CardTemplate.basic(
                    title=user.get("full_name"),
                    subtitle=user.get("email"),
                    content={
                        "role": user.get("role"),
                        "status": user.get("status"),
                        "department": user.get("department_name"),
                        "last_login": user.get("last_login_at"),
                    },
                    actions=[
                        {"label": "Ver", "url": f"/users/{user.get('id')}"},
                        {"label": "Editar", "url": f"/users/{user.get('id')}/edit"},
                    ],
                    badges=[
                        {"text": user.get("role", "").upper(), "color": "primary"},
                        {
                            "text": "Verificado" if user.get("is_verified") else "No verificado",
                            "color": "success" if user.get("is_verified") else "warning",
                        },
                    ],
                )
            )
        return ApiResponseTemplate.paginated(
            data=users,
            total=total,
            metadata={
                "cards": user_cards,
                "filters": filters or {},
                "actions": [
                    ButtonTemplate.primary("Nuevo Usuario", url="/users/create"),
                    ButtonTemplate.secondary("Exportar Lista", action="export_users"),
                ],
            },
        )
