/* Explorador del catálogo con busqueda y paginacion. */

const estadoCatalogo = {
  consulta: "",
  tipo: "",
  pagina: 1,
  tamano: 25,
  total: 0,
  paginas: 1,
};

let temporizador = null;

async function consultarCatalogo() {
  const parametros = new URLSearchParams({
    pagina: estadoCatalogo.pagina,
    tamano: estadoCatalogo.tamano,
  });
  if (estadoCatalogo.consulta) parametros.set("q", estadoCatalogo.consulta);
  if (estadoCatalogo.tipo) parametros.set("tipo", estadoCatalogo.tipo);

  const datos = await obtener(`/catalogo?${parametros.toString()}`);
  estadoCatalogo.total = datos.total;
  estadoCatalogo.paginas = datos.paginas;

  document.getElementById("resumenBusqueda").textContent =
    `${numero(datos.total)} títulos encontrados${estadoCatalogo.consulta ? ` para “${estadoCatalogo.consulta}”` : ""}`;

  document.getElementById("tablaCatalogo").innerHTML = datos.registros
    .map(
      (fila) => `
      <tr>
        <td class="mono">${escapar(fila.show_id)}</td>
        <td class="strong">${escapar(fila.title)}</td>
        <td><span class="chip ${fila.type === "Movie" ? "red" : "blue"}">${escapar(fila.type || "—")}</span></td>
        <td class="tiny">${escapar(fila.director || "—")}</td>
        <td class="tiny">${escapar(fila.country || "—")}</td>
        <td class="num">${fila.release_year ?? "—"}</td>
        <td><span class="chip outline">${escapar(fila.rating || "—")}</span></td>
        <td class="num">${fila.duration_min ?? "—"}</td>
      </tr>`,
    )
    .join("") || '<tr><td colspan="8" class="muted">Sin resultados para esta búsqueda.</td></tr>';

  document.getElementById("piePagina").textContent =
    `Página ${estadoCatalogo.pagina} de ${numero(estadoCatalogo.paginas)} · ${numero(estadoCatalogo.total)} registros`;

  document.getElementById("anterior").disabled = estadoCatalogo.pagina <= 1;
  document.getElementById("siguiente").disabled = estadoCatalogo.pagina >= estadoCatalogo.paginas;
}

async function cargarCatalogo() {
  try {
    await consultarCatalogo();
  } catch (error) {
    mostrarError("tablaCatalogo", error);
  }
}

function reiniciarYConsultar() {
  estadoCatalogo.pagina = 1;
  consultarCatalogo().catch((error) => mostrarError("tablaCatalogo", error));
}

alCargar(() => {
  const buscador = document.getElementById("buscador");

  buscador.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => {
      estadoCatalogo.consulta = buscador.value.trim();
      reiniciarYConsultar();
    }, 280);
  });

  document.querySelectorAll("#filtrosTipo [data-tipo]").forEach((boton) => {
    boton.addEventListener("click", () => {
      document.querySelectorAll("#filtrosTipo .btn-pro").forEach((otro) => otro.classList.remove("active"));
      boton.classList.add("active");
      estadoCatalogo.tipo = boton.dataset.tipo;
      reiniciarYConsultar();
    });
  });

  document.getElementById("anterior").addEventListener("click", () => {
    if (estadoCatalogo.pagina > 1) {
      estadoCatalogo.pagina -= 1;
      consultarCatalogo().catch((error) => mostrarError("tablaCatalogo", error));
    }
  });

  document.getElementById("siguiente").addEventListener("click", () => {
    if (estadoCatalogo.pagina < estadoCatalogo.paginas) {
      estadoCatalogo.pagina += 1;
      consultarCatalogo().catch((error) => mostrarError("tablaCatalogo", error));
    }
  });

  document.getElementById("tamanoPagina").addEventListener("change", (evento) => {
    estadoCatalogo.tamano = Number(evento.target.value);
    reiniciarConFiltros();
  });

  cargarCatalogo();
});

function reiniciarConFiltros() {
  estadoCatalogo.pagina = 1;
  consultarCatalogo().catch((error) => mostrarError("tablaCatalogo", error));
}
