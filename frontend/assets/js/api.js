/* Cliente de la API y utilidades de formato compartidas. */

const API = "/api";

const formatoNumero = new Intl.NumberFormat("es-BO");
const formatoDecimal = new Intl.NumberFormat("es-BO", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

async function obtener(ruta) {
  const respuesta = await fetch(`${API}${ruta}`, { headers: { Accept: "application/json" } });
  if (!respuesta.ok) {
    throw new Error(`La API respondió ${respuesta.status} en ${ruta}`);
  }
  return respuesta.json();
}

function numero(valor) {
  if (valor === null || valor === undefined) return "—";
  return formatoNumero.format(valor);
}

function decimal(valor) {
  if (valor === null || valor === undefined) return "—";
  return formatoDecimal.format(valor);
}

function porcentaje(valor) {
  if (valor === null || valor === undefined) return "—";
  return `${decimal(valor)} %`;
}

function escapar(texto) {
  if (texto === null || texto === undefined) return "";
  return String(texto)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function mostrarError(contenedorId, error) {
  const contenedor = document.getElementById(contenedorId);
  if (!contenedor) return;
  contenedor.innerHTML = `
    <div class="notice red">
      <strong>No se pudieron cargar los datos.</strong><br>
      ${escapar(error.message)}. Verifique que el backend esté activo en
      <span class="mono">http://127.0.0.1:8000</span>.
    </div>`;
}

/* Estado de carga simple para tablas y tarjetas. */
function esqueleto(filas = 5, columnas = 4) {
  return Array.from({ length: filas })
    .map(
      () =>
        `<tr>${Array.from({ length: columnas })
          .map(() => '<td><div style="height:11px;background:#eef1f7;border-radius:4px"></div></td>')
          .join("")}</tr>`,
    )
    .join("");
}

/* Paleta oficial de los gráficos. */
const PALETA = {
  rojo: "#e50914",
  rojoSuave: "rgba(229, 9, 20, .18)",
  azul: "#2563eb",
  teal: "#0f9d8f",
  ambar: "#d97706",
  violeta: "#7c3aed",
  gris: "#94a3b8",
  ink: "#16203a",
};

if (window.Chart) {
  Chart.defaults.font.family = '"Segoe UI", Inter, system-ui, sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = "#5a6782";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 8;
  Chart.defaults.plugins.tooltip.backgroundColor = "#0a0f1c";
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.plugins.tooltip.titleFont = { weight: "700" };
  Chart.defaults.maintainAspectRatio = false;
}

const ejeBase = {
  grid: { color: "#eef1f7", drawBorder: false },
  border: { display: false },
  ticks: { color: "#8693ad", font: { size: 11.5 } },
};

/* Ejecuta el arranque aunque DOMContentLoaded ya se haya disparado
   (por ejemplo al volver a una pagina restaurada desde la cache). */
function alCargar(callback) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", callback, { once: true });
  } else {
    callback();
  }
}

/* Crea un grafico destruyendo la instancia previa del mismo canvas. */
function crearGrafico(canvas, configuracion) {
  if (!canvas || !window.Chart) return null;
  const anterior = Chart.getChart(canvas);
  if (anterior) anterior.destroy();
  return new Chart(canvas, configuracion);
}
