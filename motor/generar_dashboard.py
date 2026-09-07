# -*- coding: utf-8 -*-
"""
Genera dashboard/index.html: un tablero autocontenido (HTML+CSS+JS, sin
dependencias externas) para revisar las licitaciones relevantes de un
vistazo, con buscador, filtros por estado y orden por columna.

Uso:
    python generar_dashboard.py
"""
import json
import sys
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import DB_PATH, DASHBOARD_HTML

CAMPOS = [
    "codigo", "nombre", "categoria_estado", "estado_nombre", "pertinencia",
    "tipo_descripcion", "nombre_organismo", "region",
    "fecha_publicacion", "fecha_cierre", "monto_estimado", "moneda",
    "descripcion", "url", "url_acta", "fecha_descubierta",
]


def cargar_licitaciones():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"SELECT {', '.join(CAMPOS)} FROM licitaciones ORDER BY fecha_publicacion DESC")
    filas = [dict(r) for r in c.fetchall()]
    conn.close()
    return filas


def main():
    filas = cargar_licitaciones()

    abiertas = sum(1 for f in filas if f["categoria_estado"] == "ABIERTA")
    adjudicadas = sum(1 for f in filas if f["categoria_estado"] == "ADJUDICADA")
    cerradas = sum(1 for f in filas if f["categoria_estado"] == "CERRADA")
    alta = sum(1 for f in filas if f["pertinencia"] == "ALTA")
    media = sum(1 for f in filas if f["pertinencia"] == "MEDIA")
    total = len(filas)

    data_json = json.dumps(filas, ensure_ascii=False)
    actualizado = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = HTML_TEMPLATE.format(
        data_json=data_json,
        total=total,
        abiertas=abiertas,
        adjudicadas=adjudicadas,
        cerradas=cerradas,
        alta=alta,
        media=media,
        actualizado=actualizado,
    )

    with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generado: {DASHBOARD_HTML}")
    print(f"  Alta pertinencia: {alta} | Media pertinencia: {media}")
    print(f"  Abiertas: {abiertas} | Adjudicadas: {adjudicadas} | Cerradas: {cerradas} | Total: {total}")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Licitaciones · Árboles Nativos — Vivero Los Tilos</title>
<style>
  :root {{
    --verde-oscuro: #1f4d3a;
    --verde: #2f6f4f;
    --verde-claro: #e7f3ec;
    --acento: #d98a2b;
    --texto: #1c2b24;
    --texto-suave: #5b6b62;
    --borde: #dfe8e2;
    --fondo: #f4f7f5;
    --blanco: #ffffff;
    --azul: #2b6cb0;
    --azul-claro: #e8f0fa;
    --rojo: #b0392b;
    --rojo-claro: #fbe9e6;
    --dorado: #a3760a;
    --dorado-claro: #fbf0d9;
    --gris: #6b7573;
    --gris-claro: #eef1ef;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--fondo); color: var(--texto);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  }}
  header {{
    background: linear-gradient(120deg, var(--verde-oscuro), var(--verde));
    color: white; padding: 28px 32px 22px;
  }}
  header h1 {{ margin: 0 0 4px; font-size: 1.6em; }}
  header p {{ margin: 0; opacity: .85; font-size: .92em; }}
  .stats {{ display: flex; gap: 14px; padding: 18px 32px 0; flex-wrap: wrap; }}
  .stat {{
    background: var(--blanco); border: 1px solid var(--borde); border-radius: 10px;
    padding: 12px 18px; min-width: 120px; box-shadow: 0 1px 2px rgba(0,0,0,.04);
  }}
  .stat .n {{ font-size: 1.5em; font-weight: 700; }}
  .stat .l {{ font-size: .78em; color: var(--texto-suave); text-transform: uppercase; letter-spacing: .04em; }}
  .stat.abiertas .n {{ color: var(--verde); }}
  .stat.adjudicadas .n {{ color: var(--azul); }}
  .stat.cerradas .n {{ color: var(--rojo); }}
  .stat.alta .n {{ color: var(--dorado); }}
  .stat.media .n {{ color: var(--azul); }}

  .toolbar {{
    display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
    padding: 18px 32px 0;
  }}
  .toolbar-fila {{
    display: flex; gap: 10px; flex-wrap: wrap; align-items: center; width: 100%;
  }}
  .toolbar-etiqueta {{
    font-size: .78em; font-weight: 700; color: var(--texto-suave);
    text-transform: uppercase; letter-spacing: .04em; margin-right: 2px;
  }}
  .toolbar input[type=text] {{
    flex: 1; min-width: 220px; padding: 10px 14px; border: 1px solid var(--borde);
    border-radius: 8px; font-size: .95em;
  }}
  .chip {{
    border: 1px solid var(--borde); background: var(--blanco); color: var(--texto-suave);
    padding: 8px 16px; border-radius: 999px; cursor: pointer; font-size: .88em; font-weight: 600;
    user-select: none;
  }}
  .chip.activo[data-estado="TODAS"] {{ background: var(--texto); color: white; border-color: var(--texto); }}
  .chip.activo[data-estado="ABIERTA"] {{ background: var(--verde); color: white; border-color: var(--verde); }}
  .chip.activo[data-estado="ADJUDICADA"] {{ background: var(--azul); color: white; border-color: var(--azul); }}
  .chip.activo[data-estado="CERRADA"] {{ background: var(--rojo); color: white; border-color: var(--rojo); }}
  .chip.activo[data-pert="TODAS"] {{ background: var(--texto); color: white; border-color: var(--texto); }}
  .chip.activo[data-pert="ALTA"] {{ background: var(--dorado); color: white; border-color: var(--dorado); }}
  .chip.activo[data-pert="MEDIA"] {{ background: var(--azul); color: white; border-color: var(--azul); }}
  .chip.activo[data-pert="SIN"] {{ background: var(--gris); color: white; border-color: var(--gris); }}

  main {{ padding: 18px 32px 40px; }}
  .tabla-wrap {{
    background: var(--blanco); border: 1px solid var(--borde); border-radius: 12px;
    overflow: auto; max-height: 72vh; box-shadow: 0 1px 3px rgba(0,0,0,.05);
  }}
  table {{ border-collapse: collapse; width: 100%; min-width: 1020px; }}
  thead th {{
    position: sticky; top: 0; background: var(--verde-oscuro); color: white;
    text-align: left; padding: 12px 14px; font-size: .82em; cursor: pointer; white-space: nowrap;
  }}
  thead th:hover {{ background: var(--verde); }}
  thead th .arrow {{ opacity: .6; font-size: .85em; margin-left: 4px; }}
  tbody td {{ padding: 11px 14px; border-bottom: 1px solid var(--borde); font-size: .88em; vertical-align: top; }}
  tbody tr:hover {{ background: var(--verde-claro); }}
  .badge {{
    display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: .76em; font-weight: 700;
  }}
  .badge.ABIERTA {{ background: var(--verde-claro); color: var(--verde-oscuro); }}
  .badge.ADJUDICADA {{ background: var(--azul-claro); color: var(--azul); }}
  .badge.CERRADA {{ background: var(--rojo-claro); color: var(--rojo); }}
  .badge.pert-ALTA {{ background: var(--dorado-claro); color: var(--dorado); }}
  .badge.pert-MEDIA {{ background: var(--azul-claro); color: var(--azul); }}
  .badge.pert-SIN {{ background: var(--gris-claro); color: var(--gris); }}
  .nombre {{ font-weight: 600; max-width: 340px; }}
  .nombre a {{ color: var(--texto); text-decoration: none; }}
  .nombre a:hover {{ color: var(--verde); text-decoration: underline; }}
  .organismo {{ color: var(--texto-suave); max-width: 200px; }}
  .monto {{ font-weight: 700; color: var(--verde-oscuro); white-space: nowrap; }}
  .fecha {{ color: var(--acento); font-weight: 600; white-space: nowrap; }}
  .desc {{
    max-width: 280px; color: var(--texto-suave); position: relative; cursor: help;
    border-bottom: 1px dotted var(--texto-suave);
  }}
  .desc .tip {{
    visibility: hidden; opacity: 0; position: absolute; z-index: 20; width: 340px;
    background: #24352c; color: #fff; padding: 12px 14px; border-radius: 8px; font-size: .85em;
    line-height: 1.45; top: 100%; left: 0; margin-top: 6px; transition: opacity .15s;
    box-shadow: 0 6px 16px rgba(0,0,0,.25);
  }}
  .desc:hover .tip {{ visibility: visible; opacity: 1; }}
  .sin-resultados {{ text-align: center; padding: 50px; color: var(--texto-suave); }}
  footer {{ text-align: center; color: var(--texto-suave); font-size: .82em; padding: 0 0 30px; }}
  a.btn {{
    display: inline-block; background: var(--verde); color: white; padding: 5px 12px;
    border-radius: 6px; text-decoration: none; font-size: .84em; font-weight: 600;
  }}
  a.btn:hover {{ background: var(--verde-oscuro); }}
</style>
</head>
<body>

<header>
  <h1>🌳 Licitaciones — Árboles y Especies Nativas</h1>
  <p>Agente de monitoreo de Mercado Público · Vivero Los Tilos</p>
</header>

<div class="stats">
  <div class="stat alta"><div class="n">{alta}</div><div class="l">⭐ Alta pertinencia</div></div>
  <div class="stat media"><div class="n">{media}</div><div class="l">✦ Media pertinencia</div></div>
  <div class="stat abiertas"><div class="n">{abiertas}</div><div class="l">Abiertas</div></div>
  <div class="stat adjudicadas"><div class="n">{adjudicadas}</div><div class="l">Adjudicadas</div></div>
  <div class="stat cerradas"><div class="n">{cerradas}</div><div class="l">Cerradas</div></div>
  <div class="stat"><div class="n">{total}</div><div class="l">Total</div></div>
</div>

<div class="toolbar">
  <div class="toolbar-fila">
    <input type="text" id="buscador" placeholder="Buscar por nombre, organismo, región o código…">
  </div>
  <div class="toolbar-fila">
    <span class="toolbar-etiqueta">Pertinencia</span>
    <span class="chip activo" data-pert="TODAS">Todas (Alta + Media)</span>
    <span class="chip" data-pert="ALTA">⭐ Alta</span>
    <span class="chip" data-pert="MEDIA">✦ Media</span>
    <span class="chip" data-pert="SIN">· Sin clasificar</span>
  </div>
  <div class="toolbar-fila">
    <span class="toolbar-etiqueta">Estado</span>
    <span class="chip activo" data-estado="TODAS">Todas</span>
    <span class="chip" data-estado="ABIERTA">🟢 Abiertas</span>
    <span class="chip" data-estado="ADJUDICADA">🔵 Adjudicadas</span>
    <span class="chip" data-estado="CERRADA">🔴 Cerradas</span>
  </div>
</div>

<main>
  <div class="tabla-wrap">
    <table id="tabla">
      <thead>
        <tr>
          <th data-col="pertinencia">Pertinencia<span class="arrow"></span></th>
          <th data-col="fecha_publicacion">Publicada<span class="arrow"></span></th>
          <th data-col="nombre">Licitación<span class="arrow"></span></th>
          <th data-col="nombre_organismo">Organismo<span class="arrow"></span></th>
          <th data-col="region">Región<span class="arrow"></span></th>
          <th data-col="categoria_estado">Estado<span class="arrow"></span></th>
          <th data-col="fecha_cierre">Cierre<span class="arrow"></span></th>
          <th data-col="monto_estimado">Monto<span class="arrow"></span></th>
          <th data-col="descripcion">Descripción<span class="arrow"></span></th>
        </tr>
      </thead>
      <tbody id="cuerpo"></tbody>
    </table>
  </div>
  <div id="vacio" class="sin-resultados" style="display:none">No hay licitaciones que coincidan con el filtro.</div>
</main>

<footer>Actualizado el {actualizado} · {total} licitaciones en la base de datos</footer>

<script>
const DATA = {data_json};

let filtroEstado = "TODAS";
let filtroPertinencia = "TODAS";
let texto = "";
let orden = {{ col: "pertinencia", dir: 1 }};

const PESO_PERTINENCIA = {{ "ALTA": 0, "MEDIA": 1 }};
function pesoPertinencia(p) {{
  return PESO_PERTINENCIA.hasOwnProperty(p) ? PESO_PERTINENCIA[p] : 2;
}}

function fmtFecha(s) {{
  if (!s) return "-";
  return s.substring(0, 10).split("-").reverse().join("/");
}}
function fmtMonto(m, moneda) {{
  if (m === null || m === undefined || m === "") return "-";
  const n = Number(m);
  if (!n) return "-";
  return "$" + n.toLocaleString("es-CL") + " " + (moneda || "");
}}
function escapeHtml(s) {{
  return (s || "").replace(/[&<>"']/g, c => ({{
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }}[c]));
}}
function iconoEstado(e) {{
  return e === "ABIERTA" ? "🟢" : e === "ADJUDICADA" ? "🔵" : "🔴";
}}
function etiquetaPertinencia(p) {{
  return p === "ALTA" ? "⭐ Alta" : p === "MEDIA" ? "✦ Media" : "· Sin clasificar";
}}
function clasePertinencia(p) {{
  return p === "ALTA" ? "pert-ALTA" : p === "MEDIA" ? "pert-MEDIA" : "pert-SIN";
}}

function aplicarFiltros() {{
  let filas = DATA.filter(f => filtroEstado === "TODAS" || f.categoria_estado === filtroEstado);
  filas = filas.filter(f => {{
    if (filtroPertinencia === "TODAS") return f.pertinencia === "ALTA" || f.pertinencia === "MEDIA";
    if (filtroPertinencia === "SIN") return !f.pertinencia;
    return f.pertinencia === filtroPertinencia;
  }});
  if (texto.trim()) {{
    const t = texto.toLowerCase();
    filas = filas.filter(f =>
      (f.nombre || "").toLowerCase().includes(t) ||
      (f.nombre_organismo || "").toLowerCase().includes(t) ||
      (f.region || "").toLowerCase().includes(t) ||
      (f.codigo || "").toLowerCase().includes(t)
    );
  }}
  filas.sort((a, b) => {{
    let va, vb;
    if (orden.col === "pertinencia") {{ va = pesoPertinencia(a.pertinencia); vb = pesoPertinencia(b.pertinencia); }}
    else if (orden.col === "monto_estimado") {{ va = a.monto_estimado || 0; vb = b.monto_estimado || 0; }}
    else {{ va = (a[orden.col] || "").toString(); vb = (b[orden.col] || "").toString(); }}
    if (va < vb) return -1 * orden.dir;
    if (va > vb) return 1 * orden.dir;
    // desempate: más reciente primero
    return (b.fecha_publicacion || "").localeCompare(a.fecha_publicacion || "");
  }});
  return filas;
}}

function render() {{
  const filas = aplicarFiltros();
  const cuerpo = document.getElementById("cuerpo");
  const vacio = document.getElementById("vacio");

  if (filas.length === 0) {{
    cuerpo.innerHTML = "";
    vacio.style.display = "block";
    return;
  }}
  vacio.style.display = "none";

  cuerpo.innerHTML = filas.map(f => {{
    const desc = f.descripcion || "";
    const descCorta = desc.length > 90 ? desc.substring(0, 90) + "…" : (desc || "-");
    const nombreCelda = f.url
      ? `<a href="${{f.url}}" target="_blank" rel="noopener">${{escapeHtml(f.nombre)}}</a>`
      : escapeHtml(f.nombre);
    const actaCelda = f.url_acta
      ? `<br><a class="btn" href="${{f.url_acta}}" target="_blank" rel="noopener">Ver acta</a>`
      : "";
    return `<tr>
      <td><span class="badge ${{clasePertinencia(f.pertinencia)}}">${{etiquetaPertinencia(f.pertinencia)}}</span></td>
      <td class="fecha">${{fmtFecha(f.fecha_publicacion)}}</td>
      <td class="nombre">${{nombreCelda}}<br><small style="color:var(--texto-suave)">${{f.codigo}}</small></td>
      <td class="organismo">${{escapeHtml(f.nombre_organismo)}}</td>
      <td class="organismo">${{escapeHtml(f.region)}}</td>
      <td><span class="badge ${{f.categoria_estado}}">${{iconoEstado(f.categoria_estado)}} ${{escapeHtml(f.estado_nombre)}}</span>${{actaCelda}}</td>
      <td class="fecha">${{fmtFecha(f.fecha_cierre)}}</td>
      <td class="monto">${{fmtMonto(f.monto_estimado, f.moneda)}}</td>
      <td class="desc">${{escapeHtml(descCorta)}}<span class="tip">${{escapeHtml(desc || "Sin descripción")}}</span></td>
    </tr>`;
  }}).join("");
}}

document.getElementById("buscador").addEventListener("input", e => {{
  texto = e.target.value;
  render();
}});

document.querySelectorAll(".chip[data-estado]").forEach(chip => {{
  chip.addEventListener("click", () => {{
    document.querySelectorAll(".chip[data-estado]").forEach(c => c.classList.remove("activo"));
    chip.classList.add("activo");
    filtroEstado = chip.dataset.estado;
    render();
  }});
}});

document.querySelectorAll(".chip[data-pert]").forEach(chip => {{
  chip.addEventListener("click", () => {{
    document.querySelectorAll(".chip[data-pert]").forEach(c => c.classList.remove("activo"));
    chip.classList.add("activo");
    filtroPertinencia = chip.dataset.pert;
    render();
  }});
}});

document.querySelectorAll("thead th").forEach(th => {{
  th.addEventListener("click", () => {{
    const col = th.dataset.col;
    if (orden.col === col) {{ orden.dir *= -1; }} else {{ orden = {{ col, dir: 1 }}; }}
    document.querySelectorAll("thead .arrow").forEach(a => a.textContent = "");
    th.querySelector(".arrow").textContent = orden.dir === 1 ? "▲" : "▼";
    render();
  }});
}});

render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
