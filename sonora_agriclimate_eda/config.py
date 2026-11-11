from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
#logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

REFERENCES_DIR = PROJ_ROOT / "references"

# --- URLs de Fuentes Externas ---
SONORA_AGRICULTURE_URL = (
    "https://datos.sonora.gob.mx/dataset/3e17a7e8-c8d4-49c4-a426-4dec099cd0cd/"
    "resource/9e455a9c-1733-490e-ba3d-6117ffe4ffe5/download/"
    "agricultura-sonora-{year}.xlsx"
)

CONAGUA_BASE_URL = "https://smn.conagua.gob.mx/tools/RESOURCES/com_archivo_datos_resumenes"

CONAGUA_DROUGHT_URL = (
    "https://smn.conagua.gob.mx/tools/RESOURCES/"
    "Monitor de Sequia en Mexico/MunicipiosSequia.xlsx"
)

HIDRICO_SONORA_URL = (
    "https://datos.sonora.gob.mx/dataset/ee8f639f-5e89-46ae-93b9-934b05fc6233/"
    "resource/213a4f46-7cd1-412f-aeec-4fab8193f51f/download/"
    "hidrico_sonora_2020-actualidad2024.xlsx"
)

MARGINACION_1990_2015_URL = (
    "https://coespo.sonora.gob.mx/documentos/Marginacion/Municipal/"
    "Indice-de-Marginacion-municipal-1990-2015(Conapo).xlsx"
)

MARGINACION_2020_URL = (
    "https://datos.sonora.gob.mx/dataset/%C3%8Dndice%20de%20marginaci%C3%B3n"
    "%20por%20municipio/download_resource/046c2f52-72aa-4059-bf05-5ad52e191d1b"
)

REPDA_URL_QUERY = "https://sigagis.conagua.gob.mx/ArcGIS/rest/services/REPDA/MapServer/1/query"

# --- Metadatos y Columnas ---
ID_VARS_CANDIDATES = [
    "Cve_Entidad",
    "Entidad",
    "Cve_Municipio",
    "Municipio",
    "CVE_CONCATENADA",
    "CVE_ENT",
    "CVE_MUN",
    "MUNICIPIO",
    "Abrevia",
]

# Parámetros agroclimáticos de referencia para Agave angustifolia (Bacanora)
AGAVE_AGROCLIMATIC_PARAMS_PROFILE = {
    "nombre_comun": "Maguey Espadín / Bacanora",
    "nombre_cientifico": "Agave angustifolia Haw.",
    "precipitacion_min_anual_mm": 250,
    "precipitacion_optima_mm": 600,
    "temperatura_critica_min_c": -3,
    "ciclo_vida_anos": (6, 8),
    "suelos_aptos": ["franco-arenoso", "pedregoso", "buen drenaje"],
    "grados_sequia_criticos": ["D3", "D4"],
    "severidad_map": {
        "Normal": 0,
        "D0": 1,
        "D1": 2,
        "D2": 3,
        "D3": 4,
        "D4": 5,
    },
}

AGAVE_AGROCLIMATIC_PARAMS = {
    # 1. Requerimientos de precipitación y balance hídrico (mm)
    "precipitacion": {
        "optima_min_anual_mm": 400,
        "optima_max_anual_mm": 600,
        "minimo_supervivencia_mm": 250,  # Límite biológico sin riego de auxilio
    },
    # 2. Umbrales Térmicos (°C)
    "temperatura": {
        "estres_frio_critico_c": -3,  # Riesgo de daño tisular / heladas
        "estres_calor_extremo_c": (
            40
        ),  # Cierre estomático prolongado por calor/sequía
    },
    # 3. Propiedades del Suelo y Drenaje
    "suelo": {
        "texturas_ideales": ["franco-arenosa", "arenosa", "pedregosa"],
        "sensibilidad_encharcamiento": (
            "alta"
        ),  # Propensión a pudrición de raíz (ej. Fusarium)
    },
    # 4. Monitor de Sequía CONAGUA (Mapeo de severidad numérica)
    "severidad_sequia_map": {
        "Normal": 0,
        "Sin Sequía": 0,
        "D0": 1,  # Anormalmente seco
        "D1": 2,  # Sequía moderada
        "D2": 3,  # Sequía severa
        "D3": 4,  # Sequía extrema (estrés hídrico crítico)
        "D4": 5,  # Sequía excepcional (riesgo alto de pérdida)
    },
    # Categorías consideradas de alerta crítica para el cultivo
    "niveles_alerta_critica": ["D3", "D4"],
}



# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass

#