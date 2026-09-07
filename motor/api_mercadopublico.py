# -*- coding: utf-8 -*-
"""
Cliente delgado para la API pública de Mercado Público.
Documentación: ver Documentacion-API-Mercado-Publico-Licitaciones.pdf
(carpeta "Vivero Carlos Saavedra").
"""
import time
import requests

from config import API_BASE, TICKET

REINTENTOS = 5
ESPERA_ENTRE_REINTENTOS = 1.5  # se duplica en cada reintento (backoff)
ESPERA_ENTRE_LLAMADAS = 0.15


def _get(params, timeout=15):
    """GET con reintentos y backoff ante 403 (rate-limit) u otros errores transitorios."""
    url = f"{API_BASE}/licitaciones.json"
    params = {**params, "ticket": TICKET}

    espera = ESPERA_ENTRE_REINTENTOS
    for intento in range(REINTENTOS):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (403, 429) and intento < REINTENTOS - 1:
                time.sleep(espera)
                espera *= 2
                continue
            return None
        except requests.RequestException:
            if intento < REINTENTOS - 1:
                time.sleep(espera)
                espera *= 2
                continue
            return None
    return None


def listar_por_fecha(fecha_ddmmyyyy):
    """Lista (resumida) de licitaciones publicadas en una fecha dada."""
    data = _get({"fecha": fecha_ddmmyyyy})
    time.sleep(ESPERA_ENTRE_LLAMADAS)
    if data:
        return data.get("Listado", [])
    return []


def obtener_detalle(codigo):
    """Ficha completa de una licitación por su código externo."""
    data = _get({"codigo": codigo})
    time.sleep(ESPERA_ENTRE_LLAMADAS)
    if data and data.get("Listado"):
        return data["Listado"][0]
    return None
