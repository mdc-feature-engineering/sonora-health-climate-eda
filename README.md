# Sonora Health-Climate EDA

> Análisis exploratorio y modelado espacio-temporal de la vulnerabilidad socioeconómica y climática ante enfermedades respiratorias en Hermosillo, Sonora.

## Preguntas de investigación

**General:** ¿Cómo inciden el calor extremo, la sequía y la contaminación del aire en la incidencia de enfermedades respiratorias en Hermosillo?

**Específica:** ¿Las zonas más marginadas de Hermosillo son las más afectadas por las enfermedades respiratorias durante olas de calor y sequía?

Objetivo del EDA: explorar la relación exposición–morbilidad para definir alcances del producto de datos final (alerta climática → modelo predictivo por AGEB → planeación en salud pública). Detalle en [`docs/docs/protocolo_eda.md`](docs/docs/protocolo_eda.md).

## Capas de datos

| # | Capa | Fuente | Estado |
|---|------|--------|--------|
| 1 | Índice de marginación | CONAPO / INEGI (AGEB 2020 + municipal 1990–2015/2020) | Pausado (template) |
| 2 | Temperatura y clima | CONAGUA/SMN (resúmenes mensuales por estación) | Disponible |
| 3 | Índice de sequía | Monitor de Sequía SMN/CONAGUA | Disponible |
| 4 | Calidad del aire (PM2.5, PM10, O3) | SINAICA / datos abiertos Sonora | Pendiente de fuente |
| 5 | Enfermedades respiratorias | Vigilancia Epidemiológica Sonora (SUIVE, datos abiertos) — semanal × municipio × diagnóstico CIE-10 | Fuente identificada, implementación pendiente |

> Las capas 4 y 5 tienen notebooks esqueleto en `notebooks/01_ingesta/`. La
> fuente de salud ya está configurada en `sonora_health_climate_eda/config.py`
> (`HEALTH_DATA_SOURCES`); falta implementar el comando de descarga.
> Ver los `TODO` en `config.py`.

## Project Organization

```
├── LICENSE
├── Makefile              <- Comandos de conveniencia (make data, make lint)
├── README.md
├── data
│   ├── external          <- Datos de terceros
│   ├── interim           <- Datos intermedios transformados
│   ├── processed         <- Datasets finales para modelado
│   └── raw               <- Datos crudos inmutables
│
├── docs                  <- Documentación mkdocs + protocolo_eda.md
├── models                <- Modelos entrenados y resultados
├── notebooks
│   ├── 00_auto_eda      <- Auto-EDA con ydata-profiling (reporte HTML)
│   ├── 01_ingesta        <- Descarga/limpieza de las capas (aire pendiente; salud por implementar)
│   ├── 02_eda            <- Fases B y C: univariado, bivariado/CCF, espacial + templates del rúbrica (faltantes, outliers, correlación, PCA/t-SNE)
│   └── 03_modelado       <- Fase D: GLM Poisson/NB con rezagos e interacciones
│
├── pyproject.toml
├── references            <- Diccionarios de datos por fuente
│   ├── clima/            <- CONAGUA (temperatura, lluvia, sequía)
│   ├── marginacion/      <- (pendiente: AGEB y municipal)
│   ├── aire/             <- (pendiente)
│   └── salud/            <- (pendiente)
├── reports
│   ├── figures           <- Gráficos generados
│   ├── auto_eda_report.html  <- Reporte auto-EDA (ydata-profiling, una vez ejecutado)
│   └── reporte_final_template.md  <- Template del reporte final (rúbrica)
├── requirements.txt
└── sonora_health_climate_eda   <- Paquete Python del proyecto
    ├── config.py         <- Rutas, URLs de fuentes, constantes del protocolo
    ├── dataset.py        <- Comandos typer de descarga/ingesta
    ├── schemas.py        <- Esquemas pydantic de los datasets
    ├── utils.py          <- Generación de diccionarios de datos
    ├── lags.py           <- Rezagos temporales y función de correlación cruzada
    ├── spatial.py        <- Spatial joins AGEB ↔ estaciones, filtros INEGI
    ├── glms.py           <- GLM Poisson/NB con interacciones
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
python -m sonora_health_climate_eda.dataset download-rain-data
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
datos faltantes, outliers, correlación, PCA/t-SNE) está en
[`notebooks/README.md`](notebooks/README.md). El template del reporte final
está en [`reports/reporte_final_template.md`](reports/reporte_final_template.md).

### Lint / formato

```bash
make lint    # ruff format --check + ruff check
make format  # ruff check --fix + ruff format
```
