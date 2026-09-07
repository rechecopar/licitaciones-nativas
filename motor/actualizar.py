# -*- coding: utf-8 -*-
"""
ACTUALIZACIÓN DEL AGENTE DE LICITACIONES

Hace dos cosas cada vez que corre:
  1. Revisa los últimos N días publicados en Mercado Público, clasifica cada
     licitación nueva por nombre (ver clasificador.py) y guarda el detalle
     completo de las relevantes.
  2. Refresca el detalle de las licitaciones que en la BD figuran como
     "ABIERTA", por si cerraron, fueron adjudicadas o declaradas desiertas
     desde la última corrida.

Uso:
    python actualizar.py                 # ventana normal (config.DIAS_VENTANA_ACTUALIZACION)
    python actualizar.py --dias 60       # ventana más larga (carga inicial / backfill)
    python actualizar.py --generar-html  # además regenera el dashboard al final
"""
import argparse
import sys
from datetime import datetime, timedelta

# Evita que la consola de Windows (cp1252) truene al imprimir emojis/acentos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import api_mercadopublico as api
import clasificador
import db
from config import DIAS_VENTANA_ACTUALIZACION, ESTADOS, TIPOS_LICITACION


def _upsert(conn, detalle, fecha_descubierta=None):
    """Inserta o actualiza una licitación a partir de su ficha completa."""
    codigo = detalle.get("CodigoExterno", "")
    if not codigo:
        return False

    nombre = detalle.get("Nombre", "")
    codigo_estado = detalle.get("CodigoEstado")
    estado_nombre, categoria_estado = ESTADOS.get(codigo_estado, ("Desconocido", "DESCONOCIDO"))

    tipo_codigo = detalle.get("Tipo", "")
    tipo_descripcion = TIPOS_LICITACION.get(tipo_codigo, tipo_codigo or "-")

    descripcion = detalle.get("Descripcion", "") or ""

    # Reclasifica con nombre + descripción completa: puede subir de MEDIA a
    # ALTA si el detalle menciona una especie puntual que el nombre no dejaba ver.
    pertinencia = clasificador.clasificar(nombre, descripcion)

    fechas = detalle.get("Fechas") or {}
    fecha_publicacion = fechas.get("FechaPublicacion") if isinstance(fechas, dict) else None
    fecha_cierre = fechas.get("FechaCierre") if isinstance(fechas, dict) else None

    monto = detalle.get("MontoEstimado")
    moneda = detalle.get("Moneda", "")

    comprador = detalle.get("Comprador") or {}
    nombre_organismo = comprador.get("NombreOrganismo", "") if isinstance(comprador, dict) else ""
    region = comprador.get("RegionUnidad", "") if isinstance(comprador, dict) else ""

    adjudicacion = detalle.get("Adjudicacion") or {}
    url_acta = adjudicacion.get("UrlActa", "") if isinstance(adjudicacion, dict) else ""

    url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"
    ahora = datetime.now().isoformat()

    conn.execute("""
        INSERT INTO licitaciones
            (codigo, nombre, codigo_estado, estado_nombre, categoria_estado,
             pertinencia, tipo_codigo, tipo_descripcion, descripcion, region,
             fecha_publicacion, fecha_cierre, monto_estimado, moneda,
             nombre_organismo, url_acta, url, fecha_descubierta,
             fecha_ultima_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            nombre=excluded.nombre,
            codigo_estado=excluded.codigo_estado,
            estado_nombre=excluded.estado_nombre,
            categoria_estado=excluded.categoria_estado,
            pertinencia=excluded.pertinencia,
            tipo_codigo=excluded.tipo_codigo,
            tipo_descripcion=excluded.tipo_descripcion,
            descripcion=excluded.descripcion,
            region=excluded.region,
            fecha_publicacion=excluded.fecha_publicacion,
            fecha_cierre=excluded.fecha_cierre,
            monto_estimado=excluded.monto_estimado,
            moneda=excluded.moneda,
            nombre_organismo=excluded.nombre_organismo,
            url_acta=excluded.url_acta,
            url=excluded.url,
            fecha_ultima_actualizacion=excluded.fecha_ultima_actualizacion
    """, (codigo, nombre, codigo_estado, estado_nombre, categoria_estado,
          pertinencia, tipo_codigo, tipo_descripcion, descripcion, region,
          fecha_publicacion, fecha_cierre, monto, moneda, nombre_organismo,
          url_acta, url, fecha_descubierta or ahora, ahora))
    return True


def buscar_nuevas(conn, dias):
    print(f"\n[1/2] Buscando licitaciones nuevas en los últimos {dias} días...")

    c = conn.cursor()
    c.execute("SELECT codigo FROM licitaciones")
    codigos_conocidos = {row[0] for row in c.fetchall()}

    fecha_actual = datetime.now()
    fecha_inicio = fecha_actual - timedelta(days=dias)

    encontradas = 0
    nuevas_relevantes = 0
    fecha_it = fecha_inicio
    dia = 0
    total_dias = dias + 1

    while fecha_it <= fecha_actual:
        dia += 1
        fecha_str = fecha_it.strftime("%d%m%Y")
        print(f"  [{dia}/{total_dias}] {fecha_it.strftime('%Y-%m-%d')}...", end=" ", flush=True)

        listado = api.listar_por_fecha(fecha_str)
        encontradas += len(listado)
        nuevas_del_dia = 0

        for lic in listado:
            codigo = lic.get("CodigoExterno", "")
            nombre = lic.get("Nombre", "")
            if not codigo or codigo in codigos_conocidos:
                continue
            if clasificador.clasificar(nombre) is None:
                continue

            detalle = api.obtener_detalle(codigo)
            if detalle and _upsert(conn, detalle):
                codigos_conocidos.add(codigo)
                nuevas_del_dia += 1
                nuevas_relevantes += 1

        print(f"{len(listado)} publicadas, {nuevas_del_dia} nuevas relevantes")
        fecha_it += timedelta(days=1)

    conn.commit()
    print(f"\n  Total revisadas: {encontradas} | Nuevas relevantes: {nuevas_relevantes}")
    return nuevas_relevantes


def refrescar_abiertas(conn):
    print("\n[2/2] Refrescando estado de licitaciones marcadas como ABIERTA...")

    c = conn.cursor()
    c.execute("SELECT codigo FROM licitaciones WHERE categoria_estado = 'ABIERTA'")
    codigos = [row[0] for row in c.fetchall()]

    if not codigos:
        print("  No hay licitaciones abiertas registradas.")
        return 0

    cambios = 0
    fallidas = []
    for i, codigo in enumerate(codigos, 1):
        detalle = api.obtener_detalle(codigo)
        if detalle:
            estado_previo = c.execute(
                "SELECT categoria_estado FROM licitaciones WHERE codigo=?", (codigo,)
            ).fetchone()[0]
            if _upsert(conn, detalle):
                estado_nuevo = ESTADOS.get(detalle.get("CodigoEstado"), ("", "DESCONOCIDO"))[1]
                if estado_nuevo != estado_previo:
                    cambios += 1
        else:
            fallidas.append(codigo)
        if i % 20 == 0:
            print(f"  {i}/{len(codigos)}...")

    conn.commit()
    print(f"  Revisadas: {len(codigos)} | Cambios de estado: {cambios}")
    if fallidas:
        print(f"  AVISO: no se pudo consultar la API para {len(fallidas)} licitación(es), "
              f"quedaron con su último dato conocido: {', '.join(fallidas)}")
    return cambios


def guardar_estadisticas(conn, tipo_actualizacion, nuevas):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM licitaciones WHERE categoria_estado='ABIERTA'")
    abiertas = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM licitaciones WHERE categoria_estado='ADJUDICADA'")
    adjudicadas = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM licitaciones WHERE categoria_estado='CERRADA'")
    otras_cerradas = c.fetchone()[0]
    total = abiertas + adjudicadas + otras_cerradas

    c.execute("""
        INSERT INTO estadisticas
            (fecha, tipo_actualizacion, nuevas, abiertas, adjudicadas, otras_cerradas, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), tipo_actualizacion, nuevas, abiertas, adjudicadas, otras_cerradas, total))
    conn.commit()

    print("\n" + "=" * 70)
    print(f"🟢 Abiertas: {abiertas}  🔵 Adjudicadas: {adjudicadas}  🔴 Cerradas: {otras_cerradas}  |  Total: {total}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Actualiza la base de licitaciones relevantes.")
    parser.add_argument("--dias", type=int, default=DIAS_VENTANA_ACTUALIZACION,
                         help="Cuántos días hacia atrás revisar (por defecto: %(default)s)")
    parser.add_argument("--generar-html", action="store_true",
                         help="Regenerar dashboard/index.html al terminar")
    args = parser.parse_args()

    print("=" * 70)
    print(f"AGENTE DE LICITACIONES - VIVERO LOS TILOS")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = db.inicializar()

    nuevas = buscar_nuevas(conn, args.dias)
    refrescar_abiertas(conn)
    guardar_estadisticas(conn, "MANUAL" if "--dias" in sys.argv else "PROGRAMADA", nuevas)

    conn.close()

    if args.generar_html:
        import generar_dashboard
        generar_dashboard.main()


if __name__ == "__main__":
    main()
