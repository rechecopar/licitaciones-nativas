# -*- coding: utf-8 -*-
"""
Configuración central del agente de licitaciones - Vivero Los Tilos
"""
import os

# --- API Mercado Público ---
# El ticket NO se hardcodea acá (este archivo se sube a GitHub). Se busca,
# en orden: variable de entorno MERCADOPUBLICO_TICKET, o motor/config_local.py
# (ver config_local.py.example) — ambos quedan fuera del repo (.gitignore).
def _cargar_ticket():
    ticket = os.environ.get("MERCADOPUBLICO_TICKET")
    if ticket:
        return ticket
    try:
        from config_local import TICKET as ticket_local
        return ticket_local
    except ImportError:
        raise RuntimeError(
            "Falta el ticket de la API de Mercado Público.\n"
            "Opción 1: define la variable de entorno MERCADOPUBLICO_TICKET.\n"
            "Opción 2: copia motor/config_local.py.example a motor/config_local.py "
            "y pon ahí tu ticket (ese archivo no se sube a GitHub)."
        )


TICKET = _cargar_ticket()
API_BASE = "https://api.mercadopublico.cl/servicios/v1/publico"

# --- Rutas del proyecto ---
# motor/ (este archivo) vive un nivel adentro de la carpeta del proyecto.
MOTOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROYECTO_DIR = os.path.dirname(MOTOR_DIR)
DATA_DIR = os.path.join(MOTOR_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "licitaciones.db")
LOG_PATH = os.path.join(DATA_DIR, "actualizaciones.log")

# El HTML que se abre a diario queda en la raíz del proyecto, no en motor/.
DASHBOARD_HTML = os.path.join(PROYECTO_DIR, "index.html")

os.makedirs(DATA_DIR, exist_ok=True)

# Ventana de días hacia atrás que revisa cada actualización incremental.
# 10 días de margen cubre feriados/fines de semana sin dejar huecos.
DIAS_VENTANA_ACTUALIZACION = 10

# Estados de licitación (CodigoEstado de la API de Mercado Público)
ESTADOS = {
    5: ("Publicada", "ABIERTA"),
    6: ("Cerrada", "CERRADA"),
    7: ("Desierta", "CERRADA"),
    8: ("Adjudicada", "ADJUDICADA"),
    18: ("Revocada", "CERRADA"),
    19: ("Suspendida", "CERRADA"),
}

TIPOS_LICITACION = {
    'L1': 'Pública · menor a 100 UTM',
    'LE': 'Pública · 100-1.000 UTM',
    'LP': 'Pública · 1.000-2.000 UTM',
    'LQ': 'Pública · 2.000-5.000 UTM',
    'LR': 'Pública · mayor a 5.000 UTM',
    'E2': 'Privada · menor a 100 UTM',
    'CO': 'Privada · 100-1.000 UTM',
    'B2': 'Privada · 1.000-2.000 UTM',
    'H2': 'Privada · 2.000-5.000 UTM',
    'I2': 'Privada · mayor a 5.000 UTM',
    'LS': 'Servicios personales especializados',
}
