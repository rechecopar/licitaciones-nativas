# -*- coding: utf-8 -*-
"""Esquema y acceso a la base de datos SQLite del agente."""
import sqlite3

from config import DB_PATH

ESQUEMA = """
CREATE TABLE IF NOT EXISTS licitaciones (
    codigo TEXT PRIMARY KEY,
    nombre TEXT,
    codigo_estado INTEGER,
    estado_nombre TEXT,
    categoria_estado TEXT,
    pertinencia TEXT,
    tipo_codigo TEXT,
    tipo_descripcion TEXT,
    descripcion TEXT,
    region TEXT,
    fecha_publicacion TEXT,
    fecha_cierre TEXT,
    monto_estimado REAL,
    moneda TEXT,
    nombre_organismo TEXT,
    url_acta TEXT,
    url TEXT,
    fecha_descubierta TEXT,
    fecha_ultima_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS estadisticas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    tipo_actualizacion TEXT,
    nuevas INTEGER,
    abiertas INTEGER,
    adjudicadas INTEGER,
    otras_cerradas INTEGER,
    total INTEGER
);
"""


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrar(conn):
    """Agrega columnas nuevas a una BD que ya existía antes de que existieran."""
    columnas = {row[1] for row in conn.execute("PRAGMA table_info(licitaciones)")}
    if "pertinencia" not in columnas:
        conn.execute("ALTER TABLE licitaciones ADD COLUMN pertinencia TEXT")
        conn.commit()


def inicializar():
    conn = conectar()
    conn.executescript(ESQUEMA)
    conn.commit()
    _migrar(conn)
    return conn
