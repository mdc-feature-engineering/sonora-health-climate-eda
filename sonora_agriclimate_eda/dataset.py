import time
from pathlib import Path
import pandas as pd
import requests
from loguru import logger
from tqdm import tqdm
import typer
import os
import urllib3
import time
import io
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sonora_agriclimate_eda.config import (
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    SONORA_AGRICULTURE_URL,
    CONAGUA_BASE_URL,
    CONAGUA_DROUGHT_URL,
    HIDRICO_SONORA_URL,
    MARGINACION_1990_2015_URL,
    MARGINACION_2020_URL,
)

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)  # Disable warnings for unverified SSL certificates.

app = typer.Typer()


@app.command()
def download_agriculture_data(start_year: int = 2019, end_year: int = 2024):
    """Descarga los datos de agricultura de Sonora por año."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    years = range(start_year, end_year + 1)

    for year in tqdm(years, total=len(years)):
        url = SONORA_AGRICULTURE_URL.format(year=year)
        dest_file = RAW_DATA_DIR / f"agricultura-sonora-{year}.xlsx"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(dest_file, "wb") as f:
                f.write(response.content)

            # logger.info(f"Downloaded agriculture {year} -> {dest_file}")
            logger.success(f"Año {year}: Descargado con éxito")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to download agriculture {year}: {e}")

    logger.success("Agriculture download complete.")


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
    severity_map = {"Sin Sequía": 0, "D0": 1, "D1": 2, "D2": 3, "D3": 4, "D4": 5}
    df_filtered["severidad_num"] = (
        df_filtered["categoria_sequia"].map(severity_map).fillna(0).astype(int)
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

    logger.success("Descargas de 2019 a 2023 completadas.")


@app.command()
def download_temperature_data(start_year: int = 2019, end_year: int = 2024):
    """Descarga los archivos mensuales de temperatura media (TMed) directamente en data/raw/."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 1. Asegurar que la carpeta data/raw exista
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Cabeceras con Referer para evitar rechazos o Status 500 del servidor
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        "Referer": (
            "https://smn.conagua.gob.mx/es/climatologia/temperaturas-y-lluvias/resumenes-mensuales-de-temperaturas-y-lluvias"
        ),
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


@app.command()
def download_hidrico_data():
    """Descarga el archivo de recursos hídricos (presas) de Sonora."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    dest_file = RAW_DATA_DIR / "hidrico_sonora_2020-actualidad2024.xlsx"

    try:
        response = requests.get(HIDRICO_SONORA_URL, timeout=30)
        response.raise_for_status()

        with open(dest_file, "wb") as f:
            f.write(response.content)

        logger.success(f"Archivo descargado con éxito: {dest_file}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to download hidrico data: {e}")


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


def download_siap_sonora(start_year: int, end_year: int):
    """
    Download SIAP data (Agricultural Year-End Report) for a range of years, filtering for the state of Sonora (IdEstado == 26).
    """
    root = Path().resolve().parent
    output_dir = INTERIM_DATA_DIR / "sonora_siap"
    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php"
    }
    session.headers.update(headers)
    
    logger.info(f"-> Conectando al portal del SIAP para obtener enlaces...")
    try:
        main_page_url = "https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php"
        response_main = session.get(main_page_url, timeout=30)
        
        if response_main.status_code != 200:
            logger.warning(f"[ERROR API] No se pudo acceder a la página principal del SIAP (HTTP {response_main.status_code})")
            return
            
        soup = BeautifulSoup(response_main.text, "html.parser")
        
        for anio in range(start_year, end_year + 1):
            logger.info(f"\n--- Procesando año: {anio} ---")
            output_path = output_dir / f"siap_sonora_cierre_{anio}.csv"
            
            # Look for the link corresponding to the current year of the loop.
            target_href = None
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if f"ANIO={anio}" in href.upper() or f"anio={anio}" in href:
                    target_href = href
                    break
                    
            if not target_href:
                logger.warning(f"[AVISO] No se encontró un enlace de descarga para el año {anio} en el portal. Omitiendo...")
                continue
                
            # Construct the full URL
            if target_href.startswith("/"):
                download_url = f"https://nube.agricultura.gob.mx{target_href}"
            elif target_href.startswith("http"):
                download_url = target_href
            else:
                download_url = f"https://nube.agricultura.gob.mx/datosAbiertos/{target_href}"
                
            logger.info(f"-> Descargando CSV para {anio}...")
            response_csv = session.get(download_url, timeout=60)
            
            if response_csv.status_code != 200:
                logger.warning(f"[ERROR API] Falló la descarga para el año {anio} (HTTP {response_csv.status_code})")
                continue
                
            # Verify that it does not return HTML by mistake.
            content_snippet = response_csv.content[:200].decode("latin1", errors="ignore")
            if "<html" in content_snippet.lower() or "<doctype" in content_snippet.lower():
                logger.warning(f"[ERROR API] El enlace para {anio} devolvió HTML en lugar de CSV.")
                continue
                
            df = pd.read_csv(
                io.StringIO(response_csv.content.decode("latin1")), 
                sep=None, 
                engine="python", 
                on_bad_lines="skip"
            )
            
            df.columns = [col.strip() for col in df.columns]
            estado_col = next((col for col in df.columns if "estado" in col.lower()), None)
            
            if not estado_col:
                logger.warning(f"[ERROR] No se encontró columna de estado para el año {anio}. Columnas: {list(df.columns)}")
                continue
                
            # Filter by Sonora (StateId == 26 or text)
            if df[estado_col].dtype in ["int64", "float64"]:
                df_sonora = df[df[estado_col] == 26].copy()
            else:
                df_sonora = df[df[estado_col].astype(str).str.contains("Sonora", case=False, na=False)].copy()
                
            if df_sonora.empty:
                logger.warning(f"[AVISO] El archivo de {anio} se descargó, pero no traía registros para Sonora.")
            else:
                df_sonora.to_csv(output_path, index=False, encoding="utf-8-sig")
                logger.success(f"¡Éxito! Datos de Sonora ({anio}) guardados en: {output_path.name}")
                logger.info(f"Total de registros: {len(df_sonora)}")
                
    except Exception as e:
        logger.warning(f"[ERROR API] Ocurrió un error en el proceso por rangos: {e}")


@app.command()
def data_ingestion_pipeline(start_year: int = 2019, end_year: int = 2024):
    """Ejecuta la descarga de agricultura y el procesamiento de sequía en un solo paso."""
    logger.info("=== Iniciando pipeline completo de datos ===")

    logger.info("Paso 1/7: Descargando datos de agricultura...")
    download_agriculture_data(start_year, end_year)

    logger.info("Paso 2/7: Descargando y preprocesando datos de sequía...")
    download_drought_data(start_year, end_year)

    logger.info("Paso 3/7: Descargando datos de lluvia...")
    download_rain_data(start_year, end_year)

    logger.info("Paso 4/7: Descargando datos de temperatura media...")
    download_temperature_data(start_year, end_year)

    logger.info("Paso 5/7: Descargando datos de recursos hídricos...")
    download_hidrico_data()
    
    logger.info("Paso 6/7: Descargando datos de SIAP...")
    download_siap_sonora(start_year, end_year)

    logger.info("Paso 7/7: Descargando datos de marginación...")
    download_marginacion_data()

    logger.success("¡Pipeline completo ejecutado con éxito!")


if __name__ == "__main__":
    app()
