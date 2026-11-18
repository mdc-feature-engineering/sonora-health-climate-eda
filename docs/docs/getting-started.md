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

   Esto descarga las seis capas: temperatura (SMN/CONAGUA), calor diario
   (Open-Meteo), sequía (Monitor de Sequía, CONAGUA), marginación
   municipal y por colonia (CONAPO/INEGI), calidad del aire (RUOA-UNAM)
   y casos de IRA (SS/DGIS, SINAIS/SUIVE), además del catálogo CLUES.

3. Ejecutar los notebooks en orden:

   - `notebooks/00_auto_eda/` — auto-EDA con `ydata-profiling`
     (genera `reports/auto_eda_report.html` a partir del panel integrado).
   - `notebooks/01_ingesta/` → `notebooks/02_procesamiento/` → `notebooks/03_eda/`.

   El índice completo está en `notebooks/README.md`. Los notebooks de
   `03_eda/` ya tienen el análisis completo (datos faltantes, outliers,
   relaciones, correlación, PCA/t-SNE, marginación urbana) y las libretas
   `1.6`, `2.6` y `3.7` resumen cada etapa. El reporte final está en
   `reports/reporte_final_eda.md`.
