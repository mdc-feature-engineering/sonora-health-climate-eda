"""Descarga e ingesta de las cinco capas de datos del protocolo EDA.

Capas (ver ``docs/docs/protocolo_eda.md``):
    1. Marginación (CONAPO/INEGI) — municipal implementado; AGEB pendiente.
    2. Clima (CONAGUA/SMN) — temperatura mensual por estación.
    3. Sequía (Monitor de Sequía SMN/CONAGUA).
    4. Calidad del aire — stub pendiente de confirmar fuente.
    5. Salud respiratoria — stub pendiente de confirmar fuente.
"""

import time

from loguru import logger
import pandas as pd
import requests
import typer
import urllib3

from sonora_health_climate_eda.config import (
    CONAGUA_BASE_URL,
    CONAGUA_DROUGHT_URL,
    CONAGUA_TEMPERATURE_REFERER,
    DROUGHT_SEVERITY_MAP,
    INTERIM_DATA_DIR,
    PANEL_END_YEAR,
    PANEL_START_YEAR,
    RAW_DATA_DIR,
)

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)  # Disable warnings for unverified SSL certificates.

app = typer.Typer()


@app.command()
def download_drought_data(start_year: int = PANEL_START_YEAR, end_year: int = PANEL_END_YEAR):
    """Procesa el archivo crudo de sequía de CONAGUA y genera un archivo Tidy por cada año."""
    raw_path = RAW_DATA_DIR / "MunicipiosSequia.xlsx"
    output_dir = INTERIM_DATA_DIR / "sonora_sequia"

    # 1. Create the folder dynamically if it does not exist (with parents=True and exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Iniciando descarga de datos de sequía desde: {CONAGUA_DROUGHT_URL}")

    try:
        raw_path.write_bytes(requests.get(CONAGUA_DROUGHT_URL, timeout=60).content)
        logger.success(f"¡Archivo descargado y guardado con éxito en: {raw_path}!")
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR DE RED] No se pudo descargar el archivo: {e}")
        raise
    except Exception as e:
        logger.error(f"[ERROR INESPERADO] Ocurrió un error al guardar el archivo: {e}")
        raise

    # 2. Save a local copy of the raw file.
    logger.info(f"Leyendo el archivo crudo de CONAGUA desde {raw_path}...")
    df = pd.read_excel(raw_path, engine="openpyxl")

    # 3. Filtrar Sonora de forma segura (usando clave que empiece con '26')
    cve_col = next((c for c in df.columns if "CVE" in str(c).upper()), None)
    if cve_col:
        df_sonora = df[df[cve_col].astype(str).str.zfill(5).str.startswith("26")].copy()
    elif "Entidad" in df.columns:
        df_sonora = df[df["Entidad"].str.lower() == "sonora"].copy()
    else:
        df_sonora = df.copy()

    # 4. Identify fixed columns (metadata) vs. date columns (fortnightly periods)
    id_vars_candidates = [
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
    id_vars = [c for c in df_sonora.columns if c in id_vars_candidates]

    # 5. Apply `melt` to convert to long format (Tidy Data).
    logger.info("Transformando a formato largo (Tidy Data)...")
    df_melted = df_sonora.melt(id_vars=id_vars, var_name="fecha", value_name="categoria_sequia")

    # 6. Clean and convert dates
    df_melted["fecha"] = pd.to_datetime(df_melted["fecha"], errors="coerce", format="mixed")
    df_melted = df_melted.dropna(subset=["fecha"])

    # 7. Filtrar estrictamente el rango de años
    df_melted["Anio"] = df_melted["fecha"].dt.year
    df_filtered = df_melted[
        (df_melted["Anio"] >= start_year) & (df_melted["Anio"] <= end_year)
    ].copy()

    # 8. Strictly filter the year range
    df_filtered["severidad_num"] = (
        df_filtered["categoria_sequia"].map(DROUGHT_SEVERITY_MAP).fillna(0).astype(int)
    )

    # 9. Save a separate CSV file for each year
    for year, df_year in df_filtered.groupby("Anio"):
        output_csv = output_dir / f"sonora_sequia_{year}.csv"
        df_year.to_csv(output_csv, index=False, encoding="utf-8-sig")
        logger.success(f"Año {year}: Descargado con éxito")

    logger.success("¡Proceso de sequía por año completado exitosamente!")


@app.command()
def download_temperature_data(start_year: int = PANEL_START_YEAR, end_year: int = PANEL_END_YEAR):
    """Descarga los archivos mensuales de temperatura media (TMed) directamente en data/raw/."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 1. Asegurar que la carpeta data/raw exista
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Cabeceras con Referer para evitar rechazos o Status 500 del servidor
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        "Referer": CONAGUA_TEMPERATURE_REFERER,
    }

    # 3. Recorrido por años y meses
    for current_year in range(start_year, end_year + 1):
        year_str = str(current_year)
        logger.info(f"--- Descarga de temperatura del año: {year_str} ---")

        # Se crea directamente en data/raw/temperatura_XXXX
        year_folder = RAW_DATA_DIR / f"temperatura_{year_str}"
        year_folder.mkdir(parents=True, exist_ok=True)

        for month in range(1, 13):
            mes_str = str(month).zfill(2)
            file_name = f"{year_str}{mes_str}010000TMed.csv"
            file_url = f"{CONAGUA_BASE_URL.rstrip('/')}/{file_name}"
            local_path = year_folder / file_name

            # Si el archivo ya existe localmente, se omite
            if local_path.exists() and local_path.stat().st_size > 0:
                logger.info(f"Año {year_str} | Mes {mes_str}: Ya existe localmente")
                continue

            try:
                res = requests.get(file_url, headers=headers, verify=False, timeout=20)

                if res.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(res.content)
                    logger.success(f"Año {year_str} | Mes {mes_str}: Descargado con éxito")
                else:
                    logger.warning(
                        f"Año {year_str} | Mes {mes_str}: No disponible (Status {res.status_code})"
                    )

                # Pausa de cortesía para no saturar al SMN
                time.sleep(0.5)

            except (requests.RequestException, OSError) as e:
                logger.error(f"Error al descargar {file_name}: {e}")

    logger.success("Descargas de temperatura media completadas.")


@app.command()
def download_temperature_extremes_data(
    start_year: int = PANEL_START_YEAR, end_year: int = PANEL_END_YEAR
):
    """Descarga los resúmenes mensuales de temperatura máxima (TMax) y
    mínima (TMin) del SMN — proxy de calor extremo / ola de calor.

    Misma estructura que ``download_temperature_data``: un CSV por mes con
    todas las estaciones del país. Se guardan en
    ``data/raw/temperatura_max_YYYY/`` y ``data/raw/temperatura_min_YYYY/``.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        "Referer": CONAGUA_TEMPERATURE_REFERER,
    }

    for series, suffix, col_name in (
        ("TMax", "temperatura_max", "Tmax"),
        ("TMin", "temperatura_min", "Tmin"),
    ):
        for current_year in range(start_year, end_year + 1):
            year_str = str(current_year)
            logger.info(f"--- {series} del año: {year_str} ---")
            year_folder = RAW_DATA_DIR / f"{suffix}_{year_str}"
            year_folder.mkdir(parents=True, exist_ok=True)

            for month in range(1, 13):
                mes_str = str(month).zfill(2)
                file_name = f"{year_str}{mes_str}010000{series}.csv"
                file_url = f"{CONAGUA_BASE_URL.rstrip('/')}/{file_name}"
                local_path = year_folder / file_name

                if local_path.exists() and local_path.stat().st_size > 0:
                    continue

                try:
                    res = requests.get(file_url, headers=headers, verify=False, timeout=20)
                    if res.status_code == 200:
                        local_path.write_bytes(res.content)
                        logger.success(f"{series} {year_str}-{mes_str}: OK")
                    else:
                        logger.warning(
                            f"{series} {year_str}-{mes_str}: no disponible (Status {res.status_code})"
                        )
                    time.sleep(0.5)
                except (requests.RequestException, OSError) as e:
                    logger.error(f"Error al descargar {file_name}: {e}")

    logger.success("Descargas de temperatura máxima/mínima completadas.")


@app.command()
def download_marginacion_data(overwrite: bool = False):
    """Descarga los índices municipales de marginación — template pendiente.

    TODO: implementar al retomar la capa de marginación (asignada al equipo).
    Fuentes: Excel municipal 1990-2015 y 2020 (CONAPO/Sonora) y CSV modernos
    de datos.gob.mx. Ver ``config.MARGINACION_1990_2015_URL``,
    ``config.MARGINACION_2020_URL`` y ``config.MARGINACION_MUNICIPAL_CSV_URLS``.
    """
    logger.warning(
        "La ingesta de marginación municipal está pausada (template). "
        "Ver config.MARGINACION_* y docs/docs/protocolo_eda.md."
    )


@app.command()
def download_marginacion_ageb_data(overwrite: bool = False):
    """Descarga el índice de marginación urbana a nivel AGEB — template.

    TODO: implementar al retomar la capa de marginación (asignada al equipo).
    Fuente: CSV nacional en datos.gob.mx (``config.MARGINACION_AGEB_URL``),
    filtrar Sonora y ``config.TARGET_MUNICIPIOS`` →
    ``data/interim/marginacion/marginacion_imu_2020.csv``.
    Cartografía AGEB por separado del INEGI — ver diccionario en
    ``references/marginacion/``.
    """
    logger.warning(
        "La ingesta de marginación AGEB está pausada (template). "
        "Ver config.MARGINACION_AGEB_URL y docs/docs/protocolo_eda.md."
    )


@app.command()
def download_marginacion_municipal_csvs(overwrite: bool = False):
    """Descarga los CSV municipales modernos — template pendiente.

    TODO: implementar al retomar la capa de marginación. Serie
    ``IM_YYYY/GM_YYYY/IMN_YYYY`` en ``config.MARGINACION_MUNICIPAL_CSV_URLS``
    (datos.gob.mx, filtro ``CVE_ENT=26`` → ``data/interim/marginacion/``).
    """
    logger.warning(
        "La ingesta de marginación municipal moderna está pausada (template). "
        "Ver config.MARGINACION_MUNICIPAL_CSV_URLS y docs/docs/protocolo_eda.md."
    )


@app.command()
def download_air_quality_data():
    """Descarga datos de calidad del aire (PM2.5, PM10, O3) — pendiente de fuente.

    TODO: Confirmar fuente operativa para Hermosillo (SINAICA, datos abiertos
    del estado de Sonora o IMECA histórico). Ver ``config.AIR_QUALITY_SOURCES``.
    """
    logger.warning(
        "La ingesta de calidad del aire aún no está implementada. "
        "Ver config.AIR_QUALITY_SOURCES y docs/docs/protocolo_eda.md."
    )


@app.command()
def download_respiratory_health_data():
    """Descarga morbilidad respiratoria — pendiente de fuente y granularidad.

    TODO: SINAVE publica morbilidad anual por jurisdicción sanitaria; verificar
    si existe desglose más fino (municipal/AGEB/unidad médica) para Sonora.
    Ver ``config.HEALTH_DATA_SOURCES``.
    """
    logger.warning(
        "La ingesta de datos de salud respiratoria aún no está implementada. "
        "Ver config.HEALTH_DATA_SOURCES y docs/docs/protocolo_eda.md."
    )


@app.command()
def data_ingestion_pipeline(start_year: int = PANEL_START_YEAR, end_year: int = PANEL_END_YEAR):
    """Ejecuta la descarga de las capas disponibles en un solo paso."""
    logger.info("=== Iniciando pipeline de ingesta de datos ===")

    logger.info("Paso 1/5: Descargando y preprocesando datos de sequía...")
    download_drought_data(start_year, end_year)

    logger.info("Paso 2/5: Descargando datos de temperatura media...")
    download_temperature_data(start_year, end_year)

    logger.info("Capas pendientes (marginación, aire, salud)...")
    download_marginacion_ageb_data()
    download_marginacion_data()
    download_marginacion_municipal_csvs()
    download_air_quality_data()
    download_respiratory_health_data()

    logger.warning(
        "Pipeline completado con advertencias: las capas de marginación, "
        "aire y salud están pendientes. Ver docs/docs/protocolo_eda.md."
    )


if __name__ == "__main__":
    app()
