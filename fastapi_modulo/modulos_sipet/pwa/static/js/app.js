const Auth = {
  getAccess: () => localStorage.getItem("access_token"),
  getRefresh: () => localStorage.getItem("refresh_token"),
  set: (access, refresh) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  },
  clear: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
  isLoggedIn: () => Boolean(localStorage.getItem("access_token")),
};

async function safeJson(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return null;
}

async function apiFetch(url, options = {}) {
  const headers = { ...options.headers };
  const hasJsonBody = options.body && !(options.body instanceof FormData) && !headers["Content-Type"];
  if (hasJsonBody) {
    headers["Content-Type"] = "application/json";
  }

  const token = Auth.getAccess();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401 && Auth.getRefresh()) {
    const refreshResponse = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: Auth.getRefresh() }),
    });

    if (refreshResponse.ok) {
      const refreshed = await refreshResponse.json();
      Auth.set(refreshed.access_token, refreshed.refresh_token);
      headers.Authorization = `Bearer ${refreshed.access_token}`;
      response = await fetch(url, { ...options, headers });
    } else {
      Auth.clear();
      window.location.href = "/login";
      return refreshResponse;
    }
  }

  return response;
}

function toast(message, type = "info") {
  const root = document.getElementById("toast-root");
  if (!root) return;

  const item = document.createElement("div");
  item.className = `toast toast-${type}`;
  item.textContent = message;
  root.appendChild(item);

  window.setTimeout(() => {
    item.classList.add("toast-hide");
    window.setTimeout(() => item.remove(), 250);
  }, 3200);
}

function updateConnectionBanner() {
  const banner = document.getElementById("connection-banner");
  if (!banner) return;
  banner.classList.toggle("is-hidden", navigator.onLine);
}

let deferredPrompt = null;

function wireInstallPrompt() {
  const installButton = document.getElementById("install-btn");
  if (!installButton) return;

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;
    installButton.classList.remove("is-hidden");
  });

  installButton.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    installButton.classList.add("is-hidden");
  });

  window.addEventListener("appinstalled", () => {
    installButton.classList.add("is-hidden");
    toast("App instalada", "success");
  });
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  try {
    const registration = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    registration.addEventListener?.("updatefound", () => {
      toast("Hay una nueva versión disponible", "info");
    });
  } catch (error) {
    console.error("SW error:", error);
  }
}

window.addEventListener("online", () => {
  updateConnectionBanner();
  toast("Conexión restaurada", "success");
});
window.addEventListener("offline", () => {
  updateConnectionBanner();
  toast("Sin conexión · modo offline", "warning");
});
window.addEventListener("DOMContentLoaded", () => {
  updateConnectionBanner();
  wireInstallPrompt();
  registerServiceWorker();
});

window.Auth = Auth;
window.apiFetch = apiFetch;
window.toast = toast;
window.safeJson = safeJson;
