(async () => {
  const statusNode = document.getElementById("modulo-base-status");
  const totalNode = document.getElementById("modulo-base-total");
  const openModalButton = document.getElementById("modulo-base-open-modal");
  const modal = document.getElementById("modulo-base-modal");

  if (openModalButton && modal && typeof modal.showModal === "function") {
    openModalButton.addEventListener("click", () => modal.showModal());
  }

  try {
    const response = await fetch("/api/modulo-base/resumen", { credentials: "same-origin" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    const data = payload.data || {};
    if (statusNode) statusNode.textContent = data.health || "ok";
    if (totalNode) totalNode.textContent = String(data.total_registros ?? 0);
  } catch (error) {
    if (statusNode) statusNode.textContent = error.message;
  }
})();
