(function () {
  'use strict';

  var SIDEBAR_CSS = [
    ':root{',
    '--sb-bg-1:#07122b;--sb-bg-2:#0a1736;--sb-bg-3:#0d1f47;',
    '--sb-surface:rgba(255,255,255,.05);--sb-surface-2:rgba(255,255,255,.08);',
    '--sb-border:rgba(255,255,255,.10);--sb-border-soft:rgba(255,255,255,.06);',
    '--sb-text:#f5f8ff;--sb-text-soft:rgba(233,239,255,.72);--sb-text-muted:rgba(213,223,246,.56);',
    '--sb-accent:#ff8c42;--sb-accent-2:#ffb347;--sb-accent-deep:#e06317;',
    '--sb-shadow:0 24px 60px rgba(5,12,30,.35),0 8px 24px rgba(8,16,40,.22);',
    '--sb-radius-xl:34px;--sb-radius-lg:26px;--sb-radius-md:24px;--sb-radius-sm:18px;',
    '--sb-transition:220ms cubic-bezier(.2,.8,.2,1);',
    '}',
    '*{box-sizing:border-box}',
    '.sidebar-dark{',
    'position:sticky;top:20px;',
    'width:280px;min-width:280px;',
    'min-height:calc(100vh - 84px);max-height:calc(100vh - 84px);',
    'padding:20px 16px 16px;',
    'border-radius:var(--sb-radius-xl);',
    'color:var(--sb-text);',
    'background:radial-gradient(circle at 18% 12%,rgba(255,140,50,.18),transparent 20%),',
    'radial-gradient(circle at 52% 54%,rgba(230,100,20,.10),transparent 28%),',
    'radial-gradient(circle at 80% 88%,rgba(255,140,50,.09),transparent 18%),',
    'linear-gradient(180deg,var(--sb-bg-1) 0%,var(--sb-bg-2) 42%,#0a1430 100%);',
    'border:1px solid rgba(255,255,255,.08);',
    'box-shadow:var(--sb-shadow);',
    'overflow:hidden;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);',
    'display:flex;flex-direction:column;',
    '}',
    '.sidebar-dark::before{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;',
    'background:linear-gradient(180deg,rgba(255,255,255,.09),rgba(255,255,255,0) 18%),',
    'linear-gradient(90deg,rgba(255,255,255,.04),transparent 12%,transparent 88%,rgba(255,255,255,.03));',
    'opacity:.9}',
    '.sidebar-dark::after{content:"";position:absolute;inset:1px;',
    'border-radius:calc(var(--sb-radius-xl) - 1px);pointer-events:none;',
    'border:1px solid rgba(255,255,255,.03)}',
    '.sidebar-dark .sb-header,.sidebar-dark .sb-divider,.sidebar-dark .sb-scroll,.sidebar-dark .sb-footer{position:relative;z-index:1}',
    '.sidebar-dark .sb-header{display:flex;align-items:center;gap:14px;padding:4px 4px 14px}',
    '.sidebar-dark .sb-toggle{width:30px;height:30px;border-radius:10px;',
    'border:1px solid rgba(255,255,255,.10);display:flex;align-items:center;justify-content:center;',
    'color:rgba(244,248,255,.72);background:rgba(255,255,255,.05);cursor:pointer;flex-shrink:0;margin-left:auto;',
    'transition:background var(--sb-transition),border-color var(--sb-transition),transform var(--sb-transition)}',
    '.sidebar-dark .sb-toggle:hover{background:rgba(255,255,255,.10);border-color:rgba(255,255,255,.16);color:var(--sb-text)}',
    '.sidebar-dark .sb-logo{width:60px;height:60px;border-radius:18px;display:flex;align-items:center;justify-content:center;',
    'background:linear-gradient(180deg,#ffb347 0%,#f06a1a 100%);',
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.30),0 8px 18px rgba(230,100,20,.30),0 0 0 1px rgba(255,255,255,.12);',
    'flex-shrink:0}',
    '.sidebar-dark .sb-logo i{font-size:26px;color:#fff;filter:drop-shadow(0 2px 8px rgba(0,0,0,.18))}',
    '.sidebar-dark .sb-title-wrap{min-width:0}',
    '.sidebar-dark .sb-title{margin:0;font-size:20px;line-height:1.1;font-weight:800;letter-spacing:-.03em;color:var(--sb-text)}',
    '.sidebar-dark .sb-subtitle{margin-top:4px;font-size:13px;line-height:1.35;color:var(--sb-text-soft);font-weight:500}',
    '.sidebar-dark .sb-divider{height:1px;margin:8px 6px 18px;',
    'background:linear-gradient(90deg,rgba(255,255,255,.06),rgba(255,180,100,.20),rgba(255,255,255,.06))}',
    '.sidebar-dark .sb-scroll{display:flex;flex-direction:column;gap:10px;overflow:auto;padding:2px 4px 8px;flex:1;',
    'scrollbar-width:thin;scrollbar-color:rgba(255,160,80,.25) transparent}',
    '.sidebar-dark .sb-scroll::-webkit-scrollbar{width:6px}',
    '.sidebar-dark .sb-scroll::-webkit-scrollbar-thumb{background:rgba(255,160,80,.22);border-radius:999px}',
    '.sidebar-dark .sb-scroll::-webkit-scrollbar-track{background:transparent}',
    '.sidebar-dark .sb-section{display:flex;flex-direction:column;gap:4px}',
    '.sidebar-dark .sb-section-label{display:flex;align-items:center;gap:10px;margin:2px 10px 4px;',
    'font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--sb-text-muted)}',
    '.sidebar-dark .sb-section-label::before{content:"";width:2px;height:16px;border-radius:999px;',
    'background:linear-gradient(180deg,var(--sb-accent-2),transparent);box-shadow:0 0 12px rgba(255,150,50,.35)}',
    '.sidebar-dark .sb-item{position:relative;display:flex;align-items:center;gap:10px;padding:9px 12px;',
    'border-radius:16px;text-decoration:none;color:var(--sb-text);',
    'transition:transform var(--sb-transition),background var(--sb-transition),border-color var(--sb-transition),box-shadow var(--sb-transition);',
    'border:1px solid transparent;overflow:hidden}',
    '.sidebar-dark .sb-item::before{content:"";position:absolute;inset:0;border-radius:inherit;',
    'background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,0));opacity:0;transition:opacity var(--sb-transition)}',
    '.sidebar-dark .sb-item:hover{transform:translateX(3px);background:rgba(255,255,255,.03);border-color:rgba(255,255,255,.06)}',
    '.sidebar-dark .sb-item:hover::before{opacity:1}',
    '.sidebar-dark .sb-item-icon{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;',
    'background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.03));',
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 4px 10px rgba(0,0,0,.14);',
    'flex-shrink:0;transition:transform var(--sb-transition),background var(--sb-transition),box-shadow var(--sb-transition);',
    'position:relative;z-index:1}',
    '.sidebar-dark .sb-item:hover .sb-item-icon{transform:translateY(-1px)}',
    '.sidebar-dark .sb-item-icon i{font-size:18px;color:rgba(240,245,255,.92)}',
    '.sidebar-dark .sb-item-body{min-width:0;display:flex;flex-direction:column;gap:2px;position:relative;z-index:1}',
    '.sidebar-dark .sb-item-title{font-size:14px;line-height:1.1;font-weight:700;letter-spacing:-.01em;color:var(--sb-text)}',
    '.sidebar-dark .sb-item-subtitle{font-size:12px;line-height:1.35;font-weight:500;color:var(--sb-text-soft);',
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.sidebar-dark .sb-item.is-active{',
    'background:linear-gradient(180deg,rgba(255,120,40,.28),rgba(180,70,15,.34));',
    'border-color:rgba(255,160,80,.34);',
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.10),0 14px 30px rgba(80,30,5,.28),0 0 0 1px rgba(255,150,50,.14);',
    'transform:none}',
    '.sidebar-dark .sb-item.is-active::before{opacity:1;background:linear-gradient(180deg,rgba(255,255,255,.12),rgba(255,255,255,0) 42%)}',
    '.sidebar-dark .sb-item.is-active::after{content:"";position:absolute;left:0;top:10px;bottom:10px;width:3px;border-radius:999px;',
    'background:linear-gradient(180deg,#ffd180 0%,#ff8c42 100%);',
    'box-shadow:0 0 16px rgba(255,150,50,.80),0 0 28px rgba(230,100,20,.40)}',
    '.sidebar-dark .sb-item.is-active .sb-item-icon{background:linear-gradient(180deg,#ffb347 0%,#f06a1a 100%);',
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.26),0 6px 14px rgba(230,100,20,.35),0 0 0 1px rgba(255,255,255,.12)}',
    '.sidebar-dark .sb-item.is-active .sb-item-icon i{color:#fff}',
    '.sidebar-dark .sb-item.is-active .sb-item-title{color:#fff}',
    '.sidebar-dark .sb-item.is-active .sb-item-subtitle{color:rgba(244,248,255,.82)}',
    '.sidebar-dark .sb-footer{margin-top:10px;padding:10px 4px 4px}',
    '.sidebar-dark .sb-footer-card{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:18px;',
    'background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.02));',
    'border:1px solid rgba(255,255,255,.07);',
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 10px 24px rgba(5,12,30,.18)}',
    '.sidebar-dark .sb-avatar{width:38px;height:38px;border-radius:50%;flex-shrink:0;',
    'border:2px solid rgba(255,255,255,.18);overflow:hidden;box-shadow:0 8px 18px rgba(0,0,0,.20);',
    'display:flex;align-items:center;justify-content:center;',
    'background:linear-gradient(180deg,#ffb347 0%,#f06a1a 100%);',
    'font-size:15px;font-weight:700;color:#fff}',
    '.sidebar-dark .sb-avatar img{width:100%;height:100%;object-fit:cover;display:block}',
    '.sidebar-dark .sb-user{min-width:0;flex:1}',
    '.sidebar-dark .sb-user-name{font-size:13px;line-height:1.15;font-weight:700;color:var(--sb-text);',
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.sidebar-dark .sb-user-meta{margin-top:2px;display:flex;align-items:center;gap:6px;font-size:12px;',
    'color:var(--sb-text-soft);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.sidebar-dark .sb-flag{font-size:16px;line-height:1}',
    '.sidebar-dark .sb-footer-actions{display:flex;align-items:center;gap:8px;margin-left:auto}',
    '.sidebar-dark .sb-action{width:30px;height:30px;border-radius:10px;border:1px solid transparent;',
    'display:flex;align-items:center;justify-content:center;color:rgba(244,248,255,.82);',
    'background:transparent;cursor:pointer;text-decoration:none;',
    'transition:background var(--sb-transition),border-color var(--sb-transition),transform var(--sb-transition)}',
    '.sidebar-dark .sb-action:hover{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.08);transform:translateY(-1px)}',
    '.sidebar-dark.is-collapsed{width:76px;min-width:76px;padding-left:10px;padding-right:10px}',
    '.sidebar-dark.is-collapsed .sb-title-wrap,.sidebar-dark.is-collapsed .sb-divider,',
    '.sidebar-dark.is-collapsed .sb-section-label span,.sidebar-dark.is-collapsed .sb-item-body,',
    '.sidebar-dark.is-collapsed .sb-user{display:none}',
    '.sidebar-dark.is-collapsed .sb-header{flex-direction:column;align-items:center;gap:8px;padding-bottom:10px}',
    '.sidebar-dark.is-collapsed .sb-toggle{margin-left:0}',
    '.sidebar-dark.is-collapsed .sb-footer-card,.sidebar-dark.is-collapsed .sb-item{justify-content:center}',
    '.sidebar-dark.is-collapsed .sb-logo{width:44px;height:44px;border-radius:14px}',
    '.sidebar-dark.is-collapsed .sb-item{padding:8px}',
    '.sidebar-dark.is-collapsed .sb-item-icon{width:38px;height:38px;border-radius:12px}',
    '.sidebar-dark.is-collapsed .sb-footer-actions{display:none}',
    '@media(max-width:480px){',
    '.sidebar-dark{max-width:100%;border-radius:20px}',
    '.sidebar-dark .sb-logo{width:44px;height:44px;border-radius:14px}',
    '.sidebar-dark .sb-logo i{font-size:20px}',
    '.sidebar-dark .sb-title{font-size:16px}',
    '.sidebar-dark .sb-subtitle{font-size:11px}',
    '.sidebar-dark .sb-item{padding:8px 10px;gap:8px}',
    '.sidebar-dark .sb-item-icon{width:34px;height:34px;border-radius:10px}',
    '.sidebar-dark .sb-item-icon i{font-size:15px}',
    '.sidebar-dark .sb-item-title{font-size:13px}',
    '.sidebar-dark .sb-item-subtitle{font-size:11px}',
    '}'
  ].join('');

  var STORAGE_KEY = 'multitienda_sb_collapsed';

  function injectStyles() {
    if (document.getElementById('__sb_core_css')) return;
    var style = document.createElement('style');
    style.id = '__sb_core_css';
    style.textContent = SIDEBAR_CSS;
    document.head.appendChild(style);
  }

  function applySidebarCollapsed(sidebar, btn, collapsed) {
    if (!sidebar) return;
    sidebar.classList.toggle('is-collapsed', !!collapsed);
    if (!btn) return;
    btn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    btn.innerHTML = collapsed
      ? '<i class="fa-solid fa-chevron-left" aria-hidden="true"></i>'
      : '<i class="fa-solid fa-chevron-right" aria-hidden="true"></i>';
  }

  function initSidebar() {
    var sidebar = document.querySelector('.sidebar-dark');
    if (!sidebar) return;
    var btn = sidebar.querySelector('[data-multitienda-sidebar-toggle]');
    var collapsed = false;
    try { collapsed = !!JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch (e) {}
    applySidebarCollapsed(sidebar, btn, collapsed);
    if (btn) {
      btn.addEventListener('click', function () {
        var next = !sidebar.classList.contains('is-collapsed');
        applySidebarCollapsed(sidebar, btn, next);
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch (e) {}
      });
    }
  }

  injectStyles();

  window.initBackendSidebarCore = function () {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initSidebar);
    } else {
      initSidebar();
    }
  };
})();
