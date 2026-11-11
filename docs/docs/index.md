# Sonora Health-Climate EDA documentation!

## Description

Análisis exploratorio y modelado espacio-temporal de la vulnerabilidad
socioeconómica y climática ante enfermedades respiratorias en Hermosillo,
Sonora. El protocolo metodológico está en
[`protocolo_eda.md`](protocolo_eda.md). Referencias metodológicas:
[`heat_index.md`](heat_index.md) (índice de calor Rothfusz/NWS usado
para exposición a calor húmedo).

## Comandos

El `Makefile` contiene los puntos de entrada principales:

- `make data` — ejecuta el pipeline de ingesta (`data-ingestion-pipeline`)
- `make lint` / `make format` — linting y formato con ruff
- `make clean` — elimina archivos `.pyc` y `__pycache__`
