# -*- coding: utf-8 -*-
"""
Reclasifica TODAS las licitaciones ya guardadas en la base de datos con la
versión actual de clasificador.py (nombre + descripción), sin volver a
consultar la API. Útil cada vez que se ajusta el algoritmo de pertinencia.

Uso:
    python reclasificar.py
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import clasificador
import db


def main():
    conn = db.inicializar()
    c = conn.cursor()

    c.execute("SELECT codigo, nombre, descripcion, pertinencia FROM licitaciones")
    filas = c.fetchall()

    conteo = {"ALTA": 0, "MEDIA": 0, "SIN_CLASIFICAR": 0}
    cambios = 0

    for codigo, nombre, descripcion, pertinencia_previa in filas:
        nueva = clasificador.clasificar(nombre, descripcion)
        etiqueta = nueva or "SIN_CLASIFICAR"
        conteo[etiqueta] = conteo.get(etiqueta, 0) + 1

        if nueva != pertinencia_previa:
            cambios += 1
            c.execute("UPDATE licitaciones SET pertinencia = ? WHERE codigo = ?", (nueva, codigo))

    conn.commit()
    conn.close()

    print(f"Reclasificadas {len(filas)} licitaciones ({cambios} cambiaron de categoría).")
    print(f"  ALTA pertinencia:  {conteo.get('ALTA', 0)}")
    print(f"  MEDIA pertinencia: {conteo.get('MEDIA', 0)}")
    print(f"  Sin clasificar (ya no matchean ninguna regla, quedan igual en la BD "
          f"pero puedes revisarlas o borrarlas a mano): {conteo.get('SIN_CLASIFICAR', 0)}")


if __name__ == "__main__":
    main()
