const VERSION = 'v5';
const STATIC_CACHE = `sipet-static-${VERSION}`;
const RUNTIME_CACHE = `sipet-runtime-${VERSION}`;
const OFFLINE_URL = '/offline';
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/manifest.webmanifest',
  '/static/css/main.css',
  '/static/js/app.js',
  '/static/js/push.js',
  '/static/js/conversations.js',
  '/static/js/notifications.js',
  '/static/js/sipet_dashboard.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/favicon.ico',
];

// ── API routes never cached ───────────────────────────────────────────────────
const API_PATTERN = /\/api\//;

// ── Sync queue tag ────────────────────────────────────────────────────────────
const SYNC_TAG = 'pwa-offline-queue';

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((key) => ![STATIC_CACHE, RUNTIME_CACHE].includes(key))
        .map((key) => caches.delete(key))
    );
    await self.clients.claim();
  })());
});

function staleWhileRevalidate(request) {
  return caches.open(RUNTIME_CACHE).then((cache) => {
    return cache.match(request).then((cached) => {
      const networkFetch = fetch(request)
        .then((response) => {
          if (response.ok) {
            cache.put(request, response.clone());
          }
          return response;
        })
        .catch(() => cached || new Response('', { status: 503, statusText: 'Service Unavailable' }));
      return cached || networkFetch;
    });
  });
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET' || !request.url.startsWith(self.location.origin)) {
    return;
  }

  if (API_PATTERN.test(request.url)) {
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          const offline = await caches.match(OFFLINE_URL);
          return cached || offline || new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
        })
    );
    return;
  }

  event.respondWith(staleWhileRevalidate(request));
});

self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// ── Background Sync ───────────────────────────────────────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(flushOfflineQueue());
  }
});

async function flushOfflineQueue() {
  const db = await openQueueDB();
  const tx = db.transaction('queue', 'readwrite');
  const store = tx.objectStore('queue');
  const all = await idbAll(store);

  for (const item of all) {
    try {
      const response = await fetch(item.url, {
        method: item.method,
        headers: item.headers,
        body: item.body || null,
      });
      if (response.ok) {
        await idbDelete(db, item.id);
      }
    } catch (_) {
      // keep in queue — will retry on next sync
    }
  }
}

// ── Push Notifications ────────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;

  let payload;
  try {
    payload = event.data.json();
  } catch (_) {
    payload = { title: 'SIPET', body: event.data.text() };
  }

  const title = payload.title || 'SIPET';
  const options = {
    body: payload.body || '',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    data: { url: payload.url || '/', ref_type: payload.ref_type, ref_id: payload.ref_id },
    tag: payload.tag || 'pwa-notification',
    renotify: Boolean(payload.renotify),
    vibrate: [100, 50, 100],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      const existing = clients.find((c) => c.url === url && 'focus' in c);
      if (existing) return existing.focus();
      return self.clients.openWindow(url);
    })
  );
});

// ── Minimal IndexedDB helpers (no library dependency) ─────────────────────────
function openQueueDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('pwa-offline', 1);
    req.onupgradeneeded = (e) => {
      e.target.result.createObjectStore('queue', { keyPath: 'id', autoIncrement: true });
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

function idbAll(store) {
  return new Promise((resolve, reject) => {
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

function idbDelete(db, id) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('queue', 'readwrite');
    const req = tx.objectStore('queue').delete(id);
    req.onsuccess = () => resolve();
    req.onerror = (e) => reject(e.target.error);
  });
}
