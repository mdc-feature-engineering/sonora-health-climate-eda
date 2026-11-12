# Sonora Health-Climate EDA

> Análisis exploratorio y modelado espacio-temporal de la vulnerabilidad socioeconómica y climática ante enfermedades respiratorias en Hermosillo, Sonora.

## Preguntas de investigación

**Pregunta general:**

> ¿Cómo inciden el calor extremo, la sequía y la contaminación del aire en la incidencia de enfermedades respiratorias en Hermosillo?

**Pregunta específica (hipótesis de vulnerabilidad diferencial):**

> ¿Las zonas más marginadas de Hermosillo son las más afectadas por las enfermedades respiratorias durante olas de calor y sequía?


Objetivo del EDA: explorar la relación exposición–morbilidad para definir alcances del producto de datos final (alerta climática → modelo predictivo por AGEB → planeación en salud pública). Detalle en [`docs/docs/protocolo_eda.md`](docs/docs/protocolo_eda.md).

## Capas de datos

| # | Capa | Fuente | Estado |
|---|------|--------|--------|
| 1 | Índice de marginación | CONAPO / INEGI (municipal 2010/2015/2020 en `data/interim/`; AGEB IMU 2020 disponible sin geometría) | Datos en interim; ingesta pausada (stubs) |
| 2 | Temperatura y clima | CONAGUA/SMN (resúmenes mensuales por estación) | Disponible — descarga 2015–2020 |
| 3 | Índice de sequía | Monitor de Sequía SMN/CONAGUA (quincenal → mensual) | Disponible — 2015–2020 |
| 4 | Calidad del aire (PM2.5, PM10, O3) | SINAICA / datos abiertos Sonora | Pendiente de fuente |
| 5 | Enfermedades respiratorias | Salud Sonora/SUIVE — casos confirmados de IRA, semanal × municipio × sexo × edad, 2010–2020 (`data/raw/salud/`) | Disponible — agregado a mensual |

### Panel integrado

`data/processed/panel_hermosillo.parquet`: Hermosillo, mensual, 2015–2020 (72 meses × 40 columnas).

- **Clima:** datos diarios de Open-Meteo agregados por mes (olas de calor ≥35 °C y p95, humedad relativa).
- **Flags:** `mes_ola_calor_p95`, `mes_sequia`, `mes_ola_calor_p95_y_sequia`.
- **Salud:** un mes suma 4 o 5 semanas (`n_semanas`); `casos_ira_por_semana` permite comparar meses.
- **Cómo se genera:** `panel.build_panel()`; ver [`3.0-integracion-espacial.ipynb`](notebooks/03_eda/3.0-integracion-espacial.ipynb). Los años se ajustan en `config.py`.
- **Calidad del aire:** pendiente de fuente.

### Alcance actual y próximos pasos

Por ahora el proyecto cubre la **ingesta** de las capas y el panel integrado, más los templates de datos faltantes, outliers, relaciones por visualización, correlación y PCA/t-SNE. El análisis univariado, los rezagos (panel semanal), el GLM y los mapas por AGEB quedan como **plan** hasta tener todos los datos; ver la sección 3 de [`protocolo_eda.md`](docs/docs/protocolo_eda.md).

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
│   ├── 01_ingesta        <- Descarga/limpieza de las capas (aire pendiente; salud y panel implementados)
│   ├── 02_procesamiento  <- Limpieza, homologación y agregación mensual por capa (templates; aire pendiente)
│   └── 03_eda            <- 3.0 panel integrado ✅; templates del rúbrica (faltantes, outliers, relaciones, correlación, PCA/t-SNE)
│
├── pyproject.toml
├── references            <- Diccionarios de datos por fuente
│   ├── clima/            <- CONAGUA (temperatura, sequía)
│   ├── marginacion/      <- (pendiente)
│   ├── aire/             <- (pendiente)
│   └── salud/            <- Diccionario de casos confirmados de IRA (Salud Sonora)
├── reports
│   ├── figures           <- Gráficos generados
│   ├── auto_eda_report.html  <- Reporte auto-EDA (ydata-profiling, una vez ejecutado)
│   └── reporte_final_template.md  <- Template del reporte final (rúbrica)
├── requirements.txt
└── sonora_health_climate_eda   <- Paquete Python del proyecto
    ├── config.py         <- Rutas, URLs de fuentes, constantes del protocolo
    ├── dataset.py        <- Comandos typer de descarga/ingesta
    ├── panel.py          <- Panel mensual integrado (clima+sequía+marginación+salud)
    ├── schemas.py        <- Esquemas pydantic de los datasets
    ├── utils.py          <- Generación de diccionarios de datos
    ├── spatial.py        <- Spatial joins AGEB ↔ estaciones, filtros INEGI
    ├── features.py       <- Ingeniería de características
    ├── plots.py          <- Visualizaciones
    └── modeling/         <- Entrenamiento/predicción (stub)
```

## Setup

Requiere **Python 3.13** (`ydata-profiling` no soporta 3.14).

```bash
# Opción A — uv (recomendada, no requiere pip en el venv)
uv venv --python 3.13 .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Opción B — venv + pip
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .   # opcional, para usar el paquete sin sys.path
```

## Uso

### Descargar datos (capas disponibles)

```bash
# Pipeline completo de capas disponibles
python -m sonora_health_climate_eda.dataset data-ingestion-pipeline

# Individuales (solo capas activas: clima y sequía)
python -m sonora_health_climate_eda.dataset download-drought-data
python -m sonora_health_climate_eda.dataset download-temperature-data
```

O desde el Makefile:

```bash
make data
```

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
