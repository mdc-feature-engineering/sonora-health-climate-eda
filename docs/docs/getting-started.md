Primeros pasos
==============

Requiere **Python 3.13** (`ydata-profiling` no es compatible con 3.14).

1. Crear el entorno e instalar dependencias:

   ```bash
   # Con uv (recomendado)
   uv venv --python 3.13 .venv && source .venv/bin/activate
   uv pip install -r requirements.txt

   # O con venv + pip
   python3.13 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Descargar las capas de datos disponibles:

   ```bash
   python -m sonora_health_climate_eda.dataset data-ingestion-pipeline
   ```

   Esto descarga sequía (CONAGUA), lluvia y temperatura (SMN), y marginación
   municipal (CONAPO). Las capas de calidad del aire y salud respiratoria
   están pendientes de confirmar fuente — ver los `TODO` en
   `sonora_health_climate_eda/config.py`.

3. Ejecutar los notebooks en orden:

   - `notebooks/00_auto_eda/` — auto-EDA con `ydata-profiling`
     (genera `reports/auto_eda_report.html`; requiere el panel integrado).
   - `notebooks/01_ingesta/` → `notebooks/02_eda/` → `notebooks/03_modelado/`.

   El índice completo está en `notebooks/README.md`. Los notebooks de
   `02_eda/` incluyen templates del rúbrica (datos faltantes, outliers,
   correlación, PCA/t-SNE) listos para llenar cuando exista el panel
   integrado. El template del reporte final está en
   `reports/reporte_final_template.md`.
