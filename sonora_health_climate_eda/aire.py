"""Calidad del aire de Hermosillo (RUOA-UNAM, ERNO): horas → días → semanas y meses.

Cada paso tiene su notebook y su comando equivalente (tablas horaria y diaria
en ``data/interim/aire/``; datasets limpios semanal y mensual en
``data/processed/aire/``):

1. Ingesta — ``notebooks/01_ingesta/1.4-calidad-aire.ipynb``::

       python -m sonora_health_climate_eda.dataset download-air-quality-data  # CSV crudos
       python -m sonora_health_climate_eda.aire horario   # -> aire_hermosillo_horario.csv

   ``aire_hermosillo_horario.csv`` junta los CSV mensuales sin limpiar: el
   valor tal como lo reporta RUOA y su bandera (``OK``, ``BDL``, ``OR``, ``OS``).

2. Procesamiento — ``notebooks/02_procesamiento/2.4-procesamiento-calidad-aire.ipynb``::

       python -m sonora_health_climate_eda.aire diario    # -> interim: aire_hermosillo_diario.csv
       python -m sonora_health_climate_eda.aire semanal   # -> processed: ..._semanal.csv
       python -m sonora_health_climate_eda.aire mensual   # -> processed: ..._mensual.csv

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
- Semana epidemiológica (domingo a sábado): al menos 75 % de sus días con dato
  válido (6 de 7).
- Mes: al menos 75 % de los días del mes con dato válido.

Un estadístico que no cumple la suficiencia queda en NaN; las columnas de
conteo (``*_horas_validas``, ``*_horas_bdl``, ``*_dias_validos``) dicen por qué.

Huecos cortos (``interpolate_short_gaps``): en las tablas semanal y mensual,
los promedios de huecos de hasta ``AIR_QUALITY_MAX_INTERP_WEEKS`` semanas o
``AIR_QUALITY_MAX_INTERP_MONTHS`` meses se rellenan por interpolación lineal y
quedan marcados en ``*_interpolado``. Los huecos largos no se imputan. La
justificación está en la notebook 2.4.

Nivel del aire (``category_codes``): cada día se clasifica con las bandas del
Índice AIRE Y SALUD de la NOM-172-SEMARNAT-2019 (``AIR_QUALITY_INDEX_BANDS``),
de Buena a Extremadamente mala, por contaminante y para la peor de PM10 y O3.
Las tablas semanal y mensual guardan la categoría del peor día y los días
Aceptable o peor; no se clasifica el promedio, que esconde los días malos.
"""

import io
import math
from pathlib import Path

from loguru import logger
import numpy as np
import pandas as pd
import typer

from sonora_health_climate_eda.config import (
    AIR_QUALITY_CATEGORIES,
    AIR_QUALITY_DETECTION_LIMITS,
    AIR_QUALITY_INDEX_BANDS,
    AIR_QUALITY_INTERIM_DIR,
    AIR_QUALITY_MAX_BDL_FRACTION,
    AIR_QUALITY_MAX_INTERP_MONTHS,
    AIR_QUALITY_MAX_INTERP_WEEKS,
    AIR_QUALITY_MAX_PLAUSIBLE,
    AIR_QUALITY_MIN_COVERAGE,
    AIR_QUALITY_NOM_LIMITS,
    AIR_QUALITY_PM25_PM10_TOLERANCE,
    AIR_QUALITY_POLLUTANTS,
    AIR_QUALITY_PROCESSED_DIR,
    AIR_QUALITY_RAW_DIR,
    AIR_QUALITY_UNITS,
    PANEL_END_YEAR,
    PANEL_START_YEAR,
)

app = typer.Typer()

HOURLY_PATH = AIR_QUALITY_INTERIM_DIR / "aire_hermosillo_horario.csv"
DAILY_PATH = AIR_QUALITY_INTERIM_DIR / "aire_hermosillo_diario.csv"
WEEKLY_PATH = AIR_QUALITY_PROCESSED_DIR / "aire_hermosillo_semanal.csv"
MONTHLY_PATH = AIR_QUALITY_PROCESSED_DIR / "aire_hermosillo_mensual.csv"

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


# Peor categoría de PM10 y O3 (prefijo de columna). PM2.5 no entra: falta desde
# 2018 y el índice combinado mejoraría solo por dejar de medirlo.
COMBINED_KEY = "pm10_o3"


def _band_code(values: pd.Series, bands: list) -> pd.Series:
    """Código de la categoría (0 = Buena … 4 = Extremadamente mala); NaN si no hay valor."""
    return pd.cut(values, [-np.inf, *bands, np.inf], labels=False).astype(float)


def category_codes(daily: pd.DataFrame) -> pd.DataFrame:
    """Código de la categoría AIRE Y SALUD de cada día (NOM-172-SEMARNAT-2019).

    Columnas ``pm25``, ``pm10``, ``o3`` y ``pm10_o3``, con 0 = Buena …
    4 = Extremadamente mala. PM se clasifica con el promedio de 24 h; O3 con
    la peor de las categorías de su máximo de 1 h y de 8 h. Un día sin la
    métrica normada válida queda en NaN. ``pm10_o3`` es la peor de PM10 y O3
    y solo existe si los dos tienen dato.
    """
    codes = pd.DataFrame(index=daily.index)
    for pol in AIR_QUALITY_POLLUTANTS:
        if pol == "O3":
            code_1h = _band_code(daily[col(pol, "max1h")], AIR_QUALITY_INDEX_BANDS["O3_1h"])
            code_8h = _band_code(daily[col(pol, "max8h")], AIR_QUALITY_INDEX_BANDS["O3_8h"])
            code = np.fmax(code_1h, code_8h)
        else:
            code = _band_code(daily[col(pol)], AIR_QUALITY_INDEX_BANDS[pol])
        codes[_PREFIX[pol]] = code.where(daily[normed_col(pol)].notna())
    codes[COMBINED_KEY] = codes[[_PREFIX["PM10"], _PREFIX["O3"]]].max(axis=1, skipna=False)
    return codes


def category_label(codes: pd.Series) -> pd.Series:
    """Nombre de la categoría de cada código ("Buena", "Aceptable"...); NaN sigue en NaN."""
    return codes.map(dict(enumerate(AIR_QUALITY_CATEGORIES)))


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
    el máximo diario del promedio móvil de 8 h (``o3_max8h_ppb``). Al final,
    la categoría AIRE Y SALUD del día (``pm25_categoria``... y
    ``pm10_o3_categoria``, ver ``category_codes``).
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
    # Se clasifica con los valores ya redondeados: igual que al leer el CSV
    for key, codes in category_codes(out).items():
        out[f"{key}_categoria"] = category_label(codes)
    out.index.name = "fecha"
    return out.reset_index()


def _category_summary(codes: pd.Series, period: pd.Index, ok: pd.Series, key: str) -> dict:
    """Categoría del peor día y días Aceptable o peor por periodo; NaN sin suficiencia."""
    return {
        f"{key}_categoria_peor_dia": category_label(codes.groupby(period).max().where(ok)),
        f"{key}_dias_aceptable_o_peor": (codes >= 1).groupby(period).sum().where(ok).astype(float),
    }


def _aggregate_periods(daily: pd.DataFrame, period: pd.Index, n_days: pd.Series) -> pd.DataFrame:
    """Agrega los días a periodos; base de ``aggregate_weekly`` y ``aggregate_monthly``.

    ``daily`` viene indexado por ``fecha``; ``period`` asigna cada día a su
    periodo y ``n_days`` dice cuántos días tiene cada periodo. Un periodo es
    válido para un contaminante si al menos ``AIR_QUALITY_MIN_COVERAGE`` de
    sus días tienen la métrica normada; si no, sus estadísticos quedan en NaN.
    Del índice AIRE Y SALUD guarda la categoría del peor día y los días
    Aceptable o peor, por contaminante y para la peor de PM10 y O3.
    """
    codes = category_codes(daily)
    cols = {}
    for pol in AIR_QUALITY_POLLUTANTS:
        key = _PREFIX[pol]
        normed = daily[normed_col(pol)]
        g = normed.groupby(period)
        n_valid = g.count()
        ok = n_valid >= AIR_QUALITY_MIN_COVERAGE * n_days.reindex(n_valid.index).to_numpy()

        cols[col(pol)] = daily[col(pol)].groupby(period).mean().where(ok)
        if pol == "O3":
            cols[col(pol, "max8h")] = g.mean().where(ok)
            cols[col(pol, "max8h_max")] = g.max().where(ok)
        else:
            cols[col(pol, "max_diario")] = g.max().where(ok)
        exceed = (normed > AIR_QUALITY_NOM_LIMITS[pol]).groupby(period).sum()
        # float con NaN, como el resto de las columnas (no Int64 con <NA>): un solo
        # tipo de faltante, igual en memoria y al leer el CSV.
        cols[f"{key}_dias_excede_nom"] = exceed.where(ok).astype(float)
        cols.update(_category_summary(codes[key], period, ok, key))
        cols[f"{key}_dias_validos"] = n_valid

    # Peor de PM10 y O3: periodo válido si al menos 75 % de sus días tienen los dos
    both = codes[COMBINED_KEY]
    n_both = both.groupby(period).count()
    ok_both = n_both >= AIR_QUALITY_MIN_COVERAGE * n_days.reindex(n_both.index).to_numpy()
    cols.update(_category_summary(both, period, ok_both, COMBINED_KEY))
    cols[f"{COMBINED_KEY}_dias_validos"] = n_both

    # Dos decimales, como RUOA: el CSV y la tabla en memoria quedan iguales y
    # las tablas salen idénticas desde la notebook o desde el comando.
    return pd.DataFrame(cols).round(2)


def aggregate_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    """Agrega los días (salida de ``aggregate_daily``) a semanas epidemiológicas.

    Semanas de domingo a sábado, como los casos de IRA
    (``panel.health_ira_weekly``): ``fecha_semana`` es el domingo de inicio y
    ``anio`` / ``semana`` son el año y la semana epidemiológicos. La SE1 es la
    que contiene el 4 de enero, así que puede empezar en diciembre del año
    anterior. Solo quedan las semanas epidemiológicas de ``PANEL_START_YEAR``
    a ``PANEL_END_YEAR``.

    Mismas métricas que ``aggregate_monthly``. ``n_dias`` son los días de la
    semana que caben en la serie diaria (7, salvo la última semana si la serie
    termina a media semana) y la suficiencia se mide contra ellos.
    """
    daily = daily.assign(fecha=pd.to_datetime(daily["fecha"])).set_index("fecha")
    # weekday(): lunes=0 … domingo=6 → días que hay que retroceder hasta el domingo
    week = daily.index - pd.to_timedelta((daily.index.weekday + 1) % 7, unit="D")
    n_days = pd.Series(1, index=week).groupby(level=0).size()

    out = _aggregate_periods(daily, week, n_days)
    out.index.name = "fecha_semana"
    out = out.reset_index()

    # La SE1 contiene el 4 de enero si y solo si su miércoles cae entre el 1 y
    # el 7 de enero: el miércoles da el año y la semana epidemiológicos.
    wednesday = out["fecha_semana"] + pd.Timedelta(days=3)
    # int64 (no el int32 de .dt): así la tabla queda igual al leer el CSV
    out.insert(1, "anio", wednesday.dt.year.astype("int64"))
    out.insert(2, "semana", ((wednesday.dt.dayofyear - 1) // 7 + 1).astype("int64"))
    out.insert(3, "n_dias", out["fecha_semana"].map(n_days))
    out = out[out["anio"].between(PANEL_START_YEAR, PANEL_END_YEAR)]
    return out.reset_index(drop=True)


def aggregate_monthly(daily: pd.DataFrame) -> pd.DataFrame:
    """Agrega los días (salida de ``aggregate_daily``) a meses.

    Columnas por contaminante (las mismas en ``aggregate_weekly``):

    - ``pm25_ugm3`` / ``o3_ppb``: media de los promedios de 24 h.
    - ``o3_max8h_ppb``: media del máximo diario de 8 h.
    - ``pm25_max_diario_ugm3`` / ``o3_max8h_max_ppb``: el peor día del periodo.
    - ``*_dias_excede_nom``: días sobre el límite de ``AIR_QUALITY_NOM_LIMITS``.
    - ``*_dias_validos``: días con la métrica normada; decide la suficiencia.

    ``fecha_mes`` es el primer día del mes, como en el resto del panel.
    """
    daily = daily.assign(fecha=pd.to_datetime(daily["fecha"])).set_index("fecha")
    month = daily.index.to_period("M").to_timestamp()
    months = month.unique()

    out = _aggregate_periods(daily, month, pd.Series(months.days_in_month, index=months))
    out.index.name = "fecha_mes"
    return out.reset_index()


def interpolate_short_gaps(df: pd.DataFrame, max_gap: int) -> pd.DataFrame:
    """Rellena por interpolación lineal los huecos cortos de una tabla semanal o mensual.

    Un hueco es una racha de periodos seguidos sin la métrica normada. Solo se
    rellenan los de a lo más ``max_gap`` periodos con dato a los dos lados (no
    se extrapola al inicio ni al final de la serie), y solo los promedios
    (``pm25_ugm3``, ``pm10_ugm3``, ``o3_ppb``, ``o3_max8h_ppb``). Los máximos y
    ``*_dias_excede_nom`` quedan en NaN: un extremo o un conteo no se interpola.
    ``*_interpolado`` marca los periodos rellenados; ``*_dias_validos`` no cambia.

    Espera la tabla ordenada por fecha (salida de ``aggregate_weekly`` o
    ``aggregate_monthly``); la interpolación es por posición, con los
    periodos igualmente espaciados.
    """
    out = df.copy()
    for pol in AIR_QUALITY_POLLUTANTS:
        normed = out[normed_col(pol)]
        missing = normed.isna()
        run = (missing != missing.shift()).cumsum()
        run_size = missing.groupby(run).transform("size")
        inside = normed.ffill().notna() & normed.bfill().notna()
        fill = missing & (run_size <= max_gap) & inside

        mean_cols = [col(pol), col(pol, "max8h")] if pol == "O3" else [col(pol)]
        for c in mean_cols:
            interpolated = out[c].interpolate(method="linear", limit_area="inside")
            out[c] = out[c].mask(fill, interpolated.round(2))
        flag_pos = out.columns.get_loc(f"{_PREFIX[pol]}_dias_validos") + 1
        out.insert(flag_pos, f"{_PREFIX[pol]}_interpolado", fill)
        if fill.any():
            logger.info(f"{pol}: {int(fill.sum())} periodos interpolados (huecos ≤ {max_gap}).")
    return out


def valid_by_year(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Filas (días, semanas o meses) con la métrica normada válida, por año y contaminante.

    Si la tabla trae ``anio`` (la semanal) se usa ese año epidemiológico en
    lugar del año de ``date_col``.
    """
    if "anio" in df.columns:
        year = df["anio"]
    else:
        year = pd.to_datetime(df[date_col]).dt.year.rename("anio")
    valid = pd.DataFrame({pol: df[normed_col(pol)].notna() for pol in AIR_QUALITY_POLLUTANTS})
    return valid.groupby(year).sum()


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def _load_daily(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Corre primero: python -m sonora_health_climate_eda.aire diario"
        )
    return pd.read_csv(path, parse_dates=["fecha"])


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


@app.command("semanal")
def build_weekly(input_path: Path = DAILY_PATH, output_path: Path = WEEKLY_PATH):
    """Serie diaria → serie por semana epidemiológica (requiere correr ``diario`` antes)."""
    weekly = aggregate_weekly(_load_daily(input_path))
    weekly = interpolate_short_gaps(weekly, AIR_QUALITY_MAX_INTERP_WEEKS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(output_path, index=False)
    logger.info("Semanas válidas por año:\n" + valid_by_year(weekly, "fecha_semana").to_string())
    logger.success(f"Serie semanal: {len(weekly)} semanas en {output_path}")


@app.command("mensual")
def build_monthly(input_path: Path = DAILY_PATH, output_path: Path = MONTHLY_PATH):
    """Serie diaria → serie mensual de Hermosillo (requiere correr ``diario`` antes)."""
    monthly = aggregate_monthly(_load_daily(input_path))
    monthly = interpolate_short_gaps(monthly, AIR_QUALITY_MAX_INTERP_MONTHS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(output_path, index=False)
    logger.info("Meses válidos por año:\n" + valid_by_year(monthly, "fecha_mes").to_string())
    logger.success(f"Serie mensual: {len(monthly)} meses en {output_path}")


if __name__ == "__main__":
    app()
