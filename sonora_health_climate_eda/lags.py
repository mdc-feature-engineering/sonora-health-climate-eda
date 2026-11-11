"""Utilidades para rezagos temporales y funciones de correlación cruzada.

Implementa el manejo de *lag effects* descrito en el protocolo EDA:
los efectos de la exposición ambiental (temperatura, PM2.5, PM10) sobre la
morbilidad respiratoria no son instantáneos y se reflejan entre lag 0 y lag 5.
"""

import numpy as np
import pandas as pd


def add_lags(
    df: pd.DataFrame,
    columns: list[str],
    lags: range | list[int] = range(1, 5),
) -> pd.DataFrame:
    """Agrega columnas con rezagos temporales para las columnas indicadas.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame ordenado por fecha (índice o columna temporal).
    columns : list[str]
        Variables a rezagar (p.ej. ``["temp_max", "pm25"]``).
    lags : range | list[int]
        Rezagos a generar. Por defecto 1 a 4 días (protocolo EDA).

    Returns
    -------
    pd.DataFrame
        Copia del DataFrame con columnas ``{col}_lag{k}``.
    """
    result = df.copy()
    for col in columns:
        for lag in lags:
            result[f"{col}_lag{lag}"] = result[col].shift(lag)
    return result


def add_rolling_mean(
    df: pd.DataFrame,
    columns: list[str],
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """Agrega promedios móviles para exposición acumulada.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame ordenado por fecha.
    columns : list[str]
        Variables a promediar.
    windows : list[int]
        Ventanas en días (p.ej. ``[3, 7]`` para promedios de 3 y 7 días).

    Returns
    -------
    pd.DataFrame
        Copia con columnas ``{col}_ma{w}``.
    """
    if windows is None:
        windows = [3, 7]
    result = df.copy()
    for col in columns:
        for window in windows:
            result[f"{col}_ma{window}"] = result[col].rolling(window=window, min_periods=1).mean()
    return result


def build_lagged_dataset(
    df: pd.DataFrame,
    exposure_cols: list[str],
    response_col: str,
    lags: range | list[int] = range(6),
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """Construye la matriz de diseño con rezagos para el modelado GLM.

    Genera ``{exposure}_lag{k}`` para cada exposición y rezago, promedios
    móviles opcionales, y conserva la variable de respuesta junto con las
    covariables estáticas (p.ej. marginación, tendencia temporal).

    Parameters
    ----------
    df : pd.DataFrame
        Series temporal diaria/multivariada ordenada por fecha.
    exposure_cols : list[str]
        Variables de exposición ambiental (temperatura, PM2.5, PM10, O3).
    response_col : str
        Conteo de casos de enfermedad respiratoria.
    lags : range | list[int]
        Rezagos a incluir. El protocolo sugiere 0–5 días.
    rolling_windows : list[int] | None
        Ventanas para promedios móviles de exposición acumulada.

    Returns
    -------
    pd.DataFrame
        Dataset listo para ``statsmodels`` (sin NaNs inducidos por rezagos
        al inicio de la serie).
    """
    result = df.copy()

    for col in exposure_cols:
        for lag in lags:
            if lag == 0:
                result[f"{col}_lag0"] = result[col]
            else:
                result[f"{col}_lag{lag}"] = result[col].shift(lag)

    if rolling_windows:
        result = add_rolling_mean(result, exposure_cols, rolling_windows)

    # Eliminar las primeras filas donde los rezagos introducen NaN
    result = result.dropna()
    return result


def cross_correlation_function(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    """Calcula la función de correlación cruzada (CCF) entre dos series.

    Identifica empíricamente el rezago óptimo entre la exposición ambiental
    y la respuesta médica (Fase C del protocolo).

    Parameters
    ----------
    x : pd.Series
        Serie de exposición (p.ej. PM2.5 diario).
    y : pd.Series
        Serie de respuesta (p.ej. consultas respiratorias diarias).
    max_lag : int
        Rezago máximo a evaluar en días.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(lags, ccf_values)`` donde ``lags`` va de ``-max_lag`` a
        ``max_lag``. Un pico en lag positivo indica que ``x`` antecede a ``y``.
    """
    x = x.dropna().to_numpy(dtype=float)
    y = y.dropna().to_numpy(dtype=float)

    if len(x) < 2 * max_lag + 2 or len(y) < 2 * max_lag + 2:
        raise ValueError(
            f"Series demasiado cortas para CCF con max_lag={max_lag} (n_x={len(x)}, n_y={len(y)})."
        )

    lags = np.arange(-max_lag, max_lag + 1)
    ccf_values = np.array([_ccf_at_lag(x, y, lag) for lag in lags])
    return lags, ccf_values


def _ccf_at_lag(x: np.ndarray, y: np.ndarray, lag: int) -> float:
    """Correlación de Pearson entre ``x`` y ``y`` desplazada ``lag`` periodos.

    ``lag > 0`` evalúa si ``x[t]`` se correlaciona con ``y[t+lag]``
    (la exposición antecede a la respuesta).
    """
    if lag >= 0:
        x_seg = x[: len(x) - lag] if lag > 0 else x
        y_seg = y[lag : lag + len(x_seg)]
    else:
        y_seg = y[: len(y) + lag]
        x_seg = x[-lag : -lag + len(y_seg)]

    n = min(len(x_seg), len(y_seg))
    if n < 3:
        return np.nan
    x_seg = x_seg[:n]
    y_seg = y_seg[:n]

    x_std = x_seg.std()
    y_std = y_seg.std()
    if x_std == 0 or y_std == 0:
        return np.nan
    return float(np.corrcoef(x_seg, y_seg)[0, 1])


def best_lag(
    x: pd.Series,
    y: pd.Series,
    max_lag: int = 10,
    positive_only: bool = True,
) -> int:
    """Devuelve el rezago con la correlación cruzada máxima.

    Parameters
    ----------
    x : pd.Series
        Serie de exposición.
    y : pd.Series
        Serie de respuesta.
    max_lag : int
        Rezago máximo a evaluar.
    positive_only : bool
        Si ``True``, solo considera rezagos >= 0 (exposición antecede a
        respuesta), que es el caso epidemiológico esperado.

    Returns
    -------
    int
        Rezago óptimo en días.
    """
    lags, ccf_values = cross_correlation_function(x, y, max_lag=max_lag)
    mask = lags >= 0 if positive_only else np.ones_like(lags, dtype=bool)
    if not mask.any():
        return 0
    best_idx = np.argmax(ccf_values[mask])
    return int(lags[mask][best_idx])


def lagged_correlations(
    df: pd.DataFrame,
    exposure_col: str,
    response_col: str,
    max_lag: int = 5,
) -> pd.DataFrame:
    """Tabla de correlaciones de Pearson/Spearman por rezago.

    Parameters
    ----------
    df : pd.DataFrame
        Series temporal ordenada por fecha.
    exposure_col : str
        Variable de exposición.
    response_col : str
        Variable de respuesta (conteo de casos).
    max_lag : int
        Rezago máximo a evaluar.

    Returns
    -------
    pd.DataFrame
        Columnas: ``lag``, ``pearson``, ``spearman``.
    """
    rows = []
    for lag in range(max_lag + 1):
        x = df[exposure_col].shift(lag)
        y = df[response_col]
        valid = x.notna() & y.notna()
        if valid.sum() < 3:
            continue
        rows.append(
            {
                "lag": lag,
                "pearson": x[valid].corr(y[valid], method="pearson"),
                "spearman": x[valid].corr(y[valid], method="spearman"),
            }
        )
    return pd.DataFrame(rows)
