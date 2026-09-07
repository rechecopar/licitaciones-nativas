# Agente de licitaciones — Árboles nativos (Vivero Los Tilos)

Monitorea la API pública de Mercado Público, detecta licitaciones
relacionadas con la compra/plantación de árboles y especies nativas, y las
deja listas para mirar en un solo archivo:

## 👉 [`index.html`](index.html) — ábrelo, es el tablero

Todo lo demás (código, base de datos) vive adentro de `motor/` y no hace
falta tocarlo salvo para actualizar los datos.

```
index.html          ← el tablero. Ábrelo en el navegador cuando quieras mirar.
motor/               ← el "motor" del agente
  config.py           Ticket de API, rutas, tablas de estados/tipos
  clasificador.py      Algoritmo de pertinencia (ALTA / MEDIA), calibrado con el dossier del vivero
  api_mercadopublico.py Cliente HTTP de la API de Mercado Público
  db.py                Esquema y conexión SQLite
  actualizar.py        Busca licitaciones nuevas + refresca las abiertas
  generar_dashboard.py Regenera index.html a partir de la base de datos
  reclasificar.py       Reaplica clasificador.py a lo ya guardado, sin llamar a la API
  migrar_datos_antiguos.py  Importó los datos del proyecto anterior (ya se usó, no hace falta correrlo de nuevo)
  ejecutar_actualizacion.bat  Para el Programador de tareas de Windows
  data/licitaciones.db  La base de datos
```

## Actualizar los datos

```bash
cd motor
python actualizar.py --generar-html
```

Esto revisa los últimos 10 días publicados en Mercado Público, agrega las
licitaciones relevantes nuevas, refresca el estado de las que estaban
"abiertas" (por si cerraron o fueron adjudicadas) y vuelve a generar
`index.html` en la raíz.

## Automatizar (Programador de tareas de Windows)

```bash
schtasks /create /tn "Licitaciones Vivero Los Tilos" /tr "\"C:\Users\reche\Documents\02_Laboral\Laboral\Vivero Los Tilos\licitaciones-nativas\motor\ejecutar_actualizacion.bat\"" /sc weekly /d FRI /st 18:00
```

(Opcional — pídele a Claude que lo registre cuando quieras.)

## El algoritmo de pertinencia (ALTA / MEDIA)

`motor/clasificador.py` clasifica cada licitación en **ALTA**, **MEDIA** o
descartada, calibrado contra el dossier de Ensenada Los Tilos (especies que
vende y servicios que presta):

- **ALTA** — señal específica del negocio: menciona alguna de las 6 especies
  que vende el vivero (Quillay, Peumo, Belloto del Norte, Maitén, Algarrobo,
  Guayacán, por nombre común o científico), "compensación de biodiversidad /
  ambiental", monitoreo de sobrevivencia post-plantación, o
  "vivero"/"plantación"/"reforestación" en contexto de bosque o especies
  nativas.
- **MEDIA** — toca el tema (plantación, reforestación, vivero, manejo de
  bosque nativo, restauración/recuperación ecológica, arborización) pero sin
  una señal puntual del negocio — puede ser de otro rubro (ornamentales,
  agrícola). Vale la pena mirarla, pero con más cautela que las ALTA.

El filtro inicial (para decidir si vale la pena descargar la ficha completa
de una licitación del día) solo puede mirar el **nombre**, que es lo único
que entrega el listado diario de la API. Una vez descargada la ficha
completa, se vuelve a clasificar con nombre + descripción — así una
licitación puede subir de MEDIA a ALTA si el detalle menciona una especie
puntual que el nombre no dejaba ver.

Si vuelves a ajustar `clasificador.py`, corre `python reclasificar.py` para
reaplicar el algoritmo nuevo a todo lo que ya está guardado, sin gastar
llamadas a la API.

## Próximos pasos (fase 2, aún no implementada)

- Procesar las licitaciones detectadas para extraer información útil de la
  ficha completa: cantidad de ejemplares, especies pedidas, plazos de
  mantención, garantías exigidas, etc.
- Notificaciones (correo/WhatsApp) cuando aparezca una licitación ALTA
  abierta nueva.
