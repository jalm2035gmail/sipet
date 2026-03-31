"""
servicios/render_service.py
─────────────────────────────────────────────────────────────────────────────
Servicio de renderizado de páginas públicas del módulo frontend.

Responsabilidades:
  • Convertir un dict de página (gjs_html / gjs_css / blocks / meta) en
    un HTMLResponse completo listo para servir al cliente.
  • Inyectar CSS variables de marca, logo, menú inferior y script de formularios.
  • Intentar renderizado con Jinja2 (page_render.html); si el template no
    existe, usa el renderizado inline como respaldo sin romper nada.
  • Renderizar el sistema de bloques legacy (hero, text, image, columns, etc.)
    cuando no hay gjs_html disponible.

Dependencias internas:
  • get_colores_context()     → colores de marca
  • _load_login_identity()    → posición del menú
  • cache_service.page_cache  → NO se usa aquí; el caché lo gestiona
                                el controlador para mantener este servicio
                                puro y testeable.
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Any, Dict, List

from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import _load_login_identity
from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import get_colores_context

logger = logging.getLogger(__name__)

# ── Rutas de templates ────────────────────────────────────────────────────────
_TEMPLATES_DIR    = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "vistas")
_PAGE_RENDER_TMPL = "page_render.html"
_NAV_RE = re.compile(r"<nav\b[^>]*>.*?</nav>", re.IGNORECASE | re.DOTALL)
_FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.IGNORECASE | re.DOTALL)

# ── Script de widget de formulario (inyectado solo si la página lo necesita) ─
_FORM_WIDGET_SCRIPT = """
<script>
(function(){
  'use strict';
  function _e(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function _field(f,slug){
    var id='sfw-'+slug+'-'+f.name;
    var b='width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;outline:none;';
    var fc='onFocus="this.style.borderColor=\'#3b82f6\'" onBlur="this.style.borderColor=\'#d1d5db\'";';
    if(f.type==='divider') return '<hr style="border:none;border-top:1px solid #e5e7eb;margin:4px 0;">';
    if(f.type==='header')  return '<h3 style="font-size:1.1rem;font-weight:700;color:#111827;">'+_e(f.label||'')+'</h3>';
    if(f.type==='paragraph') return '<p style="font-size:14px;color:#64748b;line-height:1.6;">'+_e(f.label||'')+'</p>';
    var w='<div style="display:flex;flex-direction:column;gap:5px;">';
    if(f.type!=='checkbox'){
      w+='<label for="'+_e(id)+'" style="font-size:13px;font-weight:600;color:#374151;">'+_e(f.label||f.name)+(f.required?' <span style="color:#ef4444">*</span>':'')+'</label>';
    }
    if(f.type==='textarea'){
      w+='<textarea id="'+_e(id)+'" name="'+_e(f.name)+'" rows="4" placeholder="'+_e(f.placeholder||'')+'" style="'+b+'resize:vertical;" '+fc+(f.required?' required':'')+'></textarea>';
    } else if(f.type==='select'){
      w+='<select id="'+_e(id)+'" name="'+_e(f.name)+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
        +'<option value="">-- Seleccionar --</option>';
      (f.options||[]).forEach(function(o){var v=typeof o==='object'?(o.value||o):o;var l=typeof o==='object'?(o.label||o.value||o):o;w+='<option value="'+_e(v)+'">'+_e(l)+'</option>';});
      w+='</select>';
    } else if(f.type==='radio'){
      w+='<div style="display:flex;flex-direction:column;gap:8px;">';
      (f.options||[]).forEach(function(o){var v=typeof o==='object'?(o.value||o):o;var l=typeof o==='object'?(o.label||o.value||o):o;w+='<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="radio" name="'+_e(f.name)+'" value="'+_e(v)+'"'+(f.required?' required':'')+'>'+_e(l)+'</label>';});
      w+='</div>';
    } else if(f.type==='checkboxes'){
      w+='<div style="display:flex;flex-direction:column;gap:8px;">';
      (f.options||[]).forEach(function(o){var v=typeof o==='object'?(o.value||o):o;var l=typeof o==='object'?(o.label||o.value||o):o;w+='<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="checkbox" name="'+_e(f.name)+'" value="'+_e(v)+'">'+_e(l)+'</label>';});
      w+='</div>';
    } else if(f.type==='checkbox'){
      w+='<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="checkbox" id="'+_e(id)+'" name="'+_e(f.name)+'" value="1"'+(f.required?' required':'')+'>'+_e(f.label||f.name)+'</label>';
    } else if(f.type==='date'){
      w+='<input type="date" id="'+_e(id)+'" name="'+_e(f.name)+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
    } else if(f.type==='time'){
      w+='<input type="time" id="'+_e(id)+'" name="'+_e(f.name)+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
    } else {
      var t=(f.type==='email'||f.type==='url'||f.type==='number'||f.type==='integer'||f.type==='decimal')? f.type.replace('integer','number').replace('decimal','number') : 'text';
      w+='<input type="'+t+'" id="'+_e(id)+'" name="'+_e(f.name)+'" placeholder="'+_e(f.placeholder||'')+'" style="'+b+'" '+fc+(f.required?' required':'')+'>'
    }
    if(f.helpText) w+='<span style="font-size:11px;color:#64748b;">'+_e(f.helpText)+'</span>';
    w+='</div>';
    return w;
  }
  function _render(data,el){
    var cfg=data.config||{};
    var pc=cfg.primary_color||'#3b82f6';
    var lbl=cfg.submit_label||'Enviar';
    var ok=cfg.success_message||'¡Gracias! Tu respuesta fue enviada.';
    var h='<form data-slug="'+_e(data.slug)+'" novalidate style="display:flex;flex-direction:column;gap:18px;">';
    if(data.name) h+='<h2 style="font-size:1.4rem;font-weight:800;color:#111827;">'+_e(data.name)+'</h2>';
    if(data.description) h+='<p style="font-size:14px;color:#64748b;margin-top:-10px;line-height:1.6;">'+_e(data.description)+'</p>';
    (data.fields||[]).forEach(function(f){h+=_field(f,data.slug);});
    h+='<div style="display:flex;align-items:center;gap:12px;"><button type="submit" style="padding:12px 28px;background:'+_e(pc)+';color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;">'+_e(lbl)+'</button><span class="_sfw_msg" style="display:none;font-size:13px;"></span></div>';
    h+='</form>';
    el.innerHTML=h;
    el.querySelector('form').addEventListener('submit',function(ev){
      ev.preventDefault();
      var btn=this.querySelector('button[type=submit]'),msg=this.querySelector('._sfw_msg'),fd={};
      new FormData(this).forEach(function(v,k){fd[k]=v;});
      if(btn)btn.disabled=true;
      fetch('/api/forms/'+encodeURIComponent(data.slug)+'/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(fd),credentials:'include'})
        .then(function(r){return r.json();})
        .then(function(j){
          if(j.success){
            el.innerHTML='<div style="padding:24px;background:#ecfdf5;border-radius:10px;color:#065f46;font-weight:600;text-align:center;font-size:15px;">&#10003; '+_e(ok)+'</div>';
          } else {
            if(msg){msg.style.display='inline';msg.style.color='#b91c1c';msg.textContent=j.error||'Error al enviar';}
            if(btn)btn.disabled=false;
          }
        }).catch(function(){
          if(msg){msg.style.display='inline';msg.style.color='#b91c1c';msg.textContent='Error de conexión';}
          if(btn)btn.disabled=false;
        });
    });
  }
  function init(){
    document.querySelectorAll('.sipet-form-widget[data-slug]').forEach(function(el){
      var slug=el.dataset.slug;
      if(!slug){el.innerHTML='<p style="color:#94a3b8;padding:16px;font-style:italic;">Formulario sin configurar</p>';return;}
      el.innerHTML='<p style="color:#94a3b8;font-size:13px;padding:16px;text-align:center;">&#8987; Cargando formulario…</p>';
      fetch('/api/forms/'+encodeURIComponent(slug),{credentials:'include'})
        .then(function(r){return r.json();})
        .then(function(j){
          if(!j.success||!j.data){el.innerHTML='<p style="color:#ef4444;padding:16px;font-size:13px;">Formulario &ldquo;'+_e(slug)+'&rdquo; no encontrado</p>';return;}
          _render(j.data,el);
        }).catch(function(){el.innerHTML='<p style="color:#ef4444;padding:16px;font-size:13px;">Error al cargar formulario</p>';});
    });
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}else{init();}
})();
</script>"""


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — HELPERS DE ESCAPE Y MARCA
# ══════════════════════════════════════════════════════════════════════════════

def _esc(s: Any) -> str:
    """Escapa caracteres HTML para uso seguro en atributos y texto."""
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def brand_css_vars() -> str:
    """
    Genera un bloque <style>:root{...}</style> con los colores de marca
    actuales. Devuelve '' si no hay colores configurados o falla la lectura.
    """
    try:
        data = get_colores_context()
        if not data:
            return ""
        rules = "".join(
            f"--{k.replace(' ', '-')}:{v};"
            for k, v in data.items()
            if isinstance(v, str)
        )
        return f"<style>:root{{{rules}}}</style>" if rules else ""
    except Exception as exc:
        logger.debug("brand_css_vars() falló: %s", exc)
        return ""


def menu_position() -> str:
    """Devuelve 'arriba' o 'abajo' según la configuración de identidad."""
    try:
        data  = _load_login_identity()
        value = str(data.get("menu_position") or "arriba").strip().lower()
        return value if value in {"arriba", "abajo"} else "arriba"
    except Exception:
        return "arriba"


def mobile_bottom_menu_html() -> str:
    """Devuelve el HTML+CSS+JS del menú de navegación inferior móvil."""
    return """
<style>
.sipet-mobile-bottom-nav{
  position:fixed;bottom:0;left:0;right:0;display:flex;z-index:2000;
  background:#fff;border-top:1px solid #e2e8f0;box-shadow:0 -4px 16px rgba(0,0,0,.08)
}
body.sipet-menu-bottom{padding-bottom:76px}
.sipet-mobile-bottom-nav a{
  flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:3px;padding:10px 4px;text-decoration:none;color:#94a3b8;font-family:system-ui,sans-serif
}
.sipet-mobile-bottom-nav a.is-active{color:#3b82f6}
.sipet-mobile-bottom-nav__icon{font-size:1.3rem;line-height:1}
.sipet-mobile-bottom-nav__label{font-size:.65rem;font-weight:600;line-height:1.1}
@media (min-width:901px){
  .sipet-mobile-bottom-nav{
    left:50%;right:auto;bottom:20px;transform:translateX(-50%);
    width:min(680px,calc(100vw - 32px));border:1px solid #e2e8f0;border-radius:18px;
    box-shadow:0 20px 50px rgba(15,23,42,.18)
  }
  body.sipet-menu-bottom{padding-bottom:96px}
  .sipet-mobile-bottom-nav a{padding:12px 8px}
}
</style>
<nav class="sipet-mobile-bottom-nav" aria-label="Menú móvil inferior">
  <a href="/backend/inicio"><span class="sipet-mobile-bottom-nav__icon">🏠</span><span class="sipet-mobile-bottom-nav__label">Inicio</span></a>
  <a href="/backend/funcionalidades"><span class="sipet-mobile-bottom-nav__icon">💳</span><span class="sipet-mobile-bottom-nav__label">Servicios</span></a>
  <a href="/backend/descripcion"><span class="sipet-mobile-bottom-nav__icon">🔍</span><span class="sipet-mobile-bottom-nav__label">Buscar</span></a>
  <a href="/web/inicio"><span class="sipet-mobile-bottom-nav__icon">👤</span><span class="sipet-mobile-bottom-nav__label">Perfil</span></a>
</nav>
<script>
(function(){
  var path=(window.location.pathname||'').replace(/\/+$/,'')||'/';
  document.body.classList.add('sipet-menu-bottom');
  document.querySelectorAll('.sipet-mobile-bottom-nav a[href]').forEach(function(link){
    var href=(link.getAttribute('href')||'').replace(/\/+$/,'')||'/';
    if(href===path||(href!=='/'&&path.indexOf(href+'/')===0)){link.classList.add('is-active');}
  });
})();
</script>
"""


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — INYECCIÓN DE LOGO
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_logo_url() -> str:
    """
    Determina la URL del logo a inyectar en las páginas públicas.
    Prioridad: 1) brand_store (logo personalizado del módulo frontend)
               2) identidad_login.json (logo institucional global)
               3) uploads de personalización
    """
    # Prioridad 1: brand store en BD
    try:
        from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import get_brand
        brand_logo = str(get_brand().get("logo_url") or "").strip()
        if brand_logo:
            return brand_logo
    except Exception:
        pass

    # Prioridad 2 y 3: identidad institucional / personalización
    return _resolve_identidad_logo_url()


def _resolve_identidad_logo_url() -> str:
    """
    Lee el logo desde la identidad institucional en BD y, si no existe un
    logo personalizado, usa la carpeta de uploads de personalización.
    """
    import glob as _glob

    # Prioridad 2: identidad institucional
    try:
        from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import _build_login_asset_url
        data = _load_login_identity()
        logo_filename = str(data.get("logo_filename") or "").strip()
        if logo_filename and logo_filename != "icon.png":
            return _build_login_asset_url(logo_filename, "icon.png")
    except Exception:
        pass

    # Prioridad 3: uploads de personalización
    _UPLOADS = os.path.join("fastapi_modulo", "modulos", "personalizacion", "uploads")
    candidates = sorted(
        _glob.glob(os.path.join(_UPLOADS, "logo_empresa.*")),
        key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
        reverse=True,
    )
    if candidates:
        fname = os.path.basename(candidates[0])
        v = int(os.path.getmtime(candidates[0])) if os.path.exists(candidates[0]) else 0
        return f"/personalizar/uploads/{fname}?v={v}"

    return ""


def inject_logo(html: str) -> str:
    """
    Reemplaza el contenido interno de cualquier elemento con atributo
    data-sipet-logo='1' por el tag <img> del logo actual.
    Si no hay logo configurado o el html no contiene el marcador, devuelve
    el html sin modificar.
    """
    logo_url = _resolve_logo_url()
    if not logo_url or "data-sipet-logo" not in (html or ""):
        return html

    logo_markup = (
        f'<img src="{_esc(logo_url)}" '
        'style="height:38px;width:auto;object-fit:contain;display:block;" '
        'alt="Logo" data-sipet-logo="1">'
    )
    pattern = re.compile(
        r'(<[^>]*data-sipet-logo="1"[^>]*>)(.*?)(</[^>]+>)',
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub(lambda m: f"{m.group(1)}{logo_markup}{m.group(3)}", html)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — JINJA2
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _get_jinja_env() -> Environment:
    """
    Entorno Jinja2 con autoescape desactivado para HTML crudo de GrapesJS.
    El lru_cache garantiza una sola instancia por proceso.
    """
    return Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — RENDERIZADO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def render_page(page: Dict[str, Any]) -> HTMLResponse:
    """
    Punto de entrada principal del servicio.
    Convierte un dict de página en un HTMLResponse completo.

    Flujo:
      1. Extrae título, meta, html/css y bloques del dict.
      2. Inyecta el logo en el html del builder.
      3. Decide si inyectar el script de formularios.
      4. Obtiene CSS vars de marca, posición del menú y menú inferior.
      5. Intenta renderizar con Jinja2 (page_render.html).
      6. Si el template no existe, usa render inline como respaldo.
    """
    title      = _esc(page.get("title", ""))
    meta       = page.get("meta") or {}
    meta_title = _esc(meta.get("title") or page.get("title") or "")
    meta_desc  = _esc(meta.get("description") or "")
    og_image   = _esc(meta.get("og_image") or "")

    gjs_html = page.get("gjs_html") or ""
    gjs_css  = page.get("gjs_css") or ""

    # Contenido del body: GrapesJS o bloques legacy
    raw_body     = gjs_html if gjs_html else render_blocks(page.get("blocks", []))
    raw_body = _FOOTER_RE.sub("", _NAV_RE.sub("", raw_body)).strip()
    try:
        from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import get_brand
        brand = get_brand()
        global_nav = str(brand.get("global_nav_html") or "").strip()
        global_footer = str(brand.get("global_footer_html") or "").strip()
        if global_nav:
            raw_body = global_nav + raw_body
        if global_footer:
            raw_body = raw_body + global_footer
    except Exception:
        pass
    body_content = inject_logo(raw_body)
    extra_style  = f"<style>{gjs_css}</style>" if gjs_css else ""

    # Inyectar script de formularios solo si la página los usa
    has_forms   = "sipet-form-widget" in body_content
    form_script = _FORM_WIDGET_SCRIPT if has_forms else ""

    brand_vars  = brand_css_vars()
    pos         = menu_position()
    bottom_menu = mobile_bottom_menu_html() if pos == "abajo" else ""

    context = {
        "title":        title,
        "meta_title":   meta_title,
        "meta_desc":    meta_desc,
        "og_image":     og_image,
        "body_content": body_content,
        "extra_style":  extra_style,
        "form_script":  form_script,
        "brand_vars":   brand_vars,
        "bottom_menu":  bottom_menu,
    }

    # ── Intento Jinja2 ────────────────────────────────────────────────────────
    try:
        tmpl = _get_jinja_env().get_template(_PAGE_RENDER_TMPL)
        return HTMLResponse(tmpl.render(**context))
    except TemplateNotFound:
        logger.debug(
            "render_service: template '%s' no encontrado en '%s', "
            "usando render inline.",
            _PAGE_RENDER_TMPL, _TEMPLATES_DIR,
        )
    except Exception as exc:
        logger.warning("render_service: Jinja2 falló (%s), usando render inline.", exc)

    # ── Render inline (respaldo) ──────────────────────────────────────────────
    return _render_inline(context)


def _render_inline(ctx: Dict[str, Any]) -> HTMLResponse:
    """
    Renderizado HTML inline sin Jinja2.
    Se usa cuando page_render.html no existe (primera instalación, tests).
    """
    meta_desc_tag = (
        f'<meta name="description" content="{ctx["meta_desc"]}">'
        if ctx["meta_desc"] else ""
    )
    og_image_tag = (
        f'<meta property="og:image" content="{ctx["og_image"]}">'
        if ctx["og_image"] else ""
    )
    title = ctx["meta_title"] or ctx["title"]

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  {meta_desc_tag}
  {og_image_tag}
  <meta property="og:title" content="{title}">
  <meta property="og:type" content="website">
  <link rel="stylesheet" href="/static/vendor/fontawesome/css/all.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  {ctx["brand_vars"]}
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,sans-serif;color:#1e293b;position:relative;isolation:isolate}}
    .sipet-auth-corner{{position:fixed;top:14px;right:14px;z-index:4300;display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:999px;border:1px solid rgba(255,255,255,.22);background:rgba(15,23,42,.82);color:#ffffff;text-decoration:none;box-shadow:0 18px 40px rgba(15,23,42,.22);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);transition:transform .18s ease,box-shadow .18s ease,background .18s ease}}
    .sipet-auth-corner:hover{{transform:translateY(-1px);box-shadow:0 24px 52px rgba(15,23,42,.28);background:rgba(15,23,42,.92)}}
    .sipet-auth-corner:focus-visible{{outline:3px solid rgba(59,130,246,.28);outline-offset:3px}}
    .sipet-auth-corner__icon{{font-size:.56rem;line-height:1}}
    .sipet-auth-corner__avatar{{display:none;width:100%;height:100%;border-radius:inherit;object-fit:cover}}
    .sipet-auth-corner.is-user-image{{padding:0;overflow:hidden;border-color:rgba(255,255,255,.34);background:rgba(255,255,255,.92)}}
    .sipet-auth-corner.is-user-image .sipet-auth-corner__icon{{display:none}}
    .sipet-auth-corner.is-user-image .sipet-auth-corner__avatar{{display:block}}
    .sipet-auth-corner__label{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
    .promo-bar{{position:relative;z-index:4200 !important}}
    .topbar{{position:relative;z-index:4100 !important}}
    body nav[style*="position:sticky"],
    body nav[style*="position: fixed"],
    body nav[style*="position:fixed"],
    body nav[style*="position:absolute"][style*="top:0"],
    body nav[style*="position: absolute"][style*="top: 0"]{{z-index:4100 !important}}
    @media (max-width:560px){{.sipet-auth-corner{{top:10px;right:10px;width:24px;height:24px}}}}
  </style>
  {ctx["extra_style"]}
</head>
<body><a class="sipet-auth-corner" data-sipet-auth-link="1" href="/backend/login" title="Ingresar" aria-label="Ingresar"><i class="sipet-auth-corner__icon fa-solid fa-right-to-bracket" aria-hidden="true"></i><img class="sipet-auth-corner__avatar" data-sipet-auth-avatar alt=""><span class="sipet-auth-corner__label" data-sipet-auth-label>Ingresar</span></a>{ctx["body_content"]}{ctx["bottom_menu"]}{ctx["form_script"]}
<script>
(function(){{
  var links=document.querySelectorAll('[data-sipet-auth-link]');
  if(!links.length) return;
  fetch('/api/backend/me',{{credentials:'include'}})
    .then(function(r){{return r.ok?r.json():null;}})
    .then(function(data){{
      var authenticated=!!(data&&data.authenticated);
      var username=authenticated?String(data.username||data.user_name||'').trim():'';
      var imageUrl=authenticated?String(data.image_url||data.imagen||'').trim():'';
      links.forEach(function(link){{
        var label=link.querySelector('[data-sipet-auth-label]');
        var avatar=link.querySelector('[data-sipet-auth-avatar]');
        var accessibleLabel=authenticated?'Abrir panel':'Ingresar';
        var targetHref=authenticated?String(data.panel_url||'/inicio').trim()||'/inicio':'/backend/login';
        if(label){{
          label.textContent=authenticated?(username||accessibleLabel):accessibleLabel;
        }}
        if(avatar){{
          if(authenticated&&imageUrl){{
            avatar.src=imageUrl;
            avatar.alt=username||accessibleLabel;
            link.classList.add('is-user-image');
          }} else {{
            avatar.removeAttribute('src');
            avatar.alt='';
            link.classList.remove('is-user-image');
          }}
        }}
        link.setAttribute('href',targetHref);
        link.setAttribute('title', authenticated?'Abrir panel del backend':accessibleLabel);
        link.setAttribute('aria-label', authenticated?'Abrir panel del backend':accessibleLabel);
      }});
    }})
    .catch(function(){{}});
}})();
</script></body>
</html>""")


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — RENDERIZADO DE BLOQUES LEGACY
# ══════════════════════════════════════════════════════════════════════════════

def render_blocks(blocks: List[Dict[str, Any]]) -> str:
    """
    Convierte la lista de bloques legacy (hero, text, image, columns…)
    a HTML equivalente. Se usa cuando la página no tiene gjs_html.
    """
    html = ""
    for b in blocks:
        btype = b.get("type", "")
        p     = b.get("props", {})

        if btype == "hero":
            btn = (
                f'<a href="{_esc(p.get("btn_url","#"))}" style="display:inline-block;'
                f'padding:14px 32px;background:{_esc(p.get("btn_bg","#3b82f6"))};'
                f'color:#fff;border-radius:8px;text-decoration:none;font-weight:700;">'
                f'{_esc(p.get("btn_label",""))}</a>'
                if p.get("btn_label") else ""
            )
            html += (
                f'<section style="background:{_esc(p.get("bg","#1e293b"))};'
                f'color:{_esc(p.get("color","#ffffff"))};padding:80px 24px;'
                f'text-align:{_esc(p.get("align","center"))};">'
                f'<h1 style="font-size:2.5rem;font-weight:800;margin-bottom:16px;">'
                f'{_esc(p.get("title",""))}</h1>'
                f'<p style="font-size:1.2rem;opacity:.8;margin-bottom:32px;">'
                f'{_esc(p.get("subtitle",""))}</p>{btn}</section>'
            )

        elif btype == "text":
            html += (
                f'<section style="max-width:{_esc(p.get("max_width","760px"))};'
                f'margin:0 auto;padding:{_esc(p.get("padding","48px 24px"))};">'
                f'<div style="font-size:{_esc(p.get("font_size","1rem"))};'
                f'line-height:1.7;color:{_esc(p.get("color","#1e293b"))};">'
                f'{p.get("content","")}</div></section>'
            )

        elif btype == "image":
            caption = (
                f'<p style="margin-top:10px;color:#64748b;font-size:.9rem;">'
                f'{_esc(p.get("caption",""))}</p>'
                if p.get("caption") else ""
            )
            html += (
                f'<section style="padding:{_esc(p.get("padding","32px 24px"))};'
                f'text-align:{_esc(p.get("align","center"))};">'
                f'<img src="{_esc(p.get("src",""))}" alt="{_esc(p.get("alt",""))}" '
                f'style="max-width:{_esc(p.get("max_width","100%"))};'
                f'border-radius:{_esc(p.get("radius","0px"))};">'
                f'{caption}</section>'
            )

        elif btype in ("columns2", "columns3"):
            n     = 3 if btype == "columns3" else 2
            gap   = "24" if n == 3 else "32"
            cols  = (p.get("columns", []) + [{}, {}, {}])[:n]
            tpl   = " ".join(["1fr"] * n)
            inner = "".join(f'<div>{c.get("content","")}</div>' for c in cols)
            html += (
                f'<section style="padding:{_esc(p.get("padding","48px 24px"))};'
                f'max-width:1100px;margin:0 auto;">'
                f'<div style="display:grid;grid-template-columns:{tpl};gap:{gap}px;">'
                f'{inner}</div></section>'
            )

        elif btype == "cta":
            btn = (
                f'<a href="{_esc(p.get("btn_url","#"))}" style="display:inline-block;'
                f'padding:14px 36px;background:{_esc(p.get("btn_bg","#3b82f6"))};'
                f'color:#fff;border-radius:8px;text-decoration:none;font-weight:700;">'
                f'{_esc(p.get("btn_label",""))}</a>'
                if p.get("btn_label") else ""
            )
            html += (
                f'<section style="background:{_esc(p.get("bg","#0f172a"))};'
                f'color:{_esc(p.get("color","#fff"))};padding:60px 24px;text-align:center;">'
                f'<h2 style="font-size:2rem;font-weight:700;margin-bottom:12px;">'
                f'{_esc(p.get("title",""))}</h2>'
                f'<p style="opacity:.8;margin-bottom:28px;">{_esc(p.get("subtitle",""))}</p>'
                f'{btn}</section>'
            )

        elif btype == "cards":
            cards_html = "".join(
                f'<div style="background:#fff;border:1px solid #e2e8f0;'
                f'border-radius:12px;padding:24px;">'
                f'<h3 style="font-size:1.1rem;font-weight:700;margin-bottom:8px;">'
                f'{_esc(c.get("title",""))}</h3>'
                f'<p style="color:#64748b;font-size:.9rem;">{_esc(c.get("body",""))}</p>'
                f'</div>'
                for c in p.get("cards", [])
            )
            title_html = (
                f'<h2 style="text-align:center;font-size:1.8rem;font-weight:700;'
                f'margin-bottom:32px;">{_esc(p.get("title",""))}</h2>'
                if p.get("title") else ""
            )
            html += (
                f'<section style="padding:{_esc(p.get("padding","48px 24px"))};'
                f'max-width:1100px;margin:0 auto;">{title_html}'
                f'<div style="display:grid;grid-template-columns:'
                f'repeat(auto-fit,minmax(240px,1fr));gap:20px;">'
                f'{cards_html}</div></section>'
            )

        elif btype == "divider":
            html += (
                f'<hr style="border:none;border-top:'
                f'{_esc(p.get("thickness","1px"))} solid '
                f'{_esc(p.get("color","#e2e8f0"))};'
                f'margin:{_esc(p.get("margin","0"))};">'
            )

        elif btype == "spacer":
            html += f'<div style="height:{_esc(p.get("height","48px"))};"></div>'

        elif btype == "html":
            html += p.get("content", "")

    return html
    
