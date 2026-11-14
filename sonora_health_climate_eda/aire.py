"""Calidad del aire de Hermosillo (RUOA-UNAM, observatorio ERNO): horas → días → meses.

Cada paso tiene su notebook y su comando equivalente (salidas en
``data/interim/aire/``):

1. Ingesta — ``notebooks/01_ingesta/1.4-calidad-aire.ipynb``::

       python -m sonora_health_climate_eda.dataset download-air-quality-data  # CSV crudos
       python -m sonora_health_climate_eda.aire horario   # -> aire_hermosillo_horario.csv

   ``aire_hermosillo_horario.csv`` junta los CSV mensuales sin limpiar: el
   valor tal como lo reporta RUOA y su bandera (``OK``, ``BDL``, ``OR``, ``OS``).

2. Procesamiento — ``notebooks/02_procesamiento/2.4-procesamiento-calidad-aire.ipynb``::

       python -m sonora_health_climate_eda.aire diario    # -> aire_hermosillo_diario.csv
       python -m sonora_health_climate_eda.aire mensual   # -> aire_hermosillo_mensual.csv

Control de calidad de cada hora (``clean_hourly``; constantes en ``config.py``,
sección Capa 4):

1. Solo cuentan las banderas ``OK`` y ``BDL``; ``OR`` (fuera de rango) y
   ``OS`` (fuera de servicio) quedan como NaN.
2. ``BDL`` (bajo el límite de detección) se sustituye por la mitad del límite;
   RUOA reporta en esas horas ceros y negativos.
3. O3 por encima de ``AIR_QUALITY_MAX_PLAUSIBLE`` es un artefacto del equipo → NaN.
4. PM2.5 mayor que PM10 + tolerancia en la misma hora (ambas OK) → NaN.

Suficiencia (75 %):

- Día: al menos 18 horas válidas y menos de 75 % de ellas en BDL (un sensor
  que falla reporta horas seguidas en cero con bandera BDL).
- O3 8 h: promedio móvil de las 8 horas que terminan en cada hora, con al
  menos 6 válidas; el máximo diario necesita al menos 18 promedios válidos.
- Mes: al menos 75 % de los días del mes con dato válido.

Un estadístico que no cumple la suficiencia queda en NaN; las columnas de
conteo (``*_horas_validas``, ``*_horas_bdl``, ``*_dias_validos``) dicen por qué.
"""

import io
import math
from pathlib import Path

from loguru import logger
import numpy as np
import pandas as pd
import typer

from sonora_health_climate_eda.config import (
    AIR_QUALITY_DETECTION_LIMITS,
    AIR_QUALITY_INTERIM_DIR,
    AIR_QUALITY_MAX_BDL_FRACTION,
    AIR_QUALITY_MAX_PLAUSIBLE,
    AIR_QUALITY_MIN_COVERAGE,
    AIR_QUALITY_NOM_LIMITS,
    AIR_QUALITY_PM25_PM10_TOLERANCE,
    AIR_QUALITY_POLLUTANTS,
    AIR_QUALITY_RAW_DIR,
    AIR_QUALITY_UNITS,
)

app = typer.Typer()

HOURLY_PATH = AIR_QUALITY_INTERIM_DIR / "aire_hermosillo_horario.csv"
DAILY_PATH = AIR_QUALITY_INTERIM_DIR / "aire_hermosillo_diario.csv"
MONTHLY_PATH = AIR_QUALITY_INTERIM_DIR / "aire_hermosillo_mensual.csv"

# Contaminante RUOA -> prefijo de columna; unidad RUOA -> sufijo de columna.
_PREFIX = {"PM2.5": "pm25", "PM10": "pm10", "O3": "o3"}
_UNIT_SUFFIX = {"ug/m^3": "ugm3", "ppb": "ppb"}


def col(pollutant: str, stat: str = "") -> str:
    """Nombre de columna de un contaminante: ``pm25_ugm3``, ``o3_max8h_ppb``..."""
    unit = _UNIT_SUFFIX[AIR_QUALITY_UNITS[pollutant]]
    return "_".join(part for part in (_PREFIX[pollutant], stat, unit) if part)


def flag_col(pollutant: str) -> str:
    """Columna con la bandera RUOA de un contaminante: ``pm25_bandera``..."""
    return f"{_PREFIX[pollutant]}_bandera"


def normed_col(pollutant: str) -> str:
    """Métrica diaria que se compara con la NOM: 24 h (PM) o máximo de 8 h (O3)."""
    return col(pollutant, "max8h") if pollutant == "O3" else col(pollutant)


# ---------------------------------------------------------------------------
# 1. Ingesta: CSV mensuales crudos -> tabla horaria sin limpiar
# ---------------------------------------------------------------------------
def read_ruoa_file(path: Path) -> pd.DataFrame:
    """Lee un CSV mensual de RUOA sin las líneas de metadatos ni la fila de unidades.

    Devuelve ``fecha_hora`` y, por cada contaminante de
    ``AIR_QUALITY_POLLUTANTS``, el valor tal como viene (``pm25_ugm3``) y su
    bandera (``pm25_bandera``). Valida que las unidades sean las esperadas.
    Algunos meses no traen NO ni CO; esas columnas no se usan.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.startswith("Time,")), None)
    if header_idx is None or header_idx + 1 >= len(lines):
        raise ValueError(f"{path.name}: no tiene el encabezado 'Time,' de RUOA.")
    header = lines[header_idx].split(",")
    units = dict(zip(header, lines[header_idx + 1].split(",")))
    body = "\n".join([lines[header_idx], *lines[header_idx + 2 :]])
    df = pd.read_csv(io.StringIO(body), na_values=["null"])

    for pol in AIR_QUALITY_POLLUTANTS:
        if pol not in df.columns:
            logger.warning(f"{path.name}: sin columna {pol}; se toma como fuera de servicio.")
            df[pol] = np.nan
            df[f"{pol}_flag"] = "OS"
        elif units.get(pol) != AIR_QUALITY_UNITS[pol]:
            raise ValueError(
                f"{path.name}: {pol} viene en {units.get(pol)!r}, "
                f"se esperaba {AIR_QUALITY_UNITS[pol]!r}."
            )

    out = pd.DataFrame({"fecha_hora": pd.to_datetime(df["Time"], format="%Y-%m-%d %H:%M:%S")})
    for pol in AIR_QUALITY_POLLUTANTS:
        out[col(pol)] = pd.to_numeric(df[pol], errors="coerce")
        out[flag_col(pol)] = df[f"{pol}_flag"]
    return out


def consolidate_hourly(raw_dir: Path = AIR_QUALITY_RAW_DIR) -> pd.DataFrame:
    """Junta los CSV mensuales crudos en una sola tabla horaria, sin limpiar.

    Solo ordena por ``fecha_hora`` y quita horas duplicadas entre archivos
    (se conserva la primera). Los valores y banderas quedan como en RUOA.
    """
    files = sorted(raw_dir.glob("*-ERNO_hora_L1_caire.csv"))
    if not files:
        raise FileNotFoundError(
            f"No hay CSV de RUOA en {raw_dir}. Descárgalos primero con: "
            "python -m sonora_health_climate_eda.dataset download-air-quality-data"
        )
    df = pd.concat([read_ruoa_file(f) for f in files], ignore_index=True)
    df = df.sort_values("fecha_hora", kind="stable")
    dup = df["fecha_hora"].duplicated()
    if dup.any():
        logger.warning(f"RUOA: {int(dup.sum())} horas duplicadas; se conserva la primera.")
        df = df[~dup]
    logger.info(
        f"RUOA horario: {len(files)} archivos, {len(df)} horas "
        f"({df['fecha_hora'].min():%Y-%m-%d} a {df['fecha_hora'].max():%Y-%m-%d})."
    )
    return df.reset_index(drop=True)


def load_hourly(path: Path = HOURLY_PATH) -> pd.DataFrame:
    """Lee la tabla horaria sin limpiar que deja la ingesta (``aire horario`` o 1.4)."""
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Corre primero la ingesta "
            "(notebook 1.4 o python -m sonora_health_climate_eda.aire horario)."
        )
    return pd.read_csv(path, parse_dates=["fecha_hora"])


# ---------------------------------------------------------------------------
# 2. Procesamiento: limpieza horaria y agregación a días y meses
# ---------------------------------------------------------------------------
def clean_hourly(hourly: pd.DataFrame) -> pd.DataFrame:
    """Aplica el control de calidad horario (pasos 1–4 del docstring del módulo).

    Parte de la tabla horaria sin limpiar y la lleva a una malla horaria
    completa (índice ``fecha_hora``): las horas sin registro cuentan como no
    válidas y el promedio móvil de 8 h no salta huecos. Devuelve, por
    contaminante, el valor limpio (``pm25_ugm3``...) y si la hora fue BDL
    (``pm25_bdl``...).
    """
    raw = hourly.set_index("fecha_hora").sort_index()
    start = raw.index.min().floor("D")
    end = raw.index.max().floor("D") + pd.Timedelta(hours=23)
    grid = pd.date_range(start, end, freq="h", name="fecha_hora")
    if len(grid) > len(raw):
        logger.info(f"Malla horaria: {len(grid) - len(raw)} horas sin registro en RUOA.")
    raw = raw.reindex(grid)

    out = pd.DataFrame(index=raw.index)
    for pol in AIR_QUALITY_POLLUTANTS:
        flag = raw[flag_col(pol)]
        value = raw[col(pol)].where(flag.isin(["OK", "BDL"]))
        bdl = flag.eq("BDL") & value.notna()
        value = value.mask(bdl, AIR_QUALITY_DETECTION_LIMITS[pol] / 2)

        cap = AIR_QUALITY_MAX_PLAUSIBLE.get(pol)
        if cap is not None:
            implausible = value > cap
            if implausible.any():
                logger.info(f"{pol}: {int(implausible.sum())} horas > {cap:g} descartadas.")
            value = value.mask(implausible)

        out[col(pol)] = value
        out[f"{_PREFIX[pol]}_bdl"] = bdl

    if {"PM2.5", "PM10"} <= set(AIR_QUALITY_POLLUTANTS):
        pm25, pm10 = col("PM2.5"), col("PM10")
        both_ok = raw[flag_col("PM2.5")].eq("OK") & raw[flag_col("PM10")].eq("OK")
        excess = both_ok & (out[pm25] > out[pm10] + AIR_QUALITY_PM25_PM10_TOLERANCE)
        if excess.any():
            logger.info(f"PM2.5: {int(excess.sum())} horas con PM2.5 > PM10 descartadas.")
        out.loc[excess, pm25] = np.nan
    return out


def aggregate_daily(clean: pd.DataFrame) -> pd.DataFrame:
    """Agrega las horas limpias (salida de ``clean_hourly``) a días en hora local.

    Columnas por contaminante: promedio de 24 h (``pm25_ugm3``), máximo
    horario (``pm25_max1h_ugm3``), horas válidas y horas BDL; para O3 además
    el máximo diario del promedio móvil de 8 h (``o3_max8h_ppb``).
    """
    day = clean.index.floor("D")
    min_hours = math.ceil(24 * AIR_QUALITY_MIN_COVERAGE)  # 18 de 24
    min_hours_8h = math.ceil(8 * AIR_QUALITY_MIN_COVERAGE)  # 6 de 8

    cols = {}
    for pol in AIR_QUALITY_POLLUTANTS:
        key = _PREFIX[pol]
        g = clean[col(pol)].groupby(day)
        n_valid = g.count()
        n_bdl = clean[f"{key}_bdl"].groupby(day).sum()
        ok = (n_valid >= min_hours) & (n_bdl < AIR_QUALITY_MAX_BDL_FRACTION * n_valid)

        cols[col(pol)] = g.mean().where(ok)
        cols[col(pol, "max1h")] = g.max().where(ok)
        if pol == "O3":
            # Cada promedio se asigna a la última de sus 8 horas, así que los
            # primeros de cada día usan horas del día anterior.
            ma8 = clean[col(pol)].rolling(8, min_periods=min_hours_8h).mean()
            g8 = ma8.groupby(day)
            cols[col(pol, "max8h")] = g8.max().where(ok & (g8.count() >= min_hours))
        cols[f"{key}_horas_validas"] = n_valid
        cols[f"{key}_horas_bdl"] = n_bdl.astype(int)

    # Dos decimales, como RUOA: el CSV y la tabla en memoria quedan iguales y el
    # mensual sale idéntico desde la notebook o desde el comando.
    out = pd.DataFrame(cols).round(2)
    out.index.name = "fecha"
    return out.reset_index()


def aggregate_monthly(daily: pd.DataFrame) -> pd.DataFrame:
    """Agrega los días (salida de ``aggregate_daily``) a meses.

    Columnas por contaminante:

    - ``pm25_ugm3`` / ``o3_ppb``: media mensual de los promedios de 24 h.
    - ``o3_max8h_ppb``: media mensual del máximo diario de 8 h.
    - ``pm25_max_diario_ugm3`` / ``o3_max8h_max_ppb``: el peor día del mes.
    - ``*_dias_excede_nom``: días sobre el límite de ``AIR_QUALITY_NOM_LIMITS``.
    - ``*_dias_validos``: días con la métrica normada; decide la suficiencia.

    ``fecha_mes`` es el primer día del mes, como en el resto del panel.
    """
    daily = daily.assign(fecha=pd.to_datetime(daily["fecha"])).set_index("fecha")
    month = daily.index.to_period("M").to_timestamp()

    cols = {}
    for pol in AIR_QUALITY_POLLUTANTS:
        key = _PREFIX[pol]
        normed = daily[normed_col(pol)]
        g = normed.groupby(month)
        n_days = g.count()
        ok = n_days >= AIR_QUALITY_MIN_COVERAGE * n_days.index.days_in_month

        cols[col(pol)] = daily[col(pol)].groupby(month).mean().where(ok)
        if pol == "O3":
            cols[col(pol, "max8h")] = g.mean().where(ok)
            cols[col(pol, "max8h_max")] = g.max().where(ok)
        else:
            cols[col(pol, "max_diario")] = g.max().where(ok)
        exceed = (normed > AIR_QUALITY_NOM_LIMITS[pol]).groupby(month).sum()
        cols[f"{key}_dias_excede_nom"] = exceed.where(ok).astype("Int64")
        cols[f"{key}_dias_validos"] = n_days

    # Dos decimales, como RUOA: el CSV y la tabla en memoria quedan iguales y el
    # mensual sale idéntico desde la notebook o desde el comando.
    out = pd.DataFrame(cols).round(2)
    out.index.name = "fecha_mes"
    return out.reset_index()


def valid_by_year(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Filas (días o meses) con la métrica normada válida, por año y contaminante."""
    year = pd.to_datetime(df[date_col]).dt.year.rename("anio")
    valid = pd.DataFrame({pol: df[normed_col(pol)].notna() for pol in AIR_QUALITY_POLLUTANTS})
    return valid.groupby(year).sum()


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
@app.command("horario")
def build_hourly(raw_dir: Path = AIR_QUALITY_RAW_DIR, output_path: Path = HOURLY_PATH):
    """CSV mensuales crudos de RUOA → tabla horaria sin limpiar (ingesta)."""
    hourly = consolidate_hourly(raw_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(output_path, index=False)
    logger.success(f"Tabla horaria: {len(hourly)} horas en {output_path}")


@app.command("diario")
def build_daily(input_path: Path = HOURLY_PATH, output_path: Path = DAILY_PATH):
    """Tabla horaria → limpieza → serie diaria de Hermosillo."""
    daily = aggregate_daily(clean_hourly(load_hourly(input_path)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(output_path, index=False)
    logger.info(
        "Días válidos por año (PM: 24 h; O3: máx. 8 h):\n"
        + valid_by_year(daily, "fecha").to_string()
    )
    logger.success(f"Serie diaria: {len(daily)} días en {output_path}")


@app.command("mensual")
def build_monthly(input_path: Path = DAILY_PATH, output_path: Path = MONTHLY_PATH):
    """Serie diaria → serie mensual de Hermosillo (requiere correr ``diario`` antes)."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"No existe {input_path}. Corre primero: python -m sonora_health_climate_eda.aire diario"
        )
    monthly = aggregate_monthly(pd.read_csv(input_path, parse_dates=["fecha"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(output_path, index=False)
    logger.info("Meses válidos por año:\n" + valid_by_year(monthly, "fecha_mes").to_string())
    logger.success(f"Serie mensual: {len(monthly)} meses en {output_path}")


if __name__ == "__main__":
    app()
