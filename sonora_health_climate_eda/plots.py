from pathlib import Path
from loguru import logger
import pandas as pd
import typer

from sonora_health_climate_eda.config import FIGURES_DIR, PROCESSED_DATA_DIR, PANEL_START_YEAR, PANEL_END_YEAR, DROUGHT_EXTREME_MIN_SEVERITY

app = typer.Typer()

import matplotlib.dates as mdates
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Colores de plot_cobertura: medido (dato real), interpolado (relleno) y sin dato.
COBERTURA_COLORES = {"medido": "#2a78d6", "interpolado": "#86b6ef", "sin dato": "#e4e3df"}


def plot_cobertura(tabla, fecha_col, capas, interpoladas=None, ax=None):
    """Dibuja una franja por capa con los periodos medidos, interpolados y sin dato.

    Muestra de un vistazo en qué periodos se puede comparar cada capa con las
    demás. ``tabla`` tiene una fila por periodo (semana o mes) y ``fecha_col``
    es la fecha de inicio de cada periodo. ``capas`` mapea la etiqueta de cada
    franja a su columna; un NaN cuenta como "sin dato". ``interpoladas``
    (opcional) mapea la etiqueta a una columna booleana que marca los valores
    rellenados. A la derecha de cada franja se anota el % de periodos con dato.
    """
    tabla = tabla.sort_values(fecha_col).reset_index(drop=True)
    inicio = pd.to_datetime(tabla[fecha_col])
    fin = inicio.shift(-1).fillna(inicio.iloc[-1] + inicio.diff().median())
    x0 = mdates.date2num(inicio)
    ancho = mdates.date2num(fin) - x0
    interpoladas = interpoladas or {}

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 0.45 * len(capas) + 1.2))
    for i, (etiqueta, columna) in enumerate(capas.items()):
        y = len(capas) - 1 - i  # la primera capa queda arriba
        interp = (
            tabla[interpoladas[etiqueta]].fillna(False).to_numpy(bool)
            if etiqueta in interpoladas
            else np.zeros(len(tabla), bool)
        )
        con_dato = tabla[columna].notna().to_numpy()
        estado = np.select([interp, con_dato], ["interpolado", "medido"], "sin dato")
        # Une los periodos seguidos con el mismo estado en un solo tramo
        racha = np.r_[0, np.cumsum(estado[1:] != estado[:-1])]
        for r in np.unique(racha):
            m = racha == r
            ax.broken_barh(
                [(x0[m][0], ancho[m].sum())], (y - 0.35, 0.7),
                facecolor=COBERTURA_COLORES[estado[m][0]], edgecolor="none",
            )
        ax.annotate(
            f"{con_dato.mean() * 100:.0f} % con dato",
            xy=(1, y), xycoords=("axes fraction", "data"),
            xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color="#52514e",
        )

    ax.set_yticks(range(len(capas)), list(capas)[::-1])
    ax.set_ylim(-0.6, len(capas) - 0.4)
    ax.set_xlim(x0[0], x0[-1] + ancho[-1])
    # Marca el 1 de enero y escribe el año a mitad de cada año
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(plt.NullFormatter())
    ax.xaxis.set_minor_locator(mdates.YearLocator(month=7, day=1))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", which="minor", length=0)
    ax.tick_params(axis="y", length=0)
    ax.grid(False)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.legend(
        handles=[Patch(facecolor=c, label=n) for n, c in COBERTURA_COLORES.items()],
        loc="lower left", bbox_to_anchor=(0, 1), ncols=3, frameon=False, fontsize=9,
    )
    return ax


def plot_serie_temporal_ira(df_panel):
    """
    Genera un gráfico de línea temporal para visualizar la evolución 
    de los casos semanales de IRA en Hermosillo.
    """
    # Configurar el estilo visual estilo académico/científico
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 6))
    
    # Crear un índice temporal secuencial (t) para evitar saltos en el eje X
    df_panel = df_panel.sort_values(['anio', 'semana']).copy()
    df_panel['indice_temporal'] = range(len(df_panel))
    
    # Graficar la serie de tiempo
    ax = sns.lineplot(
        data=df_panel, 
        x='indice_temporal', 
        y='casos_ira_total', 
        color='#1f77b4', 
        linewidth=1.2
    )
    
    # Añadir etiquetas y título orientados al EDA
    plt.title('Incidencia Semanal de Infecciones Respiratorias Agudas (IRA) - Hermosillo', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel(f'Semanas Epidemiológicas ({PANEL_START_YEAR} - {PANEL_END_YEAR})', fontsize=12)
    plt.ylabel('Casos Totales de IRA', fontsize=12)
    
    # Marcar visualmente los cambios de año en el eje X para mayor legibilidad
    # Buscamos las posiciones donde cambia el año
    cambios_anio = df_panel[df_panel['semana'] == 1]['indice_temporal'].values
    etiquetas_anio = df_panel[df_panel['semana'] == 1]['anio'].values
    
    plt.xticks(ticks=cambios_anio, labels=etiquetas_anio, rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_severidad_sequia_mensual(sequia_mensual):
    """
    Genera un gráfico de línea para visualizar la evolución mensual de la severidad de sequía.
    """
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 3.5))
    
    # Usamos la columna de fecha mensual y la severidad numérica calculada
    ax.step(sequia_mensual["fecha_mes"], sequia_mensual["severidad_sequia"], where="post", color="#1f77b4", linewidth=1.5)
    
    # Línea de umbral (ej. D1 en adelante)
    ax.axhline(DROUGHT_EXTREME_MIN_SEVERITY, ls="--", color="gray", label="Umbral de sequía (≥ D1)")
    
    # Configurar las etiquetas del eje Y para que muestren las categorías de sequía
    ax.set_yticks(range(6))
    ax.set_yticklabels(["Sin sequía", "D0", "D1", "D2", "D3", "D4"])
    
    ax.set_title("Evolución Mensual de la Severidad de Sequía — Hermosillo", fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel("Fecha (Meses)", fontsize=10)
    ax.set_ylabel("Severidad (0 - 5)", fontsize=10)
    
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.show()

def plot_severidad_sequia_semanal(sequia_semanal):
    """
    Genera un gráfico de línea para visualizar la evolución semanal de la severidad de sequía.
    """
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 3.5))
    
    # Usamos la columna de fecha semanal y la severidad numérica calculada
    ax.step(sequia_semanal["fecha_semana"], sequia_semanal["severidad_sequia"], where="post", color="#d95f02", linewidth=1.5)
    
    # Línea de umbral (ej. D1 en adelante)
    ax.axhline(DROUGHT_EXTREME_MIN_SEVERITY, ls="--", color="gray", label="Umbral de sequía (≥ D1)")
    
    # Configurar las etiquetas del eje Y para que muestren las categorías de sequía
    ax.set_yticks(range(6))
    ax.set_yticklabels(["Sin sequía", "D0", "D1", "D2", "D3", "D4"])
    
    ax.set_title("Evolución Semanal de la Severidad de Sequía — Hermosillo", fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel("Fecha (Semanas)", fontsize=10)
    ax.set_ylabel("Severidad (0 - 5)", fontsize=10)
    
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.show()

@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = FIGURES_DIR / "plot.png",
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Generating plot from data...")
    df_panel = pd.read_csv(input_path)
    plot_serie_temporal_ira(df_panel)
    logger.success("Plot generation complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
