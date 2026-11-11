# Sonora Health-Climate EDA

> Análisis exploratorio y modelado espacio-temporal de la vulnerabilidad socioeconómica y climática ante enfermedades respiratorias en Hermosillo, Sonora.

## Pregunta de investigación

¿De qué manera la población **marginalizada en Hermosillo** presenta una mayor **exposición y vulnerabilidad** a enfermedades asociadas al **calor extremo y la sequía**, mediada por la **calidad del aire** y los **efectos de rezago temporal**?

El protocolo metodológico completo está en [`docs/docs/protocolo_eda.md`](docs/docs/protocolo_eda.md).

## Capas de datos

| # | Capa | Fuente | Estado |
|---|------|--------|--------|
| 1 | Índice de marginación | CONAPO / INEGI (AGEB 2020 + municipal 1990–2015/2020) | Disponible |
| 2 | Temperatura y clima | CONAGUA/SMN (resúmenes mensuales por estación) | Disponible |
| 3 | Índice de sequía | Monitor de Sequía SMN/CONAGUA | Disponible |
| 4 | Calidad del aire (PM2.5, PM10, O3) | SINAICA / datos abiertos Sonora | Pendiente de fuente |
| 5 | Enfermedades respiratorias | SINAVE / SSA | Pendiente de fuente y granularidad |

> Las capas 4 y 5 tienen comandos stub en `dataset.py` y notebooks esqueleto en `notebooks/01_ingesta/`. Ver los `TODO` en `sonora_health_climate_eda/config.py`.

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
│   ├── 01_ingesta        <- Descarga/limpieza de las capas (aire y salud pendientes)
│   ├── 02_eda            <- Fases B y C: univariado, bivariado/CCF, espacial
│   └── 03_modelado       <- Fase D: GLM Poisson/NB con rezagos e interacciones
│
├── pyproject.toml
├── references            <- Diccionarios de datos por fuente
│   ├── clima/            <- CONAGUA (temperatura, lluvia, sequía)
│   ├── aire/             <- (pendiente)
│   └── salud/            <- (pendiente)
├── reports
│   └── figures           <- Gráficos generados
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

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .   # opcional, para usar el paquete sin sys.path
```

## Uso

### Descargar datos (capas disponibles)

```bash
# Pipeline completo de capas disponibles
python -m sonora_health_climate_eda.dataset data-ingestion-pipeline

# Individuales
python -m sonora_health_climate_eda.dataset download-marginacion-data
python -m sonora_health_climate_eda.dataset download-drought-data
python -m sonora_health_climate_eda.dataset download-temperature-data
python -m sonora_health_climate_eda.dataset download-rain-data
```

O desde el Makefile:

```bash
make data
```

Los archivos existentes en `data/raw/` se conservan; usa `--overwrite` donde
aplique para volver a descargarlos.

### Lint / formato

```bash
make lint    # ruff format --check + ruff check
make format  # ruff check --fix + ruff format
```
