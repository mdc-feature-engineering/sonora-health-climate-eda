"""Descarga e ingesta de las cinco capas de datos del protocolo EDA.

Capas (ver ``docs/docs/protocolo_eda.md``):
    1. Marginación (CONAPO/INEGI) — municipal implementado; AGEB pendiente.
    2. Clima (CONAGUA/SMN) — temperatura y lluvia mensuales por estación.
    3. Sequía (Monitor de Sequía SMN/CONAGUA).
    4. Calidad del aire — stub pendiente de confirmar fuente.
    5. Salud respiratoria — stub pendiente de confirmar fuente.
"""

import os
import time
import urllib3
from pathlib import Path

import pandas as pd
import requests
import typer
from loguru import logger
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from sonora_health_climate_eda.config import (
    CONAGUA_BASE_URL,
    CONAGUA_DROUGHT_URL,
    CONAGUA_TEMPERATURE_REFERER,
    DROUGHT_SEVERITY_MAP,
    INTERIM_DATA_DIR,
    MARGINACION_1990_2015_URL,
    MARGINACION_2020_URL,
    MARGINACION_AGEB_URL,
    MARGINACION_AGEB_YEAR,
    MARGINACION_MUNICIPAL_CSV_URLS,
    RAW_DATA_DIR,
    TARGET_MUNICIPIOS,
)

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)  # Disable warnings for unverified SSL certificates.

app = typer.Typer()


@app.command()
def download_drought_data(start_year: int = 2019, end_year: int = 2024):
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
    df_melted = df_sonora.melt(
        id_vars=id_vars, var_name="fecha", value_name="categoria_sequia"
    )

    # 6. Clean and convert dates
    df_melted["fecha"] = pd.to_datetime(
        df_melted["fecha"], errors="coerce", format="mixed"
    )
    df_melted = df_melted.dropna(subset=["fecha"])

    # 7. Filtrar estrictamente el rango de años
    df_melted["Anio"] = df_melted["fecha"].dt.year
    df_filtered = df_melted[
        (df_melted["Anio"] >= start_year) & (df_melted["Anio"] <= end_year)
    ].copy()

    # 8. Strictly filter the year range
    df_filtered["severidad_num"] = (
        df_filtered["categoria_sequia"]
        .map(DROUGHT_SEVERITY_MAP)
        .fillna(0)
        .astype(int)
    )

    # 9. Save a separate CSV file for each year
    for year, df_year in df_filtered.groupby("Anio"):
        output_csv = output_dir / f"sonora_sequia_{year}.csv"
        df_year.to_csv(output_csv, index=False, encoding="utf-8-sig")
        logger.success(f"Año {year}: Descargado con éxito")

    logger.success("¡Proceso de sequía por año completado exitosamente!")


def download_rain_data(start_year: int = 2019, end_year: int = 2024):
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )  # Desactivar avisos de certificados SSL no verificados.

    # Definicion de la URL de la base de datos de lluvia del SMN (Servicio Meteorológico Nacional) de CONAGUA.
    # Ruta para guardar en data/raw/ subiendo un nivel desde la carpeta notebooks/
    # Usamos '..' para salir de notebooks/ hacia la raíz del proyecto

    main_folder = RAW_DATA_DIR
    os.makedirs(main_folder, exist_ok=True)

    # Cabecera HTTP estándar para simular una petición de navegador.
    headers = {"User-Agent": "Mozilla/5.0"}

    # Bucle for para recorrer cada año en el rango definido y descargar los archivos de lluvia correspondientes a cada mes.
    for current_year in range(start_year, end_year):
        year_str = str(current_year)
        logger.info(f"--- Descarga del año: {year_str} ---")
        # Creamos una subcarpeta para cada año (ej. ../data/raw/datos_lluvia_2019_2023/lluvia_2019)
        year_folder = os.path.join(main_folder, "lluvia_" + year_str)
        os.makedirs(year_folder, exist_ok=True)

        # Recorremos los meses del 1 al 12 (enero a diciembre)
        for month in range(1, 13):
            mes_str = str(month).zfill(2)
            file_name = (
                year_str + mes_str + "010000Lluv.csv"
            )  # Formato: [AÑO] + [MES] + 010000Lluv.csv
            file_url = (
                CONAGUA_BASE_URL + "/" + file_name
            )  # Url completa del archivo en el servidor
            local_path = os.path.join(
                year_folder, file_name
            )  # Ruta local final del archivo

            try:
                res = requests.get(
                    file_url, headers=headers, verify=False
                )  # Peticion GET al servidor

                if res.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(res.content)
                    logger.success(
                        f"Año {year_str} | Mes {mes_str}: Descargado con éxito"
                    )
                else:
                    # Si el mes no está disponible en el servidor (ej. código 404)
                    logger.warning(
                        f"Año {year_str} | Mes {mes_str}: No disponible (Status {res.status_code})"
                    )
            except Exception as e:
                # Por si se interrumpe la conexión a internet
                logger.error("Error al descargar %s: %s", file_name, e)

    logger.success("Descargas de lluvia completadas.")


@app.command()
def download_temperature_data(start_year: int = 2019, end_year: int = 2024):
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
    for current_year in range(start_year, end_year):
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
                    logger.success(
                        f"Año {year_str} | Mes {mes_str}: Descargado con éxito"
                    )
                else:
                    logger.warning(
                        f"Año {year_str} | Mes {mes_str}: No disponible (Status"
                        f" {res.status_code})"
                    )

                # Pausa de cortesía para no saturar al SMN
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error al descargar {file_name}: {e}")

    logger.success("Descargas de temperatura media completadas.")


def _download_marginacion_file(
    url: str,
    dest_file: Path,
    session: requests.Session,
    overwrite: bool = False,
) -> Path:
    """Descarga un Excel a un archivo temporal y valida su firma antes de guardarlo."""
    if dest_file.exists() and not overwrite:
        logger.info(f"Ya existe, se omite: {dest_file.name}")
        return dest_file

    temporary_file = dest_file.with_suffix(f"{dest_file.suffix}.part")
    try:
        with session.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with temporary_file.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        file.write(chunk)

        with temporary_file.open("rb") as file:
            signature = file.read(8)
        is_excel = signature.startswith(b"PK") or signature.startswith(
            b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
        )
        if not is_excel:
            raise ValueError(
                f"Lo descargado de {url} no parece un archivo Excel válido."
            )

        temporary_file.replace(dest_file)
    finally:
        temporary_file.unlink(missing_ok=True)

    logger.success(
        f"Descargado: {dest_file.name} ({dest_file.stat().st_size / 1024:.1f} KB)"
    )
    return dest_file


@app.command()
def download_marginacion_data(overwrite: bool = False):
    """Descarga los índices municipales de marginación de 1990-2015 y 2020."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "*/*",
        }
    )
    retries = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        sources = (
            (
                "indice_marginacion_municipal_1990_2015.xlsx",
                MARGINACION_1990_2015_URL,
            ),
            ("indice_marginacion_municipal_2020.xlsx", MARGINACION_2020_URL),
        )
        for filename, url in sources:
            _download_marginacion_file(
                url,
                RAW_DATA_DIR / filename,
                session,
                overwrite=overwrite,
            )
    finally:
        session.close()


@app.command()
def download_marginacion_ageb_data(overwrite: bool = False):
    """Descarga el índice de marginación urbana a nivel AGEB (CONAPO 2020).

    Fuente: CSV nacional en datos.gob.mx (``config.MARGINACION_AGEB_URL``).
    Filtra Sonora y los municipios de ``config.TARGET_MUNICIPIOS`` y guarda
    el resultado en ``data/interim/marginacion_imu_2020.csv``.

    La cartografía de AGEB (geometrías) se obtiene por separado del INEGI —
    ver ``references/marginacion/data_dictionary_marginacion_imu_2020.md``.
    """
    raw_path = RAW_DATA_DIR / f"imu_{MARGINACION_AGEB_YEAR}.csv"
    output_dir = INTERIM_DATA_DIR / "marginacion"
    output_csv = output_dir / f"marginacion_imu_{MARGINACION_AGEB_YEAR}.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Descargar CSV nacional (requiere User-Agent de navegador)
    if not (raw_path.exists() and raw_path.stat().st_size > 0) or overwrite:
        logger.info(f"Descargando IMU {MARGINACION_AGEB_YEAR} desde datos.gob.mx...")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/csv,*/*",
        }
        try:
            with requests.get(
                MARGINACION_AGEB_URL, headers=headers, stream=True, timeout=120
            ) as response:
                response.raise_for_status()
                with raw_path.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR DE RED] No se pudo descargar IMU AGEB: {e}")
            raise
        logger.success(f"Descargado: {raw_path} ({raw_path.stat().st_size / 1e6:.1f} MB)")
    else:
        logger.info(f"Ya existe, se omite descarga: {raw_path}")

    # 2. Cargar solo las columnas necesarias y filtrar Sonora / municipios objetivo
    usecols = [
        "CVE_AGEB", "ENT", "NOM_ENT", "MUN", "NOM_MUN", "LOC", "NOM_LOC",
        "AGEB", "POB_TOTAL", "P6A14NAE", "SBASC", "PSDSS", "OVSDE", "OVSEE",
        "OVSAE", "OVPT", "OVSREF", "OVSINT", "OVSCEL", "OVHAC",
        "IM_2020", "GM_2020", "IMN_2020", "fn_CVE_AGEB", "fn_AGEB",
    ]
    logger.info("Filtrando AGEBs de Sonora y municipios objetivo...")
    df = pd.read_csv(raw_path, usecols=lambda c: c in usecols)

    df_sonora = df[df["ENT"].astype(str).str.zfill(2) == "26"].copy()
    if TARGET_MUNICIPIOS:
        # CVE_AGEB = ENT(2) + MUN(3) + LOC(4) + AGEB(4) -> municipio = pos 0:5
        muni_keys = {str(m).zfill(5) for m in TARGET_MUNICIPIOS}
        df_sonora = df_sonora[
            df_sonora["CVE_AGEB"].astype(str).str[:5].isin(muni_keys)
        ].copy()

    df_sonora.to_csv(output_csv, index=False, encoding="utf-8-sig")
    logger.success(
        f"Guardado: {output_csv} "
        f"({len(df_sonora)} AGEBs de {df_sonora['NOM_MUN'].nunique()} municipios)"
    )


@app.command()
def download_marginacion_municipal_csvs(overwrite: bool = False):
    """Descarga los CSV municipales modernos (2010, 2015, 2020) de datos.gob.mx.

    Serie con esquema ``IM_YYYY/GM_YYYY/IMN_YYYY`` (ver
    ``references/marginacion/data_dictionary_marginacion_municipal.md``).
    Los CSV son nacionales; se filtran a Sonora (``CVE_ENT=26``) y se guardan
    en ``data/interim/marginacion/``.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/csv,*/*",
    }
    output_dir = INTERIM_DATA_DIR / "marginacion"
    output_dir.mkdir(parents=True, exist_ok=True)

    for year, url in MARGINACION_MUNICIPAL_CSV_URLS.items():
        raw_path = RAW_DATA_DIR / f"marginacion_municipal_imm_{year}.csv"
        output_csv = output_dir / f"marginacion_municipal_{year}.csv"

        if not (raw_path.exists() and raw_path.stat().st_size > 0) or overwrite:
            logger.info(f"Descargando marginación municipal {year}...")
            try:
                with requests.get(
                    url, headers=headers, stream=True, timeout=60
                ) as response:
                    response.raise_for_status()
                    with raw_path.open("wb") as f:
                        for chunk in response.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                f.write(chunk)
            except requests.exceptions.RequestException as e:
                logger.error(f"[ERROR DE RED] {year}: {e}")
                continue
            logger.success(f"{year}: descargado ({raw_path.stat().st_size / 1e6:.1f} MB)")

        logger.info(f"Filtrando Sonora ({year})...")
        df = pd.read_csv(raw_path)
        cve_ent_col = next(
            (c for c in df.columns if str(c).upper() in ("CVE_ENT", "ENT")), None
        )
        if cve_ent_col is not None:
            df_sonora = df[
                df[cve_ent_col].astype(str).str.replace(".0", "", regex=False).str.zfill(2) == "26"
            ].copy()
        else:
            df_sonora = df.copy()

        df_sonora.to_csv(output_csv, index=False, encoding="utf-8-sig")
        logger.success(
            f"{year}: {len(df_sonora)} municipios guardados en {output_csv.name}"
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
def data_ingestion_pipeline(start_year: int = 2019, end_year: int = 2024):
    """Ejecuta la descarga de las capas disponibles en un solo paso."""
    logger.info("=== Iniciando pipeline de ingesta de datos ===")

    logger.info("Paso 1/5: Descargando y preprocesando datos de sequía...")
    download_drought_data(start_year, end_year)

    logger.info("Paso 2/5: Descargando datos de lluvia...")
    download_rain_data(start_year, end_year)

    logger.info("Paso 3/5: Descargando datos de temperatura media...")
    download_temperature_data(start_year, end_year)

    logger.info("Paso 4/5: Descargando datos de marginación municipal...")
    download_marginacion_data()

    logger.info("Paso 5/6: Descargando marginación AGEB (CONAPO 2020)...")
    download_marginacion_ageb_data()

    logger.info("Paso 6/6: Descargando marginación municipal moderna (2010-2020)...")
    download_marginacion_municipal_csvs()

    logger.info("Capas pendientes (aire, salud)...")
    download_air_quality_data()
    download_respiratory_health_data()

    logger.warning(
        "Pipeline completado con advertencias: las capas de aire y salud "
        "están pendientes de fuente. Ver docs/docs/protocolo_eda.md."
    )


if __name__ == "__main__":
    app()
