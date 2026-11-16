/* Reto 1 - Tabla 1, nulos y muestra del archivo limpio. */

function tamaño(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

async function cargarLimpieza() {
  try {
    const datos = await obtener("/limpieza");
    const { tabla1, metricas, nulos_por_columna, muestra, archivos, rango_fechas, columnas } = datos;

    if (archivos.original) {
      document.getElementById("detalleOriginal").textContent =
        `${numero(mostrarFilasOriginal(metricas))} filas · ${columnas.originales} columnas · ${tamaño(archivos.original.bytes)}`;
    }
    if (archivos.limpio) {
      document.getElementById("detalleLimpio").textContent =
        `${numero(metricas.registros_limpios)} filas · ${columnas.limpias} columnas · ${tamaño(archivos.limpio.bytes)}`;
    }
    document.getElementById("chipColumnas").textContent = `${columnas.limpias} columnas`;

    document.getElementById("tablaLimpieza").innerHTML = tabla1
      .map((fila, indice) => {
        const destacada = indice === tabla1.length - 1 || fila.indicador.includes("limpio");
        return `<tr>
            <td class="${destacada ? "strong" : ""}">${escapar(fila.indicador)}</td>
            <td class="num ${destacada ? "strong" : ""}">${numero(fila.valor)}</td>
          </tr>`;
      })
      .join("");

    pintarEmbudo(metricas);
    pintarFechas(rango_fechas, metricas);
    pintarNulos(nulos_por_columna);
    pintarMuestra(muestra);
  } catch (error) {
    mostrarError("tablaLimpieza", error);
  }
}

function mostrarFilasOriginal(metricas) {
  return (
    metricas.registros_originales ??
    (metricas.registros_limpios ?? 0) + (metricas.duplicados_filas ?? 0)
  );
}

function pintarEmbudo(metricas) {
  const contenedor = document.getElementById("embudoLimpieza");
  const original = mostrarFilasOriginal(metricas);
  const limpio = metricas.registros_limpios ?? 0;
  const eliminados =
    (metricas.duplicados_filas ?? 0) + (metricas.sin_show_id ?? 0) + (metricas.show_id_repetido ?? 0);
  const porcentaje = original ? ((limpio / original) * 100).toFixed(2) : "100.00";

  contenedor.innerHTML = `
    <div class="d-flex align-items-end gap-3 mb-3">
      <div style="flex:1">
        <div class="tiny muted mb-1">Original</div>
        <div style="height:14px;background:#e9edf5;border-radius:7px;overflow:hidden">
          <div style="height:100%;width:100%;background:#94a3b8"></div>
        </div>
        <div class="mt-1 strong">${numero(original)}</div>
      </div>
      <div style="flex:1">
        <div class="tiny muted mb-1">Limpio</div>
        <div style="height:14px;background:#e9edf5;border-radius:7px;overflow:hidden">
          <div style="height:100%;width:${porcentaje}%;background:${PALETA.teal}"></div>
        </div>
        <div class="mt-1 strong">${numero(limpio)}</div>
      </div>
    </div>
    <div class="d-flex justify-content-between tiny">
      <span class="muted">Registros descartados</span>
      <span class="chip ${eliminados === 0 ? "ok" : "amber"}">${numero(eliminados)}</span>
    </div>
    <div class="d-flex justify-content-between tiny mt-2">
      <span class="muted">Películas con duración numérica</span>
      <span class="strong">${numero(metricas.peliculas_con_duracion)}</span>
    </div>
    <div class="d-flex justify-content-between tiny mt-2">
      <span class="muted">Películas sin duración válida</span>
      <span class="chip ${metricas.peliculas_sin_duracion <= 3 ? "ok" : "amber"}">${numero(metricas.peliculas_sin_duracion)}</span>
    </div>`;
}

function pintarFechas(rango, metricas) {
  const contenedor = document.getElementById("panelFechas");
  const validas = metricas.fechas_validas ?? 0;
  const vacias = metricas.fechas_vacias ?? 0;
  const total = validas + vacias || 1;

  contenedor.innerHTML = `
    <div class="d-flex justify-content-between mb-2">
      <span class="tiny muted">Ingreso más antiguo</span>
      <span class="strong">${escapar(rango.minima || "—")}</span>
    </div>
    <div class="d-flex justify-content-between mb-2">
      <span class="tiny muted">Ingreso más reciente</span>
      <span class="strong">${escapar(rango.maxima || "—")}</span>
    </div>
    <div class="d-flex justify-content-between mb-3">
      <span class="tiny muted">Formato</span>
      <span class="chip outline">dd/mm/aaaa</span>
    </div>
    <div style="height:8px;background:#eef1f7;border-radius:6px;overflow:hidden" class="mb-2">
      <div style="height:100%;width:${(validas / total) * 100}%;background:${PALETA.teal}"></div>
    </div>
    <div class="tiny muted">
      ${numero(validas)} fechas interpretadas · ${numero(vacias)} vacías (se conservan vacías, no se inventan)
    </div>`;
}

function pintarNulos(nulos) {
  const contexto = document.getElementById("graficoNulos");
  if (!contexto) return;
  const ordenados = [...nulos].sort((a, b) => b.nulos - a.nulos);
  crearGrafico(contexto, {
    type: "bar",
    data: {
      labels: ordenados.map((fila) => fila.columna),
      datasets: [
        {
          label: "Valores nulos",
          data: ordenados.map((fila) => fila.nulos),
          backgroundColor: ordenados.map((fila) =>
            fila.nulos === 0 ? "rgba(15, 157, 143, .55)" : "rgba(229, 9, 20, .65)",
          ),
          borderRadius: 5,
          maxBarThickness: 34,
        },
      ],
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => {
              const fila = ordenados[item.dataIndex];
              return `${numero(fila.nulos)} nulos (${porcentaje(fila.porcentaje)})`;
            },
          },
        },
      },
      scales: {
        x: { ...ejeBase, grid: { display: false }, ticks: { ...ejeBase.ticks, maxRotation: 45, minRotation: 30 } },
        y: { ...ejeBase, beginAtZero: true },
      },
    },
  });
}

function pintarMuestra(muestra) {
  const cuerpo = document.getElementById("tablaMuestra");
  cuerpo.innerHTML = muestra
    .map(
      (fila) => `
        <tr>
          <td class="mono">${escapar(fila.show_id)}</td>
          <td><span class="chip ${fila.type === "Movie" ? "red" : "blue"}">${escapar(fila.type)}</span></td>
          <td class="strong">${escapar(fila.title)}</td>
          <td>${escapar(fila.country || "—")}</td>
          <td class="mono">${escapar(fila.date_added || "—")}</td>
          <td class="num">${fila.duration_min ?? "—"}</td>
        </tr>`,
    )
    .join("");
}

alCargar(cargarLimpieza);
