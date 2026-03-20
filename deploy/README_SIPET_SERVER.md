# Bootstrap servidor SIPET

En el servidor remoto, como `root`:

```bash
mkdir -p /opt/sipet
```

Copiar el script:

```bash
scp deploy/targets/bootstrap-sipet-server.sh root@SERVIDOR:/root/
ssh root@SERVIDOR 'chmod +x /root/bootstrap-sipet-server.sh && DATABASE_BACKEND=postgresql POSTGRES_DB=sipet POSTGRES_USER=sipet POSTGRES_PASSWORD=CAMBIA_ESTA_CLAVE /root/bootstrap-sipet-server.sh'
```

Luego desplegar el código desde local:

```bash
SERVER=administrator@SERVIDOR DATABASE_BACKEND=postgresql POSTGRES_DB=sipet POSTGRES_USER=sipet POSTGRES_PASSWORD=CAMBIA_ESTA_CLAVE deploy/aliases/deploy-uprocach.sh
```

Qué deja listo:

- Python 3 + `venv`
- dependencias nativas para `pandas`, `numpy`, `scikit-learn`, `Pillow`, `psycopg2`, `PyMySQL`
- directorios `/opt/sipet`, `/var/lib/sipet/data`, `/var/log/sipet`
- servicio `systemd` `sipet.service`
- helper `/usr/local/bin/sipet-restart`
- PostgreSQL local con base y usuario de SIPET cuando `DATABASE_BACKEND=postgresql`

Nota:

- `deploy/aliases/deploy-uprocach.sh` no sincroniza `fastapi_modulo/modulos/`; valida que ese directorio ya exista en remoto y lo preserva.

Verificación rápida:

```bash
systemctl status sipet
journalctl -u sipet -n 100 --no-pager
```
