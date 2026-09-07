# -*- coding: utf-8 -*-
"""
Algoritmo de pertinencia: decide si una licitación tiene que ver con el
negocio de Ensenada Los Tilos (vivero + servicios de reforestación y
compensación de biodiversidad con especies nativas) y con qué tan fuerte
es la señal.

Devuelve una de tres cosas: 'ALTA', 'MEDIA' o None (no pertinente).

  ALTA   → coincide con algo específico del negocio: alguna de las especies
           que vende el vivero, "vivero"/"plantación"/"reforestación" en
           contexto de especies nativas o bosque nativo, compensación de
           biodiversidad/ambiental, o monitoreo de sobrevivencia de plantas.
  MEDIA  → toca temas cercanos (plantación, reforestación, vivero, manejo de
           bosque nativo, restauración/recuperación ecológica, arborización)
           pero sin una señal específica del negocio — vale la pena mirarla,
           pero puede ser de otro rubro (ornamentales, agrícola, etc.).

Se calibró sobre la base del algoritmo "v2" del proyecto anterior (Vivero
Carlos Saavedra, 500 licitaciones de muestra) y sobre el dossier de
Ensenada Los Tilos: especies que vende y servicios que presta.

Se evalúa sobre el NOMBRE de la licitación (única info disponible al
recorrer el listado diario de Mercado Público) y, cuando ya se descargó la
ficha completa, también sobre la DESCRIPCIÓN — lo que permite subir una
licitación de MEDIA a ALTA si el detalle menciona una especie puntual que
el nombre no dejaba ver.
"""
import re

# Si aparece cualquiera de estas palabras, la licitación queda descartada
# de entrada, aunque también contenga palabras "buenas".
PALABRAS_EXCLUYENTES = {
    # Médicas / salud
    'protesis', 'prótesis', 'medicamento', 'medicamentos', 'farmacia',
    'cirugia', 'cirugía', 'esterilizacion', 'esterilización',
    'implantacion de', 'implantación de', 'microchip', 'anestesia',
    'quirurgico', 'quirúrgico', 'hospital', 'pacientes operados',
    # Piscinas / agua
    'piscina', 'estanques de', 'tanques de agua',
    # Construcción / infraestructura
    'ascensores', 'escalera', 'fachada', 'techumbre', 'pavimento',
    'alcantarillado',
    # Arte / cultura
    'esculturas', 'murales', 'archivos', 'encuadernacion',
    'encuadernación', 'monumento publico', 'museo', 'teatro',
    # Informática
    'software', 'informatica', 'informática', 'datos', 'base de datos',
    # Transporte / maquinaria
    'camion', 'camión', 'vehiculo', 'vehículo', 'auto', 'maquinaria',
    'equipo electrico',
    # Otros
    'aseo', 'limpieza', 'pintura',
    # Dotación de personal / infraestructura sanitaria — para que "planta"
    # (palabra de contexto de las especies) no confunda "planta docente",
    # "planta de tratamiento", etc. con menciones a plantas de vivero.
    'planta docente', 'planta de personal', 'planta municipal',
    'dotacion de planta', 'dotación de planta', 'aumento de planta',
    'planta de tratamiento', 'planta de tratamiento de aguas',
}

# --- Especies que vende Ensenada Los Tilos (dossier) ---------------------
# Nombre común + nombre científico. OJO: varias de estas palabras son
# también nombres de comunas/localidades chilenas (Algarrobo y Maitencillo
# en Valparaíso, Peumo en O'Higgins, El Belloto en Quilpué, Guayacán en
# Coquimbo), así que la mención de la especie sola NO basta — abajo se
# exige además una palabra de contexto de planta/vivero/forestal.
ESPECIES_NATIVAS = [
    'quillay', 'quillaja saponaria',
    'peumo', 'cryptocarya alba',
    'belloto del norte', 'belloto', 'beilschmiedia miersii',
    'maiten', 'maitén', 'maytenus boaria',
    'algarrobo', 'prosopis chilensis',
    'guayacan', 'guayacán', 'porlieria chilensis',
]

# Palabras que confirman que una mención de especie es sobre la PLANTA y no
# sobre la comuna/localidad del mismo nombre.
CONTEXTO_PLANTA = [
    'planta', 'plantas', 'plantac', 'plantin', 'plantines', 'plántula',
    'plantula', 'vivero', 'arbol', 'árbol', 'forestal', 'especie',
    'especies', 'semilla', 'semillas', 'ejemplar', 'ejemplares', 'flora',
    'bosque', 'reforestacion', 'reforestación', 'silvicultura',
]

# --- Servicio de compensación de biodiversidad (dossier) ------------------
PALABRAS_COMPENSACION = [
    'compensacion de biodiversidad', 'compensación de biodiversidad',
    'compensacion ambiental', 'compensación ambiental',
    'compensacion de bosque nativo', 'compensación de bosque nativo',
    'plan de compensacion', 'plan de compensación',
    'medida de compensacion', 'medida de compensación',
]

# Monitoreo de sobrevivencia post-plantación: uno de los servicios del
# dossier (2 a 6 años de seguimiento) — señal muy específica del rubro.
PALABRAS_MONITOREO = [
    'monitoreo de sobrevivencia', 'seguimiento de sobrevivencia',
    'sobrevivencia de plantacion', 'sobrevivencia de plantación',
    'sobrevivencia de la plantacion', 'sobrevivencia de la plantación',
]

# Palabras "núcleo" del rubro plantación/reforestación/vivero.
PALABRAS_PLANTACION = [
    'plantacion', 'plantaciones', 'plantación',
    'reforestacion', 'reforestación',
    'plantines', 'plantin', 'plántulas', 'plantulas',
    'replante',
]

# Contexto que confirma que se trata de especies o bosque NATIVO (y no,
# por ejemplo, arbolado ornamental o especies exóticas/agrícolas).
CONTEXTO_NATIVO = [
    'nativo', 'nativos', 'nativa', 'nativas',
    'bosque', 'bosques',
    'ecologico', 'ecológica', 'ecológico', 'ecologica',
    'ecosistema', 'ecosistemas', 'biodiversidad',
]

# Palabras contextuales más débiles (regla heredada del algoritmo v2):
# solo cuentan si además aparece contexto nativo/bosque.
PALABRAS_CONTEXTUALES = [
    'restauracion', 'restauración', 'recuperacion', 'recuperación',
    'manejo', 'conservacion', 'conservación',
]

# Palabras complementarias: solas no dicen mucho, pero dos o más juntas
# (regla heredada del algoritmo v2) son señal de MEDIA pertinencia.
PALABRAS_COMPLEMENTARIAS = [
    'revegetacion', 'revegetación', 'arbolado', 'arborizado', 'arborizacion',
    'arborización', 'arboles', 'árboles', 'especies nativas',
    'plantas nativas', 'regeneracion', 'regeneración', 'flora', 'vivero',
]


def _tiene_alguna(texto, palabras):
    return any(p in texto for p in palabras)


_PATRONES_ESPECIES = [re.compile(r"\b" + re.escape(p) + r"\b") for p in ESPECIES_NATIVAS]


def _menciona_especie(texto):
    """Coincidencia por palabra completa: 'maiten' no debe matchear
    'maitencillo' (localidad de Puchuncaví)."""
    return any(p.search(texto) for p in _PATRONES_ESPECIES)


def clasificar(nombre: str, descripcion: str = "") -> str | None:
    """Clasifica una licitación en 'ALTA', 'MEDIA' o None (no pertinente).

    `nombre` es obligatorio (viene siempre); `descripcion` es opcional y se
    suma cuando ya se descargó la ficha completa, para afinar el resultado.
    """
    if not nombre:
        return None

    # La exclusión se evalúa SOLO contra el nombre. El nombre es corto y
    # deliberado; la descripción es un texto largo de bases administrativas
    # que casi siempre menciona de pasada alguna palabra "excluyente" sin que
    # eso signifique que la licitación no sea pertinente (p. ej. una
    # reforestación que menciona "camión" para el traslado de plantas, o un
    # vivero municipal que depende del "Departamento de Aseo y Ornato").
    if _tiene_alguna(nombre.lower(), PALABRAS_EXCLUYENTES):
        return None

    texto = f"{nombre} {descripcion or ''}".lower()

    # --- ALTA: señales específicas del negocio de Ensenada Los Tilos ----
    # La especie por sí sola no basta (varias son también nombres de comunas
    # chilenas) — se exige que además aparezca una palabra de contexto de
    # planta/vivero/forestal en el mismo texto.
    if _menciona_especie(texto) and _tiene_alguna(texto, CONTEXTO_PLANTA):
        return 'ALTA'

    if _tiene_alguna(texto, PALABRAS_COMPENSACION):
        return 'ALTA'

    if _tiene_alguna(texto, PALABRAS_MONITOREO):
        return 'ALTA'

    tiene_nativo = _tiene_alguna(texto, CONTEXTO_NATIVO)
    tiene_plantacion = _tiene_alguna(texto, PALABRAS_PLANTACION)

    if 'vivero' in texto and tiene_nativo:
        return 'ALTA'

    if tiene_plantacion and tiene_nativo:
        return 'ALTA'

    # --- MEDIA: temas cercanos, sin señal específica --------------------
    if tiene_plantacion:
        return 'MEDIA'

    if 'vivero' in texto:
        return 'MEDIA'

    tiene_contextual = _tiene_alguna(texto, PALABRAS_CONTEXTUALES)
    if tiene_contextual and tiene_nativo:
        return 'MEDIA'

    count_complementarias = sum(1 for p in PALABRAS_COMPLEMENTARIAS if p in texto)
    if count_complementarias >= 2:
        return 'MEDIA'

    if 'flora' in texto and tiene_nativo:
        return 'MEDIA'

    return None


def es_relevante(nombre: str) -> bool:
    """Compatibilidad con el código viejo: True si es ALTA o MEDIA."""
    return clasificar(nombre) is not None
