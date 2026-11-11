Primeros pasos
==============

1. Crear el entorno e instalar dependencias:

   ```bash
   python -m venv .venv && source .venv/bin/activate
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

3. Ejecutar los notebooks en orden: `notebooks/01_ingesta/` →
   `notebooks/02_eda/` → `notebooks/03_modelado/`.
