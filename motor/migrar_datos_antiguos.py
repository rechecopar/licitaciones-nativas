# -*- coding: utf-8 -*-
"""
Script de migración ÚNICA: trae las licitaciones relevantes ya detectadas
por el proyecto anterior (Vivero Carlos Saavedra) a la nueva base de datos,
para no tener que volver a descargar todo desde la API.

Uso:
    python migrar_datos_antiguos.py
"""
import os
import sys
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import ESTADOS, TIPOS_LICITACION
import db

ORIGEN = (
    r"C:\Users\reche\Documents\Personal\Laboral\Vivero Carlos Saavedra"
    r"\licitaciones_vivero\vivero_licitaciones_actualizaciones"
    r"\vivero_licitaciones_actualizaciones\licitaciones_relevantes.db"
)


def main():
    if not os.path.exists(ORIGEN):
        print(f"No encontré la BD de origen en:\n  {ORIGEN}")
        print("Si ya migraste antes, no necesitas correr esto de nuevo.")
        return

    conn_origen = sqlite3.connect(ORIGEN)
    c_origen = conn_origen.cursor()
    c_origen.execute("""
        SELECT codigo, nombre, codigo_estado, estado_nombre, categoria_estado,
               tipo_codigo, tipo_descripcion, descripcion, fecha_cierre,
               monto_estimado, moneda, nombre_organismo, url_acta,
               fecha_descubierta, fecha_ultima_actualizacion
        FROM licitaciones_relevantes
    """)
    filas = c_origen.fetchall()
    conn_origen.close()

    conn = db.inicializar()
    c = conn.cursor()

    insertadas = 0
    for f in filas:
        (codigo, nombre, codigo_estado, estado_nombre, categoria_estado,
         tipo_codigo, tipo_descripcion, descripcion, fecha_cierre,
         monto_estimado, moneda, nombre_organismo, url_acta,
         fecha_descubierta, fecha_ultima_actualizacion) = f

        url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"

        c.execute("""
            INSERT OR IGNORE INTO licitaciones
            (codigo, nombre, codigo_estado, estado_nombre, categoria_estado,
             tipo_codigo, tipo_descripcion, descripcion, region,
             fecha_publicacion, fecha_cierre, monto_estimado, moneda,
             nombre_organismo, url_acta, url, fecha_descubierta,
             fecha_ultima_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nombre, codigo_estado, estado_nombre, categoria_estado,
              tipo_codigo, tipo_descripcion, descripcion, fecha_cierre,
              monto_estimado, moneda, nombre_organismo, url_acta, url,
              fecha_descubierta, fecha_ultima_actualizacion))
        insertadas += c.rowcount

    conn.commit()
    c.execute("SELECT COUNT(*) FROM licitaciones")
    total = c.fetchone()[0]
    conn.close()

    print(f"Migración completa: {insertadas} registros nuevos importados.")
    print(f"Total en la nueva base de datos: {total}")
    print("\nSugerencia: corre ahora 'python actualizar.py' para traer las")
    print("licitaciones publicadas desde la última actualización y refrescar")
    print("el estado de las que estaban abiertas.")


if __name__ == "__main__":
    main()
