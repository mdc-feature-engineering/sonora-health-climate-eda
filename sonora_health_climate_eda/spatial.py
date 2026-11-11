"""Utilidades de integración espacial para el análisis EDA.

Soporta el *spatial join* entre AGEBs (o municipios) y estaciones de
monitoreo (clima, calidad del aire), y el filtrado por clave INEGI.
"""

import geopandas as gpd
from loguru import logger
import pandas as pd

from sonora_health_climate_eda.config import (
    HERMOSILLO_CVE_MUN,
    TARGET_MUNICIPIOS,
)


def filter_by_municipio(
    df: pd.DataFrame,
    cve_mun: str | int | list[str | int] | None = None,
    cve_col: str = "CVE_MUN",
) -> pd.DataFrame:
    """Filtra un DataFrame por clave de municipio INEGI.

    Parameters
    ----------
    df : pd.DataFrame
        Datos con columna de clave municipal.
    cve_mun : str | int | list | None
        Clave(s) a conservar. Si es ``None``, usa ``TARGET_MUNICIPIOS``
        de la configuración (Hermosillo por defecto).
    cve_col : str
        Nombre de la columna de clave. Por defecto ``"CVE_MUN"``.

    Returns
    -------
    pd.DataFrame
        Subconjunto filtrado.
    """
    if cve_mun is None:
        cve_mun = TARGET_MUNICIPIOS

    claves = [str(c).zfill(5) for c in ([cve_mun] if not isinstance(cve_mun, list) else cve_mun)]
    mask = df[cve_col].astype(str).str.zfill(5).isin(claves)
    filtered = df.loc[mask].copy()
    logger.info(f"Filtro municipal {claves}: {len(filtered)}/{len(df)} registros.")
    return filtered


def stations_to_gdf(
    stations: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """Convierte una tabla de estaciones en GeoDataFrame.

    Parameters
    ----------
    stations : pd.DataFrame
        Tabla con columnas de latitud y longitud.
    lat_col, lon_col : str
        Nombres de columnas.
    crs : str
        Sistema de referencia (por defecto WGS84).

    Returns
    -------
    gpd.GeoDataFrame
    """
    return gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations[lon_col], stations[lat_col]),
        crs=crs,
    )


def assign_stations_to_areas(
    areas_gdf: gpd.GeoDataFrame,
    stations_gdf: gpd.GeoDataFrame,
    how: str = "left",
) -> gpd.GeoDataFrame:
    """Asigna cada estación a su AGEB/municipio mediante spatial join.

    Parameters
    ----------
    areas_gdf : gpd.GeoDataFrame
        Polígonos de AGEBs o municipios (deben compartir CRS con las
        estaciones; usar ``to_crs`` antes si es necesario).
    stations_gdf : gpd.GeoDataFrame
        Puntos de estaciones de monitoreo.
    how : str
        Tipo de join (``"left"`` por defecto).

    Returns
    -------
    gpd.GeoDataFrame
        Estaciones con la clave geográfica del área asignada. Si un área
        contiene varias estaciones, todas se conservan; la agregación
        posterior (promedio, interpolación) se hace en el notebook de EDA.
    """
    if areas_gdf.crs != stations_gdf.crs:
        stations_gdf = stations_gdf.to_crs(areas_gdf.crs)

    joined = gpd.sjoin(
        stations_gdf,
        areas_gdf[[c for c in areas_gdf.columns if c != "geometry"] + ["geometry"]],
        how=how,
        predicate="within",
    )
    logger.info(
        f"Spatial join: {len(stations_gdf)} estaciones → "
        f"{joined['index_right'].nunique() if 'index_right' in joined else '?'} áreas."
    )
    return joined


def clip_to_hermosillo(
    gdf: gpd.GeoDataFrame,
    cve_urbana: str | None = HERMOSILLO_CVE_MUN,
) -> gpd.GeoDataFrame:
    """Recorta un GeoDataFrame a los AGEBs/municipios objetivo.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Capa geográfica (AGEB o municipio).
    cve_urbana : str | None
        Prefijo o clave municipal a conservar. ``None`` usa todos los
        ``TARGET_MUNICIPIOS``.

    Returns
    -------
    gpd.GeoDataFrame
    """
    claves = TARGET_MUNICIPIOS if cve_urbana is None else [cve_urbana]
    # Heurística: buscar una columna de clave que empiece con CVE o CVEGEO
    cve_col = next(
        (c for c in gdf.columns if str(c).upper().startswith(("CVE", "GEO"))),
        None,
    )
    if cve_col is None:
        logger.warning("No se encontró columna de clave; se devuelve todo el gdf.")
        return gdf
    mask = gdf[cve_col].astype(str).str.startswith(tuple(claves))
    return gdf.loc[mask].copy()
