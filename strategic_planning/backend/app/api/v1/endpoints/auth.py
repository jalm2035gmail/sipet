from datetime import timedelta
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import (
    AccountLockedException,
    CredentialsException,
    TokenInvalidException,
    UserInactiveException,
)
from app.core.security import TokenUtils
from app.crud.token import token_crud
from app.crud.user import user as user_crud
from app.models.user import UserStatus
from app.schemas.token import TokenPairResponse, TokenRefreshRequest
from app.schemas.user import (
    UserLogin,
    UserLoginResponse,
    UserPasswordChange,
    UserPasswordReset,
    UserPasswordResetRequest,
    UserRegister,
    UserResponse,
    UserVerifyEmail,
)
from app.templates.api import ApiResponseTemplate
from app.templates.auth.response_templates import AuthResponseTemplates
from app.utils.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    try:
        user = user_crud.authenticate(
            db,
            email=form_data.username,
            password=form_data.password,
            ip_address=client_ip,
        )
        if not user:
            raise CredentialsException()

        tokens = TokenUtils.create_tokens_pair(
            user_id=user.id,
            email=user.email,
            role=user.role,
            department_id=user.department_id,
        )

        token_crud.create_access_token(
            db,
            user_id=user.id,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user_agent=request.headers.get("User-Agent"),
            ip_address=client_ip,
        )
        token_crud.create_refresh_token(
            db,
            user_id=user.id,
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
            user_agent=request.headers.get("User-Agent"),
            ip_address=client_ip,
        )

        user_response = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "department_id": user.department_id,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }

        return ApiResponseTemplate.success(
            data=AuthResponseTemplates.login_success(user_response, tokens),
            message="Inicio de sesión exitoso",
        )

    except (CredentialsException, UserInactiveException, AccountLockedException, TokenInvalidException) as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(exc)}",
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_in: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        user = user_crud.create(db, obj_in=user_in)
        token = token_crud.create_verification_token(
            db,
            user_id=user.id,
            expires_in_hours=24,
        )
        background_tasks.add_task(
            send_verification_email,
            email_to=user.email,
            username=user.first_name,
            token=token.token,
        )

        user_response = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "department_id": user.department_id,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }

        return ApiResponseTemplate.success(
            data=user_response,
            message="Usuario registrado exitosamente. Por favor verifica tu email.",
            status_code=status.HTTP_201_CREATED,
            metadata={
                "requires_verification": True,
                "verification_email_sent": True,
            },
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(exc)}",
        )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_token(
    request: Request,
    token_data: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    try:
        token_obj = token_crud.verify_token(
            db,
            token=token_data.refresh_token,
            token_type="refresh",
        )
        if not token_obj:
            raise CredentialsException("Refresh token inválido o expirado")

        user = user_crud.get(db, id=token_obj.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise CredentialsException("Usuario no válido")

        token_obj.revoke("Token refrescado")
        tokens = TokenUtils.create_tokens_pair(
            user_id=user.id,
            email=user.email,
            role=user.role,
            department_id=user.department_id,
        )

        client_ip = request.client.host if request.client else None
        token_crud.create_access_token(
            db,
            user_id=user.id,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user_agent=request.headers.get("User-Agent"),
            ip_address=client_ip,
        )
        token_crud.create_refresh_token(
            db,
            user_id=user.id,
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
            user_agent=request.headers.get("User-Agent"),
            ip_address=client_ip,
        )

        db.add(token_obj)
        db.commit()

        return ApiResponseTemplate.success(
            data=tokens,
            message="Tokens refrescados exitosamente",
        )

    except CredentialsException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al refrescar tokens: {str(exc)}",
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        revoked_count = token_crud.revoke_all_user_tokens(
            db,
            user_id=current_user["id"],
            reason="Logout manual",
        )
        return ApiResponseTemplate.success(
            data=AuthResponseTemplates.logout_success(revoked_count),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(exc)}",
        )


@router.post("/logout-all")
async def logout_all(
    current_user: Dict[str, any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        revoked_count = token_crud.revoke_all_user_tokens(
            db,
            user_id=current_user["id"],
            reason="Logout de todos los dispositivos",
        )
        return ApiResponseTemplate.success(
            message=f"Todas las sesiones cerradas. {revoked_count} tokens revocados.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesiones: {str(exc)}",
        )


@router.post("/verify-email")
async def verify_email(
    verify_data: UserVerifyEmail,
    db: Session = Depends(get_db),
):
    try:
        token_obj = token_crud.verify_token(
            db,
            token=verify_data.token,
            token_type="verification",
        )
        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de verificación inválido o expirado",
            )
        user = user_crud.get(db, id=token_obj.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no encontrado",
            )
        user_crud.verify_email(db, user_id=user.id)
        token_obj.revoke("Email verificado")
        db.add(token_obj)
        db.commit()
        return ApiResponseTemplate.success(
            message="Email verificado exitosamente. Tu cuenta ahora está activa.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar email: {str(exc)}",
        )


@router.post("/resend-verification")
async def resend_verification(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        user = user_crud.get_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está verificado",
            )
        token = token_crud.create_verification_token(
            db,
            user_id=user.id,
            expires_in_hours=24,
        )
        background_tasks.add_task(
            send_verification_email,
            email_to=user.email,
            username=user.first_name,
            token=token.token,
        )
        return ApiResponseTemplate.success(
            message="Email de verificación reenviado exitosamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reenviar email: {str(exc)}",
        )


@router.post("/forgot-password")
async def forgot_password(
    password_reset: UserPasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        user = user_crud.get_by_email(db, email=password_reset.email)
        if not user:
            return ApiResponseTemplate.success(
                message="Si el email existe, recibirás instrucciones para resetear tu contraseña",
            )
        token = token_crud.create_password_reset_token(
            db,
            user_id=user.id,
            expires_in_hours=24,
        )
        background_tasks.add_task(
            send_password_reset_email,
            email_to=user.email,
            username=user.first_name,
            token=token.token,
        )
        return ApiResponseTemplate.success(
            message="Si el email existe, recibirás instrucciones para resetear tu contraseña",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar solicitud: {str(exc)}",
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: UserPasswordReset,
    db: Session = Depends(get_db),
):
    try:
        user_crud.reset_password(
            db,
            token=reset_data.token,
            new_password=reset_data.new_password,
        )
        return ApiResponseTemplate.success(
            message="Contraseña actualizada exitosamente. Ahora puedes iniciar sesión con tu nueva contraseña.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resetear contraseña: {str(exc)}",
        )


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: Dict[str, any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_crud.change_password(
            db,
            user_id=current_user["id"],
            password_data=password_data,
        )
        token_crud.revoke_all_user_tokens(
            db,
            user_id=current_user["id"],
            token_type="access",
            reason="Contraseña cambiada",
        )
        return ApiResponseTemplate.success(
            message="Contraseña cambiada exitosamente. Se han cerrado todas las otras sesiones por seguridad.",
        )
    except (CredentialsException, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(exc)}",
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Dict[str, any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user = user_crud.get(db, id=current_user["id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        user_response = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "department_id": user.department_id,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
        return ApiResponseTemplate.success(
            data=user_response,
            message="Información de usuario obtenida exitosamente",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener información: {str(exc)}",
        )


@router.get("/validate-token")
async def validate_token(
    current_user: Dict[str, any] = Depends(get_current_user),
):
    return ApiResponseTemplate.success(
        data={
            "valid": True,
            "user_id": current_user["id"],
            "expires_in": f"{settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos",
        },
        message="Token válido",
    )
