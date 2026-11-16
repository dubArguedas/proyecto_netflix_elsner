/* Layout compartido: sidebar + topbar.
   Cada pagina declara data-page y data-title / data-subtitle en <html>. */

const ICONOS = {
  resumen: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19V9m5 10V5m5 14v-7m5 7V8"/></svg>',
  limpieza: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M9 7V4h6v3m-9 0 1 13h10l1-13"/><path d="M10 11v5m4-5v5"/></svg>',
  mapreduce: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="5" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="12" r="2"/><path d="M7 6h5a3 3 0 0 1 3 3v0a3 3 0 0 0 3 3M7 18h5a3 3 0 0 0 3-3v0a3 3 0 0 1 3-3"/></svg>',
  databricks: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>',
  hallazgos: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 20V6m0 14h16"/><path d="M8 16v-4m4 4V8m4 8v-6"/></svg>',
  catalogo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 4v5"/></svg>',
  api: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 9 4 12l4 3m8-6 4 3-4 3M14 5l-4 14"/></svg>',
  doc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/></svg>',
};

const NAV = [
  {
    titulo: "Panel",
    enlaces: [
      { id: "resumen", texto: "Resumen ejecutivo", href: "index.html", etiqueta: "Inicio" },
    ],
  },
  {
    titulo: "Etapas del proyecto",
    enlaces: [
      { id: "limpieza", texto: "Reto 1 · Limpieza", href: "limpieza.html", etiqueta: "Pandas" },
      { id: "mapreduce", texto: "Reto 2 · MapReduce", href: "mapreduce.html", etiqueta: "HDFS" },
      { id: "databricks", texto: "Reto 3 · Databricks", href: "databricks.html", etiqueta: "Spark" },
      { id: "hallazgos", texto: "Reto 4 · Hallazgos", href: "hallazgos.html", etiqueta: "Informe" },
    ],
  },
  {
    titulo: "Datos y recursos",
    enlaces: [
      { id: "catalogo", texto: "Explorador del catálogo", href: "catalogo.html" },
    ],
  },
];

function construirSidebar(paginaActual) {
  const contenedor = document.getElementById("sidebar");
  if (!contenedor) return;

  const grupos = NAV.map((grupo) => {
    const enlaces = grupo.enlaces
      .map((enlace) => {
        const activo = enlace.id === paginaActual ? " active" : "";
        const etiqueta = enlace.etiqueta ? `<span class="tag">${enlace.etiqueta}</span>` : "";
        return `<a class="nav-link-side${activo}" href="${enlace.href}">
            ${ICONOS[enlace.id] || ""}
            <span>${enlace.texto}</span>${etiqueta}
          </a>`;
      })
      .join("");
    return `<div class="nav-group"><div class="nav-group-title">${grupo.titulo}</div>${enlaces}</div>`;
  }).join("");

  contenedor.innerHTML = `
    <div class="brand">
      <div class="brand-mark">NF</div>
      <div class="brand-text">
        <strong>Observatorio Netflix</strong>
        <span>Big Data · TEMI I</span>
      </div>
    </div>
    <nav class="nav-scroll">
      ${grupos}
      <div class="nav-group">
        <div class="nav-group-title">Documentación</div>
        <a class="nav-link-side" href="/docs" target="_blank" rel="noopener">
          ${ICONOS.api}<span>API interactiva</span><span class="tag">Swagger</span>
        </a>
        <a class="nav-link-side" href="/api/descargas/informe" target="_blank" rel="noopener">
          ${ICONOS.doc}<span>Informe del proyecto</span>
        </a>
      </div>
    </nav>
    <div class="sidebar-foot">
      <strong>Equipo Elsner</strong>
      Jhael Arguedas · Carlos Conde · Bryan Mamani<br>
      <span style="color:#4b5a75">Tecnologías Emergentes I</span>
    </div>`;
}

function construirTopbar(paginaActual) {
  const contenedor = document.getElementById("topbar");
  if (!contenedor) return;

  const titulo = document.documentElement.dataset.title || "Observatorio Netflix";
  const subtitulo = document.documentElement.dataset.subtitle || "";
  const migaja = document.documentElement.dataset.crumb || "";

  contenedor.innerHTML = `
    <button class="btn-pro menu-toggle" id="menuToggle" aria-label="Abrir menú">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
    </button>
    <div class="topbar-title">
      <div class="tiny muted" style="letter-spacing:.08em;text-transform:uppercase;font-size:10.5px;font-weight:700">${migaja}</div>
      <h1>${titulo}</h1>
      ${subtitulo ? `<p>${subtitulo}</p>` : ""}
    </div>
    <div class="topbar-actions">
      <span class="chip teal"><span class="dot"></span> Datos reales · 8 807 títulos</span>
      <a class="btn-pro" href="/docs" target="_blank" rel="noopener">
        ${ICONOS.api} API
      </a>
      <button class="btn-pro" onclick="window.print()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 8V3h10v5M7 18H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"/><rect x="7" y="14" width="10" height="7"/></svg>
        Exportar PDF
      </button>
    </div>`;

  const toggle = document.getElementById("menuToggle");
  const backdrop = document.createElement("div");
  backdrop.className = "backdrop";
  document.body.appendChild(backdrop);

  const cerrar = () => {
    document.getElementById("sidebar").classList.remove("open");
    backdrop.classList.remove("show");
  };

  toggle?.addEventListener("click", () => {
    document.getElementById("sidebar").classList.toggle("open");
    backdrop.classList.toggle("show");
  });
  backdrop.addEventListener("click", cerrar);
  document.querySelectorAll(".nav-link-side").forEach((enlace) => enlace.addEventListener("click", cerrar));
}

function marcarAnio() {
  document.querySelectorAll("[data-anio]").forEach((nodo) => {
    nodo.textContent = new Date().getFullYear();
  });
}

alCargar(() => {
  const pagina = document.documentElement.dataset.page || "resumen";
  construirSidebar(pagina);
  construirTopbar(pagina);
  marcarAnio();
});
