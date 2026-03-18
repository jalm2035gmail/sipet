# Acceso — Gestión de bases de datos

## URL

```
http://127.0.0.1:8000/base_datos/inicializar
```

## Credenciales maestras de setup

| Campo    | Valor                  |
|----------|------------------------|
| Usuario  | `0konomiyaki`          |
| Password | `XX,$,26,sipet,26,$,XX` |

> Estas credenciales se usan **solo** durante el setup inicial (cuando la BD no está configurada).
> Se pueden sobreescribir con variables de entorno:
> - `SYSTEM_SUPERADMIN_USERNAME`
> - `SYSTEM_SUPERADMIN_PASSWORD`

## Flujo de acceso

1. Navegar a `/base_datos/inicializar`
2. Ingresar usuario y contraseña maestros
3. Se muestra la pantalla de gestión con la lista de bases de datos del sitio
4. Desde ahí se puede **Crear**, **Editar** o **Eliminar** una base de datos

## Rutas relacionadas

| Ruta                                      | Descripción                          |
|-------------------------------------------|--------------------------------------|
| `GET  /base_datos/inicializar`            | Pantalla principal de setup          |
| `GET  /base_datos/gestion`               | Gestión de BD (requiere sesión admin)|
| `POST /base_datos/setup/login`           | Login maestro (form)                 |
| `GET  /api/base_datos/gestion/list`      | Listar entradas configuradas         |
| `POST /api/base_datos/gestion/save`      | Crear / editar una entrada           |
| `DELETE /api/base_datos/gestion/{domain}`| Eliminar una entrada                 |
| `POST /api/base_datos/inicializar`       | Inicializar / conectar BD            |
