from pathlib import Path
from loguru import logger
import pandas as pd
import typer

from sonora_health_climate_eda.config import FIGURES_DIR, PROCESSED_DATA_DIR, PANEL_START_YEAR, PANEL_END_YEAR, DROUGHT_EXTREME_MIN_SEVERITY

app = typer.Typer()

import matplotlib.pyplot as plt
import seaborn as sns

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
