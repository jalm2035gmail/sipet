/**
 * push.js — Gestión de suscripciones VAPID + permisos push.
 *
 * Uso:
 *   await Push.subscribe()   // solicita permiso y registra endpoint
 *   await Push.unsubscribe() // elimina suscripción activa
 *   Push.isSupported()       // true si el navegador soporta push
 */
const Push = (() => {
  const API_SUBSCRIBE   = "/api/v2/pwa/notifications/push/subscribe";
  const API_UNSUBSCRIBE = "/api/v2/pwa/notifications/push/subscribe";

  // Clave VAPID pública — se sobrescribe desde el servidor si existe
  // <meta name="vapid-public-key" content="...">
  function getVapidKey() {
    const meta = document.querySelector('meta[name="vapid-public-key"]');
    return meta ? meta.content : null;
  }

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const raw = atob(base64);
    return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
  }

  function isSupported() {
    return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  }

  async function subscribe() {
    if (!isSupported()) {
      throw new Error("Push no soportado en este navegador");
    }

    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      throw new Error("Permiso de notificaciones denegado");
    }

    const vapidKey = getVapidKey();
    if (!vapidKey) {
      throw new Error("VAPID public key no configurada");
    }

    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey),
    });

    const { endpoint, keys } = sub.toJSON();
    const response = await apiFetch(API_SUBSCRIBE, {
      method: "POST",
      body: JSON.stringify({
        endpoint,
        p256dh: keys.p256dh,
        auth: keys.auth,
        user_agent: navigator.userAgent.slice(0, 255),
      }),
    });

    if (!response.ok) {
      throw new Error("Error al registrar suscripción push");
    }
    return sub;
  }

  async function unsubscribe() {
    if (!isSupported()) return;
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (!sub) return;

    const endpoint = sub.endpoint;
    await sub.unsubscribe();

    await apiFetch(API_UNSUBSCRIBE, {
      method: "DELETE",
      body: JSON.stringify({ endpoint }),
    });
  }

  async function getStatus() {
    if (!isSupported()) return { supported: false, permission: "denied", subscribed: false };
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    return {
      supported: true,
      permission: Notification.permission,
      subscribed: Boolean(sub),
    };
  }

  return { subscribe, unsubscribe, getStatus, isSupported };
})();

window.Push = Push;
