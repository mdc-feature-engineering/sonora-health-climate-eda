"""Configuración global del proyecto.

Enfoque: vulnerabilidad socioeconómica y climática ante enfermedades
respiratorias en Hermosillo, Sonora (ver ``docs/docs/protocolo_eda.md``).

Las cinco capas de datos del protocolo son:

1. Índice de marginación (CONAPO/INEGI) — nivel AGEB preferido, municipal como fallback.
2. Temperatura y clima (CONAGUA/SMN, estaciones REDNAMEC o reanálisis).
3. Índice de sequía (Monitor de Sequía SMN/CONAGUA).
4. Calidad del aire (PM2.5, PM10, O3 — RUOA-UNAM, observatorio ERNO Hermosillo).
5. Enfermedades respiratorias (SINAVE/SSA — IRAs, asma, EPOC, neumonías).
"""

from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

REFERENCES_DIR = PROJ_ROOT / "references"

# ---------------------------------------------------------------------------
# Área de estudio
# ---------------------------------------------------------------------------
# Hermosillo es la cabecera del estado (CVE_ENT=26, CVE_MUN=030 -> clave
# concatenada INEGI 26030). La arquitectura permite escalar a otros municipios
# vía TARGET_MUNICIPIOS.
HERMOSILLO_CVE_ENT = "26"
HERMOSILLO_CVE_MUN = "26030"
HERMOSILLO_CVE_AGEB_PREFIX = "26003"  # Prefijo de AGEBs de Hermosillo

TARGET_MUNICIPIOS = [HERMOSILLO_CVE_MUN]

# ---------------------------------------------------------------------------
# Capa 1 — Índice de marginación (CONAPO / INEGI)
# ---------------------------------------------------------------------------
MARGINACION_1990_2015_URL = (
    "https://coespo.sonora.gob.mx/documentos/Marginacion/Municipal/"
    "Indice-de-Marginacion-municipal-1990-2015(Conapo).xlsx"
)

MARGINACION_2020_URL = (
    "https://datos.sonora.gob.mx/dataset/%C3%8Dndice%20de%20marginaci%C3%B3n"
    "%20por%20municipio/download_resource/046c2f52-72aa-4059-bf05-5ad52e191d1b"
)

# Índice de marginación urbana AGEB 2020 (CONAPO vía datos.gob.mx, CSV nacional).
# Verificado 2026-11: descarga directa funciona con User-Agent de navegador.
# Respaldo ZIP con diccionario oficial:
#   http://www.conapo.gob.mx/work/models/CONAPO/Marginacion/Datos_Abiertos/IMU_2020.zip
# Geometrías AGEB: INEGI Cartografía Geoestadística (mismo año censal 2020)
# o SHP de marginación por colonia en datos.gob.mx; unir por CVE_AGEB/fn_CVE_AGEB.
MARGINACION_AGEB_URL = (
    "https://www.datos.gob.mx/dataset/"
    "d8f2a534-bcee-4114-853d-82982a81ce24/resource/"
    "9600f414-c1ba-408a-8dd6-7f73d76601d4/download/imu_2020.csv"
)
MARGINACION_AGEB_YEAR = 2020

# Series municipal moderna (esquema IM_YYYY/GM_YYYY/IMN_YYYY) en datos.gob.mx.
# Nacionales; se filtran a Sonora (CVE_ENT=26) al ingerir.
MARGINACION_MUNICIPAL_CSV_URLS = {
    2010: (
        "https://www.datos.gob.mx/dataset/d8f2a534-bcee-4114-853d-82982a81ce24/"
        "resource/216bb68c-d3fa-42a7-84ac-10337cd1f6cd/download/imm_dp2_2010.csv"
    ),
    2015: (
        "https://www.datos.gob.mx/dataset/d8f2a534-bcee-4114-853d-82982a81ce24/"
        "resource/d65dbd44-2fad-4344-bfc2-45152067a14d/download/imm_dp2_2015.csv"
    ),
    2020: (
        "https://www.datos.gob.mx/dataset/d8f2a534-bcee-4114-853d-82982a81ce24/"
        "resource/551d8f48-5d0c-4d11-964a-e2911f732615/download/imm_2020-3.csv"
    ),
}

# ---------------------------------------------------------------------------
# Capa 2 — Temperatura y clima (CONAGUA/SMN + estaciones)
# ---------------------------------------------------------------------------
CONAGUA_BASE_URL = "https://smn.conagua.gob.mx/tools/RESOURCES/com_archivo_datos_resumenes"

CONAGUA_TEMPERATURE_REFERER = (
    "https://smn.conagua.gob.mx/es/climatologia/temperaturas-y-lluvias/"
    "resumenes-mensuales-de-temperaturas-y-lluvias"
)

# TODO: Para Hermosillo conviene complementar los resúmenes mensuales SMN
# con datos diarios de estaciones REDNAMEC cercanas a la ciudad o un
# producto de reanálisis (ERA5-Land vía CDS/CDSAPI o Open-Meteo archive).
# Definir aquí el identificador de estación(es) de referencia una vez elegida
# la fuente: p.ej. estación CONAGUA más cercana al centro de Hermosillo.
CLIMATE_STATION_IDS = ["HM2SO", "HMNSO", "MMHO"]  # Estaciones SMN en Hermosillo

# Ventana del panel integrado mensual (ene-2015 a dic-2020 por defecto;
# parametrizado para permitir extensión a 2010–2020).
PANEL_START_YEAR = 2015
PANEL_END_YEAR = 2020

# Umbrales de exposición extrema para el análisis calor/sequía → IRA.
# Ojo: son promedios MENSUALES por estación, no olas de calor diarias
# (la nomenclatura oficial de ola de calor requiere Tmax diaria ≥35 °C
# por ≥3 días — no disponible en resúmenes mensuales SMN).
HEAT_EXTREME_TMAX_C = 38.0  # Tmax media mensual (°C) en Hermosillo
DROUGHT_EXTREME_MIN_SEVERITY = 2.0  # severidad_sequia mensual >= D1 (moderada)
HEAT_INDEX_DANGER_C = 40.0  # heat index (sensación térmica) >= 40 °C

# Años con reporte de salud atípico: 2020 colapsó ~70% en casos_ira por la
# disrupción COVID-19 en la notificación epidemiológica. El clima/sequía
# de esos meses sigue siendo válido — el flag solo marca la anomalía para
# excluir o tratar con una variable indicadora (no usar como exposición).
HEALTH_ANOMALY_YEARS = {2020}

# ---------------------------------------------------------------------------
# Capa 3 — Monitor de Sequía (SMN/CONAGUA)
# ---------------------------------------------------------------------------
CONAGUA_DROUGHT_URL = (
    "https://smn.conagua.gob.mx/tools/RESOURCES/Monitor de Sequia en Mexico/MunicipiosSequia.xlsx"
)

# Severidad de sequía (escala numérica usada en el análisis)
DROUGHT_SEVERITY_MAP = {
    "Normal": 0,
    "Sin Sequía": 0,
    "D0": 1,
    "D1": 2,
    "D2": 3,
    "D3": 4,
    "D4": 5,
}

# ---------------------------------------------------------------------------
# Capa 4 — Calidad del aire (PM2.5, PM10, O3)
# ---------------------------------------------------------------------------
# Fuente: Red Universitaria de Observatorios Atmosféricos (RUOA-UNAM),
# Observatorio Atmosférico Hermosillo (ERNO; 29.0814 N, 110.9706 W).
# Un CSV horario público por mes; verificado 2026-11: existen los 72 meses
# 2015–2020. Hora local UTC-7 (Hermosillo no usa horario de verano).
# Descartadas: SINAICA (la estación de Hermosillo no tiene datos) y
# Open-Meteo Air Quality (empieza en 2022-08).
RUOA_ERNO_URL_TEMPLATE = (
    "https://ruoa.unam.mx/caire/erno/hora/{year}-{month:02d}-ERNO_hora_L1_caire.csv"
)
AIR_QUALITY_SOURCES = {"ruoa_erno": RUOA_ERNO_URL_TEMPLATE}
AIR_QUALITY_RAW_DIR = RAW_DATA_DIR / "aire" / "ruoa_erno"
AIR_QUALITY_INTERIM_DIR = INTERIM_DATA_DIR / "aire"

AIR_QUALITY_POLLUTANTS = ["PM2.5", "PM10", "O3"]
AIR_QUALITY_UNITS = {"PM2.5": "ug/m^3", "PM10": "ug/m^3", "O3": "ppb"}  # fila de unidades RUOA

# Límite de detección inferido de los datos: los valores OK empiezan
# exactamente en 4 µg/m³ (PM) y 1 ppb (O3) y los BDL quedan por debajo
# (con ceros y negativos). Las horas BDL se sustituyen por la mitad.
AIR_QUALITY_DETECTION_LIMITS = {"PM2.5": 4.0, "PM10": 4.0, "O3": 1.0}
# O3 marcado OK por encima de este valor es un artefacto del equipo: mesetas
# de ~400 ppb durante horas (2018-03-08/09, 2019-08-28/29); el P99.9 de la
# serie es ~76 ppb.
AIR_QUALITY_MAX_PLAUSIBLE = {"O3": 120.0}
# PM2.5 es una fracción de PM10: una hora con PM2.5 > PM10 + tolerancia
# (ambas OK) se descarta para PM2.5. La tolerancia absorbe el ruido entre equipos.
AIR_QUALITY_PM25_PM10_TOLERANCE = 10.0
# Suficiencia de información (75 %, criterio de las NOM de salud ambiental):
# día con >= 18 de 24 horas, O3 8 h con >= 6 de 8 horas, mes con >= 75 % de días.
AIR_QUALITY_MIN_COVERAGE = 0.75
# Un día con >= 75 % de sus horas válidas en BDL se invalida: es la señal
# plana en cero de un sensor fallando (p. ej. PM2.5 en 2019), no aire limpio.
AIR_QUALITY_MAX_BDL_FRACTION = 0.75
# Límites de las normas vigentes en 2015–2020. PM: promedio de 24 h,
# NOM-025-SSA1-2014 (µg/m³). O3: máximo diario del promedio móvil de 8 h,
# NOM-020-SSA1-2014 (0.070 ppm = 70 ppb; cotejar con el texto del DOF).
AIR_QUALITY_NOM_LIMITS = {"PM2.5": 45.0, "PM10": 75.0, "O3": 70.0}

# ---------------------------------------------------------------------------
# Capa 5 — Enfermedades respiratorias (SINAVE / SSA)
# ---------------------------------------------------------------------------
# TODO: SINAVE publica morbilidad por entidad federativa y jurisdicción
# sanitaria de forma ANUAL (no diaria ni por AGEB en la mayoría de los
# tabulados públicos). Verificar si Sonora/SSA estatal publica datos más
# finos (p.ej. por unidad médica georreferenciada o apartados epidemiológicos
# municipales). Si no, el análisis espacial usará jurisdicción sanitaria y el
# temporal será anual o sub-anual.
HEALTH_DATA_SOURCES = {
    # Portal de Datos Abiertos del Gobierno del Estado de Sonora (CKAN).
    # Dataset "Vigilancia Epidemiológica" (SUIVE): semanal × jurisdicción ×
    # municipio × diagnóstico CIE-10 × edad/sexo. Verificado 2026-11 (año 2022).
    # Pendiente: confirmar si publican años adicionales bajo el mismo dataset.
    "vigilancia_epidemiologica_sonora": {
        "dataset_id": "dca16d84-dbf0-4501-b702-dc6372a480ea",
        "resource_id": "1689b19c-b0dc-4e39-bf07-e3a2e684ef1a",
        "year": 2022,
        "url": (
            "https://datos.sonora.gob.mx/dataset/"
            "dca16d84-dbf0-4501-b702-dc6372a480ea/resource/"
            "1689b19c-b0dc-4e39-bf07-e3a2e684ef1a/download/"
            "202209281339190-file.xlsx"
        ),
    },
    "sinave": None,  # Respaldo: morbilidad anual por jurisdicción sanitaria
    "ssa_sonora": None,
    # CSVs locales recibidos de la Secretaría de Salud de Sonora
    # (casos confirmados de IRA, 2010–2020, semanal × municipio × sexo ×
    # grupo de edad). Ver references/salud/data_dictionary_enf_resp_sonora.md.
    "salud_sonora_local": {
        "sonora": "data/raw/salud/enf_resp_sonora_2010_2020.csv",
        "hmo": "data/raw/salud/enf_resp_hmo_2010_2020.csv",
        "coverage": "2010-2020",
        "diagnostico": "IRA (J00-J06, J20, J21 excepto J02.0 y J03.0)",
    },
}

# Diagnósticos respiratorios de interés (cve_diagno del SUIVE) — protocolo EDA.
RESPIRATORY_DIAGNOSIS_IDS = {
    "16": "Infecciones respiratorias agudas (IRA)",
    "17": "Neumonías y bronconeumonías",
    "185": "Enfermedad pulmonar obstructiva crónica (EPOC)",
    "54": "Asma",
    "90": "Influenza",
    "19": "Tuberculosis respiratoria",
}

# ---------------------------------------------------------------------------
# Metadatos y columnas auxiliares
# ---------------------------------------------------------------------------
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

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
