"""Construcción del panel mensual integrado (Fase A del protocolo EDA).

Une las cuatro capas disponibles para Hermosillo en una granularidad
mensual común (ene-2015 a dic-2020 por defecto):

1. Clima — resúmenes mensuales SMN/CONAGUA (temperatura media, máxima y
   mínima por estación; se promedian las estaciones de la zona metropolitana de
   Hermosillo definidas en ``config.CLIMATE_STATION_IDS``).
2. Sequía — Monitor de Sequía SMN/CONAGUA (quincenal → mensual).
3. Marginación — IMN municipal CONAPO interpolado linealmente entre los
   censos 2015 y 2020 (los CSV depurados ya existen en
   ``data/interim/marginacion/``; la ingesta sigue pausada).
4. Salud — casos confirmados de IRA (CIE-10 J00-J06/J20/J21 menos
   J02.0/J03.0), semanal epidemiológica → mensual, desde los CSV de la
   Secretaría de Salud de Sonora en ``data/raw/salud/``.

Salida: ``data/processed/panel_hermosillo.parquet``.
"""

from loguru import logger
import numpy as np
import pandas as pd

from sonora_health_climate_eda.config import (
    CLIMATE_STATION_IDS,
    DROUGHT_EXTREME_MIN_SEVERITY,
    HEALTH_ANOMALY_YEARS,
    HEAT_EXTREME_TMAX_C,
    HEAT_INDEX_DANGER_C,
    HERMOSILLO_CVE_MUN,
    INTERIM_DATA_DIR,
    PANEL_END_YEAR,
    PANEL_START_YEAR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
)

SMN_ENCODING = "latin-1"


def _month_period(year: int, month: int) -> pd.Period:
    return pd.Period(f"{year}-{month:02d}", freq="M")


def _se_start(year: int, week: int) -> pd.Timestamp:
    """Fecha de inicio de la semana epidemiológica ``week`` de ``year``.

    Convención SINAVE/MMWR: semanas de domingo a sábado; SE1 es la que
    contiene el 4 de enero (2014 y 2020 tienen 53 semanas, 2015 tiene 52).
    """
    jan4 = pd.Timestamp(year, 1, 4)
    start = jan4 - pd.Timedelta(days=(jan4.weekday() + 1) % 7)
    return start + pd.Timedelta(weeks=week - 1)


def _load_smn_temperature_series(folder_glob: str, raw_col: str, out_col: str) -> pd.DataFrame:
    """Carga resúmenes mensuales SMN de una serie de temperatura.

    ``folder_glob`` selecciona ``data/raw/<folder_glob>/AAAAMM010000*.csv``;
    ``raw_col`` es la columna de valor en el CSV (``Tmed``/``Tmax``/``Tmin``)
    y ``out_col`` el nombre normalizado de salida.
    """
    frames = []
    for path in sorted(RAW_DATA_DIR.glob(folder_glob)):
        year, month = int(path.name[:4]), int(path.name[4:6])
        df = pd.read_csv(path, encoding=SMN_ENCODING)
        df = df.rename(
            columns={
                "Lon": "lon",
                "Lat": "lat",
                "Edo": "edo",
                "Clave": "clave",
                "Est": "estacion",
                raw_col: out_col,
            }
        )
        df[out_col] = pd.to_numeric(df[out_col], errors="coerce")
        df["fecha_mes"] = _month_period(year, month)
        frames.append(df[["lon", "lat", "edo", "clave", "estacion", out_col, "fecha_mes"]])
    out = pd.concat(frames, ignore_index=True)
    logger.info(f"SMN {out_col}: {len(out)} filas estación-mes.")
    return out


def load_smn_temperature() -> pd.DataFrame:
    """Temperatura media mensual SMN (``Tmed``, °C)."""
    # Ojo: el glob excluye temperatura_max_*/temperatura_min_* (nombre no
    # empieza con dígito tras el prefijo).
    return _load_smn_temperature_series("temperatura_[0-9]*/*.csv", "Tmed", "temp_media_c")


def load_smn_temperature_max() -> pd.DataFrame:
    """Temperatura máxima mensual SMN (``Tmax``, °C) — proxy de calor extremo."""
    return _load_smn_temperature_series("temperatura_max_*/*.csv", "Tmax", "temp_max_media_c")


def load_smn_temperature_min() -> pd.DataFrame:
    """Temperatura mínima mensual SMN (``Tmin``, °C)."""
    return _load_smn_temperature_series("temperatura_min_*/*.csv", "Tmin", "temp_min_media_c")


CLIMATOLOGY_START = "1991-01-01"  # base WMO ~30 años para percentiles


def load_openmeteo_daily() -> pd.DataFrame:
    """Descarga/cachea la serie diaria de Open-Meteo Archive para Hermosillo.

    Variables: ``temperature_2m_max``, ``temperature_2m_min``,
    ``relative_humidity_2m_mean``. Cobertura 1991–2020: los primeros
    ~10 años sirven solo de línea base climatológica para los umbrales
    percentiles de olas de calor (P95 por mes calendario); el panel usa
    la ventana PANEL_START_YEAR–PANEL_END_YEAR. Se cachea en
    ``data/raw/openmeteo_hermosillo_daily_1991_2020.csv``.
    """
    import requests

    cache = RAW_DATA_DIR / "openmeteo_hermosillo_daily_1991_2020.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["fecha"])

    lat, lon = 29.07, -110.95  # centro de Hermosillo
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": CLIMATOLOGY_START,
        "end_date": "2020-12-31",
        "daily": "temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean",
        "timezone": "America/Hermosillo",
    }
    resp = requests.get(
        "https://archive-api.open-meteo.com/v1/archive", params=params, timeout=120
    )
    resp.raise_for_status()
    daily = resp.json()["daily"]
    df = pd.DataFrame(daily).rename(
        columns={
            "time": "fecha",
            "temperature_2m_max": "tmax_c",
            "temperature_2m_min": "tmin_c",
            "relative_humidity_2m_mean": "humedad_rel_pct",
        }
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False)
    logger.info(f"Open-Meteo diario: {len(df)} días cacheados en {cache.name}.")
    return df


def _heat_index_c(tmax_c: pd.Series, rh_pct: pd.Series) -> pd.Series:
    """Índice de calor (heat index) de Rothfusz — temperatura de sensación
    térmica en °C a partir de Tmax (°C) y humedad relativa media (%).

    Aproximación: no aplica los ajustes del NWS para HR<40%/T extremes;
    válida sobre todo en el verano húmedo (ago–sep) de Hermosillo.
    """
    t_f = tmax_c * 9 / 5 + 32
    r = rh_pct
    # Rothfusz (regresión completa, T en °F, RH en %)
    hi_f = (
        -42.379
        + 2.04901523 * t_f
        + 10.14333127 * r
        - 0.22475541 * t_f * r
        - 0.00683783 * t_f**2
        - 0.05481717 * r**2
        + 0.00122874 * t_f**2 * r
        + 0.00085282 * t_f * r**2
        - 0.00000199 * t_f**2 * r**2
    )
    return (hi_f - 32) * 5 / 9


def _openmeteo_daily_flags() -> pd.DataFrame:
    """Serie diaria Open-Meteo con flags de ola de calor y heat index.

    Las rachas se calculan sobre la serie completa (1991–2020) para no
    cortar olas de calor a caballo entre periodos; ``run_*`` identifica
    cada racha.
    """
    daily = load_openmeteo_daily()
    daily = daily.sort_values("fecha").reset_index(drop=True)

    # Rachas de días consecutivos con Tmax ≥35 °C. Una racha de ≥3 días
    # es una ola de calor (convención SMN/CONAGUA).
    hot = daily["tmax_c"] >= 35
    daily["run_ola"] = (hot != hot.shift()).cumsum()
    run_len = hot.groupby(daily["run_ola"]).transform("sum")
    daily["en_ola"] = (hot & (run_len >= 3)).astype(int)

    # --- Umbral adaptado a clima desértico (propuesta del equipo) ---
    # Percentil 95 POR MES CALENDARIO sobre la línea base climatológica
    # completa (1991–2020). Un "día de ola" requiere que Tmax y Tmin
    # superen SIMULTÁNEAMENTE su P95 del mes (estrés térmico diurno +
    # nocturno). Ola = ≥3 días consecutivos.
    mes_cal = daily["fecha"].dt.month
    thr_tmax = daily.groupby(mes_cal)["tmax_c"].quantile(0.95)
    thr_tmin = daily.groupby(mes_cal)["tmin_c"].quantile(0.95)
    daily["thr_tmax_p95"] = mes_cal.map(thr_tmax)
    daily["thr_tmin_p95"] = mes_cal.map(thr_tmin)
    hot_p95 = (daily["tmax_c"] >= daily["thr_tmax_p95"]) & (
        daily["tmin_c"] >= daily["thr_tmin_p95"]
    )
    daily["run_ola_p95"] = (hot_p95 != hot_p95.shift()).cumsum()
    run_len_p95 = hot_p95.groupby(daily["run_ola_p95"]).transform("sum")
    daily["en_ola_p95"] = (hot_p95 & (run_len_p95 >= 3)).astype(int)

    # --- Calor húmedo: heat index (Tmax + humedad relativa) ---
    # Captura el verano de monzón (ago–sep) donde Tmax menor pero HR
    # alta produce sensación térmica igual o mayor que el calor seco.
    daily["heat_index_c"] = _heat_index_c(daily["tmax_c"], daily["humedad_rel_pct"])
    hot_hi = daily["heat_index_c"] >= HEAT_INDEX_DANGER_C
    daily["run_ola_humedo"] = (hot_hi != hot_hi.shift()).cumsum()
    run_len_hi = hot_hi.groupby(daily["run_ola_humedo"]).transform("sum")
    daily["en_ola_humedo"] = (hot_hi & (run_len_hi >= 3)).astype(int)
    return daily


def _aggregate_openmeteo(daily: pd.DataFrame, key: str, suffix: str) -> pd.DataFrame:
    """Agrega los flags diarios Open-Meteo al periodo ``key`` (mes o semana)."""
    out = (
        daily.groupby(key)
        .agg(
            **{
                f"tmax_max_{suffix}": ("tmax_c", "max"),
                f"tmax_media_{suffix}": ("tmax_c", "mean"),
                f"tmin_min_{suffix}": ("tmin_c", "min"),
                "humedad_rel_media": ("humedad_rel_pct", "mean"),
                "dias_tmax_ge_35": ("tmax_c", lambda s: int((s >= 35).sum())),
                "dias_ola_calor": ("en_ola", "sum"),
                "dias_ola_calor_p95": ("en_ola_p95", "sum"),
                f"heat_index_max_{suffix}": ("heat_index_c", "max"),
                "dias_heat_index_ge_40": ("heat_index_c", lambda s: int((s >= 40).sum())),
                "dias_ola_calor_humedo": ("en_ola_humedo", "sum"),
            }
        )
        .reset_index()
    )

    # Número de olas: cada racha caliente ≥3 días cuenta una vez,
    # atribuida al periodo de su primer día.
    for flag_col, run_col, name in (
        ("en_ola", "run_ola", "n_olas_calor"),
        ("en_ola_p95", "run_ola_p95", "n_olas_calor_p95"),
        ("en_ola_humedo", "run_ola_humedo", "n_olas_calor_humedo"),
    ):
        first_period = daily[daily[flag_col] == 1].groupby(run_col)[key].min()
        counts = first_period.value_counts().rename(name).rename_axis(key).reset_index()
        out = out.merge(counts, on=key, how="left")
        out[name] = out[name].fillna(0).astype(int)

    return out.sort_values(key).reset_index(drop=True)


def openmeteo_hermosillo_monthly() -> pd.DataFrame:
    """Agrega la serie diaria Open-Meteo a mensual con métricas de calor.

    Columnas: ``tmax_max_mes`` (Tmax absoluta), ``tmax_media_mes``,
    ``tmin_min_mes``, ``humedad_rel_media``, ``dias_tmax_ge_35``
    (días con Tmax ≥35 °C), ``dias_ola_calor`` (días dentro de olas de
    ≥3 días consecutivos ≥35 °C) y ``n_olas_calor``.
    """
    daily = _openmeteo_daily_flags()
    daily["fecha_mes"] = daily["fecha"].dt.to_period("M").dt.to_timestamp()
    return _aggregate_openmeteo(daily, "fecha_mes", "mes")


def openmeteo_hermosillo_weekly() -> pd.DataFrame:
    """Agrega la serie diaria Open-Meteo a semana epidemiológica.

    ``fecha_semana`` es el domingo de inicio de la semana (convención
    SINAVE/MMWR, la misma de ``health_ira_weekly``), para poder unir ambas
    tablas. Mismas métricas que la versión mensual, con sufijo ``_sem``.
    La primera y la última semana de la serie pueden estar incompletas.
    """
    daily = _openmeteo_daily_flags()
    # weekday(): lunes=0 … domingo=6 → días que hay que retroceder hasta el domingo
    days_since_sunday = (daily["fecha"].dt.weekday + 1) % 7
    daily["fecha_semana"] = daily["fecha"] - pd.to_timedelta(days_since_sunday, unit="D")
    return _aggregate_openmeteo(daily, "fecha_semana", "sem")


def climate_hermosillo() -> pd.DataFrame:
    """Promedia la temperatura de las estaciones de Hermosillo.

    Usa ``config.CLIMATE_STATION_IDS``; si está vacío, toma todas las
    estaciones con ``edo == 'SON'`` dentro de ~60 km del centro de
    Hermosillo.
    """
    temp = load_smn_temperature()
    temp_max = load_smn_temperature_max()
    temp_min = load_smn_temperature_min()

    if CLIMATE_STATION_IDS:
        stations = temp[temp["clave"].isin(CLIMATE_STATION_IDS)][
            ["clave", "estacion"]
        ].drop_duplicates()
    else:
        hermosillo_center = (29.07, -110.95)  # lat, lon
        son = temp[temp["edo"] == "SON"]
        dist = np.sqrt(
            (son["lat"] - hermosillo_center[0]) ** 2 + (son["lon"] - hermosillo_center[1]) ** 2
        )
        stations = son.loc[dist < 0.6, ["clave", "estacion"]].drop_duplicates()
        logger.warning(
            "CLIMATE_STATION_IDS vacío: usando estaciones SON a <~60 km "
            f"de Hermosillo: {stations['estacion'].tolist()}"
        )

    claves = stations["clave"]
    t_m = (
        temp[temp["clave"].isin(claves)]
        .groupby("fecha_mes", as_index=False)["temp_media_c"]
        .mean()
    )
    tx_m = (
        temp_max[temp_max["clave"].isin(claves)]
        .groupby("fecha_mes", as_index=False)["temp_max_media_c"]
        .mean()
    )
    tn_m = (
        temp_min[temp_min["clave"].isin(claves)]
        .groupby("fecha_mes", as_index=False)["temp_min_media_c"]
        .mean()
    )
    out = t_m.merge(tx_m, on="fecha_mes", how="outer").merge(tn_m, on="fecha_mes", how="outer")
    out["fecha_mes"] = out["fecha_mes"].dt.to_timestamp()
    out = out.sort_values("fecha_mes").reset_index(drop=True)

    # El SMN publicó archivos degenerados para dic-2015/2016/2017 en las
    # tres series (TMed/TMax/TMin): el valor es idéntico por estación en
    # las tres columnas (físicamente imposible) y ~8-10 °C más alto que el
    # diciembre típico de Hermosillo. Se marcan como faltantes.
    bad_months = pd.to_datetime(["2015-12-01", "2016-12-01", "2017-12-01"])
    temp_cols = ["temp_media_c", "temp_max_media_c", "temp_min_media_c"]
    out.loc[out["fecha_mes"].isin(bad_months), temp_cols] = np.nan
    logger.warning(
        "Temperaturas dic-2015/2016/2017 marcadas como NaN: archivos "
        "SMN degenerados (verificado 2026-11)."
    )

    logger.info(f"Clima Hermosillo: {len(out)} meses, estaciones={stations['estacion'].tolist()}")
    return out


def _drought_records_hermosillo() -> pd.DataFrame:
    """Registros quincenales del Monitor de Sequía para Hermosillo."""
    files = sorted(INTERIM_DATA_DIR.glob("sonora_sequia/*.csv"))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    hermosillo_mun = int(HERMOSILLO_CVE_MUN) % 1000  # 26030 -> 30
    df = df[df["CVE_MUN"] == hermosillo_mun].copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.sort_values("fecha").reset_index(drop=True)


def drought_hermosillo() -> pd.DataFrame:
    """Agrega el Monitor de Sequía (quincenal) a mensual para Hermosillo.

    ``severidad_promedio`` = media de ``severidad_num`` (0–5) de las
    quincenas del mes; ``categoria_sequia`` = categoría modal.
    """
    df = _drought_records_hermosillo()
    df["fecha_mes"] = df["fecha"].dt.to_period("M").dt.to_timestamp()
    df = df[(df["fecha"].dt.year >= PANEL_START_YEAR) & (df["fecha"].dt.year <= PANEL_END_YEAR)]

    g = df.groupby("fecha_mes")
    out = g["severidad_num"].mean().rename("severidad_sequia").reset_index()
    modal = (
        df.groupby(["fecha_mes", "categoria_sequia"])
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .drop_duplicates("fecha_mes")[["fecha_mes", "categoria_sequia"]]
    )
    out = out.merge(modal, on="fecha_mes", how="left")
    return out.sort_values("fecha_mes").reset_index(drop=True)


def marginacion_hermosillo() -> pd.DataFrame:
    """Interpolación mensual del IMN municipal entre censos 2015 y 2020.

    Parte de los CSV ya depurados en ``data/interim/marginacion/`` y
    filtra Hermosillo (``CVE_MUN == 26030``).
    """
    m2015 = pd.read_csv(INTERIM_DATA_DIR / "marginacion/marginacion_municipal_2015.csv")
    m2020 = pd.read_csv(INTERIM_DATA_DIR / "marginacion/marginacion_municipal_2020.csv")

    cve = "CVE_MUN" if "CVE_MUN" in m2015.columns else "CVE_CONCATENADA"
    a = m2015[m2015[cve].astype(str).str.endswith("030")].copy()
    b = m2020[m2020[cve].astype(str).str.endswith("030")].copy()

    # Normalizar nombres: IM_2015/GM_2015/IMN_2015 -> IM/GM/IMN, etc.
    for df in (a, b):
        df.rename(
            columns={
                c: c.rsplit("_", 1)[0]
                for c in df.columns
                if c.rsplit("_", 1)[-1] in {"2015", "2020"}
            },
            inplace=True,
        )

    start = pd.Timestamp(PANEL_START_YEAR, 1, 1)
    end = pd.Timestamp(PANEL_END_YEAR, 12, 1)
    months = pd.date_range(start, end, freq="MS")

    # Indicadores numéricos del IMN (se excluyen claves, nombres y POB_TOT,
    # que es un stock censal y no un indicador del índice).
    key_cols = {cve, "CVE_ENT", "NOM_ENT", "NOM_MUN", "ENTIDAD", "POB_TOT"}
    numeric_cols = [
        c
        for c in a.columns
        if c in b.columns
        and c not in key_cols
        and pd.api.types.is_numeric_dtype(a[c])
        and pd.api.types.is_numeric_dtype(b[c])
    ]

    out = pd.DataFrame({"fecha_mes": months})
    frac = np.clip(
        (months - pd.Timestamp(2015, 1, 1)).days
        / (pd.Timestamp(2020, 1, 1) - pd.Timestamp(2015, 1, 1)).days,
        0,
        1,
    )
    for col in numeric_cols:
        va, vb = float(a[col].iloc[0]), float(b[col].iloc[0])
        out[col] = va + (vb - va) * frac
    logger.info(
        f"Marginación interpolada: {len(out)} meses, "
        f"{len(numeric_cols)} indicadores: {numeric_cols}"
    )
    return out


def health_ira_weekly() -> pd.DataFrame:
    """Casos confirmados de IRA (Hermosillo) por semana epidemiológica.

    Se colapsan ``genero``, ``grupo_edad`` y ``clues``. ``fecha_semana`` es
    la fecha de inicio de la semana (``_se_start``).
    """
    path = RAW_DATA_DIR / "salud/enf_resp_sonora_2010_2020.csv"
    df = pd.read_csv(
        path,
        usecols=["clave_municipio", "municipio", "anio", "semana", "casos"],
    )
    hermosillo_clave = int(HERMOSILLO_CVE_MUN) % 1000  # 26030 -> 30
    df = df[df["clave_municipio"] == hermosillo_clave]

    df["fecha_semana"] = pd.to_datetime(
        [_se_start(int(a), int(s)) for a, s in zip(df["anio"], df["semana"])]
    )
    df = df[(df["anio"] >= PANEL_START_YEAR) & (df["anio"] <= PANEL_END_YEAR)]

    out = (
        df.groupby(["fecha_semana", "anio", "semana"], as_index=False)["casos"]
        .sum()
        .rename(columns={"casos": "casos_ira"})
        .sort_values("fecha_semana")
        .reset_index(drop=True)
    )
    logger.info(
        f"Salud IRA Hermosillo: {len(out)} semanas, {int(out['casos_ira'].sum())} casos en ventana."
    )
    return out


def health_ira_monthly() -> pd.DataFrame:
    """Casos confirmados de IRA (Hermosillo) de semanal a mensual.

    La semana epidemiológica se asigna al mes de su fecha de inicio
    (convención SUAVE). Un mes suma 4 o 5 semanas (``n_semanas``);
    ``casos_ira_por_semana`` evita que los meses de 5 semanas parezcan
    tener más casos.
    """
    weekly = health_ira_weekly()
    weekly["fecha_mes"] = weekly["fecha_semana"].dt.to_period("M").dt.to_timestamp()
    out = (
        weekly.groupby("fecha_mes", as_index=False)
        .agg(casos_ira=("casos_ira", "sum"), n_semanas=("fecha_semana", "nunique"))
        .sort_values("fecha_mes")
        .reset_index(drop=True)
    )
    out["casos_ira_por_semana"] = out["casos_ira"] / out["n_semanas"]
    return out


def build_panel() -> pd.DataFrame:
    """Construye el panel mensual integrado y lo guarda en processed/."""
    climate = climate_hermosillo()
    drought = drought_hermosillo()
    margin = marginacion_hermosillo()
    health = health_ira_monthly()
    om = openmeteo_hermosillo_monthly()

    panel = climate.merge(drought, on="fecha_mes", how="outer")
    panel = panel.merge(margin, on="fecha_mes", how="outer")
    panel = panel.merge(health, on="fecha_mes", how="outer")
    panel = panel.merge(om, on="fecha_mes", how="left")
    panel = panel.sort_values("fecha_mes").reset_index(drop=True)

    expected = pd.date_range(f"{PANEL_START_YEAR}-01-01", f"{PANEL_END_YEAR}-12-01", freq="MS")
    panel = panel.set_index("fecha_mes").reindex(expected).rename_axis("fecha_mes").reset_index()

    # Flags de exposición extrema (umbrales en config.py).
    panel["mes_calor_extremo"] = (panel["temp_max_media_c"] >= HEAT_EXTREME_TMAX_C).astype(
        "boolean"
    )
    panel["mes_sequia"] = (panel["severidad_sequia"] >= DROUGHT_EXTREME_MIN_SEVERITY).astype(
        "boolean"
    )
    panel["mes_extremo_conjunto"] = (panel["mes_calor_extremo"] & panel["mes_sequia"]).astype(
        "boolean"
    )
    # Ola de calor formal por umbral fijo (≥35 °C, ≥3 días) y por umbral
    # adaptado P95 estacional (Tmax+Tmin superan su P95 del mes calendario,
    # ≥3 días consecutivos) — ambas desde Open-Meteo diario.
    panel["mes_ola_calor"] = (panel["n_olas_calor"] > 0).astype("boolean")
    panel["mes_ola_calor_p95"] = (panel["n_olas_calor_p95"] > 0).astype("boolean")
    panel["mes_ola_calor_p95_y_sequia"] = (
        panel["mes_ola_calor_p95"] & panel["mes_sequia"]
    ).astype("boolean")
    panel["mes_calor_humedo"] = (panel["n_olas_calor_humedo"] > 0).astype("boolean")
    panel["anio_atipico"] = panel["fecha_mes"].dt.year.isin(HEALTH_ANOMALY_YEARS).astype("boolean")

    out_path = PROCESSED_DATA_DIR / "panel_hermosillo.parquet"
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out_path, index=False)
    logger.success(f"Panel guardado en {out_path} ({len(panel)} meses).")
    return panel
