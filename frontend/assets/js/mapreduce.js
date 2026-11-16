/* Reto 2 - Resultado de Hadoop. */

async function cargarMapReduce() {
  try {
    const datos = await obtener("/mapreduce");
    const { disponible, total_actores, pares_actor_titulo, top_10, comparacion } = datos;

    document.getElementById("kpiPares").textContent = numero(pares_actor_titulo);
    document.getElementById("kpiActoresMR").textContent = numero(total_actores);
    document.getElementById("pasoMapper").textContent = `${numero(pares_actor_titulo)} pares actor–show_id`;
    document.getElementById("pasoReducer").textContent = `${numero(total_actores)} actores`;

    if (top_10.length) {
      document.getElementById("kpiTopActor").textContent = top_10[0].actor;
      document.getElementById("kpiTopActorCantidad").textContent = `${numero(top_10[0].cantidad_titulos)} títulos distintos`;
    }

    if (comparacion) {
      const { tabla5 } = comparacion;
      const iguales = tabla5.ambas_iguales === tabla5.actores_mapreduce &&
        tabla5.ambas_iguales === tabla5.actores_spark;
      document.getElementById("kpiCoincidencia").textContent = iguales ? "100 %" : "Revisar";
      document.getElementById("kpiCoincidenciaHint").textContent =
        `${numero(tabla5.ambas_iguales)} de ${numero(tabla5.actores_spark)} actores con la misma cantidad`;
    }

    if (!disponible) {
      document.getElementById("tablaTopActores").innerHTML = `
        <tr><td colspan="3">
          <div class="notice amber m-3">
            No se encontró <span class="mono">mapreduce_actores.csv</span>. Ejecute
            <span class="mono">python scripts/02_simular_mapreduce_local.py</span> o descargue las partes de HDFS.
          </div>
        </td></tr>`;
      return;
    }

    document.getElementById("tablaTopActores").innerHTML = top_10
      .map(
        (fila, indice) => `
        <tr class="${indice < 3 ? "top" : ""}">
          <td><span class="rank">${indice + 1}</span></td>
          <td class="strong">${escapar(fila.actor)}</td>
          <td class="num">${numero(fila.cantidad_titulos)}</td>
        </tr>`,
      )
      .join("");

    pintarTopActores(top_10);
  } catch (error) {
    mostrarError("tablaTopActores", error);
  }
}

function pintarTopActores(actores) {
  const contexto = document.getElementById("graficoTopActores");
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
          backgroundColor: ordenados.map((fila) =>
            fila.actor === actores[0].actor ? PALETA.rojo : "rgba(229, 9, 20, .55)",
          ),
          borderRadius: 5,
          maxBarThickness: 18,
        },
      ],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: {
        x: { ...ejeBase, beginAtZero: true },
        y: { ...ejeBase, grid: { display: false } },
      },
    },
  });
}

alCargar(cargarMapReduce);
