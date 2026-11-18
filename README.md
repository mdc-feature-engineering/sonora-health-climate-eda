# Sonora Health-Climate EDA

> Condiciones ambientales y salud respiratoria en Hermosillo: análisis
> exploratorio de cómo el calor, el frío, la sequía y la calidad del aire se
> relacionan con las infecciones respiratorias agudas (IRA), y de si las zonas
> más marginadas de la ciudad cargan con más casos.

## Preguntas que buscamos responder

**Pregunta general**

> ¿Cómo inciden el calor, el frío, la sequía y la calidad del aire en la
> incidencia de enfermedades respiratorias en Hermosillo?

**Pregunta específica (vulnerabilidad diferencial)**

> ¿Las zonas más marginadas de Hermosillo son las más afectadas por esas
> condiciones ambientales?

El EDA cubre 2015–2020 a escala semanal y mensual para todo el municipio, y
baja a escala de **colonia** para la pregunta de marginación. Sus hallazgos
sirven para definir el producto de datos final (alerta climática → modelo
predictivo intra-urbano → planeación en salud pública). El método está en
[`docs/docs/protocolo_eda.md`](docs/docs/protocolo_eda.md) y los resultados en
[`reports/reporte_final.md`](reports/reporte_final.md).

## Público al que va dirigido

**Usuario principal: la Secretaría de Salud del Estado de Sonora**, en
particular sus áreas de **vigilancia epidemiológica** y de **planeación de
servicios** (y la Jurisdicción Sanitaria que cubre Hermosillo). Son quienes
generan los datos de IRA, deciden dónde reforzar consultas, insumos y personal
en temporada alta, y pueden emitir avisos preventivos a la población.

Otros usuarios que también pueden aprovechar el análisis:

| Institución | Para qué le sirve |
|-------------|-------------------|
| Instituciones de seguridad social (IMSS, ISSSTE, ISSSTESON) | Anticipar la demanda de consulta por IRA en sus unidades de Hermosillo. |
| Protección Civil (estatal y municipal) | Coordinar avisos ante olas de calor, frío, sequía o mala calidad del aire. |
| Ayuntamiento de Hermosillo (Desarrollo Social, Salud Municipal) | Priorizar colonias de alta marginación en campañas y programas. |

## Fuentes de datos

| Capa | Fuente | Qué nos ofrece | Cobertura usada |
|------|--------|----------------|-----------------|
| Enfermedades respiratorias (variable respuesta) | Secretaría de Salud / DGIS, SINAIS (formato SUIVE) | Casos confirmados de IRA por semana epidemiológica, municipio, sexo, grupo de edad y unidad médica (CLUES). Es la medida de "cuánta gente se enfermó". | Sonora 2010–2020 (Hermosillo 2015–2020 en el panel) |
| Unidades de salud | Catálogo CLUES (SS/DGIS) | Ubicación (latitud/longitud) de cada clínica u hospital, para saber en qué colonia está cada unidad que reporta IRA. | Catálogo vigente |
| Temperatura (estaciones) | CONAGUA / Servicio Meteorológico Nacional | Temperatura media, máxima y mínima mensual por estación meteorológica. | 2015–2020 |
| Temperatura diaria y humedad | Open-Meteo (Archive API) | Temperatura máxima y mínima y humedad relativa **diarias** de Hermosillo; con ellas se calculan olas de calor, frío e índice de calor. | 1991–2020 (1991–2014 como referencia climática) |
| Sequía | Monitor de Sequía de México (CONAGUA/SMN) | Categoría de sequía de cada municipio cada quincena (de "anormalmente seco" a "sequía excepcional"). | 2015–2020 |
| Calidad del aire | RUOA-UNAM, observatorio ERNO (Hermosillo) | Concentraciones horarias de PM2.5, PM10 y ozono; con ellas se calcula el Índice AIRE Y SALUD (NOM-172-SEMARNAT-2019). | 2015–2020 (PM2.5 sin datos válidos desde jun-2018) |
| Marginación municipal | CONAPO | Índice y grado de marginación de cada municipio (educación, vivienda, ingresos). Un solo valor para todo Hermosillo. | 2015 y 2020 |
| Marginación por colonia | CONAPO (cartografía urbana 2020) | Polígono, índice, grado de marginación y población de cada colonia; permite comparar zonas **dentro** de la ciudad. | 2020 |

Enlaces, fechas de descarga y detalles de cada fuente:
[`references/fuentes.md`](references/fuentes.md). Diccionarios de datos por
fuente en [`references/`](references/).

## Estructura del proyecto

```
├── data                      <- No se sube a GitHub; se genera con los pasos de abajo
│   ├── raw                   <- Datos crudos tal como se descargan
│   ├── external              <- Extractos de terceros (catálogo CLUES de Hermosillo)
│   ├── interim               <- Datos intermedios ya limpios
│   └── processed             <- Tablas tidy por capa y paneles integrados
├── docs                      <- Protocolo del EDA y catálogo de variables del panel
├── notebooks
│   ├── 00_auto_eda           <- Reporte automático con ydata-profiling
│   ├── 01_ingesta            <- Una libreta por fuente: descarga y revisión de los datos crudos
│   ├── 02_procesamiento      <- Una libreta por capa: limpieza y agregación a tablas tidy
│   └── 03_eda                <- Panel integrado (3.0) y análisis (3.1–3.6)
├── references                <- Fuentes y diccionarios de datos
├── reports                   <- Reporte final, presentación y figuras
├── sonora_health_climate_eda <- Paquete de Python del proyecto
│   ├── config.py             <- Rutas, URLs de las fuentes y años del análisis
│   ├── dataset.py            <- Comandos de descarga (pipeline de ingesta)
│   ├── aire.py               <- Calidad del aire: horario → diario → semanal y mensual
│   ├── panel.py              <- Transformaciones de cada capa y armado de los paneles
│   ├── processing.py         <- Procesamiento de salud (lo usa 2.5)
│   ├── spatial.py            <- Cruces espaciales (unidades de salud → colonias)
│   └── schemas.py, utils.py, features.py, plots.py
├── requirements.txt
└── pyproject.toml
```

El índice completo de libretas está en [`notebooks/README.md`](notebooks/README.md).

## Cómo reproducir el análisis, paso a paso

Todos los comandos se corren **desde la raíz del proyecto** (la carpeta que
contiene este README).

### Paso 1. Clonar el repositorio

```bash
git clone https://github.com/mdc-feature-engineering/sonora-health-climate-eda.git
cd sonora-health-climate-eda
```

### Paso 2. Crear el entorno virtual e instalar dependencias

Se necesita **Python 3.13** (`ydata-profiling` todavía no funciona con 3.14).

**Opción A — con `uv` (recomendada, más rápida):**

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
```

**Opción B — con `venv` y `pip`** (en Windows el ejecutable es `py -3.13`; en
Mac/Linux, `python3.13`):

```bash
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Activar el entorno** para que `python` sea el del proyecto:

| Sistema | Comando |
|---------|---------|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (cmd) | `.venv\Scripts\activate.bat` |
| Mac/Linux | `source .venv/bin/activate` |

Si PowerShell no permite ejecutar `Activate.ps1`, usa directamente
`.venv\Scripts\python.exe` en lugar de `python` en los comandos de abajo.

**Para abrir las libretas:** en VS Code (extensión Jupyter) elige el kernel
`.venv`. Si prefieres Jupyter en el navegador, instálalo en el entorno con
`pip install jupyterlab` y ábrelo con `jupyter lab`.

Cada vez que un `git pull` cambie `requirements.txt`, vuelve a correr la
instalación.

### Paso 3. Descargar los datos públicos

```bash
python -m sonora_health_climate_eda.dataset data-ingestion-pipeline
```

Tarda unos 5 minutos (hace pausas para no saturar los servidores) y deja todo
en `data/raw/`:

| Capa | Comando individual | Se guarda en |
|------|--------------------|--------------|
| Sequía (y tablas tidy por año) | `download-drought-data` | `data/raw/MunicipiosSequia.xlsx` → `data/interim/sonora_sequia/` |
| Temperatura media SMN | `download-temperature-data` | `data/raw/temperatura/temperatura_AAAA/` |
| Temperatura máxima y mínima SMN | `download-temperature-extremes-data` | `data/raw/temperatura/temperatura_{max,min}_AAAA/` |
| Open-Meteo diario | `download-openmeteo-data` | `data/raw/openmeteo_hermosillo_daily_1991_2020.csv` |
| Calidad del aire RUOA | `download-air-quality-data` | `data/raw/aire/ruoa_erno/` |
| Catálogo CLUES | `download-clues-data` | `data/raw/clues/` → `data/external/clues/` |

Si una capa falla, se puede repetir solo esa con
`python -m sonora_health_climate_eda.dataset <comando-individual>`.

### Paso 4. Copiar el archivo de salud (no es público)

Los casos de IRA no se descargan: pídelos al equipo y cópialos con este nombre
exacto:

```
data/raw/salud/enf_resp_sonora_2010_2020.csv
```

Sin este archivo corren todas las libretas de ingesta y procesamiento excepto
`2.5`, pero no se puede armar el panel ni correr el EDA (`3.0`–`3.6`).

> Si el CSV de IRA ya estaba al correr el paso 3, `download-clues-data` deja en
> `data/external/clues/clues_hermosillo_ira.csv` solo las 103 unidades que
> reportaron IRA. Si lo copiaste después, vuelve a correr
> `python -m sonora_health_climate_eda.dataset download-clues-data --overwrite`.

### Paso 5. Ingesta de marginación (municipal y por colonia)

Abre y ejecuta completa la libreta
`notebooks/01_ingesta/1.3-indice_-marginacion.ipynb`. Descarga los Excel de
CONAPO y la cartografía por colonia, y deja en `data/interim/marginacion/`:

- `marginacion_municipal_{2015,2020}.csv` — municipios de Sonora.
- `colonias_marginacion_hermosillo.gpkg` — las colonias de Hermosillo con su
  índice y población.

Los servidores de CONAPO a veces bloquean las descargas automáticas. Si la
libreta falla, el mensaje de error dice qué archivo bajar con el navegador y
en qué carpeta dejarlo; después se vuelve a correr la celda.

Las demás libretas de `01_ingesta/` (1.0, 1.1, 1.2, 1.4 y 1.5) son opcionales:
documentan y revisan lo que ya descargó el paso 3.

### Paso 6. Procesamiento a tablas tidy

En este paso cada capa se limpia y se agrega a **tablas tidy**: una fila por
periodo (semana epidemiológica o mes) y una columna por variable, listas para
unirse por fecha.

**6.1 Calidad del aire** (de horario a diario, semanal y mensual):

```bash
python -m sonora_health_climate_eda.aire horario
python -m sonora_health_climate_eda.aire diario
python -m sonora_health_climate_eda.aire semanal
python -m sonora_health_climate_eda.aire mensual
```

**6.2 Libretas de `notebooks/02_procesamiento/`**, en este orden. Cada una
guarda su tabla en `data/processed/` en la celda "Guardar salida":

| Libreta | Tabla tidy que genera |
|---------|-----------------------|
| `2.0-procesamiento-temperatura-smn` | `climate_hermosillo.parquet` (mensual) |
| `2.2-procesamiento-sequia` | `drought_hermosillo.parquet` (mensual) y `drought_hermosillo_weekly.parquet` |
| `2.3-procesamiento-marginacion` | `marginacion_hermosillo.parquet` (mensual, interpolada entre 2015 y 2020) |
| `2.4-procesamiento-calidad-aire` | `aire/` (semanal y mensual; revisa lo que hizo el paso 6.1) |
| `2.5-procesamiento-salud-ira` | `health_ira_monthly.parquet` y `health_ira_weekly.parquet` |
| `2.1-procesamiento-calor-openmeteo` | `openmeteo_hermosillo_monthly.parquet` y `openmeteo_hermosillo_weekly.parquet` |

`2.1` va al final porque una de sus celdas compara contra los casos de IRA que
genera `2.5`.

**6.3 Revisar el resultado:** `notebooks/01_ingesta/1.6-resumen-ingesta.ipynb`
resume la ingesta: para cada fuente cuenta las filas que llegaron, las valida
con su esquema pydantic (`sonora_health_climate_eda/schemas.py`) y confirma
que la tabla procesada de Hermosillo tenga los 72 meses de 2015–2020.
`notebooks/02_procesamiento/2.6-resumen-procesamiento.ipynb` resume en una
sola libreta qué se hizo en cada capa y las decisiones principales.

### Paso 7. Panel integrado y EDA

1. `notebooks/03_eda/3.0-integracion-espacial.ipynb` une todas las capas en
   los paneles de Hermosillo 2015–2020:
   - `data/processed/panel_hermosillo.parquet` — mensual (72 meses).
   - `data/processed/panel_hermosillo_semanal.parquet` — semanal (313 semanas).
   - `panel_eda.parquet` y `panel_eda_semanal.parquet` — versiones reducidas
     para el EDA.

   Las columnas de cada panel están descritas en
   [`docs/docs/catalogo_datos_panel.md`](docs/docs/catalogo_datos_panel.md).
2. Libretas `3.1` a `3.5`: datos faltantes, outliers, relaciones, correlación
   y reducción de dimensionalidad.
3. `3.6-analisis-marginacion-urbana`: marginación por colonia contra carga de
   IRA (requiere el paso 5).
4. Opcional: `00_auto_eda/0.0-auto-eda.ipynb` genera el reporte automático
   `reports/auto_eda_report.html`.

### Atajos

- `make data` corre el paso 3 (requiere `make`, que no viene en Windows, y
  `pip` en el entorno).
- `make lint` / `make format` revisan y dan formato al código con `ruff`.
- Los años del análisis se cambian en `sonora_health_climate_eda/config.py`
  (`PANEL_START_YEAR`, `PANEL_END_YEAR`).
