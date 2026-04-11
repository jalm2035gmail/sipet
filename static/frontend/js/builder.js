  (function(){
  'use strict';

  var _pages = [], _currentPageId = null, _slugEdited = false, _statusEdited = false, _editor = null, _saving = false, _htmlRawTarget = null, _htmlRawMode = 'code';

  function uid(){ return '_' + Math.random().toString(36).slice(2,10); }
  function toast(msg, ok){
    ok = ok !== false;
    var t = document.getElementById('wb-toast');
    t.textContent = msg;
    t.style.background = ok ? '#0f172a' : '#7f1d1d';
    if(!ok && window.console && typeof window.console.error === 'function'){
      console.error('[frontend-builder]', msg);
    }
    t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, 2400);
  }
  function slugify(s){
    return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')
      .replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'') || 'pagina';
  }
  function currentPage(){ return _pages.find(function(p){ return p.id === _currentPageId; }) || null; }
  function _esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function _cookie(name){
    var prefix = name + '=';
    var parts = document.cookie ? document.cookie.split(';') : [];
    for(var i=0;i<parts.length;i++){
      var item = parts[i].trim();
      if(item.indexOf(prefix) === 0) return decodeURIComponent(item.slice(prefix.length));
    }
    return '';
  }
  function _csrfHeaders(){
    var token = _cookie('csrf_token');
    return token ? { 'X-CSRF-Token': token } : {};
  }
  function _renderHtmlRawPreview(html, css){
    var frame = document.getElementById('wb-html-preview-frame');
    if(!frame) return;
    frame.srcdoc = '<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;padding:16px;font-family:system-ui,sans-serif;color:#0f172a;background:#fff;max-width:100vw;overflow-x:hidden}*{box-sizing:border-box;max-width:100%;}img,iframe,video,canvas,svg{max-width:100%;height:auto;}@media (max-width:900px){[style*=\"grid-template-columns:1fr 1fr\"],[style*=\"grid-template-columns: 1fr 1fr\"],[style*=\"grid-template-columns:minmax(0,1.25fr) minmax(280px,.75fr)\"],[style*=\"grid-template-columns:minmax(0,1.25fr) minmax(280px, .75fr)\"]{grid-template-columns:1fr!important;}nav[style*=\"display:flex\"],section[style*=\"display:flex\"],div[style*=\"display:flex\"]{flex-wrap:wrap!important;}}@media (max-width:768px){[style*=\"font-size:9rem\"],[style*=\"font-size: 9rem\"],[style*=\"font-size:8.8rem\"],[style*=\"font-size: 8.8rem\"]{font-size:clamp(3.1rem,17vw,4.8rem)!important;white-space:normal!important;text-align:center!important;}}' + (css || '') + '</style></head><body>' + (html || '') + '</body></html>';
  }
  window.setHtmlRawMode = function(mode){
    _htmlRawMode = mode === 'preview' ? 'preview' : 'code';
    var codePane = document.getElementById('wb-html-code-pane');
    var editor = document.getElementById('wb-html-editor');
    var css = document.getElementById('wb-html-css');
    var preview = document.getElementById('wb-html-preview');
    var codeBtn = document.getElementById('wb-html-code-btn');
    var previewBtn = document.getElementById('wb-html-preview-btn');
    if(codePane) codePane.classList.toggle('active', _htmlRawMode === 'code');
    if(preview) preview.classList.toggle('active', _htmlRawMode === 'preview');
    if(codeBtn) codeBtn.classList.toggle('active', _htmlRawMode === 'code');
    if(previewBtn) previewBtn.classList.toggle('active', _htmlRawMode === 'preview');
    if(_htmlRawMode === 'preview' && editor){
      _renderHtmlRawPreview(editor.value || '', css ? css.value || '' : '');
    }
  };
  window.openHtmlRawModal = function(component){
    _htmlRawTarget = component || null;
    var overlay = document.getElementById('wb-html-modal-overlay');
    var editor = document.getElementById('wb-html-editor');
    var css = document.getElementById('wb-html-css');
    if(!overlay || !editor || !css || !_htmlRawTarget) return;
    editor.value = _htmlRawTarget.get('rawHtml') || '';
    css.value = _htmlRawTarget.get('rawCss') || '';
    overlay.classList.add('open');
    window.setHtmlRawMode(_htmlRawMode || 'code');
    setTimeout(function(){ editor.focus(); editor.select(); }, 20);
  };
  window.closeHtmlRawModal = function(){
    var overlay = document.getElementById('wb-html-modal-overlay');
    if(overlay) overlay.classList.remove('open');
    _htmlRawTarget = null;
  };
  window.saveHtmlRawModal = function(){
    var editor = document.getElementById('wb-html-editor');
    var css = document.getElementById('wb-html-css');
    if(!_htmlRawTarget || !editor || !css) return;
    _htmlRawTarget.set('rawHtml', editor.value || '');
    _htmlRawTarget.set('rawCss', css.value || '');
    _setDirty(true);
    window.closeHtmlRawModal();
    toast('HTML actualizado ✓');
  };

  /* API */
  function _readJSONResponse(r){
    return r.text().then(function(text){
      var data = null;
      try { data = text ? JSON.parse(text) : {}; } catch(err) {}
      if(!r.ok){
        var message = (data && (data.error || data.message)) || ('HTTP ' + r.status);
        throw new Error(message);
      }
      if(data) return data;
      throw new Error('Respuesta inválida del servidor');
    });
  }
  function apiPages(){
    return fetch('/api/frontend/pages',{credentials:'include'})
      .then(_readJSONResponse)
      .then(function(j){ return j.data || []; });
  }
  function apiSave(page){
    return fetch('/api/frontend/pages',{
      method:'POST',
      credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(page)
    }).then(_readJSONResponse);
  }
  function apiDelete(id){
    return fetch('/api/frontend/pages',{
      method:'POST',
      credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action:'delete',id:id})
    }).then(_readJSONResponse);
  }

  /* GrapesJS init */
  function initEditor(){
    _editor = grapesjs.init({
      container: '#gjs',
      height: '100%',
      width: 'auto',
      fromElement: false,
      storageManager: false,
      noticeOnUnload: false,
      plugins: [],

      deviceManager: {
        devices: [
          { name: 'Escritorio', id: 'desktop', width: '' },
          { name: 'Tablet',     id: 'tablet',  width: '768px', widthMedia: '768px' },
          { name: 'Movil',      id: 'mobile',  width: '390px', widthMedia: '480px' },
        ]
      },

      panels: {
        defaults: [
          {
            id: 'panel-switcher', el: '#wb-panel-switcher',
            buttons: [
              { id:'show-blocks', active:true, label:'🧱', command:'show-blocks', togglable:false, attributes:{title:'Bloques'} },
              { id:'show-styles',              label:'🎨', command:'show-styles', togglable:false, attributes:{title:'Estilos'} },
              { id:'show-traits',              label:'⚙',  command:'show-traits', togglable:false, attributes:{title:'Propiedades'} },
              { id:'show-layers',              label:'☰',  command:'show-layers', togglable:false, attributes:{title:'Capas'} },
            ]
          },
          {
            id: 'panel-devices', el: '#wb-devices',
            buttons: [
              { id:'device-desktop', label:'🖥',  command:'set-device-desktop', active:true, togglable:false, className:'wb-btn wb-btn-ghost active', attributes:{title:'Escritorio'} },
              { id:'device-tablet',  label:'📱',  command:'set-device-tablet',  togglable:false, className:'wb-btn wb-btn-ghost', attributes:{title:'Tablet'} },
              { id:'device-mobile',  label:'📲',  command:'set-device-mobile',  togglable:false, className:'wb-btn wb-btn-ghost', attributes:{title:'Movil'} },
            ]
          },
        ]
      },

      styleManager: {
        appendTo: '#wb-sidebar-content',
        sectors: [
          { name:'Dimensiones', open:false, properties:[
            {property:'width'},{property:'height'},{property:'min-width'},{property:'max-width'},{property:'min-height'},
            {property:'margin',type:'composite',detached:true},{property:'padding',type:'composite',detached:true},
          ]},
          { name:'Tipografia', open:false, properties:[
            {property:'font-family',type:'select',options:[
              {value:'system-ui,sans-serif',name:'Sistema'},{value:'Georgia,serif',name:'Georgia'},
              {value:'Inter,sans-serif',name:'Inter'},{value:'Montserrat,sans-serif',name:'Montserrat'},
            ]},
            {property:'font-size'},{property:'font-weight',type:'select',options:[
              {value:'400',name:'Normal'},{value:'600',name:'Semibold'},{value:'700',name:'Bold'},{value:'800',name:'Extrabold'},
            ]},
            {property:'line-height'},{property:'letter-spacing'},
            {property:'color',type:'color'},
            {property:'text-align',type:'radio',options:[
              {value:'left',name:'←'},{value:'center',name:'↔'},{value:'right',name:'→'},{value:'justify',name:'≡'},
            ]},
            {property:'text-transform',type:'select',options:[
              {value:'none',name:'Ninguno'},{value:'uppercase',name:'MAYUSCULAS'},{value:'capitalize',name:'Capitalizado'},
            ]},
          ]},
          { name:'Decoracion', open:false, properties:[
            {property:'background-color',type:'color'},
            {property:'border-radius'},{property:'box-shadow'},
            {property:'opacity',type:'slider',min:0,max:1,step:0.01},
          ]},
          { name:'Bordes', open:false, properties:[
            {property:'border-width', label:'Grosor', type:'composite', detached:true, properties:[
              {property:'border-top-width',    label:'↑', type:'integer', units:['px','em','rem'], default:'0'},
              {property:'border-right-width',  label:'→', type:'integer', units:['px','em','rem'], default:'0'},
              {property:'border-bottom-width', label:'↓', type:'integer', units:['px','em','rem'], default:'0'},
              {property:'border-left-width',   label:'←', type:'integer', units:['px','em','rem'], default:'0'},
            ]},
            {property:'border-style', label:'Estilo', type:'select', options:[
              {value:'none',   name:'Ninguno'},
              {value:'solid',  name:'Solid'},
              {value:'dashed', name:'Dashed'},
              {value:'dotted', name:'Dotted'},
              {value:'double', name:'Double'},
              {value:'groove', name:'Groove'},
              {value:'inset',  name:'Inset'},
            ]},
            {property:'border-color', label:'Color', type:'color'},
          ]},
          { name:'Layout Flex', open:false, properties:[
            {property:'display',type:'select',options:[
              {value:'block',name:'Block'},{value:'flex',name:'Flex'},{value:'grid',name:'Grid'},{value:'inline-block',name:'Inline Block'},
            ]},
            {property:'flex-direction',type:'radio',options:[{value:'row',name:'→'},{value:'column',name:'↓'}]},
            {property:'justify-content',type:'select',options:[
              {value:'flex-start',name:'Inicio'},{value:'center',name:'Centro'},{value:'flex-end',name:'Fin'},{value:'space-between',name:'Entre'},{value:'space-around',name:'Alrededor'},
            ]},
            {property:'align-items',type:'select',options:[
              {value:'stretch',name:'Estirar'},{value:'center',name:'Centro'},{value:'flex-start',name:'Inicio'},{value:'flex-end',name:'Fin'},
            ]},
            {property:'flex-wrap',type:'radio',options:[{value:'wrap',name:'Wrap'},{value:'nowrap',name:'No wrap'}]},
            {property:'gap'},
          ]},
          { name:'Imagen', open:false, properties:[
            {property:'background-image'},
            {property:'background-size',type:'select',options:[{value:'cover',name:'Cover'},{value:'contain',name:'Contain'},{value:'auto',name:'Auto'}]},
            {property:'background-position',type:'select',options:[
              {value:'center',name:'Centro'},{value:'top',name:'Arriba'},{value:'bottom',name:'Abajo'},
            ]},
            {property:'background-repeat',type:'select',options:[
              {value:'no-repeat',name:'Sin repetir'},{value:'repeat',name:'Repetir'},
            ]},
          ]},
          { name:'Posicion', open:false, properties:[
            {property:'position',type:'select',options:[
              {value:'static',name:'Static'},{value:'relative',name:'Relative'},
              {value:'absolute',name:'Absolute'},{value:'fixed',name:'Fixed'},{value:'sticky',name:'Sticky'},
            ]},
            {property:'top'},{property:'right'},{property:'bottom'},{property:'left'},{property:'z-index'},
          ]},
        ]
      },

      traitManager:  { appendTo: '#wb-sidebar-content' },
      layerManager:  { appendTo: '#wb-sidebar-content' },
      blockManager:  { appendTo: '#wb-sidebar-content' },

      canvas: {
        styles: ['https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap']
      }
    });

    /* Commands */
    function makeShowCmd(sel){
      return {
        run: function(e){
          document.querySelectorAll('#wb-sidebar-content .gjs-blocks-c,#wb-sidebar-content .gjs-sm-sectors,#wb-sidebar-content .gjs-trt-traits,#wb-sidebar-content .gjs-layer-list').forEach(function(el){ el.style.display='none'; });
          var el = document.querySelector(sel); if(el) el.style.display='';
        },
        stop: function(){}
      };
    }
    _editor.Commands.add('show-blocks', makeShowCmd('.gjs-blocks-c'));
    _editor.Commands.add('show-styles', makeShowCmd('.gjs-sm-sectors'));
    _editor.Commands.add('show-traits', makeShowCmd('.gjs-trt-traits'));
    _editor.Commands.add('show-layers', makeShowCmd('.gjs-layer-list'));

    _editor.TraitManager.addType('html-textarea', {
      createInput: function(){
        var el = document.createElement('textarea');
        el.style.width = '100%';
        el.style.minHeight = '220px';
        el.style.padding = '10px';
        el.style.borderRadius = '8px';
        el.style.border = '1px solid var(--color-MAIN-300)';
        el.style.background = 'var(--color-MAIN-100)';
        el.style.color = 'var(--color-MAIN-content)';
        el.style.fontFamily = 'ui-monospace, monospace';
        el.style.fontSize = '11px';
        el.style.lineHeight = '1.45';
        el.style.resize = 'vertical';
        el.placeholder = '<div>Tu HTML aquí</div>';
        return el;
      },
      onEvent: function(){
        var input = this.getInputEl();
        this.target.set('rawHtml', input.value || '');
      },
      onUpdate: function(){
        var input = this.getInputEl();
        input.value = this.target.get('rawHtml') || '';
      },
    });

    function makeDeviceCmd(deviceName){
      return {
        run: function(e){
          e.setDevice(deviceName);
          document.querySelectorAll('#wb-devices .wb-btn').forEach(function(b){ b.classList.remove('active'); });
        },
        stop: function(){}
      };
    }
    _editor.Commands.add('set-device-desktop', makeDeviceCmd('Escritorio'));
    _editor.Commands.add('set-device-tablet',  makeDeviceCmd('Tablet'));
    _editor.Commands.add('set-device-mobile',  makeDeviceCmd('Movil'));
    document.getElementById('wb-undo-btn').onclick = function(){ _editor.runCommand('core:undo'); };
    document.getElementById('wb-redo-btn').onclick = function(){ _editor.runCommand('core:redo'); };

    registerBlocks(_editor);
  }

  function registerBlocks(bm){
    var editor = bm;
    var dc = editor.DomComponents;
    bm = editor.BlockManager;

    function addTypedBlock(id, config){
      var typeId = 'builder-block-' + id;
      dc.addType(typeId, {
        model: { defaults: {
          tagName: config.tagName || 'section',
          attributes: config.attributes || {},
          droppable: config.droppable !== false,
          script: config.script,
          components: config.components || '',
        }},
        view: {}
      });
      bm.add(id, {
        label: config.label,
        category: config.category,
        media: config.media,
        content: { type: typeId }
      });
    }

    /* ══════════════════════════════════════════════════
       1. MENU — variantes de barra de navegación
    ══════════════════════════════════════════════════ */
    bm.add('nav-classic', { label:'Navbar clásica', category:'Estructura general', media:'🔗',
      content:'<nav style="display:flex;align-items:center;justify-content:space-between;padding:16px 5%;background:#fff;box-shadow:0 1px 10px rgba(0,0,0,.07);position:sticky;top:0;z-index:100;"><a href="#" data-sipet-logo="1" style="font-size:1.3rem;font-weight:800;color:#0f172a;text-decoration:none;">MiEmpresa</a><div style="display:flex;gap:24px;align-items:center;"><a href="#" style="color:#475569;text-decoration:none;font-size:.95rem;font-weight:500;">Inicio</a><a href="#" style="color:#475569;text-decoration:none;font-size:.95rem;font-weight:500;">Servicios</a><a href="#" style="color:#475569;text-decoration:none;font-size:.95rem;font-weight:500;">Nosotros</a><a href="#" style="color:#475569;text-decoration:none;font-size:.95rem;font-weight:500;">Contacto</a><a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:10px;padding:8px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.9rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a></div></nav>'
    });

    bm.add('nav-dark', { label:'Navbar oscura', category:'Estructura general', media:'🌙',
      content:'<nav style="display:flex;align-items:center;justify-content:space-between;padding:16px 5%;background:#0f172a;position:sticky;top:0;z-index:100;"><a href="#" data-sipet-logo="1" style="font-size:1.3rem;font-weight:800;color:#f8fafc;text-decoration:none;">MiEmpresa</a><div style="display:flex;gap:24px;align-items:center;"><a href="#" style="color:#94a3b8;text-decoration:none;font-size:.9rem;font-weight:500;transition:color .15s;">Inicio</a><a href="#" style="color:#94a3b8;text-decoration:none;font-size:.9rem;font-weight:500;">Servicios</a><a href="#" style="color:#94a3b8;text-decoration:none;font-size:.9rem;font-weight:500;">Nosotros</a><a href="#" style="color:#94a3b8;text-decoration:none;font-size:.9rem;font-weight:500;">Contacto</a><a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:10px;padding:8px 20px;background:#3b82f6;color:#fff;border-radius:7px;font-size:.9rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a></div></nav>'
    });

    bm.add('nav-centered', { label:'Logo centrado', category:'Estructura general', media:'🎯',
      content:'<nav style="display:flex;flex-direction:column;align-items:center;padding:16px 5%;background:#fff;box-shadow:0 1px 8px rgba(0,0,0,.06);position:sticky;top:0;z-index:100;gap:10px;"><a href="#" data-sipet-logo="1" style="font-size:1.4rem;font-weight:900;color:#0f172a;text-decoration:none;letter-spacing:-.02em;">MiEmpresa</a><div style="display:flex;gap:28px;align-items:center;"><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Inicio</a><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Servicios</a><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Nosotros</a><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Blog</a><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Contacto</a></div></nav>'
    });

    bm.add('nav-minimal', { label:'Navbar minimal', category:'Estructura general', media:'➡',
      content:'<nav style="display:flex;align-items:center;justify-content:space-between;padding:14px 5%;background:#fff;border-bottom:1px solid #e2e8f0;"><a href="#" data-sipet-logo="1" style="font-size:1.1rem;font-weight:800;color:#0f172a;text-decoration:none;">Marca</a><div style="display:flex;gap:20px;align-items:center;"><a href="#" style="color:#475569;text-decoration:none;font-size:.875rem;">Servicios</a><a href="#" style="color:#475569;text-decoration:none;font-size:.875rem;">Contacto</a><a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:8px;color:#3b82f6;font-weight:700;text-decoration:none;font-size:.875rem;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a></div></nav>'
    });

    bm.add('nav-transparent', { label:'Navbar transparente', category:'Estructura general', media:'💎',
      content:'<nav style="display:flex;align-items:center;justify-content:space-between;padding:20px 5%;background:rgba(255,255,255,.1);backdrop-filter:blur(12px);position:absolute;top:0;left:0;right:0;z-index:100;"><a href="#" data-sipet-logo="1" style="font-size:1.3rem;font-weight:800;color:#fff;text-decoration:none;text-shadow:0 1px 4px rgba(0,0,0,.3);">MiEmpresa</a><div style="display:flex;gap:24px;align-items:center;"><a href="#" style="color:rgba(255,255,255,.85);text-decoration:none;font-size:.9rem;font-weight:500;">Inicio</a><a href="#" style="color:rgba(255,255,255,.85);text-decoration:none;font-size:.9rem;font-weight:500;">Servicios</a><a href="#" style="color:rgba(255,255,255,.85);text-decoration:none;font-size:.9rem;font-weight:500;">Contáctanos</a><a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:10px;padding:8px 20px;background:rgba(255,255,255,.2);color:#fff;border:1px solid rgba(255,255,255,.4);border-radius:7px;font-size:.9rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a></div></nav>'
    });

    bm.add('nav-mega', { label:'Navbar con submenu', category:'Estructura general', media:'📋',
      content:'<nav style="display:flex;align-items:center;justify-content:space-between;padding:0 5%;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,.08);position:sticky;top:0;z-index:100;height:58px;"><a href="#" data-sipet-logo="1" style="font-size:1.2rem;font-weight:800;color:#0f172a;text-decoration:none;">MiEmpresa</a><div style="display:flex;height:100%;align-items:stretch;gap:4px;"><a href="#" style="display:flex;align-items:center;padding:0 14px;color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;border-bottom:3px solid transparent;">Inicio</a><a href="#" style="display:flex;align-items:center;padding:0 14px;color:#3b82f6;text-decoration:none;font-size:.9rem;font-weight:600;border-bottom:3px solid #3b82f6;">Servicios ▾</a><a href="#" style="display:flex;align-items:center;padding:0 14px;color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;border-bottom:3px solid transparent;">Sucursales</a><a href="#" style="display:flex;align-items:center;padding:0 14px;color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;border-bottom:3px solid transparent;">Contacto</a></div><div style="display:flex;gap:8px;"><a href="#" style="padding:8px 16px;border:1px solid #e2e8f0;color:#475569;border-radius:7px;font-size:.875rem;font-weight:600;text-decoration:none;">Registrarse</a><a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:9px;padding:8px 18px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a></div></nav>'
    });

    /* ══════════════════════════════════════════════════
       2. HEADER — banners de portada / hero sections
    ══════════════════════════════════════════════════ */
    bm.add('header-hero', { label:'Hero centrado', category:'Header', media:'🦸',
      content:'<section data-sipet-bg-image="1" style="background:#1e293b;color:#fff;padding:100px 24px;text-align:center;"><h1 style="font-size:2.8rem;font-weight:800;margin:0 0 16px;line-height:1.15;">Titulo principal</h1><p style="color:#94a3b8;margin:0 0 32px;font-size:1.1rem;max-width:560px;margin-left:auto;margin-right:auto;line-height:1.7;">Explica tu propuesta de valor en dos lineas claras y concisas.</p><div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;"><a href="#" style="display:inline-block;padding:14px 34px;background:#3b82f6;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Empezar ahora</a><a href="#" style="display:inline-block;padding:14px 34px;border:2px solid rgba(255,255,255,.3);color:#e2e8f0;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Saber mas</a></div></section>'
    });

    bm.add('header-hero-img', { label:'Hero + imagen', category:'Header', media:'🖼',
      content:'<section style="display:flex;align-items:center;gap:48px;padding:80px 5%;background:#f8fafc;flex-wrap:wrap;"><div style="flex:1;min-width:280px;"><p style="font-size:.8rem;font-weight:700;color:#3b82f6;text-transform:uppercase;letter-spacing:.1em;margin:0 0 10px;">Bienvenidos</p><h1 style="font-size:2.4rem;font-weight:800;color:#0f172a;margin:0 0 16px;line-height:1.2;">Tu solucion financiera de confianza</h1><p style="color:#64748b;margin:0 0 28px;line-height:1.7;">Descripcion de beneficios del servicio o producto que ofrecen.</p><a href="#" style="display:inline-block;padding:13px 30px;background:#0f172a;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;margin-right:10px;">Conocer mas</a><a href="#" style="display:inline-block;padding:13px 30px;border:2px solid #0f172a;color:#0f172a;border-radius:8px;font-weight:700;text-decoration:none;">Asociarme</a></div><div style="flex:1;min-width:240px;text-align:center;"><img src="https://placehold.co/520x360/e2e8f0/94a3b8?text=Imagen" style="width:100%;border-radius:14px;box-shadow:0 20px 40px rgba(0,0,0,.12);" alt="Header imagen"></div></section>'
    });

    bm.add('header-gradient', { label:'Hero gradiente', category:'Header', media:'🌈',
      content:'<section data-sipet-bg-image="1" style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 50%,#0f2845 100%);color:#fff;padding:100px 5%;text-align:center;"><p style="font-size:.8rem;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:.14em;margin:0 0 14px;">Bienvenidos a</p><h1 style="font-size:3rem;font-weight:900;line-height:1.1;margin:0 0 20px;letter-spacing:-.02em;">MiEmpresa</h1><p style="font-size:1.15rem;color:#94a3b8;max-width:580px;margin:0 auto 36px;line-height:1.7;">Soluciones financieras a la medida de cada familia y empresa.</p><div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;"><a href="#" style="display:inline-block;padding:15px 36px;background:#3b82f6;color:#fff;border-radius:9px;font-weight:700;font-size:1rem;text-decoration:none;">Comenzar ahora</a><a href="#" style="display:inline-block;padding:15px 36px;background:rgba(255,255,255,.1);color:#e2e8f0;border-radius:9px;font-weight:600;font-size:1rem;text-decoration:none;border:1px solid rgba(255,255,255,.2);">Ver servicios</a></div></section>'
    });

    bm.add('header-split-dark', { label:'Header dividido', category:'Header', media:'🔀',
      content:'<section style="display:grid;grid-template-columns:1fr 1fr;min-height:480px;"><div style="background:#0f172a;color:#fff;padding:80px 5% 80px 6%;display:flex;flex-direction:column;justify-content:center;"><p style="font-size:.75rem;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:.1em;margin:0 0 12px;">Novedad 2026</p><h1 style="font-size:2.4rem;font-weight:800;line-height:1.2;margin:0 0 18px;">Abre tu cuenta en minutos</h1><p style="color:#94a3b8;line-height:1.7;margin:0 0 28px;">Sin papeleos, sin filas. Todo desde tu celular.</p><a href="#" style="display:inline-block;align-self:flex-start;padding:13px 28px;background:#3b82f6;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;">Empezar</a></div><div style="background:#1e3a5f;display:flex;align-items:center;justify-content:center;padding:40px;"><img src="https://placehold.co/420x320/1e3a8a/93c5fd?text=App+Preview" style="max-width:100%;border-radius:12px;box-shadow:0 16px 40px rgba(0,0,0,.4);" alt="App preview"></div></section>'
    });

    bm.add('header-minimal', { label:'Cabecera minimal', category:'Header', media:'▲',
      content:'<section style="padding:80px 5% 64px;max-width:1120px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(280px,.75fr);align-items:center;gap:40px;"><div><p style="font-size:.8rem;font-weight:700;color:#3b82f6;text-transform:uppercase;letter-spacing:.1em;margin:0 0 12px;">Blog / Artículo</p><h1 style="font-size:2.6rem;font-weight:800;color:#0f172a;line-height:1.2;margin:0 0 16px;">Titulo del articulo o pagina interna</h1><p style="font-size:1.05rem;color:#64748b;line-height:1.75;max-width:660px;margin:0;">Subtitulo o descripcion introductoria del contenido que viene a continuacion en esta pagina.</p></div><div style="display:flex;justify-content:flex-end;"><img src="https://placehold.co/420x280/e2e8f0/0f172a?text=Imagen" alt="Imagen de cabecera" style="width:100%;max-width:420px;border-radius:24px;object-fit:cover;box-shadow:0 24px 50px rgba(15,23,42,.14);"></div></section>'
    });

    bm.add('header-announcement', { label:'Barra anuncio', category:'Header', media:'📢',
      content:'<div style="background:var(--sidebar-bottom,#3b82f6);color:#fff;padding:10px 5%;text-align:center;font-size:.9rem;font-weight:500;display:flex;align-items:center;justify-content:center;gap:12px;">🎉 <strong>Oferta especial:</strong>&nbsp;Abre tu DPF antes del 31 de marzo y gana el doble de intereses.&nbsp;<a href="#" style="color:#fff;font-weight:700;text-decoration:underline;">Ver más →</a></div>'
    });

    addTypedBlock('header-fullphoto', { label:'Foto completa', category:'Header', media:'🌅',
      attributes: { 'data-sipet-bg-image':'1', style:'position:relative;min-height:calc(92vh - 72px);margin-top:72px;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#0f172a url(https://placehold.co/1600x900/1e3a5f/60a5fa?text=Tu+fotografía+aquí) center/cover no-repeat;' },
      components: `
  <!-- Gradiente elegante sobre la foto -->
  <div style="position:absolute;inset:0;background:linear-gradient(160deg,rgba(15,23,42,.72) 0%,rgba(15,23,42,.28) 55%,rgba(15,23,42,.65) 100%);"></div>
  <!-- Ruido de textura sutil (SVG inline) -->
  <div style="position:absolute;inset:0;opacity:.04;background-image:url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 MAINFrequency=%220.9%22 numOctaves=%224%22/></filter><rect width=%22200%22 height=%22200%22 filter=%22url(%23n)%22 opacity=%221%22/></svg>');background-size:200px;"></div>
  <!-- Contenido centrado -->
  <div style="position:relative;z-index:1;max-width:860px;margin:0 auto;padding:80px 5%;text-align:center;">
    <span style="display:inline-block;padding:5px 16px;background:rgba(59,130,246,.25);border:1px solid rgba(96,165,250,.4);border-radius:20px;font-size:.75rem;font-weight:700;color:#93c5fd;letter-spacing:.1em;text-transform:uppercase;margin-bottom:22px;backdrop-filter:blur(8px);">Bienvenidos a MiEmpresa</span>
    <h1 style="font-size:clamp(2.4rem,5vw,4rem);font-weight:900;color:#f8fafc;line-height:1.1;margin:0 0 22px;letter-spacing:-.03em;text-shadow:0 2px 24px rgba(0,0,0,.4);">
      Construyendo el futuro<br>
      <span style="background:linear-gradient(90deg,#60a5fa,#818cf8);-backendkit-background-clip:text;-backendkit-text-fill-color:transparent;background-clip:text;">financiero de tu familia</span>
    </h1>
    <p style="font-size:clamp(1rem,2vw,1.2rem);color:rgba(248,250,252,.75);max-width:620px;margin:0 auto 40px;line-height:1.75;text-shadow:0 1px 8px rgba(0,0,0,.3);">Más de 25 años acompañando a miles de socios con ahorro, crédito y servicios digitales pensados para tu bienestar.</p>
    <div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
      <a href="#" style="display:inline-flex;align-items:center;gap:8px;padding:15px 36px;background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff;border-radius:10px;font-weight:700;text-decoration:none;font-size:1rem;box-shadow:0 8px 32px rgba(59,130,246,.45);letter-spacing:.01em;">Comenzar ahora <span>→</span></a>
      <a href="#" style="display:inline-flex;align-items:center;gap:8px;padding:15px 36px;background:rgba(255,255,255,.1);backdrop-filter:blur(12px);color:#f8fafc;border:1px solid rgba(255,255,255,.25);border-radius:10px;font-weight:600;text-decoration:none;font-size:1rem;">Ver servicios</a>
    </div>
    <!-- Indicadores de confianza -->
    <div style="display:flex;gap:32px;justify-content:center;flex-wrap:wrap;margin-top:52px;padding-top:32px;border-top:1px solid rgba(255,255,255,.1);">
      <div style="text-align:center;"><div style="font-size:1.6rem;font-weight:800;color:#f8fafc;">12,000+</div><div style="font-size:.75rem;color:rgba(248,250,252,.55);margin-top:2px;text-transform:uppercase;letter-spacing:.06em;">Socios activos</div></div>
      <div style="text-align:center;"><div style="font-size:1.6rem;font-weight:800;color:#f8fafc;">25 años</div><div style="font-size:.75rem;color:rgba(248,250,252,.55);margin-top:2px;text-transform:uppercase;letter-spacing:.06em;">De experiencia</div></div>
      <div style="text-align:center;"><div style="font-size:1.6rem;font-weight:800;color:#f8fafc;">Q450M</div><div style="font-size:.75rem;color:rgba(248,250,252,.55);margin-top:2px;text-transform:uppercase;letter-spacing:.06em;">En cartera</div></div>
      <div style="text-align:center;"><div style="font-size:1.6rem;font-weight:800;color:#f8fafc;">8</div><div style="font-size:.75rem;color:rgba(248,250,252,.55);margin-top:2px;text-transform:uppercase;letter-spacing:.06em;">Sucursales</div></div>
    </div>
  </div>
  <!-- Flecha scroll -->
  <a href="#" style="position:absolute;bottom:28px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:6px;text-decoration:none;opacity:.55;z-index:2;animation:bounce 2s infinite;">
    <span style="font-size:.7rem;font-weight:600;color:#fff;text-transform:uppercase;letter-spacing:.1em;">Explorar</span>
    <svg width="20" height="12" viewBox="0 0 20 12" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 1 10 11 19 1"/></svg>
  </a>
  <style>@keyframes bounce{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(6px)}}</style>`
    });

    addTypedBlock('header-parallax-photo', { label:'Foto fija + scroll', category:'Header', media:'🧲',
      attributes: { 'data-sipet-bg-image':'1', style:'position:relative;min-height:180vh;background:transparent;' },
      components: `<div style="position:sticky;top:0;height:100vh;overflow:hidden;">
    <img src="https://placehold.co/1600x1100/0f172a/93c5fd?text=Foto+de+portada" alt="Foto fija" data-sipet-bg-target="1"
         style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;opacity:.78;">
    <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(15,23,42,.08) 0%,rgba(15,23,42,.18) 38%,rgba(15,23,42,.42) 100%);"></div>
    <div style="position:relative;z-index:1;height:100%;display:flex;align-items:center;justify-content:center;padding:0 6%;">
      <div style="max-width:860px;text-align:center;color:#fff;">
        <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#e2e8f0;margin-bottom:22px;backdrop-filter:blur(10px);">Experiencia inmersiva</div>
        <h1 style="font-size:clamp(2.8rem,5.6vw,5.4rem);line-height:.98;font-weight:900;letter-spacing:-.05em;margin:0 0 20px;text-shadow:0 10px 30px rgba(0,0,0,.35);">La fotografía se queda fija mientras la página avanza</h1>
        <p style="font-size:1.08rem;line-height:1.85;color:rgba(226,232,240,.88);max-width:620px;margin:0 auto 32px;text-shadow:0 2px 10px rgba(0,0,0,.28);">Úsalo para portadas narrativas, mensajes de marca o campañas visuales donde la imagen domina y el scroll genera el efecto de profundidad.</p>
        <div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
          <a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;background:#ffffff;color:#0f172a;font-weight:800;text-decoration:none;">Explorar contenido</a>
          <a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.08);color:#f8fafc;font-weight:700;text-decoration:none;backdrop-filter:blur(10px);">Ver servicios</a>
        </div>
      </div>
    </div>
    <div style="position:absolute;left:50%;bottom:26px;transform:translateX(-50%);z-index:2;display:flex;flex-direction:column;align-items:center;gap:8px;color:#fff;opacity:.76;">
      <span style="font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;">Desplaza</span>
      <svg width="18" height="26" viewBox="0 0 18 26" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="1.5" y="1.5" width="15" height="23" rx="7.5"></rect><path d="M9 6v6"></path></svg>
    </div>
  </div>
  <div style="position:relative;z-index:3;margin-top:-22vh;padding:0 6% 96px;">
    <div style="max-width:1120px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;">
      <div style="padding:28px;border-radius:18px;background:rgba(255,255,255,.96);box-shadow:0 24px 60px rgba(15,23,42,.18);">
        <div style="font-size:.75rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;margin-bottom:10px;">Bloque 01</div>
        <h3 style="font-size:1.2rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Contenido sobrepuesto</h3>
        <p style="font-size:.95rem;line-height:1.75;color:#475569;margin:0;">Después de la portada fija, el resto del contenido puede empezar a subir sobre la fotografía para reforzar el efecto visual.</p>
      </div>
      <div style="padding:28px;border-radius:18px;background:rgba(255,255,255,.96);box-shadow:0 24px 60px rgba(15,23,42,.18);">
        <div style="font-size:.75rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#10b981;margin-bottom:10px;">Bloque 02</div>
        <h3 style="font-size:1.2rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Ideal para storytelling</h3>
        <p style="font-size:.95rem;line-height:1.75;color:#475569;margin:0;">Puedes dejar la foto de fondo fija y después insertar mensajes, estadísticas o beneficios para que el scroll cuente una historia.</p>
      </div>
      <div style="padding:28px;border-radius:18px;background:rgba(255,255,255,.96);box-shadow:0 24px 60px rgba(15,23,42,.18);">
        <div style="font-size:.75rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#8b5cf6;margin-bottom:10px;">Bloque 03</div>
        <h3 style="font-size:1.2rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Editable desde el canvas</h3>
        <p style="font-size:.95rem;line-height:1.75;color:#475569;margin:0;">La imagen puede cambiarse con el selector del builder y los textos quedan editables como cualquier otro bloque del header.</p>
      </div>
    </div>
  </div>
`
    });

    addTypedBlock('header-collage', { label:'Collage premium', category:'Header', media:'🖼️',
      attributes: { style:'display:grid;grid-template-columns:1fr 1fr;min-height:100vh;background:#0f172a;overflow:hidden;' },
      components: `<!-- Columna izquierda: texto + badges -->
  <div style="display:flex;flex-direction:column;justify-content:center;padding:80px 5% 80px 7%;position:relative;z-index:1;">
    <!-- Borde decorativo izquierdo -->
    <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,transparent,#3b82f6 40%,#818cf8 75%,transparent);"></div>
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:rgba(59,130,246,.15);border:1px solid rgba(59,130,246,.3);border-radius:20px;font-size:.72rem;font-weight:700;color:#60a5fa;letter-spacing:.1em;text-transform:uppercase;margin-bottom:28px;width:fit-content;">
      <span style="width:6px;height:6px;border-radius:50%;background:#3b82f6;animation:pulse 2s infinite;"></span>
      Desde 2001
    </span>
    <h1 style="font-size:clamp(2rem,4vw,3.4rem);font-weight:900;color:#f8fafc;line-height:1.1;margin:0 0 20px;letter-spacing:-.03em;">
      Tu cooperativa,<br>
      <span style="background:linear-gradient(90deg,#60a5fa 0%,#a78bfa 100%);-backendkit-background-clip:text;-backendkit-text-fill-color:transparent;background-clip:text;">siempre contigo</span>
    </h1>
    <p style="font-size:1rem;color:#94a3b8;line-height:1.8;max-width:420px;margin:0 0 36px;">Ahorro, crédito y servicios digitales diseñados para acompañarte en cada etapa de tu vida financiera.</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:48px;">
      <a href="#" style="display:inline-flex;align-items:center;gap:8px;padding:13px 28px;background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff;border-radius:9px;font-weight:700;text-decoration:none;font-size:.9rem;box-shadow:0 6px 24px rgba(59,130,246,.4);">Asociarme ahora <span>→</span></a>
      <a href="#" style="display:inline-flex;align-items:center;gap:8px;padding:13px 28px;background:rgba(255,255,255,.06);color:#e2e8f0;border:1px solid rgba(255,255,255,.12);border-radius:9px;font-weight:600;text-decoration:none;font-size:.9rem;">Ver servicios</a>
    </div>
    <!-- Trust badges -->
    <div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:8px;"><div style="width:36px;height:36px;border-radius:8px;background:rgba(59,130,246,.15);display:flex;align-items:center;justify-content:center;font-size:1rem;">🏛</div><div><div style="font-size:.72rem;color:#64748b;text-transform:uppercase;letter-spacing:.05em;">Supervisado por</div><div style="font-size:.8rem;font-weight:700;color:#94a3b8;">BANGUAT</div></div></div>
      <div style="width:1px;height:32px;background:rgba(255,255,255,.08);"></div>
      <div style="display:flex;align-items:center;gap:8px;"><div style="width:36px;height:36px;border-radius:8px;background:rgba(16,185,129,.12);display:flex;align-items:center;justify-content:center;font-size:1rem;">🔒</div><div><div style="font-size:.72rem;color:#64748b;text-transform:uppercase;letter-spacing:.05em;">Depósitos</div><div style="font-size:.8rem;font-weight:700;color:#94a3b8;">Asegurados</div></div></div>
      <div style="width:1px;height:32px;background:rgba(255,255,255,.08);"></div>
      <div style="display:flex;align-items:center;gap:8px;"><div style="width:36px;height:36px;border-radius:8px;background:rgba(245,158,11,.12);display:flex;align-items:center;justify-content:center;font-size:1rem;">⭐</div><div><div style="font-size:.72rem;color:#64748b;text-transform:uppercase;letter-spacing:.05em;">Calificación</div><div style="font-size:.8rem;font-weight:700;color:#94a3b8;">AAA 2026</div></div></div>
    </div>
    <style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}</style>
  </div>
  <!-- Columna derecha: collage de fotos -->
  <div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr 1fr;gap:6px;padding:6px;position:relative;">
    <!-- Foto grande — ocupa 2 filas -->
    <div style="grid-column:1;grid-row:1/3;position:relative;overflow:hidden;border-radius:16px 0 0 0;">
      <img src="https://placehold.co/500x600/1e3a5f/60a5fa?text=Socios" alt="Socios" style="width:100%;height:100%;object-fit:cover;">
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(15,23,42,.75));"></div>
      <div style="position:absolute;bottom:16px;left:16px;right:16px;">
        <div style="font-size:.68rem;color:#93c5fd;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:4px;">Nuestros socios</div>
        <div style="font-size:1.2rem;font-weight:800;color:#fff;line-height:1.2;">12,000+<br><span style="font-size:.78rem;font-weight:400;color:rgba(255,255,255,.6);">familias confiando en nosotros</span></div>
      </div>
    </div>
    <!-- Foto superior derecha -->
    <div style="grid-column:2;grid-row:1;position:relative;overflow:hidden;border-radius:0 16px 0 0;">
      <img src="https://placehold.co/400x300/0c2461/818cf8?text=Ahorro" alt="Ahorro" style="width:100%;height:100%;object-fit:cover;">
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(12,36,97,.8));"></div>
      <div style="position:absolute;bottom:14px;left:14px;"><div style="font-size:.68rem;color:#a5b4fc;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Ahorro</div><div style="font-size:1rem;font-weight:700;color:#fff;">Tasa 3.5% anual</div></div>
    </div>
    <!-- Foto media derecha -->
    <div style="grid-column:2;grid-row:2;position:relative;overflow:hidden;">
      <img src="https://placehold.co/400x300/064e3b/34d399?text=Digital" alt="Digital" style="width:100%;height:100%;object-fit:cover;">
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(6,78,59,.8));"></div>
      <div style="position:absolute;bottom:14px;left:14px;"><div style="font-size:.68rem;color:#6ee7b7;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Banca Digital</div><div style="font-size:1rem;font-weight:700;color:#fff;">24/7 disponible</div></div>
    </div>
    <!-- Fila inferior: 2 fotos pequeñas -->
    <div style="grid-column:1;grid-row:3;position:relative;overflow:hidden;border-radius:0 0 0 16px;">
      <img src="https://placehold.co/400x220/3b1f6e/c4b5fd?text=Crédito" alt="Crédito" style="width:100%;height:100%;object-fit:cover;">
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(59,31,110,.85));"></div>
      <div style="position:absolute;bottom:12px;left:14px;"><div style="font-size:.65rem;color:#e9d5ff;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Crédito</div><div style="font-size:.95rem;font-weight:700;color:#fff;">Desde Q5,000</div></div>
    </div>
    <div style="grid-column:2;grid-row:3;position:relative;overflow:hidden;border-radius:0 0 16px 0;">
      <img src="https://placehold.co/400x220/7c2d12/fb923c?text=Sucursales" alt="Sucursales" style="width:100%;height:100%;object-fit:cover;">
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(124,45,18,.85));"></div>
      <div style="position:absolute;bottom:12px;left:14px;"><div style="font-size:.65rem;color:#fed7aa;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Sucursales</div><div style="font-size:.95rem;font-weight:700;color:#fff;">8 puntos de atención</div></div>
    </div>
  </div>`
    });

    bm.add('header-slider', { label:'Slider hero', category:'Header', media:'🎞',
      content: { type:'sipet-header-slider' }
    });

    /* ══════════════════════════════════════════════════
       3. SECCIÓN PRINCIPAL — bloques de contenido mayor
    ══════════════════════════════════════════════════ */
    addTypedBlock('sec-features', { label:'Características', category:'Secci\u00f3n principal', media:'⭐',
      attributes:{style:'padding:72px 5%;background:#fff;'},
      components:'<div style="text-align:center;margin-bottom:44px;"><h2 style="font-size:2rem;font-weight:800;color:#0f172a;margin:0 0 12px;">Nuestros servicios</h2><p style="color:#64748b;font-size:1rem;max-width:500px;margin:0 auto;">Descubre todo lo que podemos ofrecerte para tu bienestar financiero.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px;max-width:1100px;margin:0 auto;"><div style="background:#f8fafc;border-radius:14px;padding:32px 24px;text-align:center;"><div style="font-size:2.4rem;margin-bottom:14px;">💳</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Ahorro</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Haz crecer tu dinero con nuestras cuentas.</p></div><div style="background:#f8fafc;border-radius:14px;padding:32px 24px;text-align:center;"><div style="font-size:2.4rem;margin-bottom:14px;">🏦</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Creditos</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Prestamos con las mejores tasas del mercado.</p></div><div style="background:#f8fafc;border-radius:14px;padding:32px 24px;text-align:center;"><div style="font-size:2.4rem;margin-bottom:14px;">📱</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Digital</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Gestiona tu cuenta desde cualquier dispositivo.</p></div><div style="background:#f8fafc;border-radius:14px;padding:32px 24px;text-align:center;"><div style="font-size:2.4rem;margin-bottom:14px;">🔒</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Seguridad</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Fondos supervisados y auditados cada año.</p></div></div>'
    });

    addTypedBlock('sec-cards', { label:'Cards productos', category:'Secci\u00f3n principal', media:'🃏',
      attributes:{style:'padding:72px 5%;background:#f8fafc;'},
      components:'<div style="text-align:center;margin-bottom:40px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Nuestros productos</h2><p style="color:#64748b;font-size:1rem;">Elige el que mejor se adapta a tus necesidades.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;max-width:1100px;margin:0 auto;"><div style="background:#fff;border-radius:14px;padding:28px 24px;box-shadow:0 2px 16px rgba(0,0,0,.07);border-top:4px solid #3b82f6;"><div style="font-size:2rem;margin-bottom:14px;">💳</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Cuenta de Ahorro</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;margin:0 0 20px;">Haz crecer tu dinero con rendimientos competitivos y sin comisiones.</p><a href="#" style="display:inline-block;padding:9px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;">Saber mas</a></div><div style="background:#fff;border-radius:14px;padding:28px 24px;box-shadow:0 2px 16px rgba(0,0,0,.07);border-top:4px solid #10b981;"><div style="font-size:2rem;margin-bottom:14px;">🏦</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Credito Personal</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;margin:0 0 20px;">Financiamiento rapido con tasas preferenciales para socios.</p><a href="#" style="display:inline-block;padding:9px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;">Saber mas</a></div><div style="background:#fff;border-radius:14px;padding:28px 24px;box-shadow:0 2px 16px rgba(0,0,0,.07);border-top:4px solid #f59e0b;"><div style="font-size:2rem;margin-bottom:14px;">🏠</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Credito Hipotecario</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;margin:0 0 20px;">Adquiere tu vivienda con plazos flexibles y cuotas accesibles.</p><a href="#" style="display:inline-block;padding:9px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;">Saber mas</a></div></div>'
    });

    addTypedBlock('sec-stats', { label:'Estadisticas', category:'Secci\u00f3n principal', media:'📊',
      attributes:{style:'padding:56px 5%;background:#0f172a;color:#fff;text-align:center;'},
      components:'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:24px;max-width:960px;margin:0 auto;"><div><div style="font-size:2.6rem;font-weight:800;color:#3b82f6;">12,000+</div><div style="color:#94a3b8;font-size:.875rem;margin-top:4px;">Socios activos</div></div><div><div style="font-size:2.6rem;font-weight:800;color:#3b82f6;">25 anos</div><div style="color:#94a3b8;font-size:.875rem;margin-top:4px;">De experiencia</div></div><div><div style="font-size:2.6rem;font-weight:800;color:#3b82f6;">Q450M</div><div style="color:#94a3b8;font-size:.875rem;margin-top:4px;">En cartera</div></div><div><div style="font-size:2.6rem;font-weight:800;color:#3b82f6;">8</div><div style="color:#94a3b8;font-size:.875rem;margin-top:4px;">Sucursales</div></div></div>'
    });

    addTypedBlock('sec-cta', { label:'Call to Action', category:'Secci\u00f3n principal', media:'📣',
      attributes:{style:'background:#3b82f6;color:#fff;padding:72px 24px;text-align:center;'},
      components:'<h2 style="font-size:2.1rem;font-weight:800;margin:0 0 14px;">Listo para comenzar?</h2><p style="opacity:.87;margin:0 0 32px;font-size:1.05rem;max-width:520px;margin-left:auto;margin-right:auto;line-height:1.7;">Unete a miles de socios que ya confian en nosotros.</p><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;"><a href="#" style="display:inline-block;padding:14px 36px;background:#fff;color:#3b82f6;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Asociarme ahora</a><a href="#" style="display:inline-block;padding:14px 36px;background:transparent;color:#fff;border:2px solid rgba(255,255,255,.5);border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Conocer mas</a></div>'
    });

    addTypedBlock('sec-cta-dark', { label:'CTA oscuro', category:'Secci\u00f3n principal', media:'🎯',
      attributes:{style:'background:#0f172a;color:#fff;padding:72px 24px;text-align:center;'},
      components:'<h2 style="font-size:2rem;font-weight:800;margin:0 0 12px;">Listo para crecer?</h2><p style="opacity:.72;margin:0 0 28px;font-size:1.05rem;max-width:520px;margin-left:auto;margin-right:auto;">Contactanos y un asesor se comunicara contigo en menos de 24 horas.</p><a href="#" style="display:inline-block;padding:14px 36px;background:#3b82f6;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Contactar asesor</a>'
    });

    addTypedBlock('sec-tasas', { label:'Tasas de interes', category:'Secci\u00f3n principal', media:'📈',
      attributes:{style:'padding:64px 5%;background:#fff;'},
      components:'<div style="max-width:900px;margin:0 auto;"><div style="text-align:center;margin-bottom:36px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Tasas de interes vigentes</h2><p style="color:#64748b;">Actualizadas al '+new Date().toLocaleDateString('es-GT',{year:'numeric',month:'long',day:'numeric'})+'</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;"><div style="background:#f8fafc;border-radius:12px;padding:24px;border-left:4px solid #3b82f6;"><div style="font-size:.73rem;font-weight:700;color:#3b82f6;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Ahorro a la vista</div><div style="font-size:2.2rem;font-weight:800;color:#0f172a;line-height:1;">3.5%</div><div style="font-size:.82rem;color:#64748b;margin-top:4px;">Tasa anual</div></div><div style="background:#f8fafc;border-radius:12px;padding:24px;border-left:4px solid #10b981;"><div style="font-size:.73rem;font-weight:700;color:#10b981;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">DPF 6 meses</div><div style="font-size:2.2rem;font-weight:800;color:#0f172a;line-height:1;">6.25%</div><div style="font-size:.82rem;color:#64748b;margin-top:4px;">Tasa anual</div></div><div style="background:#f8fafc;border-radius:12px;padding:24px;border-left:4px solid #f59e0b;"><div style="font-size:.73rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Credito personal</div><div style="font-size:2.2rem;font-weight:800;color:#0f172a;line-height:1;">14%</div><div style="font-size:.82rem;color:#64748b;margin-top:4px;">Tasa anual</div></div><div style="background:#f8fafc;border-radius:12px;padding:24px;border-left:4px solid #8b5cf6;"><div style="font-size:.73rem;font-weight:700;color:#8b5cf6;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Credito hipotecario</div><div style="font-size:2.2rem;font-weight:800;color:#0f172a;line-height:1;">10%</div><div style="font-size:.82rem;color:#64748b;margin-top:4px;">Tasa anual</div></div></div><p style="text-align:center;font-size:.77rem;color:#94a3b8;margin-top:20px;">Las tasas pueden cambiar sin previo aviso. Consulte en sucursal.</p></div>'
    });

    addTypedBlock('sec-testimonios', { label:'Testimonios', category:'Secci\u00f3n principal', media:'💬',
      attributes:{style:'padding:72px 5%;background:#f8fafc;'},
      components:'<div style="text-align:center;margin-bottom:44px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Lo que dicen nuestros socios</h2><p style="color:#64748b;">Historias de exito de personas como tu.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1000px;margin:0 auto;"><div style="background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.06);"><p style="color:#475569;font-style:italic;font-size:.95rem;line-height:1.7;margin:0 0 20px;">&ldquo;Gracias a la cooperativa pude comprar mi casa y darle a mi familia una vida mejor.&rdquo;</p><div style="display:flex;align-items:center;gap:12px;"><div style="width:40px;height:40px;border-radius:50%;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-size:18px;">👤</div><div><strong style="display:block;font-size:.9rem;color:#0f172a;">Maria Lopez</strong><span style="font-size:.8rem;color:#94a3b8;">Socia desde 2015</span></div></div></div><div style="background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.06);"><p style="color:#475569;font-style:italic;font-size:.95rem;line-height:1.7;margin:0 0 20px;">&ldquo;El proceso para obtener mi credito fue muy sencillo. Excelente atencion y muy buenas tasas.&rdquo;</p><div style="display:flex;align-items:center;gap:12px;"><div style="width:40px;height:40px;border-radius:50%;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-size:18px;">👤</div><div><strong style="display:block;font-size:.9rem;color:#0f172a;">Carlos Mendez</strong><span style="font-size:.8rem;color:#94a3b8;">Socio desde 2019</span></div></div></div><div style="background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.06);"><p style="color:#475569;font-style:italic;font-size:.95rem;line-height:1.7;margin:0 0 20px;">&ldquo;Nunca pense que ahorrar seria tan facil. La app es intuitiva y siempre hay un asesor disponible.&rdquo;</p><div style="display:flex;align-items:center;gap:12px;"><div style="width:40px;height:40px;border-radius:50%;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-size:18px;">👤</div><div><strong style="display:block;font-size:.9rem;color:#0f172a;">Ana Ramirez</strong><span style="font-size:.8rem;color:#94a3b8;">Socia desde 2021</span></div></div></div></div>'
    });

    addTypedBlock('sec-faq', { label:'Preguntas frecuentes', category:'Secci\u00f3n principal', media:'❓',
      attributes:{style:'padding:72px 5%;background:#fff;'},
      components:'<div style="max-width:720px;margin:0 auto;"><div style="text-align:center;margin-bottom:44px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Preguntas frecuentes</h2><p style="color:#64748b;">Respuestas a las dudas mas comunes sobre nuestros servicios.</p></div><div style="display:flex;flex-direction:column;gap:12px;"><details style="background:#f8fafc;border-radius:10px;padding:0;border:1px solid #e2e8f0;overflow:hidden;"><summary style="padding:16px 20px;font-weight:600;color:#0f172a;cursor:pointer;font-size:.95rem;list-style:none;">¿Como puedo abrir una cuenta?</summary><div style="padding:0 20px 16px;color:#64748b;font-size:.9rem;line-height:1.7;">Puedes abrir tu cuenta en cualquiera de nuestras sucursales con tu DPI vigente y un deposito inicial de Q100. Tambien puedes iniciar el proceso en linea.</div></details><details style="background:#f8fafc;border-radius:10px;padding:0;border:1px solid #e2e8f0;overflow:hidden;"><summary style="padding:16px 20px;font-weight:600;color:#0f172a;cursor:pointer;font-size:.95rem;list-style:none;">¿Cuales son los requisitos para un credito?</summary><div style="padding:0 20px 16px;color:#64748b;font-size:.9rem;line-height:1.7;">Necesitas ser socio activo, tener al menos 6 meses de antiguedad, presentar DPI, recibos de salario o declaracion de ingresos, y garantia dependiendo del monto.</div></details><details style="background:#f8fafc;border-radius:10px;padding:0;border:1px solid #e2e8f0;overflow:hidden;"><summary style="padding:16px 20px;font-weight:600;color:#0f172a;cursor:pointer;font-size:.95rem;list-style:none;">¿Mis fondos estan seguros?</summary><div style="padding:0 20px 16px;color:#64748b;font-size:.9rem;line-height:1.7;">Si. Nuestra cooperativa esta supervisada por el BANGUAT y auditada anualmente por firmas independientes. Los depositos estan protegidos hasta Q100,000.</div></details><details style="background:#f8fafc;border-radius:10px;padding:0;border:1px solid #e2e8f0;overflow:hidden;"><summary style="padding:16px 20px;font-weight:600;color:#0f172a;cursor:pointer;font-size:.95rem;list-style:none;">¿Tienen banca en linea?</summary><div style="padding:0 20px 16px;color:#64748b;font-size:.9rem;line-height:1.7;">Si, contamos con app movil y portal backend donde puedes consultar saldos, realizar transferencias y pagar servicios las 24 horas del dia.</div></details></div></div>'
    });

    addTypedBlock('sec-mapa', { label:'Mapa / Sucursal', category:'Secci\u00f3n principal', media:'📍',
      attributes:{style:'padding:64px 5%;background:#f8fafc;'},
      components:'<div style="max-width:1100px;margin:0 auto;"><div style="text-align:center;margin-bottom:36px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Donde encontrarnos</h2><p style="color:#64748b;">Visita cualquiera de nuestras sucursales.</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:start;"><div style="background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.06);"><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 16px;">Sucursal Central</h3><div style="display:flex;flex-direction:column;gap:12px;font-size:.9rem;color:#475569;"><div style="display:flex;gap:10px;align-items:flex-start;"><span>📍</span><span>4a Avenida 12-34, Zona 1, Guatemala</span></div><div style="display:flex;gap:10px;align-items:center;"><span>📞</span><span>(502) 2222-3333</span></div><div style="display:flex;gap:10px;align-items:center;"><span>🕐</span><span>Lunes a Viernes: 8:00 - 17:00 hrs</span></div><div style="display:flex;gap:10px;align-items:center;"><span>✉</span><span>info@cooperativa.com</span></div></div></div><div style="border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.1);min-height:280px;background:#e2e8f0;"><iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3860.3!2d-90.5069!3d14.6349!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTTCsDM4JzA1LjYiTiA5MMKwMzAnMjQuOCJX!5e0!3m2!1ses!2sgt!4v1000000000000" width="100%" height="280" style="border:none;display:block;" allowfullscreen loading="lazy"></iframe></div></div></div>'
    });

    addTypedBlock('sec-contacto', { label:'Formulario contacto', category:'Secci\u00f3n principal', media:'📬',
      attributes:{style:'padding:72px 5%;background:#fff;'},
      components:'<div style="max-width:560px;margin:0 auto;text-align:center;"><h2 style="font-size:2rem;font-weight:800;color:#0f172a;margin:0 0 12px;">Como podemos ayudarte?</h2><p style="color:#64748b;margin:0 0 32px;">Escribenos y nos pondremos en contacto contigo.</p><form style="display:flex;flex-direction:column;gap:14px;text-align:left;" onsubmit="return false;"><input type="text" placeholder="Nombre completo" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><input type="email" placeholder="Correo electronico" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><textarea placeholder="Tu mensaje..." rows="4" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;resize:vertical;"></textarea><button type="submit" style="padding:13px;background:#0f172a;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;">Enviar mensaje</button></form></div>'
    });

    addTypedBlock('sec-precios', { label:'Tabla de precios', category:'Secci\u00f3n principal', media:'💰',
      attributes:{style:'padding:72px 5%;background:#f8fafc;'},
      components:'<div style="text-align:center;margin-bottom:44px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Nuestros planes</h2><p style="color:#64748b;">Elige el plan ideal para tus necesidades.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px;max-width:960px;margin:0 auto;"><div style="background:#fff;border-radius:14px;padding:32px 24px;box-shadow:0 2px 12px rgba(0,0,0,.07);border:1px solid #e2e8f0;text-align:center;"><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Basico</h3><div style="font-size:2.4rem;font-weight:800;color:#0f172a;margin:12px 0;"><sup style="font-size:1rem;">Q</sup>0</div><div style="font-size:.8rem;color:#94a3b8;margin-bottom:20px;">/ mes</div><ul style="list-style:none;text-align:left;display:flex;flex-direction:column;gap:10px;margin:0 0 24px;font-size:.9rem;color:#475569;"><li>✅ Hasta 5 transacciones</li><li>✅ Cuenta de ahorro</li><li>❌ Creditos</li><li>❌ App movil</li></ul><a href="#" style="display:block;padding:11px;border:2px solid #e2e8f0;border-radius:8px;font-weight:700;text-decoration:none;color:#0f172a;">Comenzar gratis</a></div><div style="background:#0f172a;border-radius:14px;padding:32px 24px;box-shadow:0 8px 32px rgba(15,23,42,.3);text-align:center;transform:scale(1.03);"><div style="font-size:.7rem;background:#3b82f6;color:#fff;padding:3px 10px;border-radius:20px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;display:inline-block;margin-bottom:12px;">Mas popular</div><h3 style="font-size:1rem;font-weight:700;color:#fff;margin:0 0 8px;">Pro</h3><div style="font-size:2.4rem;font-weight:800;color:#fff;margin:12px 0;"><sup style="font-size:1rem;">Q</sup>50</div><div style="font-size:.8rem;color:#94a3b8;margin-bottom:20px;">/ mes</div><ul style="list-style:none;text-align:left;display:flex;flex-direction:column;gap:10px;margin:0 0 24px;font-size:.9rem;color:#94a3b8;"><li>✅ Transacciones ilimitadas</li><li>✅ Cuenta de ahorro</li><li>✅ Creditos preaprobados</li><li>✅ App movil premium</li></ul><a href="#" style="display:block;padding:11px;background:#3b82f6;border-radius:8px;font-weight:700;text-decoration:none;color:#fff;">Suscribirme</a></div><div style="background:#fff;border-radius:14px;padding:32px 24px;box-shadow:0 2px 12px rgba(0,0,0,.07);border:1px solid #e2e8f0;text-align:center;"><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Empresarial</h3><div style="font-size:2.4rem;font-weight:800;color:#0f172a;margin:12px 0;"><sup style="font-size:1rem;">Q</sup>200</div><div style="font-size:.8rem;color:#94a3b8;margin-bottom:20px;">/ mes</div><ul style="list-style:none;text-align:left;display:flex;flex-direction:column;gap:10px;margin:0 0 24px;font-size:.9rem;color:#475569;"><li>✅ Todo en Pro</li><li>✅ Multiples usuarios</li><li>✅ API bancaria</li><li>✅ Asesor dedicado</li></ul><a href="#" style="display:block;padding:11px;border:2px solid #e2e8f0;border-radius:8px;font-weight:700;text-decoration:none;color:#0f172a;">Contactar ventas</a></div></div>'
    });

    /* ══════════════════════════════════════════════════
       4. TIENDA — bloques estilo WooCommerce
    ══════════════════════════════════════════════════ */
    bm.add('shop-hero', { label:'Hero tienda', category:'Tienda', media:'🛍',
      content:'<section style="padding:84px 5%;background:linear-gradient(135deg,#fff7ed 0%,#ffffff 52%,#eff6ff 100%);"><div style="max-width:1180px;margin:0 auto;display:grid;grid-template-columns:1.05fr .95fr;gap:36px;align-items:center;"><div><div style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;background:#ffffff;border:1px solid #fed7aa;color:#c2410c;font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:18px;">Nueva colección</div><h1 style="font-size:clamp(2.4rem,5vw,4.4rem);line-height:1.02;font-weight:900;letter-spacing:-.04em;color:#111827;margin:0 0 18px;">Diseña una portada de tienda con estilo moderno</h1><p style="font-size:1rem;line-height:1.8;color:#6b7280;max-width:560px;margin:0 0 28px;">Bloque principal para ecommerce con mensaje comercial, promociones y llamados a la acción como en una home de tienda online.</p><div style="display:flex;gap:14px;flex-wrap:wrap;"><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:14px 28px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:800;">Comprar ahora</a><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:14px 28px;border-radius:10px;background:#fff;border:1px solid #d1d5db;color:#111827;text-decoration:none;font-weight:700;">Ver catálogo</a></div></div><div style="position:relative;"><div style="position:absolute;inset:auto -18px -18px auto;width:160px;height:160px;border-radius:24px;background:#fde68a;"></div><img src="https://placehold.co/720x640/f3f4f6/94a3b8?text=Producto+destacado" alt="Producto destacado" style="position:relative;width:100%;border-radius:28px;box-shadow:0 28px 70px rgba(17,24,39,.18);"></div></div></section>'
    });

    bm.add('shop-grid', { label:'Grid productos', category:'Tienda', media:'🧺',
      content:'<section style="padding:72px 5%;background:#f9fafb;"><div style="max-width:1180px;margin:0 auto;"><div style="display:flex;justify-content:space-between;align-items:end;gap:16px;flex-wrap:wrap;margin-bottom:28px;"><div><div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Tienda</div><h2 style="font-size:2rem;font-weight:900;color:#111827;margin:0;">Productos destacados</h2></div><a href="#" style="color:#111827;text-decoration:none;font-weight:700;">Ver todo →</a></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:22px;"><article style="background:#fff;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;box-shadow:0 10px 30px rgba(17,24,39,.06);"><img src="https://placehold.co/560x420/e5e7eb/6b7280?text=Producto+1" alt="" style="width:100%;aspect-ratio:4/3;object-fit:cover;"><div style="padding:18px;"><div style="font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Categoría</div><h3 style="font-size:1rem;font-weight:800;color:#111827;margin:0 0 6px;">Nombre del producto</h3><div style="font-size:.9rem;color:#6b7280;margin-bottom:14px;">Descripción corta de venta.</div><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;"><div><span style="font-size:1.1rem;font-weight:900;color:#111827;">Q199</span> <span style="font-size:.85rem;color:#9ca3af;text-decoration:line-through;">Q249</span></div><a href="#" style="padding:10px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:700;font-size:.88rem;">Agregar</a></div></div></article><article style="background:#fff;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;box-shadow:0 10px 30px rgba(17,24,39,.06);"><img src="https://placehold.co/560x420/dbeafe/2563eb?text=Producto+2" alt="" style="width:100%;aspect-ratio:4/3;object-fit:cover;"><div style="padding:18px;"><div style="font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Categoría</div><h3 style="font-size:1rem;font-weight:800;color:#111827;margin:0 0 6px;">Nombre del producto</h3><div style="font-size:.9rem;color:#6b7280;margin-bottom:14px;">Descripción corta de venta.</div><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;"><div><span style="font-size:1.1rem;font-weight:900;color:#111827;">Q349</span></div><a href="#" style="padding:10px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:700;font-size:.88rem;">Agregar</a></div></div></article><article style="background:#fff;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;box-shadow:0 10px 30px rgba(17,24,39,.06);"><img src="https://placehold.co/560x420/fce7f3/db2777?text=Producto+3" alt="" style="width:100%;aspect-ratio:4/3;object-fit:cover;"><div style="padding:18px;"><div style="font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Categoría</div><h3 style="font-size:1rem;font-weight:800;color:#111827;margin:0 0 6px;">Nombre del producto</h3><div style="font-size:.9rem;color:#6b7280;margin-bottom:14px;">Descripción corta de venta.</div><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;"><div><span style="font-size:1.1rem;font-weight:900;color:#111827;">Q129</span></div><a href="#" style="padding:10px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:700;font-size:.88rem;">Agregar</a></div></div></article><article style="background:#fff;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;box-shadow:0 10px 30px rgba(17,24,39,.06);"><img src="https://placehold.co/560x420/ecfccb/65a30d?text=Producto+4" alt="" style="width:100%;aspect-ratio:4/3;object-fit:cover;"><div style="padding:18px;"><div style="font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Categoría</div><h3 style="font-size:1rem;font-weight:800;color:#111827;margin:0 0 6px;">Nombre del producto</h3><div style="font-size:.9rem;color:#6b7280;margin-bottom:14px;">Descripción corta de venta.</div><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;"><div><span style="font-size:1.1rem;font-weight:900;color:#111827;">Q269</span></div><a href="#" style="padding:10px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:700;font-size:.88rem;">Agregar</a></div></div></article></div></div></section>'
    });

    bm.add('shop-product-card', { label:'Tarjeta producto', category:'Tienda', media:'🏷',
      content:'<article style="max-width:320px;background:#fff;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;box-shadow:0 10px 30px rgba(17,24,39,.07);"><div style="position:relative;"><img src="https://placehold.co/640x520/e5e7eb/6b7280?text=Producto" alt="Producto" style="width:100%;aspect-ratio:1/1;object-fit:cover;"><span style="position:absolute;top:14px;left:14px;padding:6px 10px;border-radius:999px;background:#111827;color:#fff;font-size:.72rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;">Nuevo</span></div><div style="padding:18px;"><div style="font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Accesorios</div><h3 style="font-size:1.05rem;font-weight:800;color:#111827;margin:0 0 8px;">Nombre del producto</h3><p style="font-size:.92rem;line-height:1.7;color:#6b7280;margin:0 0 16px;">Breve texto comercial para explicar el beneficio principal del producto.</p><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;"><div style="display:flex;align-items:center;gap:8px;"><span style="font-size:1.25rem;font-weight:900;color:#111827;">Q249</span><span style="font-size:.85rem;color:#9ca3af;text-decoration:line-through;">Q299</span></div><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:11px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:700;font-size:.88rem;">Agregar al carrito</a></div></div></article>'
    });

    bm.add('shop-categories', { label:'Categorías tienda', category:'Tienda', media:'🗂',
      content:'<section style="padding:64px 5%;background:#fff;"><div style="max-width:1180px;margin:0 auto;"><div style="text-align:center;margin-bottom:28px;"><div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Explorar</div><h2 style="font-size:1.9rem;font-weight:900;color:#111827;margin:0;">Categorías principales</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;"><a href="#" style="position:relative;display:block;min-height:240px;border-radius:22px;overflow:hidden;text-decoration:none;"><img src="https://placehold.co/700x700/fef3c7/f59e0b?text=Hogar" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;"><div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 35%,rgba(17,24,39,.76) 100%);"></div><div style="position:absolute;left:18px;right:18px;bottom:18px;color:#fff;"><div style="font-size:1.1rem;font-weight:900;margin-bottom:4px;">Hogar</div><div style="font-size:.88rem;opacity:.82;">24 productos</div></div></a><a href="#" style="position:relative;display:block;min-height:240px;border-radius:22px;overflow:hidden;text-decoration:none;"><img src="https://placehold.co/700x700/dbeafe/2563eb?text=Tecnología" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;"><div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 35%,rgba(17,24,39,.76) 100%);"></div><div style="position:absolute;left:18px;right:18px;bottom:18px;color:#fff;"><div style="font-size:1.1rem;font-weight:900;margin-bottom:4px;">Tecnología</div><div style="font-size:.88rem;opacity:.82;">18 productos</div></div></a><a href="#" style="position:relative;display:block;min-height:240px;border-radius:22px;overflow:hidden;text-decoration:none;"><img src="https://placehold.co/700x700/fce7f3/db2777?text=Moda" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;"><div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 35%,rgba(17,24,39,.76) 100%);"></div><div style="position:absolute;left:18px;right:18px;bottom:18px;color:#fff;"><div style="font-size:1.1rem;font-weight:900;margin-bottom:4px;">Moda</div><div style="font-size:.88rem;opacity:.82;">32 productos</div></div></a><a href="#" style="position:relative;display:block;min-height:240px;border-radius:22px;overflow:hidden;text-decoration:none;"><img src="https://placehold.co/700x700/ecfccb/65a30d?text=Wellness" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;"><div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 35%,rgba(17,24,39,.76) 100%);"></div><div style="position:absolute;left:18px;right:18px;bottom:18px;color:#fff;"><div style="font-size:1.1rem;font-weight:900;margin-bottom:4px;">Wellness</div><div style="font-size:.88rem;opacity:.82;">14 productos</div></div></a></div></div></section>'
    });

    bm.add('shop-promo-banner', { label:'Banner promo', category:'Tienda', media:'🎟',
      content:'<section style="padding:56px 5%;background:#111827;"><div style="max-width:1180px;margin:0 auto;display:grid;grid-template-columns:1.2fr .8fr;gap:24px;align-items:center;"><div><div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#93c5fd;margin-bottom:10px;">Oferta de la semana</div><h2 style="font-size:2.3rem;font-weight:900;color:#fff;line-height:1.05;margin:0 0 14px;">Hasta 40% de descuento en productos seleccionados</h2><p style="font-size:1rem;line-height:1.8;color:#9ca3af;max-width:560px;margin:0 0 24px;">Bloque promocional para campañas, cupones, temporadas o liquidaciones.</p><div style="display:flex;gap:12px;flex-wrap:wrap;"><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:14px 26px;border-radius:10px;background:#fff;color:#111827;text-decoration:none;font-weight:800;">Comprar ahora</a><div style="display:inline-flex;align-items:center;justify-content:center;padding:14px 20px;border-radius:10px;background:rgba(255,255,255,.08);border:1px dashed rgba(255,255,255,.25);color:#fff;font-weight:800;letter-spacing:.08em;">CUPÓN: TIENDA40</div></div></div><div style="background:linear-gradient(135deg,#2563eb,#7c3aed);border-radius:28px;padding:34px 30px;color:#fff;box-shadow:0 24px 60px rgba(0,0,0,.18);"><div style="font-size:.8rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;opacity:.82;margin-bottom:8px;">Tiempo limitado</div><div style="font-size:3.2rem;font-weight:900;line-height:1;">40%</div><div style="font-size:1rem;font-weight:700;margin-top:8px;">descuento</div><p style="font-size:.92rem;line-height:1.7;opacity:.85;margin:14px 0 0;">Ideal para destacar campañas como en una tienda online comercial.</p></div></div></section>'
    });

    bm.add('shop-promocion1', { label:'Promocion1', category:'Tienda', media:'🖼️',
      content:'<section style="padding:28px 5%;background:#eef2f7;"><div style="max-width:1180px;margin:0 auto;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;"><article style="display:grid;grid-template-columns:minmax(280px,1.1fr) minmax(220px,.9fr);min-height:270px;background:#40bfcd;border-radius:18px;overflow:hidden;box-shadow:0 16px 40px rgba(15,23,42,.08);"><div style="padding:38px 42px;color:#fff;display:flex;flex-direction:column;justify-content:center;"><div style="font-size:2.25rem;font-weight:900;line-height:1.05;text-transform:uppercase;margin:0 0 14px;">10% OFF ON YOUR<br>FIRST ORDER</div><div style="font-size:1.05rem;font-weight:700;line-height:1.45;margin:0 0 24px;">use code <span style="color:#124b79;">TENOFFDOT</span></div><div style="font-size:.95rem;opacity:.82;">Minimum $100 purchase</div></div><div><img src="https://placehold.co/720x540/f4f4f5/0f172a?text=Sube+tu+foto" alt="Imagen promocional" style="width:100%;height:100%;object-fit:cover;display:block;"></div></article><article style="display:grid;grid-template-columns:minmax(220px,.9fr) minmax(280px,1.1fr);min-height:270px;background:#1487c9;border-radius:18px;overflow:hidden;box-shadow:0 16px 40px rgba(15,23,42,.08);"><div><img src="https://placehold.co/720x540/e5e7eb/0f172a?text=Sube+tu+foto" alt="Imagen promocional" style="width:100%;height:100%;object-fit:cover;display:block;"></div><div style="padding:38px 42px;color:#fff;display:flex;flex-direction:column;justify-content:center;"><div style="font-size:2.25rem;font-weight:900;line-height:1.05;text-transform:uppercase;margin:0 0 14px;">$20 OFF ON YOUR<br>FIRST ORDER</div><div style="font-size:1.05rem;font-weight:700;line-height:1.45;color:#fbbf24;margin:0 0 24px;">with all credit cards</div><div style="font-size:.95rem;opacity:.82;">Minimum $100 purchase</div></div></article></div></section>'
    });

    bm.add('shop-promocion2', { label:'Promocion2', category:'Tienda', media:'🪧',
      content:'<section style="padding:28px 5%;background:#eef2f7;"><div style="max-width:1180px;margin:0 auto;position:relative;min-height:300px;border-radius:18px;overflow:hidden;box-shadow:0 18px 44px rgba(15,23,42,.1);"><img src="https://placehold.co/1600x520/cbd5e1/0f172a?text=Sube+tu+foto" alt="Imagen promocional" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;"><div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(15,23,42,.14) 0%,rgba(149,222,208,.56) 44%,rgba(149,222,208,.9) 100%);"></div><div style="position:absolute;left:0;top:0;width:0;height:0;border-top:120px solid #ff6b73;border-right:120px solid transparent;"></div><div style="position:absolute;left:18px;top:20px;transform:rotate(-45deg);transform-origin:left top;font-size:1.1rem;font-weight:900;letter-spacing:.08em;color:#fff;text-transform:uppercase;">New</div><div style="position:absolute;left:10px;top:52px;background:#ffffffd9;color:#444;padding:6px 12px;border-radius:3px;font-size:.95rem;box-shadow:0 8px 18px rgba(15,23,42,.12);">buy-now</div><div style="position:relative;z-index:1;min-height:300px;display:flex;align-items:center;justify-content:flex-end;padding:42px 56px;"><div style="max-width:470px;text-align:left;color:#fff;"><div style="font-size:3.2rem;font-weight:900;line-height:1.02;text-transform:uppercase;margin:0 0 16px;">Amazing Sunglasses</div><div style="font-size:1.2rem;line-height:1.6;margin:0;">Get 40% off on selected items</div></div></div></div></section>'
    });

    bm.add('shop-recomendaciones', { label:'Recomendaciones', category:'Tienda', media:'🎯',
      content:'<section style="padding:26px 5%;background:#ffffff;"><div style="max-width:1280px;margin:0 auto;"><div style="display:flex;gap:28px;overflow-x:auto;padding-bottom:8px;"><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/e2e8f0/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Baby & Kids</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/f8e7b0/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Beauty & Personal...</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">6 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/e5e7eb/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Electronics</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/f2e8e5/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Fashion & Acceso...</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">3 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/faf0ca/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Grocery & Fruits</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/fde68a/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Health & Wellness</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/dbeafe/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Home & Furniture</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/e5e7eb/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Household & Esse...</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article><article style="min-width:150px;text-align:center;"><div style="width:150px;height:150px;margin:0 auto 16px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;overflow:hidden;"><img src="https://placehold.co/220x220/ecfccb/0f172a?text=Foto" alt="Categoria" style="width:100%;height:100%;object-fit:cover;"></div><div style="font-size:1rem;font-weight:900;color:#0f172a;line-height:1.25;">Patio & Garden</div><div style="font-size:.95rem;color:#64748b;margin-top:6px;">7 Products</div></article></div></div></section>'
    });

    bm.add('shop-tiendas', { label:'Tiendas', category:'Tienda', media:'🏪',
      content:'<section style="padding:64px 5%;background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);"><div style="max-width:1180px;margin:0 auto;"><div style="display:flex;justify-content:space-between;align-items:end;gap:18px;flex-wrap:wrap;margin-bottom:28px;"><div><div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#2563eb;margin-bottom:8px;">Tiendas</div><h2 style="font-size:2rem;font-weight:900;color:#0f172a;margin:0;">Explora nuestras landing pages</h2></div><p style="max-width:420px;font-size:.96rem;line-height:1.7;color:#64748b;margin:0;">Cada logo puede enlazarse a la landing page de una tienda distinta. Cambia imagen, nombre y vínculo desde el builder.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:18px;"><a href=\"#\" style=\"display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 18px;border-radius:24px;background:#ffffff;text-decoration:none;box-shadow:0 18px 38px rgba(15,23,42,.12),0 4px 12px rgba(15,23,42,.06);border:1px solid rgba(226,232,240,.9);\"><div style=\"width:112px;height:112px;border-radius:28px;background:#f8fafc;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(226,232,240,.85),0 14px 30px rgba(15,23,42,.10);overflow:hidden;\"><img src=\"https://placehold.co/220x220/ffffff/0f172a?text=Logo+1\" alt=\"Logo tienda\" style=\"width:78%;height:78%;object-fit:contain;display:block;\"></div><div style=\"font-size:1rem;font-weight:800;color:#0f172a;text-align:center;\">Tienda Centro</div></a><a href=\"#\" style=\"display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 18px;border-radius:24px;background:#ffffff;text-decoration:none;box-shadow:0 18px 38px rgba(15,23,42,.12),0 4px 12px rgba(15,23,42,.06);border:1px solid rgba(226,232,240,.9);\"><div style=\"width:112px;height:112px;border-radius:28px;background:#f8fafc;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(226,232,240,.85),0 14px 30px rgba(15,23,42,.10);overflow:hidden;\"><img src=\"https://placehold.co/220x220/ffffff/1d4ed8?text=Logo+2\" alt=\"Logo tienda\" style=\"width:78%;height:78%;object-fit:contain;display:block;\"></div><div style=\"font-size:1rem;font-weight:800;color:#0f172a;text-align:center;\">Tienda Norte</div></a><a href=\"#\" style=\"display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 18px;border-radius:24px;background:#ffffff;text-decoration:none;box-shadow:0 18px 38px rgba(15,23,42,.12),0 4px 12px rgba(15,23,42,.06);border:1px solid rgba(226,232,240,.9);\"><div style=\"width:112px;height:112px;border-radius:28px;background:#f8fafc;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(226,232,240,.85),0 14px 30px rgba(15,23,42,.10);overflow:hidden;\"><img src=\"https://placehold.co/220x220/ffffff/7c3aed?text=Logo+3\" alt=\"Logo tienda\" style=\"width:78%;height:78%;object-fit:contain;display:block;\"></div><div style=\"font-size:1rem;font-weight:800;color:#0f172a;text-align:center;\">Tienda Sur</div></a><a href=\"#\" style=\"display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 18px;border-radius:24px;background:#ffffff;text-decoration:none;box-shadow:0 18px 38px rgba(15,23,42,.12),0 4px 12px rgba(15,23,42,.06);border:1px solid rgba(226,232,240,.9);\"><div style=\"width:112px;height:112px;border-radius:28px;background:#f8fafc;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(226,232,240,.85),0 14px 30px rgba(15,23,42,.10);overflow:hidden;\"><img src=\"https://placehold.co/220x220/ffffff/ea580c?text=Logo+4\" alt=\"Logo tienda\" style=\"width:78%;height:78%;object-fit:contain;display:block;\"></div><div style=\"font-size:1rem;font-weight:800;color:#0f172a;text-align:center;\">Tienda Select</div></a><a href=\"#\" style=\"display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 18px;border-radius:24px;background:#ffffff;text-decoration:none;box-shadow:0 18px 38px rgba(15,23,42,.12),0 4px 12px rgba(15,23,42,.06);border:1px solid rgba(226,232,240,.9);\"><div style=\"width:112px;height:112px;border-radius:28px;background:#f8fafc;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(226,232,240,.85),0 14px 30px rgba(15,23,42,.10);overflow:hidden;\"><img src=\"https://placehold.co/220x220/ffffff/059669?text=Logo+5\" alt=\"Logo tienda\" style=\"width:78%;height:78%;object-fit:contain;display:block;\"></div><div style=\"font-size:1rem;font-weight:800;color:#0f172a;text-align:center;\">Tienda Market</div></a><a href=\"#\" style=\"display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 18px;border-radius:24px;background:#ffffff;text-decoration:none;box-shadow:0 18px 38px rgba(15,23,42,.12),0 4px 12px rgba(15,23,42,.06);border:1px solid rgba(226,232,240,.9);\"><div style=\"width:112px;height:112px;border-radius:28px;background:#f8fafc;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px rgba(226,232,240,.85),0 14px 30px rgba(15,23,42,.10);overflow:hidden;\"><img src=\"https://placehold.co/220x220/ffffff/be123c?text=Logo+6\" alt=\"Logo tienda\" style=\"width:78%;height:78%;object-fit:contain;display:block;\"></div><div style=\"font-size:1rem;font-weight:800;color:#0f172a;text-align:center;\">Tienda Plus</div></a></div></div></section>'
    });

    bm.add('shop-tiendas-premium-hero', { label:'Hero tiendas premium', category:'Tienda', media:'✨',
      content:'<section style="padding:32px 5%;background:#fff7ea;"><div style="max-width:1320px;margin:0 auto;border-radius:44px;padding:56px;overflow:hidden;background:radial-gradient(circle at 50% 45%, rgba(191,132,39,.92) 0%, rgba(126,84,29,.96) 48%, rgba(58,39,25,1) 100%);box-shadow:0 30px 70px rgba(68,43,16,.22);"><div style="display:grid;grid-template-columns:minmax(0,1.5fr) minmax(340px,.85fr);gap:34px;align-items:center;"><div><div style="display:inline-flex;align-items:center;gap:14px;padding:14px 22px;border-radius:999px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);color:#fff;font-size:1rem;font-weight:800;letter-spacing:.03em;text-transform:uppercase;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06);"><span style="width:14px;height:14px;border-radius:50%;background:#ffd27d;box-shadow:0 0 0 6px rgba(255,210,125,.15);display:inline-block;"></span><span>Calidad y precio a tu alcance</span></div><div style="margin-top:34px;"><h2 style="font-size:clamp(3.1rem,7vw,5.2rem);line-height:.96;font-weight:900;letter-spacing:-.06em;color:#fff;margin:0 0 12px;">Las mejores tiendas</h2><p style="font-size:1.1rem;line-height:1.5;color:rgba(255,244,230,.94);margin:0;">A un clic de distancia</p></div><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin-top:34px;"><div style="padding:26px 30px;border-radius:30px;background:rgba(226,193,142,.18);border:1px solid rgba(255,255,255,.12);min-height:118px;"><div style="font-size:1rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,241,220,.88);margin-bottom:14px;">Productos</div><div style="font-size:3.2rem;font-weight:900;color:#fff;line-height:1;">0</div></div><div style="padding:26px 30px;border-radius:30px;background:rgba(226,193,142,.18);border:1px solid rgba(255,255,255,.12);min-height:118px;"><div style="font-size:1rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,241,220,.88);margin-bottom:14px;">Categorías</div><div style="font-size:3.2rem;font-weight:900;color:#fff;line-height:1;">0</div></div><div style="padding:26px 30px;border-radius:30px;background:rgba(226,193,142,.18);border:1px solid rgba(255,255,255,.12);min-height:118px;"><div style="font-size:1rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,241,220,.88);margin-bottom:14px;">Tiendas</div><div style="font-size:3.2rem;font-weight:900;color:#fff;line-height:1;">1</div></div></div></div><aside style="padding:34px 36px;border-radius:34px;background:rgba(160,128,86,.34);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(4px);"><div style="display:flex;gap:18px;align-items:flex-start;"><div style="width:114px;height:114px;border-radius:36px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 14px 26px rgba(0,0,0,.12);overflow:hidden;flex:0 0 auto;"><img src="https://placehold.co/220x220/ffffff/8b5e34?text=Logo" alt="Logo de tienda" style="width:82%;height:82%;object-fit:contain;"></div><div style="min-width:0;"><h3 style="font-size:1.15rem;line-height:1.2;font-weight:900;color:#fff;margin:6px 0 0;">Calidad y precio a tu alcance</h3></div></div><div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:28px;"><div style="padding:22px 26px;border-radius:28px;background:rgba(227,205,173,.18);border:1px solid rgba(255,255,255,.12);min-height:96px;"><div style="font-size:1rem;font-weight:900;color:#fff;line-height:1.2;">Ofertas</div></div><div style="padding:22px 26px;border-radius:28px;background:rgba(227,205,173,.18);border:1px solid rgba(255,255,255,.12);min-height:96px;"><div style="font-size:1rem;font-weight:900;color:#fff;line-height:1.2;">Cliente destacado</div></div></div><div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:32px;"><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:18px 28px;border-radius:999px;background:#fff;color:#4f341c;text-decoration:none;font-size:1rem;font-weight:900;box-shadow:0 14px 30px rgba(0,0,0,.10);">Contactar tienda</a><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:18px 28px;border-radius:999px;background:transparent;border:1px solid rgba(255,255,255,.22);color:#fff;text-decoration:none;font-size:1rem;font-weight:800;">Ver perfil</a></div></aside></div></div></section>'
    });

    bm.add('shop-mini-cart', { label:'Mini carrito', category:'Tienda', media:'🛒',
      content:'<aside style="max-width:360px;background:#fff;border:1px solid #e5e7eb;border-radius:22px;overflow:hidden;box-shadow:0 18px 50px rgba(17,24,39,.08);"><div style="padding:20px 22px;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;"><h3 style="font-size:1.05rem;font-weight:900;color:#111827;margin:0;">Carrito</h3><span style="padding:6px 10px;border-radius:999px;background:#111827;color:#fff;font-size:.74rem;font-weight:800;">3 items</span></div><div style="padding:18px 22px;display:flex;flex-direction:column;gap:16px;"><div style="display:grid;grid-template-columns:68px 1fr auto;gap:12px;align-items:center;"><img src="https://placehold.co/180x180/e5e7eb/6b7280?text=1" alt="" style="width:68px;height:68px;border-radius:14px;object-fit:cover;"><div><div style="font-size:.92rem;font-weight:800;color:#111827;">Producto uno</div><div style="font-size:.84rem;color:#6b7280;">Cantidad: 1</div></div><div style="font-size:.92rem;font-weight:800;color:#111827;">Q129</div></div><div style="display:grid;grid-template-columns:68px 1fr auto;gap:12px;align-items:center;"><img src="https://placehold.co/180x180/dbeafe/2563eb?text=2" alt="" style="width:68px;height:68px;border-radius:14px;object-fit:cover;"><div><div style="font-size:.92rem;font-weight:800;color:#111827;">Producto dos</div><div style="font-size:.84rem;color:#6b7280;">Cantidad: 2</div></div><div style="font-size:.92rem;font-weight:800;color:#111827;">Q248</div></div></div><div style="padding:18px 22px;border-top:1px solid #e5e7eb;background:#f9fafb;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;"><span style="font-size:.9rem;color:#6b7280;">Subtotal</span><strong style="font-size:1.05rem;color:#111827;">Q377</strong></div><div style="display:flex;gap:10px;"><a href="#" style="flex:1;display:inline-flex;align-items:center;justify-content:center;padding:12px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:800;font-size:.9rem;">Finalizar compra</a><a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:12px 14px;border-radius:10px;background:#fff;border:1px solid #d1d5db;color:#111827;text-decoration:none;font-weight:700;font-size:.9rem;">Ver carrito</a></div></div></aside>'
    });

    /* ══════════════════════════════════════════════════
       5. CONTENIDO — bloques de contenido granular
    ══════════════════════════════════════════════════ */
    bm.add('text-rich', { label:'Texto', category:'Contenido', media:'📝',
      content:'<div style="max-width:760px;margin:0 auto;padding:48px 24px;font-size:1rem;line-height:1.8;color:#1e293b;"><h2 style="font-size:1.8rem;font-weight:700;margin:0 0 16px;">Titulo de seccion</h2><p>Parrafo de texto. Haz clic para editar el contenido.</p></div>'
    });

    bm.add('text-cols', { label:'Texto 2 col', category:'Contenido', media:'📄',
      content:'<div style="display:grid;grid-template-columns:1fr 1fr;gap:32px;padding:48px 5%;max-width:1100px;margin:0 auto;"><div><h3 style="font-size:1.2rem;font-weight:700;color:#0f172a;margin:0 0 12px;">Columna izquierda</h3><p style="color:#64748b;line-height:1.8;font-size:.95rem;">Texto de la primera columna. Haz clic para editar.</p></div><div><h3 style="font-size:1.2rem;font-weight:700;color:#0f172a;margin:0 0 12px;">Columna derecha</h3><p style="color:#64748b;line-height:1.8;font-size:.95rem;">Texto de la segunda columna. Haz clic para editar.</p></div></div>'
    });

    bm.add('image-block', { label:'Imagen', category:'Contenido', media:'🖼',
      content:'<div style="padding:24px;text-align:center;"><img src="https://placehold.co/800x400/e2e8f0/94a3b8?text=Imagen" alt="Imagen" style="max-width:100%;border-radius:10px;"><p style="font-size:.85rem;color:#94a3b8;margin-top:10px;">Descripcion opcional</p></div>'
    });

    bm.add('image-text', { label:'Imagen + texto', category:'Contenido', media:'🖼',
      content:'<div style="display:flex;gap:32px;align-items:flex-start;padding:40px 5%;max-width:1100px;margin:0 auto;flex-wrap:wrap;"><img src="https://placehold.co/420x280/e2e8f0/94a3b8?text=Imagen" style="width:380px;max-width:100%;border-radius:10px;flex-shrink:0;" alt=""><div style="flex:1;min-width:240px;"><h3 style="font-size:1.3rem;font-weight:700;color:#0f172a;margin:0 0 12px;">Titulo del bloque</h3><p style="color:#64748b;line-height:1.8;">Descripcion detallada. Haz clic en cualquier elemento para editarlo directamente en el canvas.</p><a href="#" style="display:inline-block;margin-top:16px;padding:10px 24px;background:#0f172a;color:#fff;border-radius:7px;font-weight:700;text-decoration:none;font-size:.9rem;">Saber mas</a></div></div>'
    });

    bm.add('galeria', { label:'Galeria fotos', category:'Contenido', media:'🗃',
      content:'<section style="padding:48px 5%;"><div style="text-align:center;margin-bottom:28px;"><h2 style="font-size:1.6rem;font-weight:800;color:#0f172a;margin:0 0 8px;">Galeria</h2><p style="color:#64748b;font-size:.9rem;">Un vistazo a nuestra cooperativa.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;"><img src="https://placehold.co/400x300/dbeafe/3b82f6?text=Foto+1" style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;" alt=""><img src="https://placehold.co/400x300/dcfce7/16a34a?text=Foto+2" style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;" alt=""><img src="https://placehold.co/400x300/fef9c3/ca8a04?text=Foto+3" style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;" alt=""><img src="https://placehold.co/400x300/fce7f3/db2777?text=Foto+4" style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;" alt=""><img src="https://placehold.co/400x300/ede9fe/7c3aed?text=Foto+5" style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;" alt=""><img src="https://placehold.co/400x300/e2e8f0/475569?text=Foto+6" style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;" alt=""></div></section>'
    });

    bm.add('button-block', { label:'Boton', category:'Contenido', media:'🔘',
      content:'<div style="padding:16px;text-align:center;"><a href="#" style="display:inline-block;padding:13px 32px;background:#3b82f6;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Boton de accion</a></div>'
    });

    bm.add('video-yt', { label:'Video YouTube', category:'Contenido', media:'▶',
      content:'<div style="padding:24px;"><div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;background:#0f172a;"><iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;" allowfullscreen></iframe></div></div>'
    });

    bm.add('columns-2', { label:'2 Columnas', category:'Contenido', media:'⊞',
      content:'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:32px 5%;"><div style="padding:16px;border:1px dashed #e2e8f0;border-radius:8px;min-height:80px;">Columna 1</div><div style="padding:16px;border:1px dashed #e2e8f0;border-radius:8px;min-height:80px;">Columna 2</div></div>'
    });

    bm.add('columns-3', { label:'3 Columnas', category:'Contenido', media:'⊟',
      content:'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;padding:32px 5%;"><div style="padding:14px;border:1px dashed #e2e8f0;border-radius:8px;min-height:60px;">Col 1</div><div style="padding:14px;border:1px dashed #e2e8f0;border-radius:8px;min-height:60px;">Col 2</div><div style="padding:14px;border:1px dashed #e2e8f0;border-radius:8px;min-height:60px;">Col 3</div></div>'
    });

    bm.add('section-wrap', { label:'Contenedor secci\u00f3n', category:'Contenido', media:'□',
      content:'<section style="padding:48px 5%;background:#fff;"><div style="max-width:1100px;margin:0 auto;"><p style="color:#64748b;">Contenido de la secci\u00f3n</p></div></section>'
    });

    bm.add('divider', { label:'Divisor', category:'Contenido', media:'━',
      content:'<hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 24px;">'
    });

    bm.add('spacer', { label:'Espacio', category:'Contenido', media:'↕',
      content:'<div style="height:48px;"></div>'
    });

    bm.add('html-raw', { label:'HTML libre', category:'Contenido', media:'</>',
      content:{ type:'sipet-html-raw' }
    });

    /* ══════════════════════════════════════════════════
       6. BARRA LATERAL — widgets y sidebars
    ══════════════════════════════════════════════════ */
    bm.add('sidebar-basic', { label:'Sidebar basico', category:'Barra lateral', media:'⬛',
      content:'<aside style="width:280px;display:flex;flex-direction:column;gap:20px;padding:24px;"><div style="background:#f8fafc;border-radius:12px;padding:20px;border:1px solid #e2e8f0;"><h3 style="font-size:.85rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:.06em;margin:0 0 12px;">Menu</h3><ul style="list-style:none;display:flex;flex-direction:column;gap:6px;"><li><a href="#" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:7px;color:#475569;text-decoration:none;font-size:.9rem;background:#fff;">🏠 Inicio</a></li><li><a href="#" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:7px;color:#fff;text-decoration:none;font-size:.9rem;background:#0f172a;font-weight:600;">💳 Servicios</a></li><li><a href="#" style="display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:7px;color:#475569;text-decoration:none;font-size:.9rem;background:#fff;">📞 Contacto</a></li></ul></div></aside>'
    });

    bm.add('sidebar-search', { label:'Widget busqueda', category:'Barra lateral', media:'🔍',
      content:'<div style="background:#f8fafc;border-radius:12px;padding:20px;border:1px solid #e2e8f0;"><h3 style="font-size:.85rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:.06em;margin:0 0 12px;">Buscar</h3><div style="display:flex;gap:6px;"><input type="text" placeholder="Buscar..." style="flex:1;padding:9px 12px;border:1px solid #e2e8f0;border-radius:7px;font-size:.875rem;outline:none;"><button style="padding:9px 14px;background:#0f172a;color:#fff;border:none;border-radius:7px;cursor:pointer;font-size:.875rem;">🔍</button></div></div>'
    });

    bm.add('sidebar-categories', { label:'Categorias', category:'Barra lateral', media:'📂',
      content:'<div style="background:#f8fafc;border-radius:12px;padding:20px;border:1px solid #e2e8f0;"><h3 style="font-size:.85rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:.06em;margin:0 0 14px;">Categorias</h3><ul style="list-style:none;display:flex;flex-direction:column;gap:4px;"><li style="display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:7px;cursor:pointer;background:#fff;"><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;">Ahorro</a><span style="background:#e2e8f0;border-radius:20px;padding:2px 8px;font-size:.75rem;color:#475569;font-weight:600;">12</span></li><li style="display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:7px;cursor:pointer;background:#fff;"><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;">Creditos</a><span style="background:#e2e8f0;border-radius:20px;padding:2px 8px;font-size:.75rem;color:#475569;font-weight:600;">8</span></li><li style="display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:7px;cursor:pointer;background:#fff;"><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;">Noticias</a><span style="background:#e2e8f0;border-radius:20px;padding:2px 8px;font-size:.75rem;color:#475569;font-weight:600;">5</span></li><li style="display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:7px;cursor:pointer;background:#fff;"><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;">Eventos</a><span style="background:#e2e8f0;border-radius:20px;padding:2px 8px;font-size:.75rem;color:#475569;font-weight:600;">3</span></li></ul></div>'
    });

    bm.add('sidebar-contact-widget', { label:'Info de contacto', category:'Barra lateral', media:'📞',
      content:'<div style="background:#0f172a;color:#fff;border-radius:12px;padding:24px;"><h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:0 0 16px;color:#60a5fa;">Contactanos</h3><div style="display:flex;flex-direction:column;gap:12px;font-size:.875rem;color:#94a3b8;"><div style="display:flex;gap:10px;align-items:flex-start;"><span>📍</span><span>4a Avenida 12-34, Zona 1</span></div><div style="display:flex;gap:10px;align-items:center;"><span>📞</span><span>(502) 2222-3333</span></div><div style="display:flex;gap:10px;align-items:center;"><span>✉</span><span>info@cooperativa.com</span></div><div style="display:flex;gap:10px;align-items:center;"><span>🕐</span><span>Lun–Vie: 8:00–17:00</span></div></div><a href="#" style="display:block;margin-top:16px;padding:10px;background:#3b82f6;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;font-size:.875rem;text-align:center;">Enviar mensaje</a></div>'
    });

    bm.add('sidebar-social', { label:'Redes sociales', category:'Barra lateral', media:'🌐',
      content:'<div style="background:#f8fafc;border-radius:12px;padding:20px;border:1px solid #e2e8f0;"><h3 style="font-size:.85rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:.06em;margin:0 0 14px;">Siguenos</h3><div style="display:flex;gap:10px;flex-wrap:wrap;"><a href="#" style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:#1877f2;color:#fff;border-radius:8px;font-size:.8rem;font-weight:600;text-decoration:none;">Facebook</a><a href="#" style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:linear-gradient(135deg,#f58529,#dd2a7b,#8134af);color:#fff;border-radius:8px;font-size:.8rem;font-weight:600;text-decoration:none;">Instagram</a><a href="#" style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:#1da1f2;color:#fff;border-radius:8px;font-size:.8rem;font-weight:600;text-decoration:none;">Twitter / X</a><a href="#" style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:#25d366;color:#fff;border-radius:8px;font-size:.8rem;font-weight:600;text-decoration:none;">WhatsApp</a></div></div>'
    });

    bm.add('sidebar-newsletter', { label:'Newsletter widget', category:'Barra lateral', media:'📰',
      content:'<div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);color:#fff;border-radius:12px;padding:24px;text-align:center;"><div style="font-size:1.8rem;margin-bottom:10px;">📧</div><h3 style="font-size:.95rem;font-weight:700;margin:0 0 6px;">Suscribete</h3><p style="font-size:.82rem;color:#94a3b8;margin:0 0 16px;line-height:1.6;">Recibe nuestras noticias y promociones.</p><form onsubmit="return false;" style="display:flex;flex-direction:column;gap:8px;"><input type="email" placeholder="tu@correo.com" style="padding:9px 12px;border-radius:7px;border:none;font-size:.875rem;outline:none;"><button type="submit" style="padding:9px;background:#3b82f6;color:#fff;border:none;border-radius:7px;font-weight:700;cursor:pointer;font-size:.875rem;">Suscribirse</button></form></div>'
    });

    bm.add('sidebar-cta-widget', { label:'CTA lateral', category:'Barra lateral', media:'🚀',
      content:'<div style="background:#3b82f6;color:#fff;border-radius:12px;padding:24px;text-align:center;"><div style="font-size:1.8rem;margin-bottom:10px;">🏦</div><h3 style="font-size:.95rem;font-weight:700;margin:0 0 8px;">Abre tu cuenta</h3><p style="font-size:.82rem;opacity:.87;margin:0 0 16px;line-height:1.6;">Empieza a ahorrar hoy. Sin comisiones.</p><a href="#" style="display:block;padding:10px;background:#fff;color:#3b82f6;border-radius:8px;font-weight:700;text-decoration:none;font-size:.875rem;">Empezar ahora →</a></div>'
    });

    /* ══════════════════════════════════════════════════
       7. FOOTER — pies de página
    ══════════════════════════════════════════════════ */
    bm.add('footer-full', { label:'Footer completo', category:'Estructura general', media:'🏛',
      content:'<footer style="background:#0f172a;color:#94a3b8;padding:56px 5% 24px;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:32px;margin-bottom:36px;"><div><h3 style="color:#f8fafc;font-size:1.05rem;font-weight:700;margin:0 0 12px;">MiEmpresa</h3><p style="font-size:.85rem;line-height:1.75;margin:0 0 16px;">Servicios financieros para toda la familia desde 2001.</p><div style="display:flex;gap:8px;"><a href="#" style="width:32px;height:32px;background:#1e293b;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;text-decoration:none;">f</a><a href="#" style="width:32px;height:32px;background:#1e293b;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;text-decoration:none;color:#94a3b8;">in</a></div></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:.06em;">Servicios</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:8px;font-size:.85rem;"><li><a href="#" style="color:#94a3b8;text-decoration:none;">Ahorro</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Creditos</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">DPF</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Banca digital</a></li></ul></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:.06em;">Empresa</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:8px;font-size:.85rem;"><li><a href="#" style="color:#94a3b8;text-decoration:none;">Nosotros</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Blog</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Sucursales</a></li></ul></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:.06em;">Contacto</h4><ul style="list-style:none;gap:8px;display:flex;flex-direction:column;font-size:.85rem;"><li>📞 (502) 2222-3333</li><li>✉ info@empresa.com</li><li>📍 Zona 1, Guatemala</li><li>🕐 Lun–Vie 8:00–17:00</li></ul></div></div><div style="border-top:1px solid #1e293b;padding-top:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;font-size:.8rem;"><span>© 2026 MiEmpresa. Todos los derechos reservados.</span><div style="display:flex;gap:16px;"><a href="#" style="color:#64748b;text-decoration:none;">Privacidad</a><a href="#" style="color:#64748b;text-decoration:none;">Terminos</a></div></div></footer>'
    });

    bm.add('footer-minimal', { label:'Footer minimal', category:'Estructura general', media:'➖',
      content:'<footer style="background:#0f172a;color:#64748b;padding:20px 5%;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:.82rem;"><span style="font-weight:700;color:#f8fafc;">MiEmpresa</span><span>© 2026 Todos los derechos reservados.</span><div style="display:flex;gap:16px;"><a href="#" style="color:#64748b;text-decoration:none;">Privacidad</a><a href="#" style="color:#64748b;text-decoration:none;">Cookies</a></div></footer>'
    });

    bm.add('footer-light', { label:'Footer claro', category:'Estructura general', media:'☀',
      content:'<footer style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:48px 5% 24px;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:28px;margin-bottom:28px;"><div><h3 style="font-size:1rem;font-weight:800;color:#0f172a;margin:0 0 10px;">MiEmpresa</h3><p style="font-size:.85rem;line-height:1.75;color:#64748b;">Soluciones financieras para cada etapa de tu vida.</p></div><div><h4 style="font-size:.8rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:.06em;margin:0 0 10px;">Servicios</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:7px;font-size:.875rem;"><li><a href="#" style="color:#475569;text-decoration:none;">Ahorro</a></li><li><a href="#" style="color:#475569;text-decoration:none;">Creditos</a></li><li><a href="#" style="color:#475569;text-decoration:none;">Banca digital</a></li></ul></div><div><h4 style="font-size:.8rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:.06em;margin:0 0 10px;">Contacto</h4><ul style="list-style:none;gap:7px;display:flex;flex-direction:column;font-size:.875rem;color:#475569;"><li>📞 (502) 2222-3333</li><li>✉ info@empresa.com</li></ul></div></div><div style="border-top:1px solid #e2e8f0;padding-top:18px;text-align:center;font-size:.8rem;color:#94a3b8;">© 2026 MiEmpresa. Todos los derechos reservados.</div></footer>'
    });

    bm.add('footer-social', { label:'Footer redes sociales', category:'Estructura general', media:'📲',
      content:'<footer style="background:#0f172a;color:#94a3b8;padding:48px 5% 24px;"><div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:32px;margin-bottom:32px;max-width:1100px;margin-left:auto;margin-right:auto;flex-wrap:wrap;"><div><h3 style="color:#f8fafc;font-size:1.05rem;font-weight:700;margin:0 0 10px;">MiEmpresa</h3><p style="font-size:.85rem;line-height:1.75;max-width:320px;">Comprometidos con el crecimiento financiero de nuestros socios.</p><div style="display:flex;gap:10px;margin-top:16px;"><a href="#" style="padding:8px 14px;background:#1877f2;color:#fff;border-radius:7px;font-size:.8rem;font-weight:600;text-decoration:none;">Facebook</a><a href="#" style="padding:8px 14px;background:linear-gradient(135deg,#f58529,#dd2a7b,#8134af);color:#fff;border-radius:7px;font-size:.8rem;font-weight:600;text-decoration:none;">Instagram</a><a href="#" style="padding:8px 14px;background:#25d366;color:#fff;border-radius:7px;font-size:.8rem;font-weight:600;text-decoration:none;">WhatsApp</a></div></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:.06em;">Servicios</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:8px;font-size:.85rem;"><li><a href="#" style="color:#94a3b8;text-decoration:none;">Ahorro</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Creditos</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">DPF</a></li></ul></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:.06em;">Legal</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:8px;font-size:.85rem;"><li><a href="#" style="color:#94a3b8;text-decoration:none;">Privacidad</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Terminos</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Cookies</a></li></ul></div></div><div style="border-top:1px solid #1e293b;padding-top:18px;text-align:center;font-size:.8rem;">© 2026 MiEmpresa. Todos los derechos reservados.</div></footer>'
    });

    bm.add('footer-newsletter', { label:'Footer + newsletter', category:'Estructura general', media:'📧',
      content:'<footer style="background:#0f172a;color:#94a3b8;"><div style="background:#1e293b;padding:40px 5%;"><div style="max-width:560px;margin:0 auto;text-align:center;"><h3 style="color:#f8fafc;font-size:1.1rem;font-weight:700;margin:0 0 8px;">Mantente informado</h3><p style="font-size:.875rem;margin:0 0 18px;">Suscribete y recibe noticias, tasas actualizadas y promociones.</p><form onsubmit="return false;" style="display:flex;gap:8px;max-width:400px;margin:0 auto;"><input type="email" placeholder="tu@correo.com" style="flex:1;padding:10px 14px;border-radius:7px;border:1px solid #334155;background:#0f172a;color:#f1f5f9;font-size:.875rem;outline:none;"><button type="submit" style="padding:10px 18px;background:#3b82f6;color:#fff;border:none;border-radius:7px;font-weight:700;cursor:pointer;white-space:nowrap;font-size:.875rem;">Suscribirse</button></form></div></div><div style="padding:40px 5% 24px;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:28px;max-width:1100px;margin:0 auto 28px;"><div><h3 style="color:#f8fafc;font-size:1rem;font-weight:700;margin:0 0 10px;">MiEmpresa</h3><p style="font-size:.85rem;line-height:1.75;">Servicios financieros seguros y confiables.</p></div><div><h4 style="color:#f8fafc;font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:0 0 10px;">Servicios</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:7px;font-size:.85rem;"><li><a href="#" style="color:#94a3b8;text-decoration:none;">Ahorro</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Creditos</a></li></ul></div><div><h4 style="color:#f8fafc;font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:0 0 10px;">Contacto</h4><ul style="list-style:none;gap:7px;display:flex;flex-direction:column;font-size:.85rem;"><li>📞 (502) 2222-3333</li><li>✉ info@empresa.com</li></ul></div></div><div style="border-top:1px solid #1e293b;padding-top:18px;text-align:center;font-size:.8rem;">© 2026 MiEmpresa. Todos los derechos reservados.</div></div></footer>'
    });

    /* ══════════════════════════════════════════════════
       8. MENÚ — navegación de página: tabs, breadcrumbs,
          paginación, anclas, menú desplegable, sidebar nav
    ══════════════════════════════════════════════════ */
    bm.add('menu-tabs', { label:'Tabs / pesta\u00f1as', category:'Estructura general', media:'📑',
      content:'<div style="border-bottom:2px solid #e2e8f0;position:sticky;top:0;z-index:100;background:#fff;"><div style="display:flex;gap:0;max-width:1100px;margin:0 auto;padding:0 5%;overflow-x:auto;scrollbar-width:none;">'
        +'<button style="padding:13px 20px;background:none;border:none;border-bottom:2px solid #3b82f6;margin-bottom:-2px;font-size:.9rem;font-weight:700;color:#3b82f6;cursor:pointer;white-space:nowrap;">Inicio</button>'
        +'<button style="padding:13px 20px;background:none;border:none;border-bottom:2px solid transparent;margin-bottom:-2px;font-size:.9rem;font-weight:500;color:#64748b;cursor:pointer;white-space:nowrap;">Servicios</button>'
        +'<button style="padding:13px 20px;background:none;border:none;border-bottom:2px solid transparent;margin-bottom:-2px;font-size:.9rem;font-weight:500;color:#64748b;cursor:pointer;white-space:nowrap;">Nosotros</button>'
        +'<button style="padding:13px 20px;background:none;border:none;border-bottom:2px solid transparent;margin-bottom:-2px;font-size:.9rem;font-weight:500;color:#64748b;cursor:pointer;white-space:nowrap;">Blog</button>'
        +'<button style="padding:13px 20px;background:none;border:none;border-bottom:2px solid transparent;margin-bottom:-2px;font-size:.9rem;font-weight:500;color:#64748b;cursor:pointer;white-space:nowrap;">Contacto</button>'
        +'</div></div>'
    });

    bm.add('menu-tabs-pill', { label:'Tabs pill', category:'Estructura general', media:'💊',
      content:'<div style="padding:16px 5%;position:sticky;top:0;z-index:100;background:#fff;"><div style="display:inline-flex;gap:6px;background:#f1f5f9;border-radius:10px;padding:5px;">'
        +'<button style="padding:8px 18px;background:#fff;border:none;border-radius:8px;font-size:.875rem;font-weight:600;color:#0f172a;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.1);">Todo</button>'
        +'<button style="padding:8px 18px;background:none;border:none;border-radius:8px;font-size:.875rem;font-weight:500;color:#64748b;cursor:pointer;">Ahorro</button>'
        +'<button style="padding:8px 18px;background:none;border:none;border-radius:8px;font-size:.875rem;font-weight:500;color:#64748b;cursor:pointer;">Credito</button>'
        +'<button style="padding:8px 18px;background:none;border:none;border-radius:8px;font-size:.875rem;font-weight:500;color:#64748b;cursor:pointer;">Digital</button>'
        +'</div></div>'
    });

    bm.add('menu-breadcrumb', { label:'Migas de pan', category:'Estructura general', media:'🍞',
      content:'<nav style="padding:12px 5%;background:#f8fafc;border-bottom:1px solid #e2e8f0;font-size:.85rem;position:sticky;top:0;z-index:100;">'
        +'<ol style="list-style:none;display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin:0;">'
        +'<li><a href="#" style="color:#3b82f6;text-decoration:none;font-weight:500;">Inicio</a></li>'
        +'<li style="color:#94a3b8;margin:0 4px;">›</li>'
        +'<li><a href="#" style="color:#3b82f6;text-decoration:none;font-weight:500;">Servicios</a></li>'
        +'<li style="color:#94a3b8;margin:0 4px;">›</li>'
        +'<li style="color:#475569;font-weight:600;">Credito Personal</li>'
        +'</ol></nav>'
    });

    bm.add('menu-breadcrumb-dark', { label:'Migas oscuras', category:'Estructura general', media:'🌑',
      content:'<nav style="padding:12px 5%;background:#0f172a;font-size:.85rem;position:sticky;top:0;z-index:100;">'
        +'<ol style="list-style:none;display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin:0;">'
        +'<li><a href="#" style="color:#60a5fa;text-decoration:none;font-weight:500;">Inicio</a></li>'
        +'<li style="color:#475569;margin:0 4px;">/</li>'
        +'<li><a href="#" style="color:#60a5fa;text-decoration:none;font-weight:500;">Blog</a></li>'
        +'<li style="color:#475569;margin:0 4px;">/</li>'
        +'<li style="color:#94a3b8;font-weight:500;">Articulo del mes</li>'
        +'</ol></nav>'
    });

    bm.add('menu-pagination', { label:'Paginaci\u00f3n', category:'Estructura general', media:'📄',
      content:'<div style="display:flex;justify-content:center;align-items:center;gap:6px;padding:16px 24px;position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid #e2e8f0;">'
        +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;color:#475569;text-decoration:none;font-size:.875rem;">‹</a>'
        +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;color:#475569;text-decoration:none;font-size:.875rem;">1</a>'
        +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:1px solid transparent;background:#0f172a;color:#fff;text-decoration:none;font-size:.875rem;font-weight:700;">2</a>'
        +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;color:#475569;text-decoration:none;font-size:.875rem;">3</a>'
        +'<span style="color:#94a3b8;font-size:.875rem;padding:0 4px;">…</span>'
        +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;color:#475569;text-decoration:none;font-size:.875rem;">8</a>'
        +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;color:#475569;text-decoration:none;font-size:.875rem;">›</a>'
        +'</div>'
    });

    bm.add('menu-anchors', { label:'Anclas / Accesos', category:'Estructura general', media:'⚓',
      content:'<div style="background:#f8fafc;border-bottom:1px solid #e2e8f0;position:sticky;top:0;z-index:90;">'
        +'<div style="display:flex;gap:0;max-width:1100px;margin:0 auto;padding:0 5%;overflow-x:auto;scrollbar-width:none;">'
        +'<a href="#ahorro"  style="padding:13px 16px;color:#64748b;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;white-space:nowrap;display:block;">Ahorro</a>'
        +'<a href="#credito" style="padding:13px 16px;color:#3b82f6;text-decoration:none;font-size:.875rem;font-weight:700;border-bottom:2px solid #3b82f6;white-space:nowrap;display:block;">Credito</a>'
        +'<a href="#dpf"     style="padding:13px 16px;color:#64748b;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;white-space:nowrap;display:block;">DPF</a>'
        +'<a href="#digital" style="padding:13px 16px;color:#64748b;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;white-space:nowrap;display:block;">Digital</a>'
        +'<a href="#seguros" style="padding:13px 16px;color:#64748b;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;white-space:nowrap;display:block;">Seguros</a>'
        +'</div></div>'
    });

    addTypedBlock('menu-dropdown-preview', { label:'Men\u00fa desplegable', category:'Estructura general', media:'▾',
      tagName:'nav',
      attributes:{style:'display:flex;align-items:center;gap:0;padding:0 5%;background:#fff;box-shadow:0 1px 8px rgba(0,0,0,.07);height:52px;position:sticky;top:0;z-index:100;'},
      components:'<a href="#" data-sipet-logo="1" style="font-size:1.2rem;font-weight:800;color:#0f172a;text-decoration:none;margin-right:24px;">MiEmpresa</a>'
        +'<div style="display:flex;gap:0;height:100%;align-items:stretch;">'
        +'<a href="#" style="display:flex;align-items:center;padding:0 14px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;">Inicio</a>'
        +'<details style="position:relative;height:100%;">'
        +'<summary style="display:flex;align-items:center;gap:4px;padding:0 14px;color:#0f172a;text-decoration:none;font-size:.875rem;font-weight:600;border-bottom:2px solid #3b82f6;height:100%;cursor:pointer;list-style:none;">Servicios <span style="font-size:10px;">▾</span></summary>'
        +'<div style="position:absolute;top:calc(100% + 2px);left:0;background:#fff;border-radius:10px;box-shadow:0 8px 32px rgba(0,0,0,.14);padding:10px 0;min-width:200px;z-index:200;">'
        +'<a href="#" style="display:block;padding:9px 18px;color:#475569;text-decoration:none;font-size:.875rem;">💳 Cuentas de Ahorro</a>'
        +'<a href="#" style="display:block;padding:9px 18px;color:#475569;text-decoration:none;font-size:.875rem;">🏦 Credito Personal</a>'
        +'<a href="#" style="display:block;padding:9px 18px;color:#475569;text-decoration:none;font-size:.875rem;">🏠 Credito Hipotecario</a>'
        +'<hr style="border:none;border-top:1px solid #f1f5f9;margin:6px 0;">'
        +'<a href="#" style="display:block;padding:9px 18px;color:#3b82f6;text-decoration:none;font-size:.875rem;font-weight:600;">Ver todos →</a>'
        +'</div></details>'
        +'<a href="#" style="display:flex;align-items:center;padding:0 14px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;">Nosotros</a>'
        +'<a href="#" style="display:flex;align-items:center;padding:0 14px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;border-bottom:2px solid transparent;">Contacto</a>'
        +'</div><div style="flex:1;"></div>'
        +'<a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:9px;padding:8px 18px;background:#0f172a;color:#fff;border-radius:7px;font-size:.85rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a>'
    });

    addTypedBlock('menu-mega', { label:'Mega men\u00fa', category:'Estructura general', media:'🗺',
      tagName:'nav',
      attributes:{style:'display:flex;align-items:center;justify-content:space-between;padding:0 5%;background:#fff;box-shadow:0 1px 8px rgba(0,0,0,.07);height:56px;position:sticky;top:0;z-index:100;'},
      components:`<a href="#" data-sipet-logo="1" style="font-size:1.2rem;font-weight:800;color:#0f172a;text-decoration:none;">MiEmpresa</a>
  <details style="position:relative;">
    <summary style="display:flex;align-items:center;gap:5px;padding:8px 14px;color:#0f172a;background:#fff;text-decoration:none;font-size:.875rem;font-weight:600;border:1px solid #e2e8f0;border-radius:8px;cursor:pointer;list-style:none;">
      Categorías <span style="font-size:10px;">▾</span>
    </summary>
    <div style="position:absolute;top:calc(100% + 8px);left:0;background:#fff;border-radius:12px;box-shadow:0 12px 40px rgba(0,0,0,.15);padding:20px;width:580px;z-index:300;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
      <a href="#" style="display:flex;flex-direction:column;gap:4px;padding:12px;border-radius:8px;text-decoration:none;background:#f8fafc;"><span style="font-size:1.2rem;">💳</span><strong style="font-size:.825rem;color:#0f172a;">Ahorro</strong><span style="font-size:.76rem;color:#64748b;">Cuentas y DPF</span></a>
      <a href="#" style="display:flex;flex-direction:column;gap:4px;padding:12px;border-radius:8px;text-decoration:none;background:#f8fafc;"><span style="font-size:1.2rem;">🏦</span><strong style="font-size:.825rem;color:#0f172a;">Créditos</strong><span style="font-size:.76rem;color:#64748b;">Personal e hipotecario</span></a>
      <a href="#" style="display:flex;flex-direction:column;gap:4px;padding:12px;border-radius:8px;text-decoration:none;background:#f8fafc;"><span style="font-size:1.2rem;">📱</span><strong style="font-size:.825rem;color:#0f172a;">Digital</strong><span style="font-size:.76rem;color:#64748b;">App y banca en línea</span></a>
      <a href="#" style="display:flex;flex-direction:column;gap:4px;padding:12px;border-radius:8px;text-decoration:none;background:#f8fafc;"><span style="font-size:1.2rem;">🔒</span><strong style="font-size:.825rem;color:#0f172a;">Seguros</strong><span style="font-size:.76rem;color:#64748b;">Protección familiar</span></a>
      <a href="#" style="display:flex;flex-direction:column;gap:4px;padding:12px;border-radius:8px;text-decoration:none;background:#f8fafc;"><span style="font-size:1.2rem;">🏢</span><strong style="font-size:.825rem;color:#0f172a;">Empresarial</strong><span style="font-size:.76rem;color:#64748b;">Para PYMES</span></a>
      <a href="#" style="display:flex;flex-direction:column;gap:4px;padding:12px;border-radius:8px;text-decoration:none;background:#f8fafc;"><span style="font-size:1.2rem;">📊</span><strong style="font-size:.825rem;color:#0f172a;">Inversiones</strong><span style="font-size:.76rem;color:#64748b;">DPF y fondos</span></a>
    </div>
  </details>
  <div style="display:flex;gap:8px;">
    <a href="#" style="padding:8px 16px;border:1px solid #e2e8f0;color:#475569;border-radius:7px;font-size:.875rem;font-weight:600;text-decoration:none;">Registrarse</a>
    <a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:9px;padding:8px 18px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a>
  </div>`
    });

    dc.addType('menu-sidenav-widget', {
      model: { defaults: {
        tagName: 'section',
        attributes: {
          'data-menu-sidenav': '1',
          style: 'display:block;position:relative;'
        },
        droppable: false,
        script: function(){
          var root = this;
          var aside = root.querySelector('[data-snav-aside]');
          var toggle = root.querySelector('[data-snav-toggle]');
          if(!aside || !toggle) return;
          root.classList.add('snav-open');
          aside.classList.remove('snav-hidden');
          toggle.addEventListener('click', function(){
            var open = root.classList.toggle('snav-open');
            aside.classList.toggle('snav-hidden', !open);
          });
        },
        components: `<style>
  [data-menu-sidenav="1"] {
    position: relative;
  }
  [data-menu-sidenav="1"] [data-snav-aside] {
    width: min(232px, calc(100vw - 48px));
    position: fixed; left: 24px; top: 88px;
    transition: transform .28s cubic-bezier(.4,0,.2,1), opacity .25s;
    z-index: 120;
  }
  [data-menu-sidenav="1"] [data-snav-aside].snav-hidden {
    transform: translateX(calc(-100% - 18px));
    opacity: 0;
    pointer-events: none;
  }
  [data-menu-sidenav="1"] [data-snav-main] {
    min-width: 0;
    padding: 32px 40px;
  }
  [data-menu-sidenav="1"] [data-snav-toggle] {
    position: fixed; left: 24px; top: 32px; z-index: 121;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 5px;
    width: 40px; height: 40px; flex-shrink: 0; cursor: pointer;
    border: 1px solid #e2e8f0; border-radius: 9px;
    background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,.07);
    transition: background .15s, box-shadow .15s;
  }
  [data-menu-sidenav="1"] [data-snav-toggle]:hover { background: #f1f5f9; box-shadow: 0 4px 14px rgba(0,0,0,.1); }
  [data-menu-sidenav="1"] [data-snav-toggle] .snav-bar {
    width: 18px; height: 2px; border-radius: 2px;
    background: #475569; transition: transform .25s, opacity .2s;
  }
  [data-menu-sidenav="1"].snav-open [data-snav-toggle] .snav-bar:nth-child(1){ transform: translateY(7px) rotate(45deg); }
  [data-menu-sidenav="1"].snav-open [data-snav-toggle] .snav-bar:nth-child(2){ opacity: 0; }
  [data-menu-sidenav="1"].snav-open [data-snav-toggle] .snav-bar:nth-child(3){ transform: translateY(-7px) rotate(-45deg); }
  @media (max-width: 640px) {
    [data-menu-sidenav="1"] [data-snav-toggle] {
      left: 14px; top: 14px;
    }
    [data-menu-sidenav="1"] [data-snav-aside] {
      left: 14px; top: 66px;
      width: min(232px, calc(100vw - 28px));
    }
    [data-menu-sidenav="1"] [data-snav-main] {
      padding: 24px 18px;
    }
  }
</style>
<button data-snav-toggle type="button" aria-label="Mostrar/ocultar menú">
  <span class="snav-bar"></span>
  <span class="snav-bar"></span>
  <span class="snav-bar"></span>
</button>
<aside data-snav-aside>
  <nav style="background:#f8fafc;border-radius:13px;padding:16px 12px;border:1px solid #e2e8f0;margin-top:32px;box-shadow:0 2px 12px rgba(0,0,0,.05);">
    <p style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8;margin:0 0 10px;padding:0 8px;">Navegación</p>
    <a href="#" style="display:flex;align-items:center;gap:9px;padding:10px 11px;border-radius:9px;background:#0f172a;color:#fff;text-decoration:none;font-size:.875rem;font-weight:600;margin-bottom:3px;">🏠 Inicio</a>
    <a href="#" style="display:flex;align-items:center;gap:9px;padding:10px 11px;border-radius:9px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;margin-bottom:3px;transition:background .12s;">💳 Servicios</a>
    <a href="#" style="display:flex;align-items:center;gap:9px;padding:10px 11px;border-radius:9px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;margin-bottom:3px;">📞 Contacto</a>
    <a href="#" style="display:flex;align-items:center;gap:9px;padding:10px 11px;border-radius:9px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;margin-bottom:3px;">🏦 Nosotros</a>
    <a href="#" style="display:flex;align-items:center;gap:9px;padding:10px 11px;border-radius:9px;color:#475569;text-decoration:none;font-size:.875rem;font-weight:500;">📰 Blog</a>
    <a data-sipet-auth-link="1" href="/web/inicio" style="display:flex;align-items:center;justify-content:center;gap:9px;padding:11px 14px;border-radius:10px;background:#0f172a;color:#fff;text-decoration:none;font-size:.875rem;font-weight:700;margin-top:14px;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a>
  </nav>
</aside>
<main data-snav-main>
  <h2 style="font-size:1.5rem;font-weight:800;color:#0f172a;margin:0 0 14px;">Contenido principal</h2>
  <p style="color:#64748b;line-height:1.8;">El contenido de la página va aquí. Puedes arrastrar cualquier bloque dentro de esta área. El panel lateral se puede ocultar con el botón ☰ de la izquierda.</p>
</main>`
      }},
      view: {}
    });
    bm.add('menu-sidenav', { label:'Nav lateral sticky', category:'Estructura general', media:'📌',
      content: { type:'menu-sidenav-widget' }
    });

    bm.add('menu-mobile-bar', { label:'Barra movil inferior', category:'Estructura general', media:'📲',
      content:'<nav style="position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #e2e8f0;display:flex;z-index:200;box-shadow:0 -4px 16px rgba(0,0,0,.08);">'
        +'<a href="#" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 4px;text-decoration:none;gap:3px;color:#3b82f6;"><span style="font-size:1.3rem;">🏠</span><span style="font-size:.65rem;font-weight:600;">Inicio</span></a>'
        +'<a href="#" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 4px;text-decoration:none;gap:3px;color:#94a3b8;"><span style="font-size:1.3rem;">💳</span><span style="font-size:.65rem;font-weight:500;">Servicios</span></a>'
        +'<a href="#" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 4px;text-decoration:none;gap:3px;color:#94a3b8;"><span style="font-size:1.3rem;">🔍</span><span style="font-size:.65rem;font-weight:500;">Buscar</span></a>'
        +'<a href="#" style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 4px;text-decoration:none;gap:3px;color:#94a3b8;"><span style="font-size:1.3rem;">👤</span><span style="font-size:.65rem;font-weight:500;">Perfil</span></a>'
        +'</nav>'
    });

    bm.add('menu-steps', { label:'Pasos / Wizard', category:'Estructura general', media:'🪜',
      content:'<div style="padding:28px 5%;background:#fff;">'
        +'<div style="display:flex;align-items:center;justify-content:center;gap:0;max-width:700px;margin:0 auto;">'
        +'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">'
        +'<div style="width:36px;height:36px;border-radius:50%;background:#3b82f6;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;">1</div>'
        +'<span style="font-size:.75rem;font-weight:600;color:#3b82f6;text-align:center;">Datos personales</span></div>'
        +'<div style="flex:1;height:2px;background:#3b82f6;margin-bottom:20px;"></div>'
        +'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">'
        +'<div style="width:36px;height:36px;border-radius:50%;background:#3b82f6;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;">✓</div>'
        +'<span style="font-size:.75rem;font-weight:600;color:#3b82f6;text-align:center;">Documentos</span></div>'
        +'<div style="flex:1;height:2px;background:#e2e8f0;margin-bottom:20px;"></div>'
        +'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">'
        +'<div style="width:36px;height:36px;border-radius:50%;background:#e2e8f0;color:#94a3b8;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;">3</div>'
        +'<span style="font-size:.75rem;font-weight:500;color:#94a3b8;text-align:center;">Confirmacion</span></div>'
        +'</div></div>'
    });

    bm.add('menu-tag-filter', { label:'Filtro por etiquetas', category:'Estructura general', media:'🏷',
      content:'<div style="padding:20px 5%;background:#f8fafc;border-bottom:1px solid #e2e8f0;">'
        +'<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">'
        +'<span style="font-size:.8rem;font-weight:600;color:#64748b;margin-right:4px;">Filtrar:</span>'
        +'<button style="padding:6px 14px;background:#0f172a;color:#fff;border:none;border-radius:20px;font-size:.8rem;font-weight:600;cursor:pointer;">Todos</button>'
        +'<button style="padding:6px 14px;background:#fff;color:#475569;border:1px solid #e2e8f0;border-radius:20px;font-size:.8rem;font-weight:500;cursor:pointer;">Ahorro</button>'
        +'<button style="padding:6px 14px;background:#fff;color:#475569;border:1px solid #e2e8f0;border-radius:20px;font-size:.8rem;font-weight:500;cursor:pointer;">Credito</button>'
        +'<button style="padding:6px 14px;background:#fff;color:#475569;border:1px solid #e2e8f0;border-radius:20px;font-size:.8rem;font-weight:500;cursor:pointer;">Digital</button>'
        +'<button style="padding:6px 14px;background:#fff;color:#475569;border:1px solid #e2e8f0;border-radius:20px;font-size:.8rem;font-weight:500;cursor:pointer;">Noticias</button>'
        +'<button style="padding:6px 14px;background:#fff;color:#475569;border:1px solid #e2e8f0;border-radius:20px;font-size:.8rem;font-weight:500;cursor:pointer;">Eventos</button>'
        +'</div></div>'
    });

  } /* fin registerBlocks */

  /* -- Fase 8: renderPageSelect con estado visual -------------------- */
  function renderPageSelect(){
    var sel = document.getElementById('wb-page-select');
    if(!sel) return;
    sel.innerHTML = _pages.length
      ? _pages.map(function(p){
          var icon = p.status === 'published' ? '\ud83c\udf10' : '\ud83d\udcdd';
          return '<option value="'+p.id+'"'+(p.id===_currentPageId?' selected':'')+'>'+icon+' '+(p.title||'Sin titulo')+'</option>';
        }).join('')
      : '<option value="">Sin paginas</option>';
  }

  /* -- renderPagesModal ----------------------------------------------- */
  function renderPagesModal(){
    var list = document.getElementById('wb-pages-list');
    if(!list) return;
    if(!_pages.length){
      list.innerHTML = '<p style="color:#64748b;padding:16px;text-align:center;">Sin paginas. Crea una nueva.</p>';
      return;
    }
    list.innerHTML = _pages.map(function(p){
      var esc = function(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); };
      return '<div class="page-item'+(p.id===_currentPageId?' active':'')+'" onclick="selectPageFromModal(\''+p.id+'\')">'
        +'<div style="flex:1;min-width:0;">'
        +'<strong style="display:block;font-size:13px;color:#e2e8f0;overflow:hidden;text-overflow:ellipsis;">'+esc(p.title||'Sin titulo')+'</strong>'
        +'<span style="font-size:11px;color:#64748b;">/web/'+esc(p.slug||'')+'</span>'
        +'</div>'
        +'<span class="pi-status '+(p.status||'draft')+'">'+(p.status==="published"?"Pub":"Bor")+'</span>'
        +'<button class="pi-dup" onclick="duplicatePageById(event,\''+p.id+'\')" title="Duplicar">&#9944;</button>'
        +'<button class="pi-del" onclick="deletePageById(event,\''+p.id+'\')" title="Eliminar">&times;</button>'
        +'</div>';
    }).join('');
  }

  function openPagesModal(){ document.getElementById('wb-pages-modal-overlay').classList.add('open'); }
  window.closePagesModal = function(){ document.getElementById('wb-pages-modal-overlay').classList.remove('open'); };
  window.selectPageFromModal = function(id){ window.closePagesModal(); loadPageIntoEditor(id); };

  function loadPageIntoEditor(id){
    var page = _pages.find(function(p){ return p.id===id; });
    if(!page) return;
    _currentPageId = id; _slugEdited = false; _statusEdited = false;
    _setDirty(false);
    document.getElementById('wb-page-title').value = page.title||'';
    document.getElementById('wb-page-slug').value  = page.slug||'';
    document.getElementById('wb-status-sel').value = page.status||'draft';
    /* cargar SEO */
    var m = page.meta || {};
    var seoTitle = document.getElementById('seo-meta-title');
    var seoDesc  = document.getElementById('seo-meta-desc');
    var seoImg   = document.getElementById('seo-og-image');
    if(seoTitle) seoTitle.value = m.title || '';
    if(seoDesc)  seoDesc.value  = m.description || '';
    if(seoImg)   seoImg.value   = m.og_image || '';
    renderPageSelect();
    if(_editor){
      _editor.setComponents(page.gjs_html||page.html||'');
      _editor.setStyle(page.gjs_css||page.css||'');
      setTimeout(injectBrandCSSVars, 200);
    }
  }

  window.createNewPage = function(ask){
    var title;
    if(ask===false){ title='Inicio'; }
    else { title=prompt('Nombre de la nueva pagina:','Nueva pagina'); if(!title) return; }
    var inheritedCss = '';
    var activePage = currentPage();
    if(_editor && activePage){
      inheritedCss = _editor.getCss() || activePage.gjs_css || '';
    } else if(activePage){
      inheritedCss = activePage.gjs_css || '';
    }
    var page = { id:uid(), title:title.trim(), slug:slugify(title), status:'draft', gjs_html:'', gjs_css:inheritedCss, blocks:[] };
    _pages.push(page);
    renderPageSelect();
    renderPagesModal();
    apiSave(page).then(function(j){
      if(j.data) _pages=j.data;
      renderPageSelect();
      renderPagesModal();
      loadPageIntoEditor(page.id);
    }).catch(function(err){
      toast('Error al crear la página: ' + (err && err.message ? err.message : 'desconocido'), false);
    });
    if(ask!==false) toast('Pagina creada');
  };

  window.deletePageById = function(e, id){
    e.stopPropagation();
    if(!confirm('Eliminar esta pagina?')) return;
    apiDelete(id).then(function(){
      _pages = _pages.filter(function(p){ return p.id!==id; });
      if(_currentPageId===id){
        if(_pages.length) loadPageIntoEditor(_pages[0].id);
        else { _currentPageId=null; if(_editor) _editor.setComponents(''); }
      }
      renderPageSelect(); renderPagesModal(); toast('Pagina eliminada');
    });
  };

  /* Save */
  var _dirty = false;
  function _setDirty(v){
    _dirty = v;
    var btn = document.getElementById('wb-save-btn');
    var lbl = document.getElementById('wb-unsaved-label');
    if(btn) btn.classList.toggle('dirty', v);
    if(lbl) lbl.classList.toggle('visible', v);
  }

  window.saveCurrentPage = function(){
    if(_saving) return Promise.resolve();
    if(!_currentPageId){ toast('Selecciona una página primero', false); return Promise.resolve(); }
    var page = currentPage(); if(!page) return Promise.resolve();
    _saving = true;
    var btn = document.getElementById('wb-save-btn');
    var origHTML = btn ? btn.innerHTML : '';
    if(btn){
      btn.disabled = true;
      btn.innerHTML = '⏳ Guardando…';
    }
    try {
      page.title  = (document.getElementById('wb-page-title').value || '').trim() || page.title;
      page.slug   = slugify((document.getElementById('wb-page-slug').value || '').trim() || page.slug);
      var selectedStatus = document.getElementById('wb-status-sel').value || 'draft';
      page.status = (!_statusEdited && page.status === 'published') ? 'published' : selectedStatus;
      if(_editor){
        page.gjs_html = _editor.getHtml();
        page.gjs_css = _editor.getCss();
      }
      page.meta = {
        title:       (document.getElementById('seo-meta-title').value || '').trim(),
        description: (document.getElementById('seo-meta-desc').value  || '').trim(),
        og_image:    (document.getElementById('seo-og-image').value   || '').trim(),
      };
    } catch(err){
      _saving = false;
      if(btn){
        btn.disabled = false;
        btn.innerHTML = origHTML;
      }
      toast('Error preparando guardado: ' + (err && err.message ? err.message : 'desconocido'), false);
      return Promise.resolve();
    }
    return apiSave(page).then(function(j){
      if(!j || !j.success) throw new Error((j && j.error) || 'Error al guardar');
      if(j.data) _pages = j.data;
      if(j.page){
        _currentPageId = j.page.id || _currentPageId;
        document.getElementById('wb-page-title').value = j.page.title || '';
        document.getElementById('wb-page-slug').value = j.page.slug || '';
        document.getElementById('wb-status-sel').value = j.page.status || 'draft';
        _statusEdited = false;
      }
      renderPageSelect();
      renderPagesModal();
      toast('Guardado ✓');
      _setDirty(false);
    }).catch(function(err){
      toast('Error al guardar: ' + (err && err.message ? err.message : 'red'), false);
    }).finally(function(){
      _saving = false;
      if(btn){
        btn.disabled = false;
        btn.innerHTML = origHTML;
      }
    });
  };

  /* ── Duplicar página ─── */
  window.duplicatePageById = function(e, id){
    e.stopPropagation();
    var src = _pages.find(function(p){ return p.id===id; });
    if(!src) return;
    var copy = JSON.parse(JSON.stringify(src));
    copy.id    = uid();
    copy.title = copy.title + ' (copia)';
    copy.slug  = slugify(copy.title);
    copy.status = 'draft';
    _pages.push(copy);
    apiSave(copy).then(function(j){ if(j.data) _pages=j.data; renderPageSelect(); renderPagesModal(); toast('Página duplicada'); });
    loadPageIntoEditor(copy.id);
  };

  /* ── SEO modal ─── */
  window.openSeoModal = function(){
    if(!_currentPageId){ toast('Selecciona una página primero', false); return; }
    document.getElementById('wb-seo-modal-overlay').classList.add('open');
  };
  window.closeSeoModal = function(){
    document.getElementById('wb-seo-modal-overlay').classList.remove('open');
  };
  window.saveSeoModal = function(){
    var page = currentPage(); if(!page) return;
    page.meta = {
      title:       (document.getElementById('seo-meta-title').value || '').trim(),
      description: (document.getElementById('seo-meta-desc').value  || '').trim(),
      og_image:    (document.getElementById('seo-og-image').value   || '').trim(),
    };
    window.closeSeoModal();
    window.saveCurrentPage().then(function(){ toast('SEO guardado ✓'); });
  };
  document.getElementById('wb-seo-btn').addEventListener('click', window.openSeoModal);
  document.getElementById('wb-seo-modal-overlay').addEventListener('click', function(e){ if(e.target===this) window.closeSeoModal(); });

  /* Toolbar wiring */
  document.getElementById('wb-save-btn').addEventListener('click', window.saveCurrentPage);
  document.getElementById('wb-page-select').addEventListener('change', function(){ loadPageIntoEditor(this.value); });
  document.getElementById('wb-manage-pages-btn').addEventListener('click', openPagesModal);
  document.getElementById('wb-pages-modal-overlay').addEventListener('click', function(e){ if(e.target===this) window.closePagesModal(); });
  document.getElementById('wb-page-title').addEventListener('input', function(){
    var page = currentPage(); if(!page) return;
    page.title = this.value;
    if(!_slugEdited){
      var s = slugify(this.value);
      document.getElementById('wb-page-slug').value = s;
      page.slug = s;
    }
    renderPageSelect();
    _setDirty(true);
  });
  document.getElementById('wb-page-slug').addEventListener('input', function(){
    _slugEdited = true;
    var page = currentPage(); if(page) page.slug = this.value;
    _setDirty(true);
  });
  document.getElementById('wb-status-sel').addEventListener('change', function(){
    var page = currentPage(); if(page) page.status = this.value;
    _statusEdited = true;
    _setDirty(true);
  });
  document.addEventListener('keydown', function(e){
    if((e.ctrlKey || e.metaKey) && e.key === 's'){ e.preventDefault(); window.saveCurrentPage(); }
  });

  /* ── Paleta corporativa ─────────────────────────────────────────── */
  var _brandColors = [];
  var _brandLogo = '';

  /* Etiquetas legibles para cada clave de /guardar-colores */
  var _colorLabels = {
    'navbar-bg':      'Navbar fondo',
    'navbar-text':    'Navbar texto',
    'sidebar-top':    'Sidebar superior',
    'sidebar-bottom': 'Sidebar inferior',
    'sidebar-text':   'Sidebar texto',
    'field-color':    'Campos',
    'button-bg':      'Botón fondo',
    'button-text':    'Botón texto',
    'sidebar-icon':   'Iconos',
    'sidebar-hover':  'Hover sidebar'
  };

  /* Inyecta CSS variables en el iframe del canvas para que los bloques puedan usarlas */
  function injectBrandCSSVars(){
    if(!_editor || !_brandColors.length) return;
    try {
      var doc = _editor.Canvas.getDocument();
      var existing = doc.getElementById('_sipet_brand_vars');
      if(existing) existing.parentNode.removeChild(existing);
      var css = ':root{';
      _brandColors.forEach(function(c){ css += '--'+c.key.replace(/[^a-z0-9]/gi,'-')+':'+c.value+';'; });
      css += '}';
      var s = doc.createElement('style');
      s.id = '_sipet_brand_vars';
      s.textContent = css;
      doc.head.appendChild(s);
    } catch(e){}
  }

  function applyBrandLogoToComp(comp){
    if(!_brandLogo || !comp || !comp.getAttributes) return;
    var attrs = comp.getAttributes() || {};
    if(attrs['data-sipet-logo'] && (comp.get('content') || '').indexOf('<img') === -1){
      comp.set('content', '<img src="'+_brandLogo+'" style="height:38px;width:auto;object-fit:contain;display:block;" alt="Logo" data-sipet-logo="1">');
    }
    if(!comp.components) return;
    var children = comp.components();
    if(!children || !children.length) return;
    for(var i = 0; i < children.length; i++){
      var child = children.at ? children.at(i) : children[i];
      applyBrandLogoToComp(child);
    }
  }

  function applyBrandLogoToCanvas(){
    if(!_brandLogo || !_editor || !_editor.getWrapper) return;
    applyBrandLogoToComp(_editor.getWrapper());
  }

  /* Construye la barra de swatches corporativos en el panel lateral */
  function renderBrandSwatches(){
    var container = document.getElementById('_wb_brand_palette');
    if(!container) return;
    if(!_brandColors.length){
      container.innerHTML = '<p style="color:#475569;font-size:11px;padding:8px 12px;">Sin colores corporativos guardados.</p>';
      return;
    }
    var html = '<div style="display:flex;flex-wrap:wrap;gap:6px;padding:10px 12px;">';
    _brandColors.forEach(function(c){
      var label = _colorLabels[c.key] || c.key;
      html += '<div title="'+label+' — '+c.value+'" '
            + 'onclick="applySwatch(\''+c.value+'\')" '
            + 'style="width:26px;height:26px;border-radius:5px;cursor:pointer;'
            + 'background:'+c.value+';border:2px solid rgba(255,255,255,.15);'
            + 'box-shadow:0 1px 4px rgba(0,0,0,.35);transition:transform .1s;" '
            + 'onmouseover="this.style.transform=\'scale(1.2)\'" '
            + 'onmouseout="this.style.transform=\'\'"></div>';
    });
    html += '</div>';
    container.innerHTML = html;
  }

  /* Aplica el color del swatch a la propiedad de estilo activa del componente seleccionado */
  window.applySwatch = function(color){
    if(!_editor) return;
    var sel = _editor.getSelected();
    if(!sel){ toast('Selecciona un elemento en el canvas primero', false); return; }
    /* Intenta aplicar al último sector de color activo; si no, aplica background-color */
    var sm = _editor.StyleManager;
    var focusedProp = null;
    ['color','background-color','border-color'].forEach(function(prop){
      var el = document.activeElement;
      if(el && el.dataset && el.dataset.property === prop) focusedProp = prop;
    });
    var prop = focusedProp || 'background-color';
    sel.addStyle({ [prop]: color });
    _editor.trigger('component:update', sel);
    toast('Color '+color+' aplicado a '+prop);
  };

  /* Carga colores desde la API y actualiza la paleta + canvas */
  function loadBrandColors(){
    fetch('/guardar-colores', {credentials:'include'})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if(!j.success || !j.data) return;
        _brandColors = Object.keys(j.data).map(function(k){ return {key:k, value:j.data[k]}; })
          .filter(function(c){ return /^#[0-9a-fA-F]{3,8}$/.test(c.value); });
        renderBrandSwatches();
        injectBrandCSSVars();
      })
      .catch(function(){});
  }

  /* ── Fase 6: Plantillas, Exportar/Importar ─────────────────────── */

  var _TEMPLATES = [
    {
      id: 'home-coop', title: 'Home Cooperativa', thumb: '🏦',
      desc: 'Página de inicio completa: navbar, hero, estadísticas, servicios, CTA, pie.',
      css: 'section,nav,footer{box-sizing:border-box}',
      html: '<nav style="display:flex;align-items:center;justify-content:space-between;padding:16px 5%;background:#fff;box-shadow:0 1px 10px rgba(0,0,0,.07);position:sticky;top:0;z-index:100;"><a href="#" style="font-size:1.3rem;font-weight:800;color:#0f172a;text-decoration:none;">Cooperativa</a><div style="display:flex;gap:20px;align-items:center;"><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Inicio</a><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Servicios</a><a href="#" style="color:#475569;text-decoration:none;font-size:.9rem;font-weight:500;">Nosotros</a><a data-sipet-auth-link="1" href="/web/inicio" style="display:inline-flex;align-items:center;gap:9px;padding:7px 18px;background:#0f172a;color:#fff;border-radius:7px;font-size:.85rem;font-weight:700;text-decoration:none;"><i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i><span data-sipet-auth-label style="display:none;"></span></a></div></nav><section style="display:flex;align-items:center;gap:48px;padding:80px 5%;background:#f8fafc;flex-wrap:wrap;"><div style="flex:1;min-width:280px;"><p style="font-size:.8rem;font-weight:700;color:#3b82f6;text-transform:uppercase;letter-spacing:.1em;margin:0 0 10px;">Bienvenidos</p><h1 style="font-size:2.4rem;font-weight:800;color:#0f172a;margin:0 0 16px;line-height:1.2;">Tu solución financiera de confianza</h1><p style="color:#64748b;margin:0 0 28px;line-height:1.7;">Ahorro, crédito y servicios financieros para toda la familia.</p><a href="#" style="display:inline-block;padding:13px 30px;background:#0f172a;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;margin-right:10px;">Conocer más</a><a href="#" style="display:inline-block;padding:13px 30px;border:2px solid #0f172a;color:#0f172a;border-radius:8px;font-weight:700;text-decoration:none;">Asociarme</a></div><div style="flex:1;min-width:240px;text-align:center;"><img src="https://placehold.co/520x360/e2e8f0/94a3b8?text=Cooperativa" style="width:100%;border-radius:16px;box-shadow:0 20px 40px rgba(0,0,0,.12);" alt="Hero"></div></section><section style="padding:48px 5%;background:#0f172a;color:#fff;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:24px;max-width:900px;margin:0 auto;text-align:center;"><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">12,000+</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">Socios activos</div></div><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">25 años</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">De experiencia</div></div><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">Q450M</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">En cartera</div></div><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">8</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">Sucursales</div></div></div></section><section style="padding:64px 5%;background:#fff;"><div style="text-align:center;margin-bottom:36px;"><h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Nuestros servicios</h2><p style="color:#64748b;">Diseñados para acompañar cada etapa de tu vida.</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;max-width:1100px;margin:0 auto;"><div style="background:#f8fafc;border-radius:12px;padding:28px;text-align:center;"><div style="font-size:2rem;margin-bottom:12px;">💳</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Ahorro</h3><p style="color:#64748b;font-size:.875rem;line-height:1.65;">Cuentas con rendimientos competitivos y sin comisiones.</p></div><div style="background:#f8fafc;border-radius:12px;padding:28px;text-align:center;"><div style="font-size:2rem;margin-bottom:12px;">🏦</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Créditos</h3><p style="color:#64748b;font-size:.875rem;line-height:1.65;">Préstamos personales e hipotecarios a tu medida.</p></div><div style="background:#f8fafc;border-radius:12px;padding:28px;text-align:center;"><div style="font-size:2rem;margin-bottom:12px;">📱</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Digital</h3><p style="color:#64748b;font-size:.875rem;line-height:1.65;">Gestiona tu cuenta desde cualquier dispositivo.</p></div><div style="background:#f8fafc;border-radius:12px;padding:28px;text-align:center;"><div style="font-size:2rem;margin-bottom:12px;">🔒</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Seguro</h3><p style="color:#64748b;font-size:.875rem;line-height:1.65;">Fondos protegidos y auditados cada año.</p></div></div></section><section style="background:#3b82f6;color:#fff;padding:64px 24px;text-align:center;"><h2 style="font-size:2rem;font-weight:800;margin:0 0 12px;">¿Listo para empezar?</h2><p style="opacity:.85;margin:0 0 28px;font-size:1.05rem;max-width:520px;margin-left:auto;margin-right:auto;">Únete a miles de socios que ya confían en nosotros.</p><a href="#" style="display:inline-block;padding:14px 36px;background:#fff;color:#3b82f6;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">Asociarme ahora</a></section><footer style="background:#0f172a;color:#94a3b8;padding:48px 5% 24px;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:32px;margin-bottom:32px;"><div><h3 style="color:#f8fafc;font-size:1.05rem;font-weight:700;margin:0 0 10px;">Cooperativa</h3><p style="font-size:.85rem;line-height:1.7;">Financiando el futuro de nuestros socios desde 2001.</p></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 8px;text-transform:uppercase;letter-spacing:.06em;">Servicios</h4><ul style="list-style:none;display:flex;flex-direction:column;gap:6px;font-size:.85rem;"><li><a href="#" style="color:#94a3b8;text-decoration:none;">Ahorro</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Créditos</a></li><li><a href="#" style="color:#94a3b8;text-decoration:none;">Digital</a></li></ul></div><div><h4 style="color:#f8fafc;font-size:.85rem;font-weight:700;margin:0 0 8px;text-transform:uppercase;letter-spacing:.06em;">Contacto</h4><ul style="list-style:none;gap:6px;display:flex;flex-direction:column;font-size:.85rem;"><li>📞 (502) 2222-3333</li><li>✉ info@cooperativa.com</li></ul></div></div><div style="border-top:1px solid #1e293b;padding-top:18px;text-align:center;font-size:.8rem;">© 2026 Cooperativa. Todos los derechos reservados.</div></footer>'
    },
    {
      id: 'servicios', title: 'Página de Servicios', thumb: '💼',
      desc: 'Muestra tus productos y servicios con cards detalladas y sección de tasas.',
      css: 'section,nav{box-sizing:border-box}',
      html: '<nav style="display:flex;align-items:center;justify-content:space-between;padding:16px 5%;background:#fff;box-shadow:0 1px 10px rgba(0,0,0,.07);position:sticky;top:0;z-index:100;"><a href="#" style="font-size:1.3rem;font-weight:800;color:#0f172a;text-decoration:none;">Cooperativa</a><div style="display:flex;gap:20px;align-items:center;"><a href="#" style="color:#475569;font-size:.9rem;font-weight:500;text-decoration:none;">Inicio</a><a href="#" style="color:#3b82f6;font-size:.9rem;font-weight:700;text-decoration:none;border-bottom:2px solid #3b82f6;">Servicios</a><a href="#" style="color:#475569;font-size:.9rem;font-weight:500;text-decoration:none;">Contacto</a></div></nav><section style="background:#0f172a;color:#fff;padding:64px 5%;text-align:center;"><p style="font-size:.8rem;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:.1em;margin:0 0 10px;">Productos financieros</p><h1 style="font-size:2.2rem;font-weight:800;margin:0 0 14px;">Soluciones a tu medida</h1><p style="color:#94a3b8;font-size:1rem;max-width:560px;margin:0 auto;">Elige el producto que mejor se adapta a tus necesidades y metas financieras.</p></section><section style="padding:64px 5%;background:#f8fafc;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;max-width:1100px;margin:0 auto;"><div style="background:#fff;border-radius:14px;padding:28px 24px;box-shadow:0 2px 16px rgba(0,0,0,.07);border-top:4px solid #3b82f6;"><div style="font-size:2rem;margin-bottom:14px;">💳</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 10px;">Cuenta de Ahorro</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;margin:0 0 20px;">Haz crecer tu dinero con rendimientos competitivos. Sin comisiones de mantenimiento.</p><ul style="padding-left:18px;color:#64748b;font-size:.875rem;line-height:1.9;margin:0 0 20px;"><li>Tasa del 3.5% anual</li><li>Retiros sin límite</li><li>Acceso digital</li></ul><a href="#" style="display:inline-block;padding:9px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;">Abrir cuenta</a></div><div style="background:#fff;border-radius:14px;padding:28px 24px;box-shadow:0 2px 16px rgba(0,0,0,.07);border-top:4px solid #10b981;"><div style="font-size:2rem;margin-bottom:14px;">📈</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 10px;">DPF — Depósito a Plazo</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;margin:0 0 20px;">Maximiza tus ahorros con tasas preferenciales a 3, 6 y 12 meses.</p><ul style="padding-left:18px;color:#64748b;font-size:.875rem;line-height:1.9;margin:0 0 20px;"><li>Hasta 7% anual</li><li>Seguro de depósito</li><li>Renovación automática</li></ul><a href="#" style="display:inline-block;padding:9px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;">Invertir ahora</a></div><div style="background:#fff;border-radius:14px;padding:28px 24px;box-shadow:0 2px 16px rgba(0,0,0,.07);border-top:4px solid #f59e0b;"><div style="font-size:2rem;margin-bottom:14px;">🏦</div><h3 style="font-size:1.05rem;font-weight:700;color:#0f172a;margin:0 0 10px;">Crédito Personal</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;margin:0 0 20px;">Financiamiento rápido con cuotas fijas adaptables a tu capacidad de pago.</p><ul style="padding-left:18px;color:#64748b;font-size:.875rem;line-height:1.9;margin:0 0 20px;"><li>Desde Q5,000</li><li>Plazo hasta 60 meses</li><li>Tasa del 14% anual</li></ul><a href="#" style="display:inline-block;padding:9px 20px;background:#0f172a;color:#fff;border-radius:7px;font-size:.875rem;font-weight:700;text-decoration:none;">Solicitar crédito</a></div></div></section><section style="background:#0f172a;color:#fff;padding:64px 24px;text-align:center;"><h2 style="font-size:1.9rem;font-weight:800;margin:0 0 12px;">¿Necesitas orientación?</h2><p style="opacity:.75;margin:0 0 28px;max-width:480px;margin-left:auto;margin-right:auto;">Nuestros asesores están listos para ayudarte a elegir el producto correcto.</p><a href="#" style="display:inline-block;padding:13px 32px;background:#3b82f6;color:#fff;border-radius:8px;font-weight:700;text-decoration:none;">Hablar con un asesor</a></section>'
    },
    {
      id: 'contacto', title: 'Contacto', thumb: '📬',
      desc: 'Página de contacto con formulario, teléfonos, horarios y mapa de ubicación.',
      css: 'section,nav{box-sizing:border-box}',
      html: '<nav style="display:flex;align-items:center;justify-content:space-between;padding:16px 5%;background:#fff;box-shadow:0 1px 10px rgba(0,0,0,.07);position:sticky;top:0;z-index:100;"><a href="#" style="font-size:1.3rem;font-weight:800;color:#0f172a;text-decoration:none;">Cooperativa</a><div style="display:flex;gap:20px;align-items:center;"><a href="#" style="color:#475569;font-size:.9rem;font-weight:500;text-decoration:none;">Inicio</a><a href="#" style="color:#475569;font-size:.9rem;font-weight:500;text-decoration:none;">Servicios</a><a href="#" style="color:#3b82f6;font-size:.9rem;font-weight:700;text-decoration:none;border-bottom:2px solid #3b82f6;">Contacto</a></div></nav><section style="background:#0f172a;color:#fff;padding:56px 5%;text-align:center;"><h1 style="font-size:2.2rem;font-weight:800;margin:0 0 12px;">¿Cómo podemos ayudarte?</h1><p style="color:#94a3b8;max-width:480px;margin:0 auto;">Escríbenos o visítanos. Estamos disponibles de lunes a viernes.</p></section><section style="padding:64px 5%;background:#f8fafc;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;max-width:1000px;margin:0 auto;"><div><h2 style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:0 0 20px;">Envíanos un mensaje</h2><form style="display:flex;flex-direction:column;gap:14px;" onsubmit="return false;"><input type="text" placeholder="Nombre completo" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><input type="email" placeholder="Correo electrónico" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><input type="tel" placeholder="Teléfono (opcional)" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><textarea rows="4" placeholder="Tu mensaje…" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;resize:vertical;"></textarea><button type="submit" style="padding:13px;background:#0f172a;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;">Enviar mensaje</button></form></div><div style="display:flex;flex-direction:column;gap:20px;"><h2 style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:0 0 4px;">Información de contacto</h2><div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 12px rgba(0,0,0,.06);"><div style="display:flex;flex-direction:column;gap:14px;font-size:.9rem;color:#475569;"><div style="display:flex;gap:12px;align-items:flex-start;"><span style="font-size:1.2rem;">📍</span><div><strong style="color:#0f172a;display:block;margin-bottom:2px;">Sede Central</strong>4a Avenida 12-34, Zona 1, Guatemala</div></div><div style="display:flex;gap:12px;align-items:center;"><span style="font-size:1.2rem;">📞</span><span>(502) 2222-3333</span></div><div style="display:flex;gap:12px;align-items:center;"><span style="font-size:1.2rem;">✉</span><span>info@cooperativa.com</span></div><div style="display:flex;gap:12px;align-items:center;"><span style="font-size:1.2rem;">🕐</span><span>Lunes a Viernes: 8:00 – 17:00 hrs</span></div></div></div><div style="border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.1);"><iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3860.3!2d-90.5069!3d14.6349!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTTCsDM4JzA1LjYiTiA5MMKwMzAnMjQuOCJX!5e0!3m2!1ses!2sgt!4v1000000000000" width="100%" height="220" style="border:none;display:block;" allowfullscreen loading="lazy"></iframe></div></div></div></section>'
    },
    {
      id: 'nosotros', title: 'Sobre Nosotros', thumb: '🤝',
      desc: 'Historia, misión, visión, estadísticas y equipo de la cooperativa.',
      css: 'section,nav{box-sizing:border-box}',
      html: '<nav style="display:flex;align-items:center;justify-content:space-between;padding:16px 5%;background:#fff;box-shadow:0 1px 10px rgba(0,0,0,.07);position:sticky;top:0;z-index:100;"><a href="#" style="font-size:1.3rem;font-weight:800;color:#0f172a;text-decoration:none;">Cooperativa</a><div style="display:flex;gap:20px;align-items:center;"><a href="#" style="color:#475569;font-size:.9rem;text-decoration:none;">Inicio</a><a href="#" style="color:#3b82f6;font-size:.9rem;font-weight:700;text-decoration:none;border-bottom:2px solid #3b82f6;">Nosotros</a><a href="#" style="color:#475569;font-size:.9rem;text-decoration:none;">Contacto</a></div></nav><section style="background:#0f172a;color:#fff;padding:80px 5%;text-align:center;"><p style="font-size:.8rem;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:.1em;margin:0 0 10px;">Desde 2001</p><h1 style="font-size:2.4rem;font-weight:800;margin:0 0 16px;line-height:1.2;">Construyendo futuro juntos</h1><p style="color:#94a3b8;max-width:560px;margin:0 auto;font-size:1rem;line-height:1.7;">Somos una cooperativa de ahorro y crédito comprometida con el bienestar financiero de nuestros socios y sus familias.</p></section><section style="padding:64px 5%;background:#fff;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center;max-width:1100px;margin:0 auto;"><div><h2 style="font-size:1.8rem;font-weight:800;color:#0f172a;margin:0 0 16px;">Nuestra historia</h2><p style="color:#64748b;line-height:1.8;margin:0 0 14px;">Fundada por un grupo de 50 socios visionarios, nuestra cooperativa nació con el propósito de democratizar el acceso al sistema financiero.</p><p style="color:#64748b;line-height:1.8;margin:0 0 24px;">Hoy, con más de 12,000 socios y 8 sucursales, seguimos fiel a esa misión original: crecer juntos.</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;"><div style="background:#f8fafc;border-radius:10px;padding:16px;text-align:center;"><div style="font-size:.7rem;font-weight:700;color:#3b82f6;text-transform:uppercase;margin-bottom:4px;">Misión</div><p style="font-size:.85rem;color:#475569;margin:0;">Facilitar el acceso a servicios financieros justos y seguros.</p></div><div style="background:#f8fafc;border-radius:10px;padding:16px;text-align:center;"><div style="font-size:.7rem;font-weight:700;color:#10b981;text-transform:uppercase;margin-bottom:4px;">Visión</div><p style="font-size:.85rem;color:#475569;margin:0;">Ser la mayor cooperativa de Centroamérica para 2030.</p></div></div></div><div style="text-align:center;"><img src="https://placehold.co/480x360/e2e8f0/94a3b8?text=Nuestro+equipo" style="width:100%;border-radius:16px;box-shadow:0 16px 36px rgba(0,0,0,.1);" alt="Equipo"></div></div></section><section style="padding:48px 5%;background:#0f172a;color:#fff;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:24px;max-width:900px;margin:0 auto;text-align:center;"><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">12,000+</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">Socios</div></div><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">25 años</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">De trayectoria</div></div><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">8</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">Sucursales</div></div><div><div style="font-size:2.4rem;font-weight:800;color:#3b82f6;">98%</div><div style="color:#94a3b8;font-size:.85rem;margin-top:4px;">Satisfacción</div></div></div></section><section style="padding:64px 5%;background:#f8fafc;"><div style="max-width:760px;margin:0 auto;text-align:center;"><h2 style="font-size:1.7rem;font-weight:800;color:#0f172a;margin:0 0 32px;">Lo que dicen nuestros socios</h2><div style="background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.06);"><p style="color:#475569;font-style:italic;font-size:1rem;line-height:1.7;margin:0 0 16px;">&ldquo;Gracias a la cooperativa pude comprar mi casa y darle a mi familia una vida mejor. El servicio siempre ha sido excelente.&rdquo;</p><div style="display:flex;align-items:center;justify-content:center;gap:12px;"><div style="width:40px;height:40px;border-radius:50%;background:#e2e8f0;display:flex;align-items:center;justify-content:center;font-size:18px;">👤</div><div style="text-align:left;"><strong style="font-size:.9rem;color:#0f172a;">María López</strong><br><span style="font-size:.8rem;color:#94a3b8;">Socia desde 2015</span></div></div></div></div></section>'
    },
    {
      id: 'landing-promo', title: 'Landing Promocional', thumb: '🚀',
      desc: 'Página de aterrizaje de alto impacto para campañas y captación de nuevos socios.',
      css: 'section,nav{box-sizing:border-box}',
      html: '<section style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);color:#fff;padding:100px 5%;text-align:center;"><div style="max-width:680px;margin:0 auto;"><p style="font-size:.8rem;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:.12em;margin:0 0 14px;">Oferta por tiempo limitado</p><h1 style="font-size:2.8rem;font-weight:800;line-height:1.15;margin:0 0 20px;">Abre tu cuenta hoy y gana el doble de intereses</h1><p style="font-size:1.1rem;color:#94a3b8;max-width:520px;margin:0 auto 32px;line-height:1.7;">Hasta el 31 de marzo: tasa especial del 7% anual en DPF a 6 meses para nuevos socios.</p><div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;"><a href="#" style="display:inline-block;padding:15px 36px;background:#3b82f6;color:#fff;border-radius:9px;font-weight:700;font-size:1rem;text-decoration:none;">Aprovechar ahora</a><a href="#" style="display:inline-block;padding:15px 36px;background:transparent;color:#e2e8f0;border:2px solid rgba(255,255,255,.3);border-radius:9px;font-weight:700;font-size:1rem;text-decoration:none;">Ver condiciones</a></div></div></section><section style="padding:56px 5%;background:#fff;"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px;max-width:1000px;margin:0 auto;"><div style="text-align:center;padding:24px;"><div style="font-size:2.5rem;margin-bottom:12px;">⚡</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Apertura en 15 min</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Proceso 100% digital. Solo necesitas tu DPI.</p></div><div style="text-align:center;padding:24px;"><div style="font-size:2.5rem;margin-bottom:12px;">🏆</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Tasa premiada</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Las mejores tasas del mercado, respaldadas por 25 años de experiencia.</p></div><div style="text-align:center;padding:24px;"><div style="font-size:2.5rem;margin-bottom:12px;">🔒</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Fondos seguros</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">Supervisado por BANCAS y auditado anualmente.</p></div><div style="text-align:center;padding:24px;"><div style="font-size:2.5rem;margin-bottom:12px;">📱</div><h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 8px;">Todo en tu móvil</h3><p style="color:#64748b;font-size:.9rem;line-height:1.65;">App disponible para iOS y Android sin costo adicional.</p></div></div></section><section style="background:#f8fafc;padding:64px 5%;"><div style="max-width:520px;margin:0 auto;text-align:center;"><h2 style="font-size:1.8rem;font-weight:800;color:#0f172a;margin:0 0 8px;">Regístrate gratis</h2><p style="color:#64748b;margin:0 0 24px;">Un asesor te contactará en menos de 24 horas.</p><form style="display:flex;flex-direction:column;gap:14px;" onsubmit="return false;"><input type="text" placeholder="Nombre completo" style="padding:13px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><input type="tel" placeholder="Teléfono" style="padding:13px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><input type="email" placeholder="Correo electrónico" style="padding:13px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;"><button type="submit" style="padding:14px;background:#3b82f6;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;">Quiero mi cuenta →</button></form><p style="font-size:.78rem;color:#94a3b8;margin-top:12px;">Sin compromisos. Cancela cuando quieras.</p></div></section>'
    }
  ];

  /* ── Templates modal ── */
  function renderTplGrid(){
    var grid = document.getElementById('wb-tpl-grid');
    if(!grid) return;
    grid.innerHTML = _TEMPLATES.map(function(t){
      return '<div class="tpl-card" title="'+t.title+'">'
        +'<div class="tpl-thumb">'+t.thumb+'</div>'
        +'<div class="tpl-info"><h3>'+t.title+'</h3><p>'+t.desc+'</p>'
        +'<button onclick="applyTemplate(\''+t.id+'\')"  >Usar plantilla</button></div></div>';
    }).join('');
  }
  window.openTplModal  = function(){ renderTplGrid(); document.getElementById('wb-tpl-modal-overlay').classList.add('open'); };
  window.closeTplModal = function(){ document.getElementById('wb-tpl-modal-overlay').classList.remove('open'); };
  window.applyTemplate = function(id){
    var tpl = _TEMPLATES.find(function(t){ return t.id===id; });
    if(!tpl) return;
    if(!confirm('¿Aplicar la plantilla "'+tpl.title+'"? El contenido actual del canvas será reemplazado.')) return;
    if(_editor){
      _editor.setComponents(tpl.html);
      _editor.setStyle(tpl.css||'');
    }
    window.closeTplModal();
    toast('Plantilla aplicada ✓');
  };
  document.getElementById('wb-tpl-btn').addEventListener('click', window.openTplModal);
  document.getElementById('wb-tpl-modal-overlay').addEventListener('click', function(e){ if(e.target===this) window.closeTplModal(); });

  /* ── Export / Import modal ── */
  window.openIOModal  = function(){ document.getElementById('wb-io-modal-overlay').classList.add('open'); };
  window.closeIOModal = function(){ document.getElementById('wb-io-modal-overlay').classList.remove('open'); };
  window.exportPage = function(){
    var page = currentPage(); if(!page) return;
    if(_editor){ page.gjs_html = _editor.getHtml(); page.gjs_css = _editor.getCss(); }
    var json = JSON.stringify({
      title: page.title, slug: page.slug, status: page.status,
      meta: page.meta||{}, gjs_html: page.gjs_html||'', gjs_css: page.gjs_css||''
    }, null, 2);
    var ta = document.getElementById('wb-io-json');
    ta.value = json;
    ta.removeAttribute('readonly');
    toast('JSON generado');
  };
  window.copyJSON = function(){
    var ta = document.getElementById('wb-io-json');
    if(!ta.value){ toast('Primero exporta la página', false); return; }
    try{ navigator.clipboard.writeText(ta.value).then(function(){ toast('Copiado al portapapeles'); }); }
    catch(e){ ta.select(); document.execCommand('copy'); toast('Copiado'); }
  };
  window.importPage = function(){
    var ta = document.getElementById('wb-io-json');
    var raw = (ta.value||'').trim();
    if(!raw){ toast('Pega un JSON válido en el área de texto', false); return; }
    var data;
    try{ data = JSON.parse(raw); } catch(e){ toast('JSON inválido: '+e.message, false); return; }
    if(!_currentPageId){ toast('Selecciona una página destino primero', false); return; }
    var page = currentPage(); if(!page) return;
    if(!confirm('¿Importar a la página "'+page.title+'"? El contenido actual será reemplazado.')) return;
    if(data.gjs_html !== undefined) page.gjs_html = data.gjs_html;
    if(data.gjs_css  !== undefined) page.gjs_css  = data.gjs_css;
    if(data.meta)  page.meta   = data.meta;
    if(_editor){
      _editor.setComponents(page.gjs_html||'');
      _editor.setStyle(page.gjs_css||'');
    }
    window.saveCurrentPage().then(function(){ toast('Importado y guardado ✓'); });
    window.closeIOModal();
  };
  document.getElementById('wb-io-btn').addEventListener('click', window.openIOModal);
  document.getElementById('wb-io-modal-overlay').addEventListener('click', function(e){ if(e.target===this) window.closeIOModal(); });
  document.getElementById('wb-html-modal-overlay').addEventListener('click', function(e){ if(e.target===this) window.closeHtmlRawModal(); });
  document.getElementById('wb-html-editor').addEventListener('input', function(){
    if(_htmlRawMode === 'preview') _renderHtmlRawPreview(this.value || '', (document.getElementById('wb-html-css').value || ''));
  });
  document.getElementById('wb-html-css').addEventListener('input', function(){
    if(_htmlRawMode === 'preview') _renderHtmlRawPreview((document.getElementById('wb-html-editor').value || ''), this.value || '');
  });

  /* ── Fase 7: Preview, Publicar, Versiones ──────────────────── */

  /* ── Preview en iframe con franja admin ── */
  window.openPreviewModal = function(){
    var page = currentPage();
    if(!page){ toast('Selecciona una página primero', false); return; }
    var url = '/p-preview/' + page.slug;
    var ovl = document.getElementById('wb-preview-overlay');
    document.getElementById('wb-preview-label').textContent =
      '👁 Previsualización: ' + page.title + ' (' + (page.status === 'published' ? '🌐 Publicado' : '📝 Borrador') + ')';
    document.getElementById('wb-preview-link').href = url;
    document.getElementById('wb-preview-iframe').src = url;
    ovl.classList.add('open');
  };
  window.closePreviewModal = function(){
    document.getElementById('wb-preview-overlay').classList.remove('open');
    document.getElementById('wb-preview-iframe').src = '';
  };
  document.getElementById('wb-preview-btn').addEventListener('click', window.openPreviewModal);

  /* ── Publicar ── */
  window.publishCurrentPage = function(){
    var page = currentPage();
    if(!page){ toast('Selecciona una página primero', false); return; }
    if(!confirm('¿Publicar "' + page.title + '"? Estará disponible en /web/' + page.slug)) return;
    return window.saveCurrentPage().then(function(){
      return fetch('/api/frontend/pages/' + page.id + '/publish', {method:'POST'});
    })
      .then(function(r){ return r.json(); })
      .then(function(j){
        if(j.success){
          page.status = 'published';
          var sel = document.getElementById('wb-status-sel');
          if(sel) sel.value = 'published';
          renderPageSelect(); renderPagesModal();
          toast('Página publicada 🌐');
        } else { toast('Error: '+(j.error||'desconocido'), false); }
      })
      .catch(function(){ toast('Error de red', false); });
  };
  document.getElementById('wb-publish-btn').addEventListener('click', window.publishCurrentPage);

  /* Ver publicado — abre /web/{slug} en nueva pestaña */
  document.getElementById('wb-view-published-btn').addEventListener('click', function(){
    var page = currentPage();
    if(!page){ toast('Selecciona una página primero', false); return; }
    if(page.status !== 'published'){
      toast('⚠ La página aún no está publicada. Usa “Publicar” primero.', false);
      return;
    }
    window.open('/web/' + page.slug, '_blank');
  });

  /* ── Historial de versiones ── */
  window.openVerModal = function(){
    if(!_currentPageId){ toast('Selecciona una página primero', false); return; }
    document.getElementById('wb-ver-modal-overlay').classList.add('open');
    loadVersions();
  };
  window.closeVerModal = function(){
    document.getElementById('wb-ver-modal-overlay').classList.remove('open');
  };
  window.loadVersions = function(){
    var list = document.getElementById('wb-ver-list');
    list.innerHTML = '<p style="color:#64748b;padding:20px;text-align:center;">Cargando…</p>';
    fetch('/api/frontend/versions/'+_currentPageId)
      .then(function(r){ return r.json(); })
      .then(function(j){
        var snaps = j.data||[];
        if(!snaps.length){
          list.innerHTML = '<p style="color:#64748b;padding:24px;text-align:center;">No hay versiones guardadas aún.<br><small>Se crean automáticamente al guardar.</small></p>';
          return;
        }
        list.innerHTML = snaps.map(function(s, i){
          return '<div class="ver-item">'
            +'<div class="ver-meta"><strong>'+(s.title||'Sin título')+'</strong>'
            +'<span>'+s.saved_at+' &nbsp;·&nbsp; '+(s.status==='published'?'🌐 Publicado':'📝 Borrador')+'</span></div>'
            +(i===0
              ? '<span style="font-size:11px;color:#10b981;font-weight:700;">actual</span>'
              : '<button onclick="restoreVersion('+i+')">Restaurar</button>')
            +'</div>';
        }).join('');
      })
      .catch(function(){ list.innerHTML = '<p style="color:#ef4444;padding:20px;text-align:center;">Error al cargar versiones.</p>'; });
  };
  window.restoreVersion = function(idx){
    if(!confirm('¿Restaurar esta versión? El contenido actual del canvas se reemplazará.')) return;
    fetch('/api/frontend/versions/'+_currentPageId+'/restore/'+idx, {method:'POST'})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if(j.success){
          var p = j.page;
          if(_editor){ _editor.setComponents(p.gjs_html||''); _editor.setStyle(p.gjs_css||''); }
          var page = currentPage();
          if(page){ page.gjs_html=p.gjs_html; page.gjs_css=p.gjs_css; page.meta=p.meta; }
          window.closeVerModal();
          toast('Versión restaurada ✓');
        } else { toast('Error: '+(j.error||'desconocido'), false); }
      })
      .catch(function(){ toast('Error de red', false); });
  };
  document.getElementById('wb-ver-btn').addEventListener('click', window.openVerModal);
  document.getElementById('wb-ver-modal-overlay').addEventListener('click', function(e){ if(e.target===this) window.closeVerModal(); });

  /* Boot */
  initEditor();
  if (typeof sipetWidgets === 'function') sipetWidgets(_editor);

  /* ── Componentes dinámicos Fase 5 ───────────────────────────────── */
  (function registerDynamicTypes(){
    var dc = _editor.DomComponents;
    var bm = _editor.BlockManager;

    dc.addType('sipet-header-slider', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'header-slider'; },
      model: { defaults: {
        tagName: 'section',
        attributes: {
          'data-sipet-block':'header-slider',
          style:'position:relative;min-height:88vh;overflow:hidden;background:#0f172a;color:#fff;'
        },
        droppable: false,
        script: function(){
          var root = this;
          var slides = Array.prototype.slice.call(root.querySelectorAll('[data-sipet-slide]'));
          var dots = Array.prototype.slice.call(root.querySelectorAll('[data-sipet-dot]'));
          var prev = root.querySelector('[data-sipet-prev]');
          var next = root.querySelector('[data-sipet-next]');
          if(!slides.length) return;
          var current = 0;
          var timer = null;
          function show(index){
            current = (index + slides.length) % slides.length;
            slides.forEach(function(slide, idx){
              slide.style.opacity = idx === current ? '1' : '0';
              slide.style.pointerEvents = idx === current ? 'auto' : 'none';
              slide.style.transform = idx === current ? 'scale(1)' : 'scale(1.03)';
              slide.style.zIndex = idx === current ? '2' : '1';
            });
            dots.forEach(function(dot, idx){
              dot.style.opacity = idx === current ? '1' : '.45';
              dot.style.transform = idx === current ? 'scale(1.08)' : 'scale(1)';
            });
          }
          function start(){
            stop();
            timer = setInterval(function(){ show(current + 1); }, 5000);
          }
          function stop(){
            if(timer){ clearInterval(timer); timer = null; }
          }
          if(prev){ prev.addEventListener('click', function(){ show(current - 1); start(); }); }
          if(next){ next.addEventListener('click', function(){ show(current + 1); start(); }); }
          dots.forEach(function(dot, idx){
            dot.addEventListener('click', function(){ show(idx); start(); });
          });
          root.addEventListener('mouseenter', stop);
          root.addEventListener('mouseleave', start);
          show(0);
          start();
        },
        components:
          '<div style="position:absolute;inset:0;">'
            +'<div data-sipet-slide style="position:absolute;inset:0;opacity:1;transition:opacity .6s ease,transform .6s ease;transform:scale(1);">'
              +'<img src="https://placehold.co/1600x900/0f172a/60a5fa?text=Slide+1" alt="Slide 1" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.34;">'
              +'<div style="position:absolute;inset:0;background:linear-gradient(120deg,rgba(15,23,42,.88) 0%,rgba(15,23,42,.56) 45%,rgba(30,58,95,.58) 100%);"></div>'
              +'<div style="position:relative;z-index:2;min-height:88vh;display:flex;align-items:center;padding:120px 6% 100px;">'
                +'<div style="max-width:640px;">'
                  +'<div style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;background:rgba(96,165,250,.16);border:1px solid rgba(96,165,250,.35);font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#93c5fd;margin-bottom:20px;">Nuevo ingreso 2026</div>'
                  +'<h1 style="font-size:clamp(2.6rem,5vw,4.4rem);line-height:1.02;font-weight:900;letter-spacing:-.04em;margin:0 0 18px;">Crea una portada con impacto real</h1>'
                  +'<p style="font-size:1.08rem;line-height:1.8;color:rgba(226,232,240,.86);margin:0 0 32px;max-width:560px;">Cada slide puede llevar su propio título, texto, botones y fotografía, para construir un header más cercano a un slider tipo Revolution.</p>'
                  +'<div style="display:flex;gap:14px;flex-wrap:wrap;">'
                    +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff;font-weight:800;text-decoration:none;">Crear campaña</a>'
                    +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);backdrop-filter:blur(12px);color:#f8fafc;font-weight:700;text-decoration:none;">Ver demo</a>'
                  +'</div>'
                +'</div>'
              +'</div>'
            +'</div>'
            +'<div data-sipet-slide style="position:absolute;inset:0;opacity:0;transition:opacity .6s ease,transform .6s ease;transform:scale(1.03);pointer-events:none;">'
              +'<img src="https://placehold.co/1600x900/123047/a7f3d0?text=Slide+2" alt="Slide 2" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.34;">'
              +'<div style="position:absolute;inset:0;background:linear-gradient(120deg,rgba(6,78,59,.84) 0%,rgba(15,23,42,.58) 52%,rgba(15,23,42,.86) 100%);"></div>'
              +'<div style="position:relative;z-index:2;min-height:88vh;display:flex;align-items:center;justify-content:flex-end;padding:120px 6% 100px;">'
                +'<div style="max-width:620px;text-align:left;">'
                  +'<div style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;background:rgba(52,211,153,.16);border:1px solid rgba(110,231,183,.35);font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#bbf7d0;margin-bottom:20px;">Servicios digitales</div>'
                  +'<h2 style="font-size:clamp(2.4rem,4.7vw,4rem);line-height:1.04;font-weight:900;letter-spacing:-.04em;margin:0 0 18px;">Presenta productos distintos en cada slide</h2>'
                  +'<p style="font-size:1.05rem;line-height:1.8;color:rgba(220,252,231,.84);margin:0 0 32px;max-width:520px;">Puedes combinar fondos, llamados a la acción y mensajes comerciales sin depender de un solo hero estático.</p>'
                  +'<div style="display:flex;gap:14px;flex-wrap:wrap;">'
                    +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;background:#10b981;color:#052e16;font-weight:800;text-decoration:none;">Conocer servicios</a>'
                    +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;border:1px solid rgba(255,255,255,.22);background:rgba(15,23,42,.22);color:#ecfdf5;font-weight:700;text-decoration:none;">Hablar con asesor</a>'
                  +'</div>'
                +'</div>'
              +'</div>'
            +'</div>'
            +'<div data-sipet-slide style="position:absolute;inset:0;opacity:0;transition:opacity .6s ease,transform .6s ease;transform:scale(1.03);pointer-events:none;">'
              +'<img src="https://placehold.co/1600x900/312e81/c4b5fd?text=Slide+3" alt="Slide 3" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.32;">'
              +'<div style="position:absolute;inset:0;background:linear-gradient(120deg,rgba(49,46,129,.82) 0%,rgba(15,23,42,.62) 48%,rgba(15,23,42,.9) 100%);"></div>'
              +'<div style="position:relative;z-index:2;min-height:88vh;display:flex;align-items:center;padding:120px 6% 100px;">'
                +'<div style="max-width:660px;">'
                  +'<div style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;background:rgba(196,181,253,.16);border:1px solid rgba(216,180,254,.35);font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#ddd6fe;margin-bottom:20px;">Promociones especiales</div>'
                  +'<h2 style="font-size:clamp(2.5rem,4.8vw,4.1rem);line-height:1.04;font-weight:900;letter-spacing:-.04em;margin:0 0 18px;">Úsalo para campañas, anuncios o temporadas</h2>'
                  +'<p style="font-size:1.05rem;line-height:1.8;color:rgba(237,233,254,.84);margin:0 0 32px;max-width:540px;">El bloque ya incluye flechas, indicadores y rotación automática. Después puedes duplicar, editar o reorganizar cada slide desde el canvas.</p>'
                  +'<div style="display:flex;gap:14px;flex-wrap:wrap;">'
                    +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;background:#8b5cf6;color:#fff;font-weight:800;text-decoration:none;">Lanzar oferta</a>'
                    +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:15px 34px;border-radius:10px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:#f5f3ff;font-weight:700;text-decoration:none;">Ver detalles</a>'
                  +'</div>'
                +'</div>'
              +'</div>'
            +'</div>'
          +'</div>'
          +'<button data-sipet-prev type="button" style="position:absolute;left:24px;top:50%;transform:translateY(-50%);z-index:5;width:52px;height:52px;border:none;border-radius:999px;background:rgba(15,23,42,.42);backdrop-filter:blur(12px);color:#fff;font-size:1.5rem;cursor:pointer;">‹</button>'
          +'<button data-sipet-next type="button" style="position:absolute;right:24px;top:50%;transform:translateY(-50%);z-index:5;width:52px;height:52px;border:none;border-radius:999px;background:rgba(15,23,42,.42);backdrop-filter:blur(12px);color:#fff;font-size:1.5rem;cursor:pointer;">›</button>'
          +'<div style="position:absolute;left:6%;bottom:36px;z-index:5;display:flex;gap:10px;">'
            +'<button data-sipet-dot type="button" style="width:38px;height:6px;border:none;border-radius:999px;background:#fff;cursor:pointer;opacity:1;"></button>'
            +'<button data-sipet-dot type="button" style="width:38px;height:6px;border:none;border-radius:999px;background:#fff;cursor:pointer;opacity:.45;"></button>'
            +'<button data-sipet-dot type="button" style="width:38px;height:6px;border:none;border-radius:999px;background:#fff;cursor:pointer;opacity:.45;"></button>'
          +'</div>',
      }},
      view: {}
    });
    try{ bm.remove('header-slider'); }catch(e){}
    bm.add('header-slider', {
      label:'Slider hero', category:'Header', media:'🎞',
      content: { type:'sipet-header-slider' }
    });

    dc.addType('sipet-header-categories-slider', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'header-categories-slider'; },
      model: { defaults: {
        tagName: 'section',
        attributes: {
          'data-sipet-block':'header-categories-slider',
          style:'display:grid;grid-template-columns:320px minmax(0,1fr);gap:0;min-height:680px;background:#eef2f7;border-radius:22px;overflow:hidden;box-shadow:0 18px 40px rgba(15,23,42,.12);'
        },
        droppable: true,
        script: function(){
          var root = this;
          var slides = Array.prototype.slice.call(root.querySelectorAll('[data-sipet-catslide]'));
          var dotsWrap = root.querySelector('[data-sipet-catslider-dots]');
          if(!slides.length) return;
          var current = 0;
          var timer = null;
          function rebuildDots(){
            if(!dotsWrap) return;
            dotsWrap.innerHTML = '';
            slides.forEach(function(_, idx){
              var dot = document.createElement('button');
              dot.type = 'button';
              dot.setAttribute('aria-label', 'Ir al slide ' + (idx + 1));
              dot.style.width = idx === current ? '34px' : '12px';
              dot.style.height = '12px';
              dot.style.borderRadius = '999px';
              dot.style.border = 'none';
              dot.style.background = idx === current ? '#0f172a' : 'rgba(15,23,42,.24)';
              dot.style.cursor = 'pointer';
              dot.style.transition = 'all .25s ease';
              dot.addEventListener('click', function(){ show(idx); start(); });
              dotsWrap.appendChild(dot);
            });
          }
          function show(index){
            current = (index + slides.length) % slides.length;
            slides.forEach(function(slide, idx){
              slide.style.opacity = idx === current ? '1' : '0';
              slide.style.pointerEvents = idx === current ? 'auto' : 'none';
              slide.style.transform = idx === current ? 'translateX(0)' : 'translateX(24px)';
              slide.style.zIndex = idx === current ? '2' : '1';
            });
            rebuildDots();
          }
          function start(){
            stop();
            timer = setInterval(function(){ show(current + 1); }, 7000);
          }
          function stop(){
            if(timer){ clearInterval(timer); timer = null; }
          }
          root.addEventListener('mouseenter', stop);
          root.addEventListener('mouseleave', start);
          show(0);
          start();
        },
        components:
          '<aside style="background:#ffffff;padding:38px 28px;display:flex;flex-direction:column;justify-content:space-between;border-right:1px solid rgba(15,23,42,.08);">'
            +'<div>'
              +'<div style="display:inline-flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;background:#fee2e2;color:#be123c;font-size:.95rem;font-weight:800;margin-bottom:18px;">On Sale! <span style="padding:4px 8px;border-radius:8px;background:#f43f5e;color:#fff;line-height:1;">7584</span></div>'
              +'<div style="display:flex;flex-direction:column;">'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Clothing <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Electronics <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Shoes <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Watches <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Health & Beauty <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Books <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Kids and Babies <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;border-bottom:1px solid rgba(15,23,42,.08);font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Sports <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
                +'<a href="#" style="display:flex;align-items:center;justify-content:space-between;padding:15px 0;font-size:1rem;font-weight:700;color:#3f3f46;text-decoration:none;">Home and Garden <span style="opacity:.35;font-size:1.4rem;">›</span></a>'
              +'</div>'
            +'</div>'
            +'<div style="font-size:.82rem;color:#94a3b8;line-height:1.6;">Puedes editar estas categorías y duplicar los slides del panel derecho desde el canvas.</div>'
          +'</aside>'
          +'<div style="position:relative;overflow:hidden;min-height:680px;background:#d8f6f1;">'
            +'<div data-sipet-catslide style="position:absolute;inset:0;opacity:1;transition:opacity .7s ease,transform .7s ease;transform:translateX(0);">'
              +'<div style="position:absolute;inset:0;background:linear-gradient(135deg,#46d3ca 0%,#5ed8cf 48%,#f4f7fb 48.1%,#f4f7fb 100%);"></div>'
              +'<div style="position:relative;z-index:2;height:100%;display:grid;grid-template-columns:minmax(320px,.9fr) minmax(360px,1.1fr);align-items:center;gap:24px;padding:48px 54px;">'
                +'<div style="max-width:520px;">'
                  +'<div style="font-size:1rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#ffffff;margin-bottom:12px;">Spring 2026</div>'
                  +'<h2 style="font-size:clamp(3rem,6vw,5.5rem);line-height:.92;font-weight:900;letter-spacing:-.05em;color:#ffffff;margin:0 0 20px;">Women Fashion</h2>'
                  +'<p style="font-size:1.15rem;line-height:1.7;color:rgba(255,255,255,.92);margin:0 0 28px;">Renueva la vitrina principal con promociones visuales, texto comercial y un collage fotográfico editable.</p>'
                  +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:18px 34px;border-radius:12px;background:#c96b80;color:#fff;font-size:1rem;font-weight:800;text-decoration:none;box-shadow:0 16px 30px rgba(201,107,128,.32);">SHOP NOW</a>'
                +'</div>'
                +'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:stretch;">'
                  +'<img src="https://placehold.co/380x420/f7d972/0f172a?text=Imagen+1" alt="Slide 1 imagen 1" style="width:100%;height:210px;object-fit:cover;border-radius:30px 30px 120px 30px;box-shadow:0 20px 32px rgba(15,23,42,.18);">'
                  +'<img src="https://placehold.co/380x420/ffd2da/0f172a?text=Imagen+2" alt="Slide 1 imagen 2" style="width:100%;height:210px;object-fit:cover;border-radius:30px 120px 30px 30px;box-shadow:0 20px 32px rgba(15,23,42,.18);">'
                  +'<img src="https://placehold.co/380x420/f4f7fb/0f172a?text=Imagen+3" alt="Slide 1 imagen 3" style="width:100%;height:210px;object-fit:cover;border-radius:120px 30px 30px 30px;box-shadow:0 20px 32px rgba(15,23,42,.18);">'
                  +'<img src="https://placehold.co/380x420/d3e7ff/0f172a?text=Imagen+4" alt="Slide 1 imagen 4" style="width:100%;height:210px;object-fit:cover;border-radius:30px 30px 30px 120px;box-shadow:0 20px 32px rgba(15,23,42,.18);">'
                +'</div>'
              +'</div>'
            +'</div>'
            +'<div data-sipet-catslide style="position:absolute;inset:0;opacity:0;transition:opacity .7s ease,transform .7s ease;transform:translateX(24px);pointer-events:none;">'
              +'<div style="position:absolute;inset:0;background:linear-gradient(135deg,#111827 0%,#0f172a 42%,#dbeafe 42.1%,#eff6ff 100%);"></div>'
              +'<div style="position:relative;z-index:2;height:100%;display:grid;grid-template-columns:minmax(320px,.9fr) minmax(360px,1.1fr);align-items:center;gap:24px;padding:48px 54px;">'
                +'<div style="max-width:520px;">'
                  +'<div style="font-size:1rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#93c5fd;margin-bottom:12px;">New arrivals</div>'
                  +'<h2 style="font-size:clamp(3rem,6vw,5.2rem);line-height:.92;font-weight:900;letter-spacing:-.05em;color:#ffffff;margin:0 0 20px;">Smart Tech</h2>'
                  +'<p style="font-size:1.15rem;line-height:1.7;color:rgba(226,232,240,.9);margin:0 0 28px;">Usa esta variación para campañas de electrónica, gadgets o productos premium con imágenes y CTA editables.</p>'
                  +'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;padding:18px 34px;border-radius:12px;background:#2563eb;color:#fff;font-size:1rem;font-weight:800;text-decoration:none;box-shadow:0 16px 30px rgba(37,99,235,.28);">VER OFERTAS</a>'
                +'</div>'
                +'<div style="display:grid;grid-template-columns:1.15fr .85fr;gap:16px;align-items:stretch;">'
                  +'<img src="https://placehold.co/500x460/dbeafe/0f172a?text=Producto+Principal" alt="Producto principal" style="width:100%;height:436px;object-fit:cover;border-radius:34px;box-shadow:0 20px 34px rgba(15,23,42,.18);">'
                  +'<div style="display:grid;grid-template-rows:repeat(2,minmax(0,1fr));gap:16px;">'
                    +'<img src="https://placehold.co/320x220/bae6fd/0f172a?text=Detalle+1" alt="Detalle 1" style="width:100%;height:210px;object-fit:cover;border-radius:24px;box-shadow:0 20px 34px rgba(15,23,42,.12);">'
                    +'<img src="https://placehold.co/320x220/c7d2fe/0f172a?text=Detalle+2" alt="Detalle 2" style="width:100%;height:210px;object-fit:cover;border-radius:24px;box-shadow:0 20px 34px rgba(15,23,42,.12);">'
                  +'</div>'
                +'</div>'
              +'</div>'
            +'</div>'
            +'<div data-sipet-catslider-dots style="position:absolute;left:54px;bottom:30px;z-index:4;display:flex;gap:10px;"></div>'
          +'</div>',
      }},
      view: {}
    });
    try{ bm.remove('header-categories-slider'); }catch(e){}
    bm.add('header-categories-slider', {
      label:'Categorías + slider', category:'Header', media:'🧭',
      content: { type:'sipet-header-categories-slider' }
    });

    dc.addType('sipet-shop-banner-slider', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'shop-banner-slider'; },
      model: { defaults: {
        tagName: 'section',
        attributes: {
          'data-sipet-block':'shop-banner-slider',
          style:'position:relative;min-height:760px;overflow:hidden;background:#f8fafc;'
        },
        droppable: false,
        script: function(){
          var root = this;
          var slides = Array.prototype.slice.call(root.querySelectorAll('[data-sipet-shop-slide]'));
          var prev = root.querySelector('[data-sipet-shop-prev]');
          var next = root.querySelector('[data-sipet-shop-next]');
          var dotsWrap = root.querySelector('[data-sipet-shop-dots]');
          if(!slides.length) return;
          var current = 0;
          var timer = null;
          function rebuildDots(){
            if(!dotsWrap) return;
            dotsWrap.innerHTML = '';
            slides.forEach(function(_, idx){
              var dot = document.createElement('button');
              dot.type = 'button';
              dot.setAttribute('data-sipet-shop-dot', String(idx));
              dot.style.width = '16px';
              dot.style.height = '16px';
              dot.style.borderRadius = '999px';
              dot.style.border = '2px solid rgba(15,23,42,.18)';
              dot.style.background = idx === current ? '#2563eb' : '#ffffff';
              dot.style.cursor = 'pointer';
              dot.style.boxShadow = '0 6px 16px rgba(15,23,42,.12)';
              dot.addEventListener('click', function(){ show(idx); start(); });
              dotsWrap.appendChild(dot);
            });
          }
          function show(index){
            current = (index + slides.length) % slides.length;
            slides.forEach(function(slide, idx){
              slide.style.opacity = idx === current ? '1' : '0';
              slide.style.pointerEvents = idx === current ? 'auto' : 'none';
              slide.style.transform = idx === current ? 'translateX(0)' : 'translateX(18px)';
              slide.style.zIndex = idx === current ? '2' : '1';
            });
            var dots = Array.prototype.slice.call(root.querySelectorAll('[data-sipet-shop-dot]'));
            dots.forEach(function(dot, idx){
              dot.style.background = idx === current ? '#2563eb' : '#ffffff';
              dot.style.borderColor = idx === current ? '#2563eb' : 'rgba(15,23,42,.18)';
              dot.style.transform = idx === current ? 'scale(1.08)' : 'scale(1)';
            });
          }
          function start(){
            stop();
            timer = setInterval(function(){ show(current + 1); }, 5000);
          }
          function stop(){
            if(timer){ clearInterval(timer); timer = null; }
          }
          rebuildDots();
          if(prev){ prev.addEventListener('click', function(){ show(current - 1); start(); }); }
          if(next){ next.addEventListener('click', function(){ show(current + 1); start(); }); }
          root.addEventListener('mouseenter', stop);
          root.addEventListener('mouseleave', start);
          show(0);
          start();
        },
        components:
          '<div style="position:absolute;inset:0;">'
            +'<div data-sipet-shop-slide style="position:absolute;inset:0;opacity:1;transition:opacity .6s ease,transform .6s ease;transform:translateX(0);">'
              +'<div style="position:absolute;inset:0;background:#fbfbfc;"></div>'
              +'<div style="position:absolute;inset:0;background:linear-gradient(135deg,transparent 16%,rgba(148,163,184,.18) 16.2%,transparent 16.5%,transparent 82%,rgba(148,163,184,.14) 82.2%,transparent 82.5%);"></div>'
              +'<div style="position:absolute;left:50%;top:120px;transform:translateX(-50%);font-size:.95rem;font-weight:900;letter-spacing:.18em;text-transform:uppercase;color:#1f2a5a;">Tech Equipment</div>'
              +'<div style="position:absolute;left:50%;top:148px;transform:translateX(-50%);font-size:9rem;font-weight:900;letter-spacing:-.06em;color:rgba(255,255,255,.9);text-transform:uppercase;text-shadow:0 20px 46px rgba(15,23,42,.14);white-space:nowrap;">Watch</div>'
              +'<div style="position:absolute;left:50%;top:230px;transform:translateX(-50%);width:min(880px,72vw);"><img src="https://placehold.co/920x560/f3f4f6/0f172a?text=Sube+tu+producto" alt="Producto destacado" style="width:100%;height:auto;object-fit:contain;display:block;filter:drop-shadow(0 22px 35px rgba(15,23,42,.18));"></div>'
              +'<div style="position:absolute;right:18%;top:318px;width:220px;height:220px;border-radius:999px;background:linear-gradient(180deg,#1d79db 0%,#1c2a99 100%);display:flex;align-items:center;justify-content:center;color:#fff;box-shadow:0 18px 36px rgba(29,121,219,.28);"><div style="text-align:center;"><div style="font-size:1.05rem;font-weight:500;margin-bottom:8px;">From</div><div style="font-size:3.2rem;font-weight:900;line-height:1;">$399</div><div style="font-size:1rem;opacity:.72;margin-top:4px;">Incl. Taxes</div></div></div>'
              +'<div style="position:absolute;left:50%;bottom:142px;transform:translateX(-50%);display:flex;flex-direction:column;gap:14px;color:#94a3b8;font-size:1rem;line-height:1.4;min-width:min(520px,70vw);"><div>✔ Dual-Core Processor, Integrated GPS</div><div>✔ WIFI (802.11b/g/n 2,4 GHz), Bluetooth 4.0</div><div>✔ OLED Retina Display</div><div>✔ 312 x 390 Pixel (42 mm)</div></div>'
              +'<a href="#" style="position:absolute;left:50%;bottom:58px;transform:translateX(-50%);display:inline-flex;align-items:center;justify-content:center;padding:18px 48px;border-radius:999px;background:#3394f3;color:#fff;font-size:1.15rem;font-weight:900;text-decoration:none;box-shadow:0 16px 30px rgba(51,148,243,.28);">🛒&nbsp;&nbsp;ADD TO CART</a>'
            +'</div>'
            +'<div data-sipet-shop-slide style="position:absolute;inset:0;opacity:0;transition:opacity .6s ease,transform .6s ease;transform:translateX(18px);pointer-events:none;">'
              +'<div style="position:absolute;inset:0;background:#fbfbfc;"></div>'
              +'<div style="position:absolute;inset:0;background:linear-gradient(135deg,transparent 16%,rgba(148,163,184,.18) 16.2%,transparent 16.5%,transparent 82%,rgba(148,163,184,.14) 82.2%,transparent 82.5%);"></div>'
              +'<div style="position:absolute;left:50%;top:120px;transform:translateX(-50%);font-size:.95rem;font-weight:900;letter-spacing:.18em;text-transform:uppercase;color:#1f2a5a;">Tech Equipment</div>'
              +'<div style="position:absolute;left:50%;top:148px;transform:translateX(-50%);font-size:8.8rem;font-weight:900;letter-spacing:-.06em;color:rgba(255,255,255,.9);text-transform:uppercase;text-shadow:0 20px 46px rgba(15,23,42,.14);white-space:nowrap;">Headphones</div>'
              +'<div style="position:absolute;left:50%;top:218px;transform:translateX(-50%);width:min(760px,64vw);"><img src="https://placehold.co/860x560/e5e7eb/0f172a?text=Sube+tu+producto" alt="Producto destacado" style="width:100%;height:auto;object-fit:contain;display:block;filter:drop-shadow(0 22px 35px rgba(15,23,42,.18));"></div>'
              +'<div style="position:absolute;right:20%;top:332px;width:200px;height:200px;border-radius:999px;background:linear-gradient(180deg,#1d79db 0%,#1c2a99 100%);display:flex;align-items:center;justify-content:center;color:#fff;box-shadow:0 18px 36px rgba(29,121,219,.28);"><div style="text-align:center;"><div style="font-size:1.05rem;font-weight:500;margin-bottom:8px;">From</div><div style="font-size:3rem;font-weight:900;line-height:1;">$299</div><div style="font-size:1rem;opacity:.72;margin-top:4px;">Incl. Taxes</div></div></div>'
              +'<div style="position:absolute;left:50%;bottom:142px;transform:translateX(-50%);display:flex;flex-direction:column;gap:14px;color:#94a3b8;font-size:1rem;line-height:1.4;min-width:min(520px,70vw);"><div>✔ Balanced High, Mid and Low tones</div><div>✔ Active Noise Cancellation</div><div>✔ Bluetooth Wireless</div><div>✔ 20 Hours Battery Life</div></div>'
              +'<a href="#" style="position:absolute;left:50%;bottom:58px;transform:translateX(-50%);display:inline-flex;align-items:center;justify-content:center;padding:18px 48px;border-radius:999px;background:#3394f3;color:#fff;font-size:1.15rem;font-weight:900;text-decoration:none;box-shadow:0 16px 30px rgba(51,148,243,.28);">🛒&nbsp;&nbsp;ADD TO CART</a>'
            +'</div>'
          +'</div>'
          +'<button data-sipet-shop-prev type="button" style="position:absolute;left:24px;top:50%;transform:translateY(-50%);z-index:5;width:64px;height:64px;border:none;background:rgba(15,23,42,.42);color:#fff;font-size:2rem;cursor:pointer;">‹</button>'
          +'<button data-sipet-shop-next type="button" style="position:absolute;right:24px;top:50%;transform:translateY(-50%);z-index:5;width:64px;height:64px;border:none;background:rgba(15,23,42,.42);color:#fff;font-size:2rem;cursor:pointer;">›</button>'
          +'<div data-sipet-shop-dots style="position:absolute;right:44px;bottom:28px;z-index:5;display:flex;gap:10px;"></div>',
      }},
      view: {}
    });
    try{ bm.remove('shop-banner'); }catch(e){}
    bm.add('shop-banner', {
      label:'Banner', category:'Tienda', media:'🎞',
      content: { type:'sipet-shop-banner-slider' }
    });

    /* ── 1. TASAS — fetch desde /api/frontend/tasas ─────────────── */
    dc.addType('sipet-tasas', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'tasas'; },
      model: { defaults: {
        tagName: 'section',
        attributes: { 'data-sipet-block':'tasas', style:'padding:64px 5%;background:#fff;' },
        droppable: false,
        script: function(){
          var el = this;
          var grid = el.querySelector('[data-sipet-grid]');
          if(!grid) return;
          fetch('/api/frontend/tasas')
            .then(function(r){ return r.json(); })
            .then(function(j){
              if(!j.success||!j.data) return;
              grid.innerHTML = j.data.map(function(t){
                return '<div style="background:#f8fafc;border-radius:12px;padding:24px;border-left:4px solid '+t.color+';">'
                  +'<div style="font-size:.75rem;font-weight:700;color:'+t.color+';text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">'+t.label+'</div>'
                  +'<div style="font-size:2.4rem;font-weight:800;color:#0f172a;line-height:1;">'+t.rate+'<span style="font-size:1rem;font-weight:600;">%</span></div>'
                  +'<div style="font-size:.85rem;color:#64748b;margin-top:4px;">'+t.unit+'</div>'
                  +'</div>';
              }).join('');
            })
            .catch(function(){ grid.innerHTML='<p style="color:#ef4444;padding:20px;">Error al cargar tasas.</p>'; });
        },
        components: '<div style="max-width:900px;margin:0 auto;">'
          +'<div style="text-align:center;margin-bottom:36px;">'
          +'<h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">Tasas de interés vigentes</h2>'
          +'<p style="color:#64748b;font-size:.9rem;">Datos en tiempo real desde SIPET</p></div>'
          +'<div data-sipet-grid style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;">'
          +'<div style="padding:24px;text-align:center;color:#94a3b8;">Cargando tasas…</div></div>'
          +'<p style="text-align:center;font-size:.78rem;color:#94a3b8;margin-top:20px;">Las tasas son referenciales. Consulta en sucursal para más información.</p>'
          +'</div>',
      }},
      view: {}
    });
    try{ bm.remove('section-tasas'); }catch(e){}
    bm.add('section-tasas', {
      label:'Tasas (API SIPET)', category:'Cooperativa', media:'📈',
      content: { type:'sipet-tasas' }
    });

    /* ── 2. CONTACTO — POST a /api/frontend/contact ─────────────── */
    dc.addType('sipet-contact', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'contact'; },
      model: { defaults: {
        tagName: 'section',
        attributes: { 'data-sipet-block':'contact', style:'padding:64px 5%;background:#fff;' },
        droppable: false,
        script: function(){
          var el = this;
          var form = el.querySelector('form[data-sipet-form]');
          var msg  = el.querySelector('[data-sipet-msg]');
          if(!form) return;
          form.addEventListener('submit', function(ev){
            ev.preventDefault();
            var btn  = form.querySelector('button[type="submit"]');
            var name    = (form.querySelector('[name="name"]').value    || '').trim();
            var email   = (form.querySelector('[name="email"]').value   || '').trim();
            var message = (form.querySelector('[name="message"]').value || '').trim();
            if(!name||!email||!message){
              if(msg){ msg.textContent='Completa todos los campos.'; msg.style.color='#ef4444'; msg.style.display='block'; }
              return;
            }
            if(btn){ btn.disabled=true; btn.textContent='Enviando…'; }
            fetch('/api/frontend/contact',{
              method:'POST', headers:{'Content-Type':'application/json'},
              body:JSON.stringify({name:name,email:email,message:message})
            })
            .then(function(r){ return r.json(); })
            .then(function(j){
              form.reset();
              if(msg){
                msg.textContent = j.success ? '¡Mensaje enviado! Nos contactaremos pronto.' : (j.error||'Error al enviar.');
                msg.style.color = j.success ? '#10b981' : '#ef4444';
                msg.style.display = 'block';
              }
            })
            .catch(function(){ if(msg){ msg.textContent='Error de red.'; msg.style.color='#ef4444'; msg.style.display='block'; } })
            .finally(function(){ if(btn){ btn.disabled=false; btn.textContent='Enviar mensaje'; } });
          });
        },
        components: '<div style="max-width:520px;margin:0 auto;text-align:center;">'
          +'<h2 style="font-size:2rem;font-weight:800;color:#0f172a;margin:0 0 12px;">¿Cómo podemos ayudarte?</h2>'
          +'<p style="color:#64748b;margin:0 0 24px;">Escríbenos y nos pondremos en contacto contigo.</p>'
          +'<p data-sipet-msg style="display:none;padding:10px 16px;border-radius:8px;margin-bottom:16px;font-size:.9rem;font-weight:600;background:#f0fdf4;"></p>'
          +'<form data-sipet-form style="display:flex;flex-direction:column;gap:14px;text-align:left;" onsubmit="return false;">'
          +'<input type="text" name="name" placeholder="Nombre completo" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;width:100%;">'
          +'<input type="email" name="email" placeholder="Correo electrónico" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;width:100%;">'
          +'<textarea name="message" placeholder="Tu mensaje…" rows="4" style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:.95rem;outline:none;resize:vertical;"></textarea>'
          +'<button type="submit" style="padding:13px;background:#0f172a;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;">Enviar mensaje</button>'
          +'</form></div>',
      }},
      view: {}
    });
    try{ bm.remove('section-contact'); }catch(e){}
    bm.add('section-contact', {
      label:'Formulario contacto', category:'Secciones', media:'📬',
      content: { type:'sipet-contact' }
    });

    /* ── 3. GALERÍA — fetch + upload /api/frontend/gallery ───────── */
    dc.addType('sipet-gallery', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'gallery'; },
      model: { defaults: {
        tagName: 'section',
        attributes: { 'data-sipet-block':'gallery', style:'padding:64px 5%;background:#f8fafc;' },
        droppable: false,
        script: function(){
          var el      = this;
          var grid    = el.querySelector('[data-sipet-gallery-grid]');
          var upBtn   = el.querySelector('[data-sipet-upload]');
          var fileInp = el.querySelector('[data-sipet-file]');
          if(!grid) return;
          function loadGallery(){
            fetch('/api/frontend/gallery')
              .then(function(r){ return r.json(); })
              .then(function(j){
                if(!j.success) return;
                if(!j.data.length){
                  grid.innerHTML='<p style="color:#94a3b8;text-align:center;padding:32px;grid-column:1/-1;">Galería vacía. Usa el botón para subir imágenes.</p>';
                  return;
                }
                grid.innerHTML = j.data.map(function(img){
                  return '<div style="border-radius:10px;overflow:hidden;cursor:pointer;aspect-ratio:4/3;background:#e2e8f0;">'
                    +'<img src="'+img.url+'" alt="'+img.filename+'" '
                    +'style="width:100%;height:100%;object-fit:cover;" '
                    +'onclick="window.open(this.src,\'_blank\')" loading="lazy"></div>';
                }).join('');
              })
              .catch(function(){ grid.innerHTML='<p style="color:#ef4444;grid-column:1/-1;">Error cargando galería.</p>'; });
          }
          loadGallery();
          if(upBtn && fileInp){
            upBtn.addEventListener('click', function(){ fileInp.click(); });
            fileInp.addEventListener('change', function(){
              if(!fileInp.files||!fileInp.files.length) return;
              var file = fileInp.files[0];
              var fd = new FormData();
              fd.append('file', file);
              fd.append('image', file);
              fd.append('files', file);
              console.log('[frontend-builder] upload component file', {
                name: file && file.name,
                size: file && file.size,
                type: file && file.type
              });
              upBtn.textContent='Subiendo…'; upBtn.disabled=true;
              fetch('/api/frontend/gallery/upload',{method:'POST',credentials:'include',headers:_csrfHeaders(),body:fd})
                .then(_readJSONResponse)
                .then(function(j){ if(j.success){ loadGallery(); } else { alert(j.error||'Error al subir'); } })
                .catch(function(err){ alert(err && err.message ? err.message : 'Error de red'); })
                .finally(function(){ upBtn.textContent='+ Subir imagen'; upBtn.disabled=false; fileInp.value=''; });
            });
          }
        },
        components: '<div style="max-width:1100px;margin:0 auto;">'
          +'<div style="text-align:center;margin-bottom:36px;display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;">'
          +'<h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0;">Galería</h2>'
          +'<button data-sipet-upload style="padding:8px 18px;background:#3b82f6;color:#fff;border:none;border-radius:7px;font-size:.85rem;font-weight:700;cursor:pointer;">+ Subir imagen</button>'
          +'<input data-sipet-file type="file" accept="image/*" style="display:none;"></div>'
          +'<div data-sipet-gallery-grid style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;">'
          +'<div style="padding:32px;text-align:center;color:#94a3b8;grid-column:1/-1;">Cargando galería…</div></div>'
          +'</div>',
      }},
      view: {}
    });
    bm.add('section-gallery', {
      label:'Galería + upload', category:'Cooperativa', media:'🖼',
      content: { type:'sipet-gallery' }
    });

    /* ── 4. MAPA configurable — trait para embed URL ─────────────── */
    dc.addType('sipet-mapa', {
      isComponent: function(el){ return el.dataset && el.dataset.sipetBlock === 'mapa'; },
      model: {
        defaults: {
          tagName: 'section',
          attributes: { 'data-sipet-block':'mapa', style:'padding:64px 5%;background:#f8fafc;', 'data-embed-url':'' },
          droppable: false,
          traits: [
            { type:'text',  name:'data-embed-url', label:'Google Maps Embed URL', placeholder:'https://www.google.com/maps/embed?pb=...' },
          ],
          script: function(){
            var el = this;
            var src = el.getAttribute('data-embed-url');
            if(!src) return;
            var iframe = el.querySelector('iframe[data-map-embed]');
            if(iframe) iframe.src = src;
          },
          components: '<div style="max-width:1100px;margin:0 auto;">'
            +'<div style="text-align:center;margin-bottom:36px;">'
            +'<h2 style="font-size:1.9rem;font-weight:800;color:#0f172a;margin:0 0 10px;">¿Dónde encontrarnos?</h2>'
            +'<p style="color:#64748b;">Visita cualquiera de nuestras sucursales.</p></div>'
            +'<div style="display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:start;">'
            +'<div style="background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.06);">'
            +'<h3 style="font-size:1rem;font-weight:700;color:#0f172a;margin:0 0 16px;">Sucursal Central</h3>'
            +'<div style="display:flex;flex-direction:column;gap:12px;font-size:.9rem;color:#475569;">'
            +'<div style="display:flex;gap:10px;"><span>📍</span><span>4a Avenida 12-34, Zona 1, Guatemala</span></div>'
            +'<div style="display:flex;gap:10px;"><span>📞</span><span>(502) 2222-3333</span></div>'
            +'<div style="display:flex;gap:10px;"><span>🕐</span><span>Lun–Vie: 8:00–17:00 hrs</span></div>'
            +'<div style="display:flex;gap:10px;"><span>✉</span><span>info@cooperativa.com</span></div>'
            +'</div></div>'
            +'<div style="border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.1);background:#e2e8f0;">'
            +'<iframe data-map-embed width="100%" height="280" style="border:none;display:block;" allowfullscreen loading="lazy" '
            +'src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3860.3!2d-90.5069!3d14.6349!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTTCsDM4JzA1LjYiTiA5MMKwMzAnMjQuOCJX!5e0!3m2!1ses!2sgt!4v1000000000000"></iframe>'
            +'</div></div></div>',
        },
        init: function(){
          this.on('change:attributes:data-embed-url', function(){
            var src = this.getAttributes()['data-embed-url'] || '';
            var el  = this.getEl();
            if(el && src){ var iframe = el.querySelector('iframe[data-map-embed]'); if(iframe) iframe.src = src; }
          });
        }
      },
      view: {}
    });
    try{ bm.remove('section-mapa'); }catch(e){}
    bm.add('section-mapa', {
      label:'Mapa (configurable)', category:'Cooperativa', media:'📍',
      content: { type:'sipet-mapa' }
    });

    /* ── sipet-form: formulario dinámico del backend ─────────────── */
    dc.addType('sipet-form', {
      isComponent: function(el){
        return el.tagName === 'DIV' && el.classList && el.classList.contains('sipet-form-widget');
      },
      model: {
        defaults: {
          tagName: 'div',
          attributes: { 'class':'sipet-form-widget', 'data-slug':'' },
          droppable: false,
          resizable: false,
          traits: [
            {
              type: 'select',
              name: 'data-slug',
              label: 'Formulario',
              options: [{ value:'', name:'⏳ Cargando formularios…' }],
            },
          ],
        },
        init: function(){
          var self = this;
          /* Re-render the canvas placeholder whenever the slug trait changes */
          self.listenTo(self, 'change:attributes', function(){
            if(self.view) self.view._updatePlaceholder();
          });
          /* Populate select options from the backend */
          fetch('/api/frontend/forms', {credentials:'include'})
            .then(function(r){ return r.json(); })
            .then(function(j){
              var opts = [{ value:'', name:'— Seleccionar formulario —' }];
              if(j.success && j.data && j.data.length){
                j.data.forEach(function(f){ opts.push({ value:f.slug, name:f.name + ' (' + f.slug + ')' }); });
              } else {
                opts.push({ value:'', name:'(No hay formularios activos)' });
              }
              var trait = self.getTrait('data-slug');
              if(trait){ trait.set('options', opts); }
            })
            .catch(function(){});
        },
      },
      view: {
        _updatePlaceholder: function(){
          var slug = this.model.getAttributes()['data-slug'] || '';
          this.el.innerHTML =
            '<div style="font-family:system-ui,sans-serif;padding:24px 20px;border:2px dashed #3b82f6;'
            + 'border-radius:12px;background:#eff6ff;text-align:center;min-height:90px;'
            + 'display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;pointer-events:none;">'
            + '<div style="font-size:1.6rem;">📋</div>'
            + '<div style="font-size:13px;font-weight:700;color:#1e40af;">'
            + (slug ? 'Formulario: <code style="background:#dbeafe;padding:2px 6px;border-radius:4px;">' + slug + '</code>'
                    : 'Formulario dinámico — configura el slug en <strong>⚙ Propiedades</strong>')
            + '</div>'
            + '<div style="font-size:11px;color:#64748b;">Se renderizará con todos sus campos en la página publicada</div>'
            + '</div>';
        },
        onRender: function(){ this._updatePlaceholder(); },
      },
    });

    bm.add('formulario', {
      label: 'Formulario', category: 'Cooperativa', media: '📋',
      content: { type:'sipet-form' },
    });

    dc.addType('sipet-html-raw', {
      isComponent: function(el){
        if (el.tagName === 'DIV' && el.classList && el.classList.contains('sipet-html-raw')) {
          var styleEl = el.querySelector('style[data-sipet-inline-css="1"]');
          var rawCss = styleEl ? styleEl.innerHTML || '' : '';
          var clone = el.cloneNode(true);
          var cloneStyle = clone.querySelector('style[data-sipet-inline-css="1"]');
          if(cloneStyle && cloneStyle.parentNode) cloneStyle.parentNode.removeChild(cloneStyle);
          return { type: 'sipet-html-raw', rawHtml: clone.innerHTML || '', rawCss: rawCss };
        }
      },
      model: {
        defaults: {
          tagName: 'div',
          classes: ['sipet-html-raw'],
          droppable: false,
          editable: false,
          rawHtml: '<div style="padding:20px;border:1px dashed #cbd5e1;border-radius:10px;background:#f8fafc;color:#475569;text-align:center;">Doble clic para agregar HTML.</div>',
          rawCss: '',
          traits: [
            { type:'html-textarea', name:'rawHtml', label:'HTML libre', changeProp: 1 },
            { type:'html-textarea', name:'rawCss', label:'CSS libre', changeProp: 1 },
          ],
        },
        init: function(){
          this.on('change:rawHtml', this._syncRawHtml);
          this.on('change:rawCss', this._syncRawHtml);
          this._syncRawHtml();
        },
        _syncRawHtml: function(){
          var html = this.get('rawHtml') || '';
          var css = this.get('rawCss') || '';
          var fallback = '<div style="padding:20px;border:1px dashed #cbd5e1;border-radius:10px;background:#f8fafc;color:#475569;text-align:center;">Doble clic para agregar HTML.</div>';
          var content = (css ? '<style data-sipet-inline-css="1">' + css + '</style>' : '') + (html || fallback);
          this.components(content);
        },
      },
      view: {
        events: {
          dblclick: '_handleDoubleClick',
        },
        _handleDoubleClick: function(event){
          event.preventDefault();
          event.stopPropagation();
          window.openHtmlRawModal(this.model);
        },
      },
    });

  })();

  /* Inyectar paleta después de que el canvas esté listo */
  _editor.on('load', function(){
    loadBrandColors();
    /* Panel de paleta corporativa: se inserta al final del contenedor de vistas */
    var container = document.getElementById('wb-sidebar-content');
    if(container && !document.getElementById('_wb_brand_palette')){
      var wrap = document.createElement('div');
      wrap.id = '_wb_brand_palette_wrap';
      wrap.innerHTML = '<div style="border-top:1px solid #1e293b;padding:0;">'
        + '<div style="font-size:10px;font-weight:700;color:#475569;letter-spacing:.08em;text-transform:uppercase;padding:8px 12px 4px;">Paleta corporativa</div>'
        + '<div id="_wb_brand_palette"></div>'
        + '</div>';
      container.appendChild(wrap);
      renderBrandSwatches();
    }
  });

  /* Re-inyectar CSS vars al cargar cada página */
  _editor.on('component:add', function(comp){
    injectBrandCSSVars();
    applyBrandLogoToComp(comp);
  });

  /* ── Galería + doble clic en imagen ───────────────────── */
  var _galleryTargetComp = null;
  var _galleryMode = 'srcattr'; /* 'srcattr' | 'bgimage' */

  function _loadGallery(){
    var grid = document.getElementById('wb-gallery-grid');
    grid.innerHTML = '<p style="color:#64748b;font-size:12px;padding:12px;">Cargando…</p>';
    fetch('/api/frontend/gallery', {credentials:'include'})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if(!j.success || !j.data || !j.data.length){
          grid.innerHTML = '<p style="color:#64748b;font-size:12px;padding:12px;">La galería está vacía. Sube imágenes con el botón de arriba.</p>';
          return;
        }
        grid.innerHTML = j.data.map(function(item){
          var u = item.url.replace(/"/g,'&quot;');
          var n = (item.filename||'').replace(/</g,'&lt;');
          return '<div class="wbg-thumb" onclick="_applyGalleryImg(\''+u+'\')"><img src="'+u+'" loading="lazy" alt="'+n+'"><span>'+n+'</span></div>';
        }).join('');
      }).catch(function(){
        grid.innerHTML = '<p style="color:#f87171;font-size:12px;padding:12px;">Error al cargar galería.</p>';
      });
  }

  function _findFirstImageComp(comp){
    if(!comp) return null;
    try{
      var tagName = comp.get && comp.get('tagName');
      var type = comp.get && comp.get('type');
      if((tagName && String(tagName).toLowerCase() === 'img') || type === 'image') return comp;
    }catch(e){}
    if(!comp.components) return null;
    var children = comp.components();
    if(!children || !children.length) return null;
    for(var i = 0; i < children.length; i++){
      var child = children.at ? children.at(i) : children[i];
      var found = _findFirstImageComp(child);
      if(found) return found;
    }
    return null;
  }

  function _setCompImageSrc(comp, url){
    if(!comp || !url) return false;
    var target = _findFirstImageComp(comp) || comp;
    try{
      if(typeof target.addAttributes === 'function'){
        target.addAttributes({ src: url });
      }
      if(typeof target.setAttributes === 'function'){
        var attrs = target.getAttributes ? (target.getAttributes() || {}) : {};
        target.setAttributes(Object.assign({}, attrs, { src: url }));
      }
      if(typeof target.set === 'function'){
        target.set('src', url);
      }
      return true;
    }catch(e){
      return false;
    }
  }

  var _imageAutosaveTimer = null;
  function _queueImageAutosave(){
    if(!_currentPageId || typeof window.saveCurrentPage !== 'function') return;
    if(_imageAutosaveTimer) clearTimeout(_imageAutosaveTimer);
    _imageAutosaveTimer = setTimeout(function(){
      _imageAutosaveTimer = null;
      window.saveCurrentPage();
    }, 250);
  }

  window._applyGalleryImg = function(url){
    if(!_galleryTargetComp){ document.getElementById('wb-gallery-overlay').classList.remove('open'); return; }
    var isLogoSlot = _galleryTargetComp.getAttributes && !!_galleryTargetComp.getAttributes()['data-sipet-logo'];
    if(isLogoSlot){
      /* Replace the text/anchor with an img */
      _galleryTargetComp.set('content', '<img src="'+url+'" style="height:38px;width:auto;object-fit:contain;display:block;" alt="Logo" data-sipet-logo="1">');
      /* Persist logo URL */
      _brandLogo = url;
      fetch('/api/frontend/brand', {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:JSON.stringify({logo_url:url})});
    } else if(_galleryMode === 'bgimage'){
      var bgApplied = false;
      var bgImgComp = _findBgTargetComp(_galleryTargetComp);
      if(bgImgComp){
        bgApplied = _setCompImageSrc(bgImgComp, url);
      }
      if(!bgApplied){
        /* Apply as CSS background-image (e.g. Hero Centrado section) */
        _galleryTargetComp.addStyle({
          'background-image':    'url("'+url+'")',
          'background-size':     'cover',
          'background-position': 'center',
          'background-repeat':   'no-repeat'
        });
      }
    } else {
      _setCompImageSrc(_galleryTargetComp, url);
    }
    _galleryMode = 'srcattr';
    _setDirty(true);
    _queueImageAutosave();
    document.getElementById('wb-gallery-overlay').classList.remove('open');
    toast('Imagen actualizada ✓');
  };

  window._cpPickBgImage = function(){
    var comp = _editor && _editor.getSelected();
    if(!comp){ toast('Selecciona un componente primero', false); return; }
    _galleryMode = 'bgimage';
    document.getElementById('wb-color-panel').classList.remove('open');
    _openGalleryForComp(comp);
  };

  function _findBgTargetComp(comp){
    if(!comp) return null;
    var attrs = comp.getAttributes ? comp.getAttributes() : {};
    if(attrs && attrs['data-sipet-bg-target']) return comp;
    if(comp.components){
      var children = comp.components();
      if(children && children.length){
        for(var i = 0; i < children.length; i++){
          var child = children.at ? children.at(i) : children[i];
          var found = _findBgTargetComp(child);
          if(found) return found;
        }
      }
    }
    return null;
  }

  function _findBgHostComp(comp){
    var current = comp;
    while(current){
      if(_isBgImageComp(current)) return current;
      current = current.parent ? current.parent() : null;
    }
    return comp || null;
  }

  function _isBgImageComp(comp){
    if(!comp || !comp.getAttributes) return false;
    var attrs = comp.getAttributes() || {};
    return !!attrs['data-sipet-bg-image'];
  }

  function _isHtmlRawComp(comp){
    return !!(comp && String(comp.get && comp.get('type') || '').toLowerCase() === 'sipet-html-raw');
  }

  function _findHtmlRawOwner(comp){
    var current = comp;
    while(current){
      if(_isHtmlRawComp(current)) return current;
      current = current.parent ? current.parent() : null;
    }
    return null;
  }

  function _openGalleryForComp(comp){
    _galleryTargetComp = _findBgHostComp(comp);
    if(_isBgImageComp(comp)) _galleryMode = 'bgimage';
    if(_isBgImageComp(_galleryTargetComp)) _galleryMode = 'bgimage';
    document.getElementById('wb-gallery-overlay').classList.add('open');
    _loadGallery();
  }

  function _resolveCompFromCanvasElement(el){
    if(!_editor || !el) return null;
    if(el.nodeType === 3 && el.parentElement){
      el = el.parentElement;
    }
    if(typeof _editor.getModelForEl === 'function'){
      var current = el;
      while(current && current.nodeType === 1){
        var currentComp = _editor.getModelForEl(current);
        if(_isHtmlRawComp(currentComp)) return currentComp;
        current = current.parentElement;
      }
    }
    var editableFromTree = _findEditableTextCompFromElement(el);
    if(editableFromTree) return editableFromTree;
    if(typeof _editor.getModelForEl === 'function'){
      var direct = _editor.getModelForEl(el);
      if(direct) return direct;
    }
    if(el.closest){
      var bgHost = el.closest('[data-sipet-bg-image]');
      if(bgHost && typeof _editor.getModelForEl === 'function'){
        var bgComp = _editor.getModelForEl(bgHost);
        if(bgComp) return bgComp;
      }
      var logoHost = el.closest('[data-sipet-logo]');
      if(logoHost && typeof _editor.getModelForEl === 'function'){
        var logoComp = _editor.getModelForEl(logoHost);
        if(logoComp) return logoComp;
      }
      var imgHost = el.closest('img');
      if(imgHost && typeof _editor.getModelForEl === 'function'){
        var imgComp = _editor.getModelForEl(imgHost);
        if(imgComp) return imgComp;
      }
    }
    return _editor.getSelected ? _editor.getSelected() : null;
  }

  function _findEditableTextCompFromElement(el){
    if(!_editor || !el || typeof _editor.getModelForEl !== 'function') return null;
    if(el.nodeType === 3 && el.parentElement){
      el = el.parentElement;
    }
    var current = el;
    while(current && current.nodeType === 1){
      var comp = _editor.getModelForEl(current);
      if(comp && _canEditText(comp)) return comp;
      if(comp){
        var nested = _findEditableTextCompInSubtree(comp, el);
        if(nested) return nested;
      }
      current = current.parentElement;
    }
    return null;
  }

  function _findEditableTextCompInSubtree(comp, originEl){
    if(!comp) return null;
    var ownEl = comp.getEl ? comp.getEl() : null;
    if(ownEl === originEl && _canEditText(comp)) return comp;
    if(ownEl && originEl && ownEl.contains && ownEl.contains(originEl) && _canEditText(comp) && _isTextLikeElement(originEl)){
      return comp;
    }
    if(!comp.components) return null;
    var children = comp.components();
    if(!children || !children.length) return null;
    for(var i = 0; i < children.length; i++){
      var child = children.at ? children.at(i) : children[i];
      if(!child) continue;
      var found = _findEditableTextCompInSubtree(child, originEl);
      if(found) return found;
    }
    return null;
  }

  /* Subir imagen desde el input */
  document.getElementById('wb-img-upload').addEventListener('change', function(){
    var file = this.files && this.files[0];
    if(!file) return;
    var fd = new FormData();
    fd.append('file', file);
    fd.append('image', file);
    fd.append('files', file);
    console.log('[frontend-builder] upload file', {
      name: file && file.name,
      size: file && file.size,
      type: file && file.type
    });
    toast('Subiendo imagen…');
    fetch('/api/frontend/gallery/upload', { method:'POST', credentials:'include', headers:_csrfHeaders(), body:fd })
      .then(_readJSONResponse)
      .then(function(j){
        if(j.success && j.url){
          window._applyGalleryImg(j.url);
        } else {
          toast('Error: '+(j.error||'sin respuesta'), false);
        }
      }).catch(function(err){ toast('Error: ' + (err && err.message ? err.message : 'red'), false); });
    this.value = '';
  });

  /* Doble clic en el canvas → abrir galería si el elemento es IMG o tiene data-sipet-logo */
  _editor.on('load', function(){
    /* Cargar logo guardado y auto-inyectarlo */
    fetch('/api/frontend/brand', {credentials:'include'})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if(j.success && j.data){
          /* Prioridad: logo guardado manualmente en el builder; si no, el de identidad institucional */
          if(j.data.logo_url){
            _brandLogo = j.data.logo_url;
          } else if(j.data.identidad_logo_url){
            _brandLogo = j.data.identidad_logo_url;
          }
          applyBrandLogoToCanvas();
        }
      });

    var canvasDoc = _editor.Canvas.getDocument();
    canvasDoc.addEventListener('dblclick', function(e){
      var t = e.target;
      var comp = _resolveCompFromCanvasElement(t);
      var htmlRawOwner = _findHtmlRawOwner(comp);
      if(htmlRawOwner){
        e.preventDefault(); e.stopPropagation();
        window.openHtmlRawModal(htmlRawOwner);
        return;
      }
      if(comp && _canEditText(comp)){
        e.preventDefault(); e.stopPropagation();
        _openTextEditor(comp);
        return;
      }
      /* Logo slot — cualquier elemento con data-sipet-logo */
      if(t && t.closest && t.closest('[data-sipet-logo]')){
        if(!comp) return;
        e.preventDefault(); e.stopPropagation();
        _openGalleryForComp(comp);
        return;
      }
      /* Sección con fondo de imagen: solo abrir galería cuando el objetivo es la foto/fondo,
         no cuando el doble clic cae sobre un texto editable dentro del bloque */
      if(t && t.closest && t.closest('[data-sipet-bg-image]')){
        if(!comp) return;
        if(_canEditText(comp)){
          e.preventDefault(); e.stopPropagation();
          _openTextEditor(comp);
          return;
        }
        e.preventDefault(); e.stopPropagation();
        _galleryMode = 'bgimage';
        _openGalleryForComp(comp);
        return;
      }
      /* Imagen normal */
      if(t && t.tagName === 'IMG'){
        if(!comp) return;
        e.preventDefault(); e.stopPropagation();
        _openGalleryForComp(comp);
      }
    }, true);

    /* Menú contextual con clic derecho en canvas */
    canvasDoc.addEventListener('contextmenu', function(e){
      e.preventDefault(); e.stopPropagation();
      var comp = _resolveCompFromCanvasElement(e.target) || _editor.getSelected();
      if(!comp) return;
      _editor.select(comp);
      _showCtxMenu(e.clientX, e.clientY, comp);
    });
  });

  /* ── Menú contextual ────────────────────────────────────── */
  var _ctxComp = null;

  function _isTextLikeElement(el){
    if(!el || el.nodeType !== 1) return false;
    var tag = el.tagName ? String(el.tagName).toUpperCase() : '';
    if(['IMG', 'VIDEO', 'IFRAME', 'SVG', 'PATH', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'STYLE', 'SCRIPT'].indexOf(tag) >= 0) return false;
    if(el.classList && el.classList.contains('sipet-editable-text')) return true;
    if(['A', 'BUTTON', 'P', 'SPAN', 'LABEL', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'SMALL', 'STRONG', 'EM', 'B', 'I', 'DIV'].indexOf(tag) >= 0){
      var text = typeof el.textContent === 'string' ? el.textContent.trim() : '';
      return !!text;
    }
    return false;
  }

  function _canEditText(comp){
    if(!comp) return false;
    var el = comp.getEl();
    var tag = el && el.tagName ? String(el.tagName).toUpperCase() : '';
    var typeName = String(comp.get('type') || '').toLowerCase();
    if(['IMG', 'VIDEO', 'IFRAME', 'SVG', 'PATH'].indexOf(tag) >= 0) return false;
    if(comp.get && (comp.get('editable') === true || comp.get('textable') === true)) return true;
    if(el && el.classList && el.classList.contains('sipet-editable-text')) return true;
    if(['text', 'textnode', 'link'].indexOf(typeName) >= 0) return true;
    if(tag && ['A', 'BUTTON', 'P', 'SPAN', 'LABEL', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'SMALL', 'STRONG', 'EM', 'B', 'I'].indexOf(tag) >= 0) return true;
    if(comp.components && comp.components().length) return false;
    var content = String(comp.get('content') || '').trim();
    if(content) return true;
    var text = el && typeof el.textContent === 'string' ? el.textContent.trim() : '';
    return !!text;
  }

  function _findEditableTextDescendant(comp){
    if(!comp || !comp.components) return null;
    var children = comp.components();
    if(!children || !children.length) return null;
    for(var i = 0; i < children.length; i++){
      var child = children.at ? children.at(i) : children[i];
      if(!child) continue;
      if(_canEditText(child)) return child;
      var nested = _findEditableTextDescendant(child);
      if(nested) return nested;
    }
    return null;
  }

  function _getEditableTextTarget(comp){
    if(!comp) return null;
    if(_canEditText(comp)) return comp;
    return _findEditableTextDescendant(comp);
  }

  function _openTextEditor(comp){
    if(!_editor || !comp) return;
    var target = _getEditableTextTarget(comp);
    if(!target) {
      toast('Selecciona un texto editable primero', false);
      return;
    }
    _editor.select(target);
    var el = target.getEl ? target.getEl() : null;
    if(!el) {
      toast('No se pudo activar la edición de texto', false);
      return;
    }
    if(!el.__sipetRichTextBound){
      el.addEventListener('input', function(){
        _setDirty(true);
      });
      el.addEventListener('blur', function(){
        _setDirty(true);
      });
      el.__sipetRichTextBound = true;
    }
    try {
      _editor.runCommand('core:component-text-edit', { target: target, event: { target: el } });
    } catch(err) {
      try {
        _editor.runCommand('rte:enable', { target: el, event: { target: el } });
      } catch(innerErr) {}
    }
    try {
      if(window.getSelection && document.createRange){
        var range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        var sel = window.getSelection();
        if(sel){
          sel.removeAllRanges();
          sel.addRange(range);
        }
      }
      el.focus();
    } catch(err) {}
  }

  function _showCtxMenu(x, y, comp){
    _ctxComp = comp;
    var el   = comp.getEl();
    var isImg = el && el.tagName === 'IMG';
    var isBgImage = _isBgImageComp(comp);
    var canEditText = _canEditText(comp);
    var menu = document.getElementById('wb-ctx-menu');
    document.getElementById('ctx-img').style.display = (isImg || isBgImage) ? 'flex' : 'none';
    document.getElementById('ctx-text').style.display = canEditText ? 'flex' : 'none';
    /* offset because canvas is inside an iframe */
    var canvasRect = document.getElementById('gjs').getBoundingClientRect();
    var left = canvasRect.left + x;
    var top  = canvasRect.top  + y;
    if(left + 200 > window.innerWidth)  left = window.innerWidth  - 204;
    if(top  + 220 > window.innerHeight) top  = window.innerHeight - 224;
    menu.style.left = left + 'px';
    menu.style.top  = top  + 'px';
    menu.classList.add('open');
  }

  function _closeCtxMenu(){ document.getElementById('wb-ctx-menu').classList.remove('open'); }
  document.addEventListener('click', _closeCtxMenu);
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') _closeCtxMenu(); });

  window._ctxChangeImage = function(){
    _closeCtxMenu();
    if(_ctxComp) _openGalleryForComp(_ctxComp);
  };
  window._ctxEditColor = function(){
    _closeCtxMenu();
    if(_ctxComp){ _editor.select(_ctxComp); _openColorPanel(_ctxComp); }
  };
  window._ctxEditText = function(){
    _closeCtxMenu();
    if(_ctxComp) _openTextEditor(_ctxComp);
  };
  window._ctxDuplicate = function(){
    _closeCtxMenu();
    if(_ctxComp) _editor.runCommand('core:copy'); setTimeout(function(){ _editor.runCommand('core:paste'); }, 50);
  };
  window._ctxSelectParent = function(){
    _closeCtxMenu();
    if(_ctxComp && _ctxComp.parent()) _editor.select(_ctxComp.parent());
  };
  window._ctxDelete = function(){
    _closeCtxMenu();
    if(_ctxComp) _ctxComp.remove();
  };

  /* ── Botón lápiz en toolbar flotante ─────────────────────── */
  function _rgbToHex(rgb){
    if(!rgb || rgb==='transparent') return '#000000';
    if(/^#/.test(rgb)) return rgb;
    var m = rgb.match(/\d+/g);
    if(!m || m.length<3) return '#000000';
    return '#'+[m[0],m[1],m[2]].map(function(n){ return ('0'+parseInt(n).toString(16)).slice(-2); }).join('');
  }
  window._cpApply = function(prop, val){
    if(!_editor) return;
    var sel = _editor.getSelected();
    if(!sel) return;
    sel.addStyle(prop, val);
    _setDirty(true);
  };
  window._cpEditText = function(){
    if(!_editor) return;
    var sel = _editor.getSelected();
    if(sel) _openTextEditor(sel);
  };
  function _openColorPanel(component){
    var panel = document.getElementById('wb-color-panel');
    var styles = component.getStyle();
    var bg = _rgbToHex(styles['background-color'] || '');
    var fg = _rgbToHex(styles['color'] || '#000000');
    var bd = _rgbToHex(styles['border-color'] || '#e2e8f0');
    document.getElementById('cp-bg-color').value = bg;
    document.getElementById('cp-bg-hex').value   = bg;
    document.getElementById('cp-fg-color').value = fg;
    document.getElementById('cp-fg-hex').value   = fg;
    document.getElementById('cp-bd-color').value = bd;
    document.getElementById('cp-bd-hex').value   = bd;
    /* posicionar cerca del toolbar flotante */
    var el = component.getEl();
    if(el){
      var r = el.getBoundingClientRect();
      var canvasRect = document.getElementById('gjs').getBoundingClientRect();
      var top  = Math.min(canvasRect.top + r.top + 40, window.innerHeight - 240);
      var left = Math.min(canvasRect.left + r.left, window.innerWidth - 240);
      if(top < 60) top = 60;
      if(left < 4) left = 4;
      panel.style.top  = top  + 'px';
      panel.style.left = left + 'px';
    }
    panel.classList.add('open');
  }
  _editor.Commands.add('sipet-color-edit', {
    run: function(ed){ _openColorPanel(ed.getSelected()); },
  });
  /* Inyectar botón en TODOS los tipos de componente MAIN */
  (function(){
    var _svgPencil = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width:14px;height:14px;fill:#fff;display:block;"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>';
    var _svgText = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width:14px;height:14px;fill:#fff;display:block;"><path d="M5 4h14v3h-1.5V5.5H13v13h2V20H9v-1.5h2v-13H6.5V7H5z"/></svg>';
    var _editBtn = { id:'sipet-color-edit', label:_svgPencil, command:'sipet-color-edit', attributes:{title:'Editar colores', class:'gjs-toolbar-item'} };
    var _textBtn = { id:'sipet-text-edit', label:_svgText, command:'sipet-text-edit', attributes:{title:'Editar texto', class:'gjs-toolbar-item'} };
    _editor.Commands.add('sipet-text-edit', {
      run: function(ed){ _openTextEditor(ed.getSelected()); },
    });
    /* Patch the default component type so the button exists before first selection */
    var domc = _editor.DomComponents;
    ['default','text','image','link','map','video','script'].forEach(function(typeName){
      var t = domc.getType(typeName);
      if(!t) return;
      var orig = t.model.prototype.defaults;
      var existingTb = (orig && orig.toolbar) || [];
      if(!existingTb.find) return;
      var nextToolbar = existingTb.slice();
      if(!existingTb.find(function(b){ return b.id==='sipet-color-edit'; })){
        nextToolbar.push(_editBtn);
      }
      if(typeName !== 'image' && typeName !== 'map' && typeName !== 'video' && typeName !== 'script' && !existingTb.find(function(b){ return b.id==='sipet-text-edit'; })){
        nextToolbar.push(_textBtn);
      }
      orig.toolbar = nextToolbar;
    });
    /* Also add on selection for any dynamic/custom type not covered above */
    _editor.on('component:selected', function(component){
      var toolbar = component.get('toolbar') || [];
      var nextToolbar = toolbar.slice();
      if(!toolbar.find(function(t){ return t.id==='sipet-color-edit'; })){
        nextToolbar.push(_editBtn);
      }
      if(_getEditableTextTarget(component) && !toolbar.find(function(t){ return t.id==='sipet-text-edit'; })){
        nextToolbar.push(_textBtn);
      }
      if(nextToolbar.length !== toolbar.length){
        component.set('toolbar', nextToolbar);
      }
    });
  })();
  _editor.on('component:deselected', function(){
    document.getElementById('wb-color-panel').classList.remove('open');
  });

  /* ── Fase 8: dirty-tracking ─────────────────────────────────── */
  _editor.on('component:update', function(){ _setDirty(true); });
  _editor.on('component:remove', function(){ _setDirty(true); });
  _editor.on('style:update',     function(){ _setDirty(true); });
  _editor.on('canvas:drop',      function(){ _setDirty(true); });

  apiPages().then(function(pages){
    _pages=pages;
    renderPageSelect(); renderPagesModal();
    if(_pages.length) loadPageIntoEditor(_pages[0].id);
    else window.createNewPage(false);
  });

  /* ── Mobile sidebar toggle ───────────────────────────────── */
  (function(){
    var toggleBtn  = document.getElementById('wb-sidebar-toggle');
    var sidebar    = document.getElementById('wb-sidebar');
    if (!toggleBtn || !sidebar) return;
    // start collapsed on mobile
    if (window.innerWidth <= 640) sidebar.classList.add('mob-hidden');
    toggleBtn.addEventListener('click', function(){
      sidebar.classList.toggle('mob-hidden');
      // let GrapesJS know the canvas size changed
      setTimeout(function(){
        window.dispatchEvent(new Event('resize'));
        if (_editor) _editor.refresh && _editor.refresh();
      }, 280);
    });
    // clicking the canvas area on mobile closes the sidebar
    document.getElementById('gjs').addEventListener('click', function(){
      if (window.innerWidth <= 640) sidebar.classList.add('mob-hidden');
    });
  })();

  })();
