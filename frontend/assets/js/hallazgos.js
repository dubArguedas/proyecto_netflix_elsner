/* Reto 4 - Gráficos obligatorios, tabla 6 y conclusiones. */

/* Plugin de etiquetas dibujadas sobre cada barra (sin dependencias externas). */
const pluginEtiquetas = {
  id: "etiquetasValor",
  afterDatasetsDraw(grafico, _argumentos, opciones) {
    const { ctx } = grafico;
    const meta = grafico.getDatasetMeta(0);
    const horizontal = grafico.options.indexAxis === "y";

    meta.data.forEach((elemento, indice) => {
      const valor = grafico.data.datasets[0].data[indice];
      const texto = opciones.formato ? opciones.formato(valor, indice) : String(valor);

      ctx.save();
      ctx.fillStyle = opciones.color || "#16203a";
      ctx.font = '700 11.5px "Segoe UI", Inter, sans-serif';
      if (horizontal) {
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(texto, elemento.x + 8, elemento.y);
      } else {
        ctx.textAlign = "center";
        ctx.textBaseline = "bottom";
        ctx.fillText(texto, elemento.x, elemento.y - 7);
      }
      ctx.restore();
    });
  },
};

async function cargarHallazgos() {
  try {
    const [tipos, actores, paises, verificacion] = await Promise.all([
      obtener("/tipos"),
      obtener("/actores?limite=10"),
      obtener("/paises?limite=10"),
      obtener("/verificacion"),
    ]);

    const clasificados = tipos.registros.filter((fila) => ["Movie", "TV Show"].includes(fila.tipo));
    document.getElementById("chipTotalClasificado").textContent =
      `${numero(tipos.total_clasificado)} títulos clasificados`;

    pintarTipos(clasificados);
    pintarActores(actores.registros);
    pintarPaises(paises.registros);
    pintarHallazgos(clasificados, actores.registros, paises.registros);
    redactarConclusiones(clasificados, actores.registros, paises.registros, verificacion);
  } catch (error) {
    mostrarError("tablaPaises", error);
  }
}

function pintarTipos(tipos) {
  const contexto = document.getElementById("graficoTipos");
  if (!contexto) return;

  crearGrafico(contexto, {
    type: "bar",
    data: {
      labels: tipos.map((fila) => fila.tipo),
      datasets: [
        {
          label: "Títulos",
          data: tipos.map((fila) => fila.cantidad_titulos),
          backgroundColor: tipos.map((fila) => (fila.tipo === "Movie" ? PALETA.rojo : PALETA.ink)),
          borderRadius: 8,
          maxBarThickness: 110,
        },
      ],
    },
    options: {
      layout: { padding: { top: 26 } },
      plugins: {
        legend: { display: false },
        etiquetasValor: {
          formato: (valor, indice) =>
            `${numero(valor)} · ${porcentaje(tipos[indice].porcentaje)}`,
          color: "#16203a",
        },
        tooltip: {
          callbacks: {
            label: (item) =>
              `${numero(item.parsed.y)} títulos (${porcentaje(tipos[item.dataIndex].porcentaje)})`,
          },
        },
      },
      scales: {
        x: { ...ejeBase, grid: { display: false } },
        y: {
          ...ejeBase,
          beginAtZero: true,
          title: { display: true, text: "Cantidad de títulos", color: "#8693ad", font: { size: 11.5 } },
        },
      },
    },
    plugins: [pluginEtiquetas],
  });
}

function pintarActores(actores) {
  const contexto = document.getElementById("graficoActores");
  if (!contexto) return;

  const ordenados = [...actores].reverse();
  crearGrafico(contexto, {
    type: "bar",
    data: {
      labels: ordenados.map((fila) => fila.actor),
      datasets: [
        {
          label: "Títulos",
          data: ordenados.map((fila) => fila.cantidad_titulos),
          backgroundColor: ordenados.map((_, indice) =>
            indice === ordenados.length - 1 ? PALETA.rojo : "rgba(229, 9, 20, .62)",
          ),
          borderRadius: 5,
          maxBarThickness: 19,
        },
      ],
    },
    options: {
      indexAxis: "y",
      layout: { padding: { right: 44 } },
      plugins: {
        legend: { display: false },
        etiquetasValor: { formato: (valor) => numero(valor) },
      },
      scales: {
        x: {
          ...ejeBase,
          beginAtZero: true,
          title: { display: true, text: "Cantidad de títulos distintos", color: "#8693ad", font: { size: 11.5 } },
        },
        y: { ...ejeBase, grid: { display: false } },
      },
    },
    plugins: [pluginEtiquetas],
  });
}

function pintarPaises(paises) {
  document.getElementById("tablaPaises").innerHTML = paises
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

function pintarHallazgos(tipos, actores, paises) {
  const peliculas = tipos.find((fila) => fila.tipo === "Movie");
  const series = tipos.find((fila) => fila.tipo === "TV Show");
  const top = actores[0];
  const primerPais = paises[0];
  const paisMasLargo = [...paises].sort(
    (a, b) => b.duracion_promedio_min - a.duracion_promedio_min,
  )[0];

  document.getElementById("panelHallazgos").innerHTML = `
    <div class="d-flex align-items-start gap-3 mb-3">
      <span class="chip red">01</span>
      <div>
        <div class="strong">El catálogo es mayoritariamente cinematográfico</div>
        <div class="tiny muted">${numero(peliculas.cantidad_titulos)} películas (${porcentaje(peliculas.porcentaje)})
          frente a ${numero(series.cantidad_titulos)} series (${porcentaje(series.porcentaje)}).</div>
      </div>
    </div>
    <div class="d-flex align-items-start gap-3 mb-3">
      <span class="chip amber">02</span>
      <div>
        <div class="strong">${escapar(top.actor)} lidera el conteo</div>
        <div class="tiny muted">Participa en ${numero(top.cantidad_titulos)} títulos distintos del catálogo;
          le siguen ${escapar(actores[1].actor)} (${numero(actores[1].cantidad_titulos)}) y
          ${escapar(actores[2].actor)} (${numero(actores[2].cantidad_titulos)}).</div>
      </div>
    </div>
    <div class="d-flex align-items-start gap-3 mb-3">
      <span class="chip teal">03</span>
      <div>
        <div class="strong">${escapar(primerPais.pais)} concentra la mayor oferta</div>
        <div class="tiny muted">${numero(primerPais.cantidad_peliculas)} películas con una duración promedio de
          ${decimal(primerPais.duracion_promedio_min)} minutos.</div>
      </div>
    </div>
    <div class="d-flex align-items-start gap-3">
      <span class="chip blue">04</span>
      <div>
        <div class="strong">Duraciones más extensas</div>
        <div class="tiny muted">Entre los diez países con más películas, ${escapar(paisMasLargo.pais)} presenta el
          promedio más alto: ${decimal(paisMasLargo.duracion_promedio_min)} minutos.</div>
      </div>
    </div>`;
}

function redactarConclusiones(tipos, actores, paises, verificacion) {
  const peliculas = tipos.find((fila) => fila.tipo === "Movie");
  const series = tipos.find((fila) => fila.tipo === "TV Show");
  const top = actores[0];
  const pais = paises[0];
  const paisLargo = [...paises].sort(
    (a, b) => b.duracion_promedio_min - a.duracion_promedio_min,
  )[0];
  const tabla5 = verificacion.tabla5 || {};
  const tabla3 = verificacion.tabla3 || [];

  const sqlSpark = tabla3.every((fila) => fila.coinciden_completamente);
  const mrSpark =
    tabla5.ambas_diferentes === 0 &&
    tabla5.solo_mapreduce === 0 &&
    tabla5.solo_spark === 0;

  document.getElementById("textoConclusiones").innerHTML = `
    El catálogo analizado contiene <strong>${numero(peliculas.cantidad_titulos + series.cantidad_titulos)}</strong>
    títulos: <strong>${numero(peliculas.cantidad_titulos)} películas</strong>
    (${porcentaje(peliculas.porcentaje)}) y <strong>${numero(series.cantidad_titulos)} series</strong>
    (${porcentaje(series.porcentaje)}). El actor con más títulos distintos es
    <strong>${escapar(top.actor)}</strong>, con ${numero(top.cantidad_titulos)}. Sobre la duración,
    <strong>${escapar(pais.pais)}</strong> aporta ${numero(pais.cantidad_peliculas)} películas al cálculo con un
    promedio de ${decimal(pais.duracion_promedio_min)} minutos, mientras que
    <strong>${escapar(paisLargo.pais)}</strong> registra el promedio más alto del grupo líder
    (${decimal(paisLargo.duracion_promedio_min)} minutos).
    Los tres análisis produjeron ${sqlSpark ? "exactamente las mismas salidas en SQL y en PySpark" : "diferencias que deben revisarse"}:
    ${numero(tabla3[0]?.filas_sql)} filas en el análisis de tipos, ${numero(tabla3[1]?.filas_sql)} actores y
    ${numero(tabla3[2]?.filas_sql)} países. El conteo de MapReduce coincidió con Spark en
    <strong>${numero(tabla5.ambas_iguales)} actores</strong>, con
    ${numero(tabla5.ambas_diferentes)} diferencias y ${numero(tabla5.solo_mapreduce + tabla5.solo_spark)} nombres
    presentes en una sola salida${mrSpark ? "" : ", lo que obliga a revisar el proceso"}.
    Por último, los campos <span class="mono">cast</span> y <span class="mono">country</span> son multivaluados:
    un título cuenta para cada actor o país que lo acompaña y los vacíos se mantienen nulos, de modo que estos
    resultados describen la composición del catálogo y no la audiencia ni el éxito comercial de los títulos.`;

  const palabras = document
    .getElementById("textoConclusiones")
    .textContent.trim()
    .split(/\s+/).length;
  document.getElementById("contadorPalabras").textContent =
    `Extensión: ${palabras} palabras (límite 250).`;
}

alCargar(cargarHallazgos);
