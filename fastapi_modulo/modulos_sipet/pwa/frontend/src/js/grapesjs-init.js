import grapesjs from "grapesjs";
import "grapesjs/dist/css/grapes.min.css";

export function initEditor(containerId, options = {}) {
  const editor = grapesjs.init({
    container: `#${containerId}`,
    height: options.height || "600px",
    width: "auto",
    storageManager: {
      type: "remote",
      stepsBeforeSave: 3,
      urlStore: options.saveUrl || "/api/v1/data/pages",
      urlLoad: options.loadUrl || "/api/v1/data/pages",
      headers: {
        Authorization: `Bearer ${window.Auth?.getAccess() || ""}`,
      },
    },
    plugins: [],
    canvas: {
      styles: ["/static/css/main.css"],
    },
    blockManager: {
      appendTo: options.blocksEl || "#blocks",
    },
    ...options.config,
  });

  // Basic blocks
  editor.BlockManager.add("section", {
    label: "Section",
    category: "Basic",
    content: '<section class="py-12 px-4"><div class="container mx-auto"></div></section>',
  });

  editor.BlockManager.add("card", {
    label: "Card",
    category: "Basic",
    content: '<div class="card bg-base-100 shadow-md p-6"><h2 class="card-title">Title</h2><p>Content</p></div>',
  });

  editor.BlockManager.add("hero", {
    label: "Hero",
    category: "Basic",
    content: '<div class="hero min-h-[40vh]"><div class="hero-content text-center"><h1 class="text-4xl font-bold">Hero Title</h1></div></div>',
  });

  return editor;
}
