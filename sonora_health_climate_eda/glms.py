"""Modelos GLM para conteos de morbilidad respiratoria (Fase D del protocolo).

Implementa Modelos Lineales Generalizados con distribución de Poisson o
Binomial Negativa, incluyendo términos de rezago y de interacción
marginación × exposición.
"""

from typing import Literal

from loguru import logger
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def fit_count_glm(
    df: pd.DataFrame,
    formula: str,
    family: Literal["poisson", "negbin"] = "negbin",
    offset_col: str | None = None,
) -> "sm.genmod.generalized_linear_model.GLMResults":
    """Ajusta un GLM de conteos con statsmodels.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset de diseño (salida de ``lags.build_lagged_dataset``).
    formula : str
        Fórmula estilo R, p.ej.::

            casos_respiratorios ~ temp_max_lag1 + temp_max_lag2 + \\
                pm25_lag0 + pm25_lag3 + marginacion + tendencia

    family : {"poisson", "negbin"}
        Distribución del GLM. Binomial Negativa suele ser preferible para
        conteos de morbilidad sobre-dispersos.
    offset_col : str | None
        Columna de offset (p.ej. log de la población expuesta o del número
        de consultas/días de reporte). Se pasa como ``log(offset)`` si el
        modelo usa tasa en lugar de conteo.

    Returns
    -------
    Resultados del modelo ajustado.

    Examples
    --------
    >>> model = fit_count_glm(
    ...     df_design,
    ...     "casos ~ temp_lag1 + temp_lag2 + pm25_lag0 + marginacion_alta"
    ...     " + np.log(poblacion)",
    ...     family="negbin",
    ... )
    >>> model.summary()
    """
    fam = sm.families.Poisson() if family == "poisson" else sm.families.NegativeBinomial()

    kwargs = {}
    if offset_col:
        # El offset debe ser logaritmo de la exposición; se asume que la
        # fórmula ya puede incluir np.log(poblacion), pero si se pasa
        # offset_col se usa directamente.
        kwargs["offset"] = df[offset_col]

    model = smf.glm(formula=formula, data=df, family=fam, **kwargs)
    result = model.fit()
    logger.info(f"GLM ({family}) ajustado: {result.nobs} observaciones.")
    return result


def incidence_rate_ratios(
    result: "sm.genmod.generalized_linear_model.GLMResults",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Extrae razones de tasa de incidencia (IRR) del GLM ajustado.

    Parameters
    ----------
    result : GLMResults
        Resultado de ``fit_count_glm``.
    alpha : float
        Nivel de significancia para los intervalos de confianza.

    Returns
    -------
    pd.DataFrame
        Índice = nombres de coeficientes; columnas ``coef``, ``se``,
        ``pvalue``, ``irr``, ``irr_ci_lower``, ``irr_ci_upper``.
    """
    params = result.params
    bse = result.bse
    pvalues = result.pvalues
    conf = result.conf_int(alpha=alpha)

    table = pd.DataFrame(
        {
            "coef": params,
            "se": bse,
            "pvalue": pvalues,
            "irr": np.exp(params),
        }
    )
    table["irr_ci_lower"] = np.exp(conf[0])
    table["irr_ci_upper"] = np.exp(conf[1])
    table["significativo"] = table["pvalue"] < alpha
    return table


def build_design_matrix(
    df: pd.DataFrame,
    exposure_cols: list[str],
    response_col: str,
    static_cols: list[str] | None = None,
    lags: range | list[int] = range(6),
    include_interactions: bool = True,
    marginacion_col: str = "marginacion",
) -> pd.DataFrame:
    """Construye el dataset de diseño para el GLM con rezagos e interacciones.

    Replica la estructura del protocolo::

        log(E[Y_t]) = β0 + β1 Temp_t + β2 Temp_{t-1} + β3 PM2.5_{t-2}
                      + β4 Marginación + Tendencia + interacciones

    Parameters
    ----------
    df : pd.DataFrame
        Series temporal con exposiciones, respuesta y covariables.
    exposure_cols : list[str]
        Variables de exposición (p.ej. ``["temp_max", "pm25"]``).
    response_col : str
        Conteo de casos de enfermedad respiratoria.
    static_cols : list[str] | None
        Covariables estáticas (marginación, tendencia, estación del año).
    lags : range | list[int]
        Rezagos a incluir por exposición.
    include_interactions : bool
        Si ``True``, agrega términos ``exposure × marginacion_alta``.
    marginacion_col : str
        Columna de marginación; se binariza en ``{col}_alta`` si es continua.

    Returns
    -------
    pd.DataFrame
        Dataset listo para ``fit_count_glm``.
    """
    from sonora_health_climate_eda.lags import build_lagged_dataset

    design = build_lagged_dataset(
        df,
        exposure_cols=exposure_cols,
        response_col=response_col,
        lags=lags,
    )

    # Binaria de alta marginación (mediana como umbral por defecto)
    if marginacion_col in design.columns:
        threshold = design[marginacion_col].median()
        design[f"{marginacion_col}_alta"] = (design[marginacion_col] > threshold).astype(int)

    # Interacciones exposición × alta marginación (término clave del protocolo)
    if include_interactions and f"{marginacion_col}_alta" in design.columns:
        for col in exposure_cols:
            for lag in lags:
                lagged = col if lag == 0 else f"{col}_lag{lag}"
                if lagged in design.columns:
                    design[f"{lagged}_x_{marginacion_col}_alta"] = (
                        design[lagged] * design[f"{marginacion_col}_alta"]
                    )

    # Eliminar columnas de exposición originales sin rezago (lag0 ya las cubre)
    drop_cols = [c for c in exposure_cols if c in design.columns]
    design = design.drop(columns=drop_cols, errors="ignore")

    return design


def formula_from_design(
    design_df: pd.DataFrame,
    response_col: str,
    static_cols: list[str],
) -> str:
    """Genera la fórmula statsmodels a partir del dataset de diseño.

    Parameters
    ----------
    design_df : pd.DataFrame
        Salida de ``build_design_matrix``.
    response_col : str
        Variable de respuesta.
    static_cols : list[str]
        Covariables estáticas a incluir explícitamente.

    Returns
    -------
    str
        Fórmula tipo ``"casos ~ var1 + var2 + ..."``.
    """
    predictors = [
        c for c in design_df.columns if c not in [response_col] and not c.startswith("fecha")
    ]
    return f"{response_col} ~ " + " + ".join(predictors)
