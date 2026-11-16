/* Reto 3 - Tablas 3, 4 y 5. */

const NOMBRES_ANALISIS = {
  peliculas_y_series: "Películas y series",
  titulos_por_actor: "Títulos por actor",
  duracion_por_pais: "Duración por país",
};

const ETIQUETAS_TABLA5 = {
  actores_mapreduce: "Actores en MapReduce",
  actores_spark: "Actores en Spark",
  ambas_iguales: "Presentes en ambas salidas con cantidades iguales",
  ambas_diferentes: "Presentes en ambas salidas con cantidades diferentes",
  solo_mapreduce: "Presentes únicamente en MapReduce",
  solo_spark: "Presentes únicamente en Spark",
};

async function cargarVerificacion() {
  try {
    const [verificacion, resumen] = await Promise.all([obtener("/verificacion"), obtener("/resumen")]);

    document.getElementById("filasNetflixClean").textContent =
      `${numero(resumen.kpis.titulos_totales)} registros · ${numero(resumen.kpis.peliculas)} películas · ${numero(resumen.kpis.series)} series`;

    const tabla3 = verificacion.tabla3 || [];
    document.getElementById("tabla3").innerHTML = tabla3
      .map((fila) => {
        const ok = fila.coinciden_completamente;
        return `<tr>
          <td class="strong">${NOMBRES_ANALISIS[fila.analisis] || fila.analisis}</td>
          <td class="num">${numero(fila.filas_sql)}</td>
          <td class="num">${numero(fila.filas_pyspark)}</td>
          <td class="num">${numero(fila.filas_con_valores_diferentes)}</td>
          <td class="num">${numero(fila.filas_en_una_sola_salida)}</td>
          <td><span class="chip ${ok ? "ok" : "amber"}">${ok ? "Sí" : "No"}</span></td>
        </tr>`;
      })
      .join("");

    const origen = document.getElementById("origenVerificacion");
    if (origen) {
      origen.textContent =
        `${verificacion.origen}. La evidencia oficial del Reto 3 es el notebook ` +
        `03_analisis_netflix ejecutado en Databricks (ver GUIA_DATABRICKS.md).`;
    }

    if (verificacion.tabla4?.length) {
      document.getElementById("tabla4").innerHTML = verificacion.tabla4
        .map(
          (fila) => `<tr class="${fila.posicion <= 3 ? "top" : ""}">
            <td><span class="rank">${fila.posicion}</span></td>
            <td class="strong">${escapar(fila.actor)}</td>
            <td class="num">${numero(fila.mapreduce)}</td>
            <td class="num">${numero(fila.spark)}</td>
            <td class="num"><span class="chip ${fila.diferencia === 0 ? "ok" : "amber"}">${fila.diferencia > 0 ? "+" : ""}${numero(fila.diferencia)}</span></td>
          </tr>`,
        )
        .join("");
    }

    const tabla5 = verificacion.tabla5 || {};
    const filas5 = Object.entries(ETIQUETAS_TABLA5)
      .filter(([clave]) => tabla5[clave] !== undefined)
      .map(
        ([clave, etiqueta]) => `
        <div class="d-flex justify-content-between align-items-center py-2" style="border-bottom:1px solid #edf1f7">
          <span class="tiny muted" style="max-width:70%">${etiqueta}</span>
          <span class="strong">${numero(tabla5[clave])}</span>
        </div>`,
      )
      .join("");

    const iguales =
      tabla5.actores_mapreduce === tabla5.actores_spark &&
      tabla5.ambas_iguales === tabla5.actores_spark &&
      tabla5.ambas_diferentes === 0 &&
      tabla5.solo_mapreduce === 0 &&
      tabla5.solo_spark === 0;

    document.getElementById("chipVerificacion").textContent = iguales ? "Coincide 100 %" : "Revisar";
    document.getElementById("chipVerificacion").className = `chip ${iguales ? "ok" : "amber"}`;
    document.getElementById("tabla5").innerHTML = filas5 || '<div class="muted tiny">Sin datos de comparación.</div>';

    if (resumen.kpis.mapreduce_actores) {
      document.getElementById("filasMapReduce").textContent =
        `${numero(resumen.kpis.mapreduce_actores)} actores · ${iguales ? "idéntico a Spark" : "requiere revisión"}`;
    }
  } catch (error) {
    mostrarError("tabla3", error);
  }
}

alCargar(() => {
  cargarVerificacion();

  // Los botones de análisis usan el estilo .btn-pro; se marca el activo.
  document.querySelectorAll('#tabsAnalisis [data-bs-toggle="pill"]').forEach((boton) => {
    boton.addEventListener("shown.bs.tab", (evento) => {
      document
        .querySelectorAll('#tabsAnalisis [data-bs-toggle="pill"]')
        .forEach((otro) => otro.classList.remove("active"));
      evento.target.classList.add("active");
    });
  });
});
