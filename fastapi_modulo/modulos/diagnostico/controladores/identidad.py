class UsuarioIdentidad:
    """
    Clase para gestionar roles y niveles de acceso de usuarios en identidad institucional.
    """
    def __init__(self, usuario_id, nombre, rol, nivel_acceso):
        self.usuario_id = usuario_id
        self.nombre = nombre
        self.rol = rol
        self.nivel_acceso = nivel_acceso

    def set_rol(self, rol):
        self.rol = rol

    def set_nivel_acceso(self, nivel):
        self.nivel_acceso = nivel

    def get_info(self):
        return {
            "usuario_id": self.usuario_id,
            "nombre": self.nombre,
            "rol": self.rol,
            "nivel_acceso": self.nivel_acceso
        }

class Roles:
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    USUARIO = "usuario"
    INVITADO = "invitado"

class NivelesAcceso:
    TOTAL = "total"
    PARCIAL = "parcial"
    SOLO_LECTURA = "solo_lectura"
    RESTRINGIDO = "restringido"
