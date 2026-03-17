Cada dominio puede tener su propio archivo `.conf` o `.ini` en este directorio.

Nombre recomendado:
- `sipet.conf`
- `midominio.com.conf`

El router de base de datos lee la sección `[options]` y soporta:
- `domain` o `host`
- `db_host`
- `db_port`
- `db_user`
- `db_password`
- `db_name`

Alternativas soportadas:
- `db_url`
- `database_url`
- `datamain_url`
- `sqlite_db_path`

Ejemplo:

```ini
[options]
domain = demo.midominio.com
db_host = localhost
db_port = 5432
db_user = sipet
db_password = secreto
db_name = sipet_demo
admin_passwd = no_usado_por_sipet
list_db = False
workers = 4
proxy_mode = True
log_level = info
```

SIPET usa en runtime solo la configuración de base de datos. El resto de claves se conservan por compatibilidad organizativa.
