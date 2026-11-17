# Sonora Health-Climate EDA

> Condiciones ambientales y salud respiratoria en Hermosillo — análisis exploratorio espacio-temporal de la vulnerabilidad socioeconómica y climática ante enfermedades respiratorias.

## Preguntas de investigación

**Pregunta general:**

> ¿Cómo inciden el calor, el frío, la sequía y la calidad del aire en la incidencia de enfermedades respiratorias en Hermosillo?

**Pregunta específica (hipótesis de vulnerabilidad diferencial):**

> ¿Las zonas más marginadas de Hermosillo son las más afectadas por esas condiciones ambientales?


Objetivo del EDA: explorar la relación exposición–morbilidad para definir alcances del producto de datos final (alerta climática → modelo predictivo a nivel intra-urbano (colonia) → planeación en salud pública). Detalle en [`docs/docs/protocolo_eda.md`](docs/docs/protocolo_eda.md).

**Público destinatario del producto de datos (tablero):** equipos de planeación y vigilancia en salud pública de Sonora (Secretaría de Salud/DGIS y autoridades municipales de Hermosillo) y protección civil, para anticipar olas de calor, sequía y episodios de contaminación y priorizar las zonas más marginadas.

## Capas de datos

| # | Capa | Fuente | Estado |
|---|------|--------|--------|
| 1 | Índice de marginación | CONAPO / INEGI (municipal 2010/2015/2020; colonia urbana 2020 con geometría, índice y población) | Municipal: se descarga con el notebook `1.3` (no con el pipeline). Colonia: integrada en `3.6` |
| 2 | Temperatura y clima | CONAGUA/SMN (resúmenes mensuales por estación) + Open-Meteo (diario) | Se descarga con el pipeline — 2015–2020 |
| 3 | Índice de sequía | Monitor de Sequía SMN/CONAGUA (quincenal → mensual y semanal) | Se descarga con el pipeline — 2015–2020 |
| 4 | Calidad del aire (PM2.5, PM10, O3) | RUOA-UNAM, observatorio ERNO Hermosillo (horario → diario → semanal y mensual) | Se descarga con el pipeline — 2015–2020 (PM2.5 sin datos válidos desde jun-2018; jun–nov 2018 sin ningún contaminante) |
| 5 | Enfermedades respiratorias | Secretaría de Salud/DGIS (SINAIS, formato SUIVE) — casos confirmados de IRA, semanal × municipio × sexo × edad × clínica (CLUES), 2010–2020 | **Archivo manual** (no se descarga): ver [Datos que se consiguen a mano](#2-datos-que-se-consiguen-a-mano) |

### Panel integrado

Dos paneles de Hermosillo, 2015–2020, con las 5 capas:

- `data/processed/panel_hermosillo.parquet`: mensual, 72 meses × 66 columnas.
- `data/processed/panel_hermosillo_semanal.parquet`: semanal (semana epidemiológica, domingo a sábado), 313 semanas × 62 columnas.

Qué trae cada capa, sus columnas y lo que hay que tomar en cuenta: [`catalogo_datos_panel.md`](docs/docs/catalogo_datos_panel.md).

- **Clima:** datos diarios de Open-Meteo agregados por mes (olas de calor ≥35 °C y p95, humedad relativa).
- **Flags:** `mes_ola_calor_p95`, `mes_sequia`, `mes_ola_calor_p95_y_sequia`.
- **Salud:** un mes suma 4 o 5 semanas (`n_semanas`); `casos_ira_por_semana` permite comparar meses.
- **Cómo se genera:** cada notebook de `02_procesamiento/` guarda su capa en `data/processed/` y `panel.build_panel_monthly()` / `build_panel_weekly()` las une (panel semanal: `panel_hermosillo_semanal.parquet`, 313 semanas); ver [`3.0-integracion-espacial.ipynb`](notebooks/03_eda/3.0-integracion-espacial.ipynb). Los años se ajustan en `config.py`.
- **Calidad del aire:** datasets limpios semanal (semana epidemiológica) y mensual en `data/processed/aire/` (notebooks 1.4 y 2.4; serie diaria en `data/interim/aire/`). Los huecos de hasta 2 semanas (1 mes) se interpolan y quedan marcados en `*_interpolado`; los huecos largos quedan en NaN. Cada día se clasifica con el Índice AIRE Y SALUD (bandas de la NOM-172-SEMARNAT-2019), y las tablas semanal y mensual guardan la categoría del peor día y los días Aceptable o peor.

### Alcance actual y próximos pasos

El proyecto cubre la ingesta y el procesamiento de las capas, los paneles mensual y semanal integrados, el EDA completo (faltantes, outliers, relaciones, correlación, PCA/t-SNE) y el análisis de marginación por colonia (`3.6`). El GLM y el análisis de rezagos formal (CCF) quedan como **plan**; ver la sección 3 de [`protocolo_eda.md`](docs/docs/protocolo_eda.md).

## Project Organization

```
├── LICENSE
├── Makefile              <- Comandos de conveniencia (make data, make lint)
├── README.md
├── data
│   ├── external          <- Datos de terceros
│   ├── interim           <- Datos intermedios transformados
│   ├── processed         <- Panel integrado
│   └── raw               <- Datos crudos inmutables
│
├── docs                  <- Documentación mkdocs + protocolo_eda.md
├── models                <- Modelos entrenados y resultados
├── notebooks
│   ├── 00_auto_eda      <- Auto-EDA con ydata-profiling (reporte HTML)
│   ├── 01_ingesta        <- Descarga/limpieza de las capas (1.3 descarga la marginación)
│   ├── 02_procesamiento  <- Revisión y agregación mensual/semanal por capa; guardan cada capa en data/processed/
│   └── 03_eda            <- 3.0 panel integrado; 3.1–3.6 faltantes, outliers, relaciones, correlación, PCA/t-SNE, marginación por colonia
│
├── pyproject.toml
├── references            <- Diccionarios de datos por fuente
│   ├── fuentes.md        <- Fuentes primarias: descripción, enlaces y fechas de descarga
│   ├── climate/          <- CONAGUA (temperatura, sequía)
│   ├── marginacion/      <- Índice de marginación CONAPO
│   ├── aire/             <- RUOA-UNAM (PM2.5, PM10, O3)
│   └── salud/            <- Diccionario de casos confirmados de IRA (SS/DGIS, SINAIS/SUIVE)
├── reports
│   ├── figures           <- Gráficos generados
│   ├── auto_eda_report.html  <- Reporte auto-EDA (ydata-profiling, una vez ejecutado)
│   └── reporte_final_template.md  <- Template del reporte final (rúbrica)
├── requirements.txt
└── sonora_health_climate_eda   <- Paquete Python del proyecto
    ├── config.py         <- Rutas, URLs de fuentes, constantes del protocolo
    ├── dataset.py        <- Comandos typer de descarga/ingesta
    ├── panel.py          <- Funciones de cada capa y paneles integrados mensual y semanal
    ├── aire.py           <- Calidad del aire: horario → diario → semanal y mensual (comandos typer)
    ├── processing.py     <- Funciones del procesamiento de salud (notebook 2.5)
    ├── schemas.py        <- Esquemas pydantic de los datasets
    ├── utils.py          <- Generación de diccionarios de datos
    ├── spatial.py        <- Spatial joins puntos → polígonos (CLUES → colonias), filtros INEGI
    ├── features.py       <- Ingeniería de características
    ├── plots.py          <- Visualizaciones
    └── modeling/         <- Entrenamiento/predicción (stub)
```

## Setup

Requiere **Python 3.13** (`ydata-profiling` no soporta 3.14). Todos los comandos se
corren desde la raíz del proyecto.

**Opción A — uv (recomendada).** `uv` crea el entorno e instala sin necesitar `pip`:

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements.txt
```

**Opción B — venv + pip.** En Windows el comando de Python 3.13 es `py -3.13`; en
Mac/Linux, `python3.13`:

```bash
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Activar el entorno** (para que `python` sea el del proyecto):

| Sistema | Comando |
|---------|---------|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (cmd) | `.venv\Scripts\activate.bat` |
| Mac/Linux | `source .venv/bin/activate` |

Si PowerShell no deja correr `Activate.ps1`, se puede usar el Python del entorno sin
activarlo: `.venv\Scripts\python.exe` en lugar de `python`. En VS Code, elegir el
kernel `.venv` en los notebooks.

Para mantener el entorno igual al del equipo, después de cada `git pull` que cambie
`requirements.txt` volver a correr la instalación.

## Uso: de cero al panel

Probado desde un clon limpio (nov-2026): con los mismos datos de entrada, el panel
sale idéntico.

### 1. Descargar los datos públicos

```bash
python -m sonora_health_climate_eda.dataset data-ingestion-pipeline
```

Tarda ~5 minutos (hace pausas para no saturar los servidores) y descarga:

| Capa | Comando individual | Se guarda en |
|------|--------------------|--------------|
| Sequía (y tablas tidy por año) | `download-drought-data` | `data/raw/MunicipiosSequia.xlsx` → `data/interim/sonora_sequia/` |
| Temperatura media SMN | `download-temperature-data` | `data/raw/temperatura/temperatura_AAAA/` |
| Temperatura máxima y mínima SMN | `download-temperature-extremes-data` | `data/raw/temperatura/temperatura_{max,min}_AAAA/` |
| Open-Meteo diario | `download-openmeteo-data` | `data/raw/openmeteo_hermosillo_daily_1991_2020.csv` |
| Calidad del aire RUOA | `download-air-quality-data` | `data/raw/aire/ruoa_erno/` |
| Catálogo CLUES (DGIS) | `download-clues-data` | `data/raw/clues/` → extracto en `data/external/clues/` |

La descripción de cada fuente, su enlace y la fecha en que se descargó está en
[`references/fuentes.md`](references/fuentes.md).

Cada comando individual se corre como
`python -m sonora_health_climate_eda.dataset <comando>`. La marginación
municipal ya está en `data/interim/` y la salud se consigue a mano: esas
capas se obtienen en los pasos 2 y 3.

Si tienes carpetas `data/raw/temperatura_AAAA/` de una descarga anterior (antes de
nov-2026), muévelas dentro de `data/raw/temperatura/`: el código ya no las busca en
`data/raw/`.

`make data` hace lo mismo, pero requiere `make` (no viene en Windows) y `pip` en el
entorno (un entorno creado con `uv` no lo trae).

### 2. Datos que se consiguen a mano

No es público ni se descarga con el pipeline; pedirlo al equipo y copiarlo con
este nombre exacto (`data/` no se sube a GitHub):

| Archivo | Qué es | Lo usa |
|---------|--------|--------|
| `data/raw/salud/enf_resp_sonora_2010_2020.csv` | Casos confirmados de IRA de la Secretaría de Salud | `2.5` |

El extracto `data/external/clues/clues_hermosillo_ira.csv` (las 103 unidades que
reportaron IRA en Hermosillo) lo genera `download-clues-data`: si el CSV de IRA
ya está, lo cruza contra el catálogo; si no, el extracto trae todos los
establecimientos de Hermosillo y el notebook 2.5 funciona igual.

> **Fuente:** SS/DGIS, SINAIS (datos en formato SUIVE), 2010–2020. El extracto CLUES
> proviene del catálogo oficial DGIS/SSA (`ESTABLECIMIENTO_SALUD_202610.xlsx`).

Sin el CSV de IRA corren todos los notebooks de ingesta y procesamiento excepto
`2.5`; tampoco se puede armar el panel (`3.0`) ni correr los notebooks de EDA
que lo usan (`3.1`–`3.5`).

### 3. Procesar las capas

En este orden:

1. **Marginación:** correr `notebooks/01_ingesta/1.3-indice_-marginacion.ipynb` (descarga
   los Excel de CONAPO y deja los CSV en `data/interim/marginacion/`).
2. **Calidad del aire:**

   ```bash
   python -m sonora_health_climate_eda.aire horario
   python -m sonora_health_climate_eda.aire diario
   python -m sonora_health_climate_eda.aire semanal
   python -m sonora_health_climate_eda.aire mensual
   ```

   El primero arma la tabla horaria (lo mismo que `01_ingesta/1.4-calidad-aire.ipynb`);
   los otros tres también los hace `02_procesamiento/2.4-procesamiento-calidad-aire.ipynb`.
3. **Notebooks `02_procesamiento/` 2.0 a 2.5:** cada uno guarda su capa en
   `data/processed/` en la celda "Guardar salida".
4. **Panel:** `notebooks/03_eda/3.0-integracion-espacial.ipynb` arma los dos paneles y
   los paneles reducidos para la EDA (`panel_eda.parquet` y `panel_eda_semanal.parquet`).

Después se pueden correr los notebooks `03_eda/` 3.1 a 3.5.

### Auto-EDA y libretas

```bash
# Reporte automático (ydata-profiling) — requiere el panel integrado en
# data/processed/panel_hermosillo.parquet; ver notebooks/00_auto_eda/
jupyter notebook notebooks/00_auto_eda/0.0-auto-eda.ipynb
```

El índice completo de libretas (incluyendo los templates del rúbrica:
datos faltantes, outliers, relaciones, correlación y PCA/t-SNE) está en
[`notebooks/README.md`](notebooks/README.md). El template del reporte final
está en [`reports/reporte_final_template.md`](reports/reporte_final_template.md).

### Lint / formato

```bash
make lint    # ruff format --check + ruff check
make format  # ruff check --fix + ruff format
```
