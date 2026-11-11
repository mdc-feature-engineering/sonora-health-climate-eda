# Sonora Agri-Climate EDA

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

> Análisis exploratorio de datos para evaluar el impacto del colapso ambiental y la sequía en los municipios agrícolas del estado de Sonora.

## Descripción del Proyecto
Este proyecto investiga cómo las crisis y el colapso ambiental (con un enfoque principal en las tendencias históricas de sequía y estrés hídrico) han afectado a los municipios agrícolas en el estado de Sonora. 

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│   │                      the creator's initials, and a short `-` delimited description, e.g.
│   │                      `1.0-jqp-initial-data-exploration`.
│   ├── agriculture    <- Data from agriculture sources.
│   ├── climate        <- Data from climate sources.
│   └── water resources<- Data from water resources sources.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         sonora_agriclimate_eda and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│   ├── agriculture    <- Data from agriculture sources.
│   ├── climate        <- Data from climate sources.
│   └── water resources<- Data from water resources sources.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── sonora_agriclimate_eda   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes sonora_agriclimate_eda a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── utils.py                <- Helper functions and reusable scripts
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------

## Descargar datos de marginación

Para descargar los archivos municipales de 1990–2015 y 2020 en `data/raw/`:

```bash
python -m sonora_agriclimate_eda.dataset download-marginacion-data
```

Los archivos existentes se conservan. Para descargarlos de nuevo, usa
`--overwrite`.
La descarga también forma parte de `data_ingestion_pipeline`.
