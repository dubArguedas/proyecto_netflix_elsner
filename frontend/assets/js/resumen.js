/* Pagina de resumen ejecutivo. */

async function cargarResumen() {
  try {
    const datos = await obtener("/resumen");
    const { kpis, tipos, top_actores, top_paises, por_anio, por_rating, calidad } = datos;

    document.getElementById("chipActualizado").textContent =
      `Actualizado ${new Date(datos.generado_en).toLocaleString("es-BO")}`;

    document.getElementById("kpiTitulos").textContent = numero(kpis.titulos_totales);
    document.getElementById("kpiTitulosHint").textContent =
      `Registros limpios · ${numero(kpis.anios_cubiertos[0])}–${numero(kpis.anios_cubiertos[1])}`;

    document.getElementById("kpiPeliculas").textContent = numero(kpis.peliculas);
    document.getElementById("kpiPeliculasHint").textContent = `${porcentaje(kpis.porcentaje_peliculas)} del catálogo`;

    document.getElementById("kpiSeries").textContent = numero(kpis.series);
    document.getElementById("kpiSeriesHint").textContent = `${porcentaje(kpis.porcentaje_series)} del catálogo`;

    document.getElementById("kpiActores").textContent = numero(kpis.actores_distintos);
    document.getElementById("kpiActoresHint").textContent =
      `MapReduce: ${numero(kpis.mapreduce_actores)} · coinciden`;

    document.getElementById("resumenTipos").innerHTML = tipos
      .map(
        (fila) =>
          `<span><strong>${escapar(fila.tipo)}</strong> · ${numero(fila.cantidad_titulos)} títulos${
            fila.porcentaje ? ` (${porcentaje(fila.porcentaje)})` : ""
          }</span>`,
      )
      .join("");

    pintarTipos(tipos);
    pintarActores(top_actores);
    pintarPaises(top_paises);
    pintarCalidad(calidad, kpis);
    pintarAnios(por_anio);
    pintarRatings(por_rating);
  } catch (error) {
    mostrarError("panelCalidad", error);
  }
}

function pintarTipos(tipos) {
  const contexto = document.getElementById("graficoTipos");
  if (!contexto) return;
  const colores = tipos.map((fila) => (fila.tipo === "Movie" ? PALETA.rojo : PALETA.ink));
  crearGrafico(contexto, {
    type: "bar",
    data: {
      labels: tipos.map((fila) => fila.tipo),
      datasets: [
        {
          label: "Títulos",
          data: tipos.map((fila) => fila.cantidad_titulos),
          backgroundColor: colores,
          borderRadius: 6,
          maxBarThickness: 74,
        },
      ],
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => {
              const fila = tipos[item.dataIndex];
              return `${numero(fila.cantidad_titulos)} títulos (${porcentaje(fila.porcentaje)})`;
            },
          },
        },
      },
      scales: { x: ejeBase, y: { ...ejeBase, beginAtZero: true } },
    },
  });
}

function pintarActores(actores) {
  const contexto = document.getElementById("graficoActores");
  if (!contexto) return;
  crearGrafico(contexto, {
    type: "bar",
    data: {
      labels: actores.map((fila) => fila.actor),
      datasets: [
        {
          label: "Títulos",
          data: actores.map((fila) => fila.cantidad_titulos),
          backgroundColor: actores.map((_, indice) =>
            indice === 0 ? PALETA.rojo : `rgba(229, 9, 20, ${0.86 - indice * 0.06})`,
          ),
          borderRadius: 5,
          maxBarThickness: 16,
        },
      ],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: {
        x: { ...ejeBase, beginAtZero: true, grid: { color: "#eef1f7" } },
        y: { ...ejeBase, grid: { display: false } },
      },
    },
  });
}

function pintarPaises(paises) {
  const cuerpo = document.getElementById("tablaPaises");
  cuerpo.innerHTML = paises
    .map(
      (fila, indice) => `
        <tr class="${indice === 0 ? "top" : ""}">
          <td><span class="rank">${indice + 1}</span></td>
          <td class="strong">${escapar(fila.pais)}</td>
          <td class="num">${numero(fila.cantidad_peliculas)}</td>
          <td class="num">${decimal(fila.duracion_promedio_min)} min</td>
        </tr>`,
    )
    .join("");
}

function pintarCalidad(calidad, kpis) {
  const contenedor = document.getElementById("panelCalidad");
  const controles = [
    { etiqueta: "Filas duplicadas eliminadas", valor: calidad.duplicados_filas, ok: calidad.duplicados_filas === 0 },
    { etiqueta: "Registros sin show_id", valor: calidad.sin_show_id, ok: calidad.sin_show_id === 0 },
    { etiqueta: "show_id repetidos", valor: calidad.show_id_repetido, ok: calidad.show_id_repetido === 0 },
    { etiqueta: "Fechas no interpretables", valor: calidad.fechas_vacias, ok: calidad.fechas_vacias <= 10 },
    { etiqueta: "Películas sin duración", valor: calidad.peliculas_sin_duracion, ok: calidad.peliculas_sin_duracion <= 3 },
  ];

  contenedor.innerHTML = `
    <div class="d-flex flex-column gap-2">
      ${controles
        .map(
          (control) => `
        <div class="d-flex align-items-center justify-content-between">
          <span class="tiny muted">${control.etiqueta}</span>
          <span class="chip ${control.ok ? "ok" : "amber"}">${numero(control.valor)}</span>
        </div>`,
        )
        .join("")}
      <div class="divider my-1"></div>
      <div class="d-flex align-items-center justify-content-between">
        <span class="tiny muted">Duración promedio de películas</span>
        <span class="strong">${decimal(kpis.duracion_promedio_peliculas)} min</span>
      </div>
      <div class="d-flex align-items-center justify-content-between">
        <span class="tiny muted">Países identificados</span>
        <span class="strong">${numero(kpis.paises_distintos)}</span>
      </div>
    </div>`;
}

function pintarAnios(porAnio) {
  const contexto = document.getElementById("graficoAnios");
  if (!contexto) return;
  const recortado = porAnio.filter((fila) => fila.anio >= 1980);
  crearGrafico(contexto, {
    type: "line",
    data: {
      labels: recortado.map((fila) => fila.anio),
      datasets: [
        {
          label: "Títulos",
          data: recortado.map((fila) => fila.titulos),
          borderColor: PALETA.azul,
          backgroundColor: "rgba(37, 99, 235, .12)",
          fill: true,
          tension: 0.35,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ...ejeBase, grid: { display: false }, ticks: { ...ejeBase.ticks, maxTicksLimit: 12 } },
        y: { ...ejeBase, beginAtZero: true },
      },
      interaction: { mode: "index", intersect: false },
    },
  });
}

function pintarRatings(ratings) {
  const cuerpo = document.getElementById("tablaRatings");
  cuerpo.innerHTML = ratings
    .map(
      (fila) => `
        <tr>
          <td><span class="chip outline">${escapar(fila.rating)}</span></td>
          <td class="num">${numero(fila.titulos)}</td>
        </tr>`,
    )
    .join("");
}

alCargar(cargarResumen);
