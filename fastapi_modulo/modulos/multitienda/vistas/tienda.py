from __future__ import annotations


def tienda_html() -> str:
    return _HTML


_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tiendas</title>
  <style>
    :root {
      --sl-bg: var(--page-bg, #f5f1e8);
      --sl-surface: color-mix(in srgb, var(--content-bg, #fffdfa) 92%, transparent);
      --sl-card: var(--content-bg, #fffdfa);
      --sl-card-strong: var(--content-bg, #ffffff);
      --sl-border: color-mix(in srgb, var(--field-border, #c9b49a) 52%, transparent);
      --sl-text: var(--body-text, #271c12);
      --sl-muted: color-mix(in srgb, var(--body-text, #271c12) 62%, #ffffff 38%);
      --sl-accent: var(--button-bg, #b7791f);
      --sl-accent-deep: var(--field-focus, var(--button-bg, #8a5b14));
      --sl-accent-soft: color-mix(in srgb, var(--button-bg, #b7791f) 16%, var(--content-bg, #fffdfa) 84%);
      --sl-shadow: 0 24px 60px rgba(62, 39, 14, 0.10);
      --sl-radius-xl: 28px;
      --sl-radius-lg: 22px;
      --sl-radius-md: 16px;
      --sl-radius-sm: 12px;
      --sl-max: 1440px;
      --sl-button-text: var(--button-text, #ffffff);
      --sl-field-bg: var(--field-color, #ffffff);
      --sl-field-text: var(--field-text, var(--body-text, #271c12));
      --sl-field-border: var(--field-border, rgba(113, 84, 44, 0.14));
      --sl-field-focus: var(--field-focus, var(--button-bg, #b7791f));
    }

    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; min-height: 100%; }
    body {
      font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--sl-text);
      background:
        radial-gradient(circle at top left, color-mix(in srgb, var(--sl-accent) 18%, transparent) 0%, transparent 28%),
        radial-gradient(circle at 85% 10%, color-mix(in srgb, var(--sl-accent-deep) 14%, transparent) 0%, transparent 22%),
        linear-gradient(
          180deg,
          color-mix(in srgb, var(--sl-bg) 84%, #eadfcb 16%) 0%,
          color-mix(in srgb, var(--sl-bg) 92%, #f7f2e8 8%) 36%,
          color-mix(in srgb, var(--sl-bg) 96%, #ffffff 4%) 100%
        );
    }

    .sl-page {
      width: min(calc(100% - 32px), var(--sl-max));
      margin: 22px auto 40px;
    }

    .sl-hero {
      position: relative;
      overflow: hidden;
      border-radius: 34px;
      padding: 34px;
      min-height: 280px;
      background:
        linear-gradient(135deg, rgba(31, 41, 55, 0.08), transparent 42%),
        linear-gradient(120deg, rgba(82, 52, 23, 0.92), rgba(140, 95, 26, 0.93) 52%, rgba(39, 28, 18, 0.96));
      box-shadow: var(--sl-shadow);
      color: #fff8f0;
      isolation: isolate;
    }

    .sl-hero::before,
    .sl-hero::after {
      content: "";
      position: absolute;
      border-radius: 999px;
      pointer-events: none;
      opacity: 0.45;
      z-index: 0;
    }

    .sl-hero::before {
      inset: auto auto -110px -80px;
      width: 320px;
      height: 320px;
      background: radial-gradient(circle, rgba(255, 227, 180, 0.70), transparent 70%);
    }

    .sl-hero::after {
      inset: -100px -80px auto auto;
      width: 300px;
      height: 300px;
      background: radial-gradient(circle, rgba(255, 255, 255, 0.26), transparent 68%);
    }

    .sl-hero-grid {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.95fr);
      gap: 28px;
      align-items: end;
    }

    .sl-hero-copy {
      display: flex;
      flex-direction: column;
      gap: 18px;
      max-width: 760px;
    }

    .sl-kicker {
      display: inline-flex;
      width: fit-content;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255, 248, 240, 0.16);
      border: 1px solid rgba(255, 244, 230, 0.24);
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      backdrop-filter: blur(12px);
    }

    .sl-kicker-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #f7d08b;
      box-shadow: 0 0 0 6px rgba(247, 208, 139, 0.12);
    }

    .sl-hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 4.15rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }

    .sl-hero p {
      margin: 0;
      max-width: 680px;
      color: rgba(255, 249, 240, 0.84);
      font-size: 1rem;
      line-height: 1.7;
    }

    .sl-widget-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }

    .sl-widget {
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding: 16px 18px;
      border-radius: 20px;
      background: rgba(255, 248, 240, 0.12);
      border: 1px solid rgba(255, 241, 221, 0.18);
      backdrop-filter: blur(16px);
    }

    .sl-widget-label {
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: rgba(255, 245, 230, 0.68);
    }

    .sl-widget-value {
      font-size: 1.7rem;
      font-weight: 700;
      letter-spacing: -0.04em;
      color: #fffaf3;
    }

    .sl-widget-note {
      font-size: 0.85rem;
      color: rgba(255, 244, 229, 0.72);
    }

    .sl-hero-card {
      justify-self: end;
      width: min(100%, 380px);
      padding: 22px;
      border-radius: 28px;
      background: rgba(255, 250, 243, 0.14);
      border: 1px solid rgba(255, 245, 230, 0.18);
      backdrop-filter: blur(18px);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .sl-store-line {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
    }

    .sl-store-logo {
      width: 72px;
      height: 72px;
      border-radius: 24px;
      object-fit: cover;
      background: #fff;
      border: 1px solid rgba(255, 250, 240, 0.24);
      box-shadow: 0 12px 30px rgba(34, 23, 13, 0.18);
    }

    .sl-store-title {
      margin: 0;
      font-size: 1.2rem;
      font-weight: 700;
      line-height: 1.2;
    }

    .sl-store-subtitle {
      margin: 4px 0 0;
      color: rgba(255, 244, 229, 0.72);
      font-size: 0.92rem;
      line-height: 1.5;
    }

    .sl-store-meta {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }

    .sl-store-meta-card {
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 250, 243, 0.10);
      border: 1px solid rgba(255, 244, 229, 0.12);
    }

    .sl-store-meta-card strong {
      display: block;
      font-size: 1rem;
      margin-bottom: 4px;
      color: #fff8f0;
    }

    .sl-store-meta-card span {
      font-size: 0.86rem;
      color: rgba(255, 244, 229, 0.72);
    }

    .sl-store-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .sl-btn,
    .sl-btn-ghost {
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
    }

    .sl-btn {
      background: var(--button-bg, var(--sl-accent));
      color: var(--sl-button-text);
      box-shadow: 0 16px 30px rgba(33, 20, 10, 0.18);
    }

    .sl-btn-ghost {
      background: transparent;
      color: var(--sl-button-text);
      border: 1px solid color-mix(in srgb, var(--sl-button-text) 22%, transparent);
    }

    .sl-btn:hover,
    .sl-btn-ghost:hover {
      transform: translateY(-1px);
    }

    .sl-toolbar {
      margin-top: 22px;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      justify-content: space-between;
      padding: 18px 22px;
      border-radius: 26px;
      background: var(--sl-surface);
      border: 1px solid rgba(255, 255, 255, 0.7);
      box-shadow: 0 18px 40px rgba(50, 33, 15, 0.08);
      backdrop-filter: blur(12px);
    }

    .sl-featured {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }

    .sl-featured-label {
      font-size: 0.84rem;
      font-weight: 700;
      color: var(--sl-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .sl-chip {
      border: 1px solid transparent;
      background: color-mix(in srgb, var(--sl-accent) 12%, var(--sl-card) 88%);
      color: var(--sl-accent-deep);
      padding: 11px 16px;
      border-radius: 999px;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s ease;
    }

    .sl-chip:hover {
      background: color-mix(in srgb, var(--sl-accent) 20%, var(--sl-card) 80%);
    }

    .sl-chip.active {
      background: linear-gradient(135deg, var(--sl-accent), var(--sl-accent-deep));
      color: var(--sl-button-text);
      box-shadow: 0 14px 28px rgba(167, 107, 22, 0.22);
    }

    .sl-content {
      display: grid;
      grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
      gap: 24px;
      margin-top: 24px;
      align-items: start;
    }

    .sl-sidebar {
      position: sticky;
      top: 16px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .sl-filter-card,
    .sl-products-shell {
      background: rgba(255, 252, 247, 0.88);
      border: 1px solid rgba(255, 255, 255, 0.78);
      box-shadow: 0 24px 55px rgba(58, 38, 15, 0.09);
      backdrop-filter: blur(14px);
    }

    .sl-filter-card {
      border-radius: 26px;
      padding: 20px;
    }

    .sl-filter-heading {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }

    .sl-filter-heading h2 {
      margin: 0;
      font-size: 1.12rem;
      letter-spacing: -0.02em;
    }

    .sl-filter-sub {
      margin: 6px 0 0;
      color: var(--sl-muted);
      font-size: 0.9rem;
      line-height: 1.5;
    }

    .sl-clear-btn {
      border: none;
      background: transparent;
      color: var(--sl-accent-deep);
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      padding: 0;
    }

    .sl-accordion {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .sl-acc-item {
      border-radius: 18px;
      background: var(--sl-card-strong);
      border: 1px solid var(--sl-border);
      overflow: hidden;
    }

    .sl-acc-toggle {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border: none;
      background: transparent;
      padding: 16px 18px;
      cursor: pointer;
      text-align: left;
    }

    .sl-acc-title {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .sl-acc-title strong {
      font-size: 0.98rem;
      letter-spacing: -0.02em;
    }

    .sl-acc-title span {
      color: var(--sl-muted);
      font-size: 0.84rem;
    }

    .sl-acc-icon {
      color: var(--sl-accent-deep);
      font-size: 1.1rem;
      transition: transform 0.2s ease;
    }

    .sl-acc-item[data-open="false"] .sl-acc-icon {
      transform: rotate(-90deg);
    }

    .sl-acc-body {
      padding: 0 18px 18px;
    }

    .sl-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .sl-list button,
    .sl-list a {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 12px 14px;
      border: 1px solid transparent;
      background: color-mix(in srgb, var(--sl-accent) 7%, var(--sl-card) 93%);
      color: var(--sl-field-text);
      border-radius: 14px;
      text-decoration: none;
      cursor: pointer;
      font-size: 0.92rem;
      font-weight: 600;
      transition: all 0.18s ease;
    }

    .sl-list button:hover,
    .sl-list a:hover {
      background: color-mix(in srgb, var(--sl-accent) 14%, var(--sl-card) 86%);
      border-color: color-mix(in srgb, var(--sl-accent) 22%, transparent);
    }

    .sl-list button.active {
      background: linear-gradient(135deg, color-mix(in srgb, var(--sl-accent) 10%, var(--sl-card) 90%), color-mix(in srgb, var(--sl-accent) 24%, var(--sl-card) 76%));
      border-color: color-mix(in srgb, var(--sl-accent) 28%, transparent);
      color: var(--sl-accent-deep);
      box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--sl-accent) 10%, transparent);
    }

    .sl-list-count {
      min-width: 30px;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.68);
      text-align: center;
      color: #8a5b14;
      font-size: 0.8rem;
      font-weight: 700;
    }

    .sl-products-shell {
      border-radius: 30px;
      padding: 20px;
    }

    .sl-products-topbar {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 14px;
      align-items: center;
      padding: 14px;
      border-radius: 22px;
      background: linear-gradient(180deg, color-mix(in srgb, var(--sl-accent) 8%, var(--sl-card) 92%), color-mix(in srgb, var(--sl-card) 96%, #ffffff 4%));
      border: 1px solid color-mix(in srgb, var(--sl-field-border) 52%, transparent);
    }

    .sl-view-switch {
      display: inline-flex;
      gap: 8px;
      padding: 8px;
      border-radius: 18px;
      background: var(--sl-field-bg);
      border: 1px solid var(--sl-field-border);
    }

    .sl-view-btn {
      border: none;
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: transparent;
      color: var(--sl-muted);
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.18s ease;
    }

    .sl-view-btn.active {
      background: linear-gradient(135deg, var(--sl-accent), var(--sl-accent-deep));
      color: var(--sl-button-text);
      box-shadow: 0 10px 22px rgba(167, 107, 22, 0.22);
    }

    .sl-search-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
      padding: 0 16px;
      height: 58px;
      background: var(--sl-field-bg);
      border-radius: 18px;
      border: 1px solid var(--sl-field-border);
    }

    .sl-search-icon {
      color: var(--sl-accent-deep);
      font-size: 1rem;
      flex-shrink: 0;
    }

    .sl-search-input {
      width: 100%;
      border: none;
      background: transparent;
      outline: none;
      font-size: 1rem;
      color: var(--sl-field-text);
    }

    .sl-search-input::placeholder {
      color: color-mix(in srgb, var(--sl-field-text) 46%, #ffffff 54%);
    }

    .sl-results-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      justify-content: flex-end;
      color: var(--sl-muted);
      font-size: 0.92rem;
      white-space: nowrap;
    }

    .sl-sort-select {
      height: 50px;
      min-width: 220px;
      padding: 0 18px;
      border-radius: 999px;
      border: 1px solid var(--sl-field-border);
      background: var(--sl-field-bg);
      color: var(--sl-field-text);
      font-size: 0.95rem;
      outline: none;
    }

    .sl-sort-select:focus,
    .sl-search-wrap:focus-within,
    .sl-list button:focus-visible,
    .sl-list a:focus-visible,
    .sl-btn:focus-visible,
    .sl-btn-ghost:focus-visible,
    .sl-card-cta:focus-visible {
      outline: 0;
      border-color: var(--sl-field-focus);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--sl-field-focus) 16%, transparent);
    }

    .sl-products-summary {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin: 18px 2px 0;
      color: var(--sl-muted);
    }

    .sl-products-summary strong {
      color: var(--sl-text);
      font-size: 1.1rem;
      letter-spacing: -0.03em;
    }

    .sl-active-filters {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .sl-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--sl-accent) 14%, var(--sl-card) 86%);
      color: var(--sl-accent-deep);
      font-size: 0.84rem;
      font-weight: 700;
    }

    .sl-pill button {
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      padding: 0;
      font-size: 0.92rem;
      line-height: 1;
    }

    .sl-products-grid {
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }

    .sl-products-list {
      margin-top: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .sl-card {
      position: relative;
      overflow: hidden;
      border-radius: 24px;
      background: var(--sl-card);
      border: 1px solid rgba(113, 84, 44, 0.12);
      box-shadow: 0 18px 40px rgba(58, 38, 15, 0.08);
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .sl-card:hover,
    .sl-card-list:hover {
      transform: translateY(-4px);
      box-shadow: 0 26px 48px rgba(58, 38, 15, 0.12);
      border-color: rgba(183, 121, 31, 0.2);
    }

    .sl-card-media {
      position: relative;
      aspect-ratio: 1 / 1;
      overflow: hidden;
      background:
        radial-gradient(circle at top right, rgba(243, 212, 159, 0.34), transparent 30%),
        linear-gradient(180deg, #f9f3e6 0%, #f4ead9 100%);
    }

    .sl-card-img,
    .sl-card-img-placeholder {
      width: 100%;
      height: 100%;
      display: block;
    }

    .sl-card-img {
      object-fit: cover;
      transition: transform 0.3s ease;
    }

    .sl-card:hover .sl-card-img,
    .sl-card-list:hover .sl-card-img {
      transform: scale(1.04);
    }

    .sl-card-img-placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #c5913a;
      font-size: 3rem;
    }

    .sl-card-badges {
      position: absolute;
      inset: 14px 14px auto;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      pointer-events: none;
    }

    .sl-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255, 252, 247, 0.88);
      color: #714f20;
      font-size: 0.78rem;
      font-weight: 700;
      border: 1px solid rgba(183, 121, 31, 0.12);
      backdrop-filter: blur(10px);
    }

    .sl-card-body {
      padding: 18px;
    }

    .sl-card-store {
      color: var(--accent, var(--sl-accent));
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
      margin-bottom: 8px;
    }

    .sl-card-name {
      margin: 0 0 8px;
      font-size: 1.12rem;
      line-height: 1.25;
      letter-spacing: -0.03em;
    }

    .sl-card-desc {
      margin: 0;
      color: var(--sl-muted);
      line-height: 1.65;
      font-size: 0.92rem;
      min-height: 48px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .sl-card-footer {
      margin-top: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .sl-card-price {
      font-size: 1.45rem;
      font-weight: 800;
      letter-spacing: -0.04em;
      color: var(--sl-accent-deep);
    }

    .sl-card-price small {
      display: block;
      margin-top: 4px;
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--sl-muted);
      letter-spacing: 0;
    }

    .sl-card-cta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: none;
      border-radius: 999px;
      padding: 11px 14px;
      background: var(--button-bg, #2f2215);
      color: var(--sl-button-text);
      cursor: pointer;
      font-size: 0.88rem;
      font-weight: 700;
    }

    .sl-card-list {
      display: grid;
      grid-template-columns: 220px minmax(0, 1fr);
      gap: 0;
      overflow: hidden;
      border-radius: 24px;
      background: var(--sl-card);
      border: 1px solid rgba(113, 84, 44, 0.12);
      box-shadow: 0 18px 40px rgba(58, 38, 15, 0.08);
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .sl-card-list .sl-card-media {
      min-height: 100%;
      aspect-ratio: auto;
    }

    .sl-card-list .sl-card-body {
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 22px;
    }

    .sl-card-list .sl-card-desc {
      min-height: 0;
      -webkit-line-clamp: 3;
    }

    .sl-empty {
      margin-top: 20px;
      padding: 48px 24px;
      border-radius: 24px;
      text-align: center;
      background: linear-gradient(180deg, color-mix(in srgb, var(--sl-accent) 7%, var(--sl-card) 93%), color-mix(in srgb, var(--sl-accent) 13%, var(--sl-card) 87%));
      border: 1px dashed color-mix(in srgb, var(--sl-accent) 30%, transparent);
      color: var(--sl-muted);
    }

    .sl-empty strong {
      display: block;
      color: var(--sl-text);
      font-size: 1.05rem;
      margin-bottom: 8px;
    }

    .sl-empty-icon {
      font-size: 2.6rem;
      margin-bottom: 14px;
      color: var(--sl-accent);
    }

    @media (max-width: 1180px) {
      .sl-hero-grid,
      .sl-content {
        grid-template-columns: 1fr;
      }

      .sl-hero-card {
        justify-self: stretch;
        width: 100%;
      }

      .sl-sidebar {
        position: static;
      }

      .sl-products-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 820px) {
      .sl-page {
        width: min(calc(100% - 20px), var(--sl-max));
        margin-top: 10px;
      }

      .sl-hero {
        padding: 24px;
        border-radius: 26px;
      }

      .sl-widget-row,
      .sl-store-meta,
      .sl-products-topbar {
        grid-template-columns: 1fr;
      }

      .sl-toolbar,
      .sl-products-shell,
      .sl-filter-card {
        border-radius: 22px;
      }

      .sl-products-grid {
        grid-template-columns: 1fr;
      }

      .sl-card-list {
        grid-template-columns: 1fr;
      }

      .sl-card-list .sl-card-media {
        aspect-ratio: 4 / 3;
      }
    }

    @media (max-width: 560px) {
      .sl-page {
        width: min(calc(100% - 16px), var(--sl-max));
      }

      .sl-hero,
      .sl-products-shell,
      .sl-filter-card,
      .sl-toolbar {
        padding-left: 16px;
        padding-right: 16px;
      }

      .sl-products-topbar {
        padding: 10px;
      }

      .sl-search-wrap {
        height: 54px;
      }
    }
  </style>
</head>
<body>
  <div class="sl-page">
    <section class="sl-hero">
      <div class="sl-hero-grid">
        <div class="sl-hero-copy">
          <span class="sl-kicker">
            <span class="sl-kicker-dot"></span>
            Calidad y precio a tu alcance
          </span>
          <div>
            <h1 id="sl-page-title">Las mejores tiendas</h1>
            <p id="sl-page-copy">
              A un clic de distancia
            </p>
          </div>
          <div class="sl-widget-row">
            <article class="sl-widget">
              <span class="sl-widget-label">Productos</span>
              <strong class="sl-widget-value" id="sl-stat-products">0</strong>
              <span class="sl-widget-note"></span>
            </article>
            <article class="sl-widget">
              <span class="sl-widget-label">Categorías</span>
              <strong class="sl-widget-value" id="sl-stat-categories">0</strong>
              <span class="sl-widget-note"></span>
            </article>
            <article class="sl-widget">
              <span class="sl-widget-label">Tiendas</span>
              <strong class="sl-widget-value" id="sl-stat-stores">1</strong>
              <span class="sl-widget-note"></span>
            </article>
          </div>
        </div>

        <aside class="sl-hero-card">
          <div class="sl-store-line">
            <img id="sl-store-logo" class="sl-store-logo" src="/static/imagenes/logo_vale.png" alt="Logo de tienda" />
            <div>
              <h2 class="sl-store-title" id="sl-store-name">Calidad y precio a tu alcance</h2>
              <p class="sl-store-subtitle" id="sl-store-copy"></p>
            </div>
          </div>

          <div class="sl-store-meta">
            <div class="sl-store-meta-card">
              <strong id="sl-store-email">Ofertas</strong>
              <span></span>
            </div>
            <div class="sl-store-meta-card">
              <strong id="sl-store-phone">Cliente destacado</strong>
              <span></span>
            </div>
          </div>

          <div class="sl-store-actions">
            <button class="sl-btn" id="sl-contact-btn" type="button">Contactar tienda</button>
            <button class="sl-btn-ghost" id="sl-view-store-btn" type="button">Ver perfil</button>
          </div>
        </aside>
      </div>
    </section>

    <section class="sl-toolbar">
      <div class="sl-featured">
        <span class="sl-featured-label">Categorias destacadas</span>
        <div id="sl-featured-categories"></div>
      </div>
    </section>

    <section class="sl-content">
      <aside class="sl-sidebar">
        <div class="sl-filter-card">
          <div class="sl-filter-heading">
            <div>
              <h2>Buscar</h2>
            </div>
            <button class="sl-clear-btn" id="sl-clear-filters" type="button">Borrar filtros</button>
          </div>

          <div class="sl-accordion">
            <section class="sl-acc-item" data-open="true">
              <button class="sl-acc-toggle" type="button" data-target="stores">
                <span class="sl-acc-title">
                  <strong>Tiendas</strong>
                  <span>Directorio visible en landing</span>
                </span>
                <span class="sl-acc-icon">⌄</span>
              </button>
              <div class="sl-acc-body" id="sl-acc-stores">
                <ul class="sl-list" id="sl-store-list"></ul>
              </div>
            </section>

            <section class="sl-acc-item" data-open="true">
              <button class="sl-acc-toggle" type="button" data-target="categories">
                <span class="sl-acc-title">
                  <strong>Categorias</strong>
                  <span>Explora por familia de producto</span>
                </span>
                <span class="sl-acc-icon">⌄</span>
              </button>
              <div class="sl-acc-body" id="sl-acc-categories">
                <ul class="sl-list" id="sl-category-list"></ul>
              </div>
            </section>

            <section class="sl-acc-item" data-open="true">
              <button class="sl-acc-toggle" type="button" data-target="offers">
                <span class="sl-acc-title">
                  <strong>Ofertas</strong>
                  <span>Atajos para promos y destacados</span>
                </span>
                <span class="sl-acc-icon">⌄</span>
              </button>
              <div class="sl-acc-body" id="sl-acc-offers">
                <ul class="sl-list" id="sl-offer-list"></ul>
              </div>
            </section>
          </div>
        </div>
      </aside>

      <main class="sl-products-shell">
        <div class="sl-products-topbar">
          <div class="sl-view-switch" aria-label="Cambiar vista">
            <button class="sl-view-btn active" id="sl-view-grid" type="button" title="Vista grid">▦</button>
            <button class="sl-view-btn" id="sl-view-list" type="button" title="Vista lista">☰</button>
          </div>

          <label class="sl-search-wrap" for="sl-search-input">
            <span class="sl-search-icon">⌕</span>
            <input id="sl-search-input" class="sl-search-input" type="search" placeholder="Buscar producto, descripcion o categoria" />
          </label>

          <div class="sl-results-meta">
            <span id="sl-results-count">0 resultados</span>
            <select id="sl-sort-select" class="sl-sort-select" aria-label="Ordenar productos">
              <option value="featured">Destacado</option>
              <option value="price-asc">Precio: menor a mayor</option>
              <option value="price-desc">Precio: mayor a menor</option>
              <option value="name-asc">Nombre A-Z</option>
            </select>
          </div>
        </div>

        <div class="sl-products-summary">
          <strong id="sl-summary-title">Todos los productos</strong>
          <div class="sl-active-filters" id="sl-active-filters"></div>
        </div>

        <div id="sl-products-container" class="sl-products-grid"></div>
      </main>
    </section>
  </div>

  <script>
  (function () {
    var DEFAULT_LOGO = "/static/imagenes/logo_vale.png";
    var DEFAULT_BANNER = "/static/imagenes/banner.png";
    var allProducts = [];
    var allCategories = [];
    var allStores = [];
    var featuredCategories = [];
    var selectedCategory = "";
    var selectedStore = "";
    var selectedOffer = "all";
    var searchQ = "";
    var viewMode = "grid";
    var sortMode = "featured";

    function safeParse(raw, fallback) {
      try { return JSON.parse(raw || ""); } catch (error) { return fallback; }
    }

    function escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function normalizeText(value) {
      return String(value || "").trim();
    }

    function normalizeCategoryName(category) {
      if (!category) return "";
      if (typeof category === "string") return normalizeText(category);
      return normalizeText(category.nombre || category.name || category.label || "");
    }

    function deriveStoreName(product) {
      var candidates = [
        product.tienda,
        product.store,
        product.storeName,
        product.vendor,
        product.vendor_name,
        product.marca,
      ];
      for (var i = 0; i < candidates.length; i += 1) {
        var value = normalizeText(candidates[i]);
        if (value) return value;
      }
      return normalizeText(localStorage.getItem("multitienda_store_name")) || "Calidad y precio a tu alcance";
    }

    function isProductPublished(product) {
      return !!(product && (product.publicado || product.ecomPublicado));
    }

    function getProductCategory(product) {
      var direct = normalizeCategoryName(product.categoria);
      if (direct) return direct;
      var ecommerce = normalizeText(product.ecomCategorias);
      if (ecommerce) return ecommerce.split(",")[0].trim();
      return "";
    }

    function hasOffer(product) {
      return !!(product.nuevo || /oferta|promo|descuento/i.test(normalizeText(product.etiquetas)));
    }

    function hasImage(product) {
      return !!(product.imagen && !String(product.imagen).includes("undefined"));
    }

    function getDisplayProducts() {
      var filtered = allProducts.filter(function (product) {
        if (!isProductPublished(product)) return false;
        var productCategory = getProductCategory(product);
        var productStore = deriveStoreName(product);
        var haystack = [
          product.nombre,
          product.descCorta,
          product.descLarga,
          productCategory,
          productStore,
          product.etiquetas,
        ].join(" ").toLowerCase();

        if (selectedCategory && productCategory !== selectedCategory) return false;
        if (selectedStore && productStore !== selectedStore) return false;
        if (selectedOffer === "offers" && !hasOffer(product)) return false;
        if (selectedOffer === "new" && !product.nuevo) return false;
        if (selectedOffer === "ready" && !hasImage(product)) return false;
        if (searchQ && haystack.indexOf(searchQ.toLowerCase()) === -1) return false;
        return true;
      });

      filtered.sort(function (a, b) {
        if (sortMode === "price-asc") return getNumericPrice(a) - getNumericPrice(b);
        if (sortMode === "price-desc") return getNumericPrice(b) - getNumericPrice(a);
        if (sortMode === "name-asc") return normalizeText(a.nombre).localeCompare(normalizeText(b.nombre), "es");
        var scoreA = (a.nuevo ? 2 : 0) + (hasImage(a) ? 1 : 0);
        var scoreB = (b.nuevo ? 2 : 0) + (hasImage(b) ? 1 : 0);
        return scoreB - scoreA;
      });

      return filtered;
    }

    function getNumericPrice(product) {
      var price = parseFloat(product && product.precio);
      return isNaN(price) ? 0 : price;
    }

    function formatPrice(value) {
      if (value === "" || value === null || value === undefined) return "Consultar";
      var numeric = parseFloat(value);
      if (isNaN(numeric)) return "Consultar";
      return "$" + numeric.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function buildDerivedCategories() {
      var map = {};
      allCategories.forEach(function (category) {
        var name = normalizeCategoryName(category);
        if (!name || map[name]) return;
        map[name] = { name: name, count: 0 };
      });
      allProducts.forEach(function (product) {
        if (!isProductPublished(product)) return;
        var name = getProductCategory(product);
        if (!name) return;
        if (!map[name]) map[name] = { name: name, count: 0 };
        map[name].count += 1;
      });
      return Object.keys(map).map(function (key) { return map[key]; }).sort(function (a, b) {
        return b.count - a.count || a.name.localeCompare(b.name, "es");
      });
    }

    function buildDerivedStores() {
      var storeMap = {};
      allProducts.forEach(function (product) {
        if (!isProductPublished(product)) return;
        var name = deriveStoreName(product);
        if (!name) return;
        if (!storeMap[name]) {
          storeMap[name] = {
            name: name,
            count: 0,
            featured: false,
            description: "",
            logo: DEFAULT_LOGO,
            phone: "",
            email: "",
          };
        }
        storeMap[name].count += 1;
      });

      allStores.forEach(function (store) {
        var name = normalizeText(store.store_name);
        if (!name) return;
        if (!storeMap[name]) {
          storeMap[name] = {
            name: name,
            count: 0,
            featured: !!store.is_featured,
            description: normalizeText(store.description),
            logo: store.logo || DEFAULT_LOGO,
            phone: normalizeText(store.phone),
            email: "",
          };
        } else {
          storeMap[name].featured = storeMap[name].featured || !!store.is_featured;
          storeMap[name].description = storeMap[name].description || normalizeText(store.description);
          storeMap[name].logo = storeMap[name].logo === DEFAULT_LOGO && store.logo ? store.logo : storeMap[name].logo;
          storeMap[name].phone = storeMap[name].phone || normalizeText(store.phone);
        }
      });

      return Object.keys(storeMap).map(function (key) { return storeMap[key]; }).sort(function (a, b) {
        return (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || b.count - a.count || a.name.localeCompare(b.name, "es");
      });
    }

    function updateHero() {
      var sidebarSettings = safeParse(localStorage.getItem("backend_template_sidebar_settings"), {});
      var storeName = normalizeText(localStorage.getItem("multitienda_store_name")) || "Calidad y precio a tu alcance";
      var storeEmail = normalizeText(localStorage.getItem("multitienda_store_email")) || "contacto@tunegocio.com";
      var storePhone = normalizeText(localStorage.getItem("multitienda_store_phone")) || "Sin telefono";
      var storeLogo = normalizeText(sidebarSettings.logo) || DEFAULT_LOGO;
      var storeDesc = "";
      var heroTitle = selectedCategory ? "Coleccion de " + selectedCategory : "Las mejores tiendas";
      var heroCopy = selectedCategory
        ? "Filtra productos publicados dentro de " + selectedCategory + " y descubre articulos listos para destacar en el marketplace."
        : "Explora productos destacados, cambia entre categorias y encuentra articulos rapidamente desde una experiencia limpia, editorial y enfocada en conversion.";

      document.getElementById("sl-page-title").textContent = heroTitle;
      document.getElementById("sl-page-copy").textContent = heroCopy;
      document.getElementById("sl-store-name").textContent = storeName;
      document.getElementById("sl-store-email").textContent = storeEmail;
      document.getElementById("sl-store-phone").textContent = storePhone;
      document.getElementById("sl-store-logo").src = storeLogo;
      document.getElementById("sl-store-copy").textContent = storeDesc;
    }

    function renderFeaturedCategories() {
      var container = document.getElementById("sl-featured-categories");
      container.innerHTML = "";
      featuredCategories = buildDerivedCategories().slice(0, 5).map(function (category) { return category.name; });

      var allButton = document.createElement("button");
      allButton.type = "button";
      allButton.className = "sl-chip" + (selectedCategory === "" ? " active" : "");
      allButton.textContent = "Todo";
      allButton.addEventListener("click", function () {
        selectedCategory = "";
        renderAll();
      });
      container.appendChild(allButton);

      featuredCategories.forEach(function (name) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "sl-chip" + (selectedCategory === name ? " active" : "");
        button.textContent = name;
        button.addEventListener("click", function () {
          selectedCategory = name;
          renderAll();
        });
        container.appendChild(button);
      });
    }

    function renderStoreList() {
      var list = document.getElementById("sl-store-list");
      var stores = buildDerivedStores();
      list.innerHTML = "";

      var allItem = document.createElement("li");
      var allButton = document.createElement("button");
      allButton.type = "button";
      allButton.className = selectedStore === "" ? "active" : "";
      allButton.innerHTML = '<span>Todas las tiendas</span><span class="sl-list-count">' + stores.length + '</span>';
      allButton.addEventListener("click", function () {
        selectedStore = "";
        renderAll();
      });
      allItem.appendChild(allButton);
      list.appendChild(allItem);

      stores.forEach(function (store) {
        var item = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.className = selectedStore === store.name ? "active" : "";
        button.innerHTML = '<span>' + escapeHtml(store.name) + '</span><span class="sl-list-count">' + store.count + '</span>';
        button.addEventListener("click", function () {
          selectedStore = store.name;
          renderAll();
        });
        item.appendChild(button);
        list.appendChild(item);
      });

      document.getElementById("sl-stat-stores").textContent = String(stores.length || 1);
    }

    function renderCategoryList() {
      var list = document.getElementById("sl-category-list");
      var categories = buildDerivedCategories();
      list.innerHTML = "";

      var allItem = document.createElement("li");
      var allButton = document.createElement("button");
      allButton.type = "button";
      allButton.className = selectedCategory === "" ? "active" : "";
      allButton.innerHTML = '<span>Todas</span><span class="sl-list-count">' + categories.length + '</span>';
      allButton.addEventListener("click", function () {
        selectedCategory = "";
        renderAll();
      });
      allItem.appendChild(allButton);
      list.appendChild(allItem);

      categories.forEach(function (category) {
        var item = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.className = selectedCategory === category.name ? "active" : "";
        button.innerHTML = '<span>' + escapeHtml(category.name) + '</span><span class="sl-list-count">' + category.count + '</span>';
        button.addEventListener("click", function () {
          selectedCategory = category.name;
          renderAll();
        });
        item.appendChild(button);
        list.appendChild(item);
      });

      document.getElementById("sl-stat-categories").textContent = String(categories.length);
    }

    function renderOfferList() {
      var list = document.getElementById("sl-offer-list");
      var items = [
        { key: "all", label: "Todo el catalogo", count: allProducts.filter(isProductPublished).length },
        { key: "offers", label: "Ofertas", count: allProducts.filter(function (product) { return isProductPublished(product) && hasOffer(product); }).length },
        { key: "new", label: "Nuevos", count: allProducts.filter(function (product) { return isProductPublished(product) && product.nuevo; }).length },
        { key: "ready", label: "Con imagen", count: allProducts.filter(function (product) { return isProductPublished(product) && hasImage(product); }).length },
      ];

      list.innerHTML = "";
      items.forEach(function (offer) {
        var item = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.className = selectedOffer === offer.key ? "active" : "";
        button.innerHTML = '<span>' + escapeHtml(offer.label) + '</span><span class="sl-list-count">' + offer.count + '</span>';
        button.addEventListener("click", function () {
          selectedOffer = offer.key;
          renderAll();
        });
        item.appendChild(button);
        list.appendChild(item);
      });
    }

    function renderActiveFilters() {
      var container = document.getElementById("sl-active-filters");
      container.innerHTML = "";
      var filters = [];
      if (selectedStore) filters.push({ key: "store", label: selectedStore });
      if (selectedCategory) filters.push({ key: "category", label: selectedCategory });
      if (selectedOffer !== "all") {
        var offerLabel = selectedOffer === "offers" ? "Ofertas" : (selectedOffer === "new" ? "Nuevos" : "Con imagen");
        filters.push({ key: "offer", label: offerLabel });
      }
      if (searchQ) filters.push({ key: "search", label: 'Busqueda: "' + searchQ + '"' });

      filters.forEach(function (filter) {
        var pill = document.createElement("span");
        pill.className = "sl-pill";
        pill.innerHTML = '<span>' + escapeHtml(filter.label) + '</span><button type="button" aria-label="Quitar filtro">x</button>';
        pill.querySelector("button").addEventListener("click", function () {
          if (filter.key === "store") selectedStore = "";
          if (filter.key === "category") selectedCategory = "";
          if (filter.key === "offer") selectedOffer = "all";
          if (filter.key === "search") {
            searchQ = "";
            document.getElementById("sl-search-input").value = "";
          }
          renderAll();
        });
        container.appendChild(pill);
      });
    }

    function makeBadgeMarkup(product) {
      var badges = [];
      if (product.nuevo) badges.push('<span class="sl-badge">Nuevo</span>');
      var category = getProductCategory(product);
      if (category) badges.push('<span class="sl-badge">' + escapeHtml(category) + '</span>');
      return badges.length ? '<div class="sl-card-badges">' + badges.join("") + "</div>" : "";
    }

    function makeMediaMarkup(product) {
      if (hasImage(product)) {
        return '<img class="sl-card-img" src="' + escapeHtml(product.imagen) + '" alt="' + escapeHtml(product.nombre || "Producto") + '" />';
      }
      return '<div class="sl-card-img-placeholder">□</div>';
    }

    function makeGridCard(product) {
      var card = document.createElement("article");
      card.className = "sl-card";
      card.innerHTML =
        '<div class="sl-card-media">' +
          makeMediaMarkup(product) +
          makeBadgeMarkup(product) +
        "</div>" +
        '<div class="sl-card-body">' +
          '<div class="sl-card-store">' + escapeHtml(deriveStoreName(product)) + "</div>" +
          '<h3 class="sl-card-name">' + escapeHtml(product.nombre || "Producto") + "</h3>" +
          '<p class="sl-card-desc">' + escapeHtml(product.descCorta || product.descLarga || "Sin descripcion disponible.") + "</p>" +
          '<div class="sl-card-footer">' +
            '<div class="sl-card-price">' + escapeHtml(formatPrice(product.precio)) + '<small>' + escapeHtml(getProductCategory(product) || "Categoria general") + "</small></div>" +
            '<button class="sl-card-cta" type="button">Ver detalle</button>' +
          "</div>" +
        "</div>";
      return card;
    }

    function makeListCard(product) {
      var card = document.createElement("article");
      card.className = "sl-card-list";
      card.innerHTML =
        '<div class="sl-card-media">' +
          makeMediaMarkup(product) +
          makeBadgeMarkup(product) +
        "</div>" +
        '<div class="sl-card-body">' +
          '<div class="sl-card-store">' + escapeHtml(deriveStoreName(product)) + "</div>" +
          '<h3 class="sl-card-name">' + escapeHtml(product.nombre || "Producto") + "</h3>" +
          '<p class="sl-card-desc">' + escapeHtml(product.descCorta || product.descLarga || "Sin descripcion disponible.") + "</p>" +
          '<div class="sl-card-footer">' +
            '<div class="sl-card-price">' + escapeHtml(formatPrice(product.precio)) + '<small>' + escapeHtml(getProductCategory(product) || "Categoria general") + "</small></div>' +
            '<button class="sl-card-cta" type="button">Ver detalle</button>' +
          "</div>" +
        "</div>";
      return card;
    }

    function renderProducts() {
      var container = document.getElementById("sl-products-container");
      var products = getDisplayProducts();
      container.className = viewMode === "grid" ? "sl-products-grid" : "sl-products-list";
      container.innerHTML = "";

      document.getElementById("sl-results-count").textContent = products.length + (products.length === 1 ? " resultado" : " resultados");
      document.getElementById("sl-summary-title").textContent = selectedCategory ? selectedCategory : "Todos los productos";
      document.getElementById("sl-stat-products").textContent = String(allProducts.filter(isProductPublished).length);

      if (!products.length) {
        container.innerHTML =
          '<div class="sl-empty">' +
            '<div class="sl-empty-icon">⌕</div>' +
            "<strong>No encontramos productos con esos filtros</strong>" +
            "<span>Ajusta la busqueda, cambia la categoria o limpia los filtros activos.</span>" +
          "</div>";
        return;
      }

      products.forEach(function (product) {
        container.appendChild(viewMode === "grid" ? makeGridCard(product) : makeListCard(product));
      });
    }

    function renderAll() {
      updateHero();
      renderFeaturedCategories();
      renderStoreList();
      renderCategoryList();
      renderOfferList();
      renderActiveFilters();
      renderProducts();
    }

    function clearFilters() {
      selectedCategory = "";
      selectedStore = "";
      selectedOffer = "all";
      searchQ = "";
      sortMode = "featured";
      document.getElementById("sl-search-input").value = "";
      document.getElementById("sl-sort-select").value = "featured";
      renderAll();
    }

    async function hydrateStores() {
      try {
        var response = await fetch("/multitienda/vendors/", { headers: { Accept: "application/json" } });
        if (!response.ok) return;
        var data = await response.json();
        if (Array.isArray(data)) allStores = data;
        renderStoreList();
      } catch (error) {}
    }

    function bindAccordion() {
      document.querySelectorAll(".sl-acc-toggle").forEach(function (button) {
        button.addEventListener("click", function () {
          var item = button.parentElement;
          var isOpen = item.getAttribute("data-open") !== "false";
          item.setAttribute("data-open", isOpen ? "false" : "true");
          var body = button.nextElementSibling;
          if (body) body.hidden = isOpen;
        });
      });
    }

    function bindEvents() {
      document.getElementById("sl-view-grid").addEventListener("click", function () {
        viewMode = "grid";
        document.getElementById("sl-view-grid").classList.add("active");
        document.getElementById("sl-view-list").classList.remove("active");
        renderProducts();
      });

      document.getElementById("sl-view-list").addEventListener("click", function () {
        viewMode = "list";
        document.getElementById("sl-view-list").classList.add("active");
        document.getElementById("sl-view-grid").classList.remove("active");
        renderProducts();
      });

      document.getElementById("sl-search-input").addEventListener("input", function (event) {
        searchQ = normalizeText(event.target.value);
        renderAll();
      });

      document.getElementById("sl-sort-select").addEventListener("change", function (event) {
        sortMode = event.target.value;
        renderProducts();
      });

      document.getElementById("sl-clear-filters").addEventListener("click", clearFilters);

      document.getElementById("sl-contact-btn").addEventListener("click", function () {
        var email = normalizeText(document.getElementById("sl-store-email").textContent);
        var subject = encodeURIComponent("Consulta sobre productos");
        if (email && email.indexOf("@") !== -1) {
          window.location.href = "mailto:" + email + "?subject=" + subject;
          return;
        }
        alert("No hay correo configurado para esta tienda.");
      });

      document.getElementById("sl-view-store-btn").addEventListener("click", function () {
        document.getElementById("sl-search-input").focus();
      });
    }

    function loadInitialData() {
      allProducts = safeParse(localStorage.getItem("multitienda_productos"), []);
      allCategories = safeParse(localStorage.getItem("multitienda_categorias"), []);
      if (!Array.isArray(allProducts)) allProducts = [];
      if (!Array.isArray(allCategories)) allCategories = [];
    }

    loadInitialData();
    bindAccordion();
    bindEvents();
    renderAll();
    hydrateStores();
  })();
  </script>
</body>
</html>"""
