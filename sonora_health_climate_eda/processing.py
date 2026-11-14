import pandas as pd
from sonora_health_climate_eda.config import PANEL_START_YEAR, PANEL_END_YEAR
from datetime import date 

def cargar_y_filtrar_salud(ruta_csv: str) -> pd.DataFrame:
    """
    Carga el dataset crudo y filtra estrictamente por Hermosillo (clave_municipio == 30).
    """
    df_raw = pd.read_csv(ruta_csv)

    # Filtrar por año 
    df_raw = df_raw[(df_raw['anio'] >= PANEL_START_YEAR) & (df_raw['anio'] <= PANEL_END_YEAR)].copy()

    print(f" [INGESTA] Registros totales en crudo: {len(df_raw)}")
    
    # Filtrar estrictamente por Hermosillo
    df_hermosillo = df_raw[df_raw['clave_municipio'] == 30].copy()
    
    # Validaciones de integridad rápidas
    if not df_hermosillo.empty:
        assert df_hermosillo['clave_municipio'].nunique() == 1, "¡Error! Hay más de un municipio en el filtro."
        assert df_hermosillo['clave_municipio'].iloc[0] == 30, "¡Error! La clave de municipio no es 30."
    
    print(f" [FILTRO] Registros filtrados para Hermosillo: {len(df_hermosillo)}")
    return df_hermosillo


def agrupar_casos_semanales(df_hermosillo: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa los datos por año y semana epidemiológica, sumando los casos de IRA.
    """
    df_semanal = (
        df_hermosillo
        .groupby(['anio', 'semana'], as_index=False)['casos']
        .sum()
        .rename(columns={'casos': 'casos_ira_total'})
    )
    return df_semanal


def construir_panel_temporal(df_semanal: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un grid temporal inteligente respetando si cada año tiene 52 o 53 semanas reales 
    (Opción A), evitando falsos picos en cero al cierre de año. Rellena los huecos reales con 0.
    """
    registros_grid = []
    
    for anio in range(PANEL_START_YEAR, PANEL_END_YEAR + 1):
        # Calcular cuántas semanas tiene realmente este año específico según el estándar ISO/Epidemiológico
        total_semanas = date(anio, 12, 28).isocalendar()[1]
        
        for semana in range(1, total_semanas + 1):
            registros_grid.append({'anio': anio, 'semana': semana})
            
    grid_completo = pd.DataFrame(registros_grid)
    
    # Hacer el merge con los datos agrupados
    df_panel = pd.merge(grid_completo, df_semanal, on=['anio', 'semana'], how='left')
    
    # Auditoría de semanas faltantes reales
    semanas_faltantes = df_panel['casos_ira_total'].isna().sum()
    print(f"[PANEL] Semanas faltantes reales detectadas e imputadas con 0: {semanas_faltantes}")
    
    # Rellenar nulos con ceros
    df_panel['casos_ira_total'] = df_panel['casos_ira_total'].fillna(0).astype(int)
    df_panel['clave_municipio'] = 30
    df_panel['municipio'] = 'HERMOSILLO'
    
    return df_panel


def validar_y_auditar_calidad(df: pd.DataFrame) -> dict:
    """
    Ejecuta el checklist de validación y calidad de datos (Sección 5)
    sobre el dataset semanal procesado de Hermosillo.
    Retorna un diccionario con las métricas del reporte de auditoría.
    """
    reporte = {}
    print("Ejecutando auditoría de calidad de datos...")
    
    # 1. Asegurar tipado entero para anio y semana
    df['anio'] = df['anio'].astype(int)
    df['semana'] = df['semana'].astype(int)
    
    # 2. Verificar valores nulos en columnas clave
    columnas_clave = ['anio', 'semana', 'casos_ira_total']
    nulos = df[columnas_clave].isnull().sum()
    reporte['valores_nulos'] = nulos.to_dict()
    
    if nulos.sum() > 0:
        raise ValueError(f" ¡Alerta de calidad! Se encontraron valores nulos en columnas clave: {nulos[nulos > 0].to_dict()}")
    else:
        print(" [OK] Cero valores nulos en columnas clave (`anio`, `semana`, `casos_ira_total`).")
        
    # 3. Validar que el rango de fechas cubra el periodo de análisis (2010–2020)
    min_anio, max_anio = df['anio'].min(), df['anio'].max()
    reporte['rango_anios'] = {"min": min_anio, "max": max_anio}
    
    if min_anio <= PANEL_START_YEAR and max_anio >= PANEL_END_YEAR:
        print(f" [OK] El rango temporal cubre el periodo esperado: {min_anio} - {max_anio}.")
    else:
        print(f" [AVISO] El rango temporal ({min_anio} - {max_anio}) difiere del periodo estándar {PANEL_START_YEAR}-{PANEL_END_YEAR}.")

    # 4. Detectar semanas con 0 casos y valores atípicos (outliers)
    semanas_cero = df[df['casos_ira_total'] == 0]
    reporte['semanas_con_cero_casos'] = len(semanas_cero)
    print(f" Se detectaron {len(semanas_cero)} semanas con 0 casos de IRA (imputadas o sin reporte).")
    
    # Detección de outliers estadísticos usando el Rango Intercuartílico (IQR)
    Q1 = df['casos_ira_total'].quantile(0.25)
    Q3 = df['casos_ira_total'].quantile(0.75)
    IQR = Q3 - Q1
    limite_superior = Q3 + 1.5 * IQR
    outliers_altos = df[df['casos_ira_total'] > limite_superior]
    reporte['total_outliers_altos'] = len(outliers_altos)
    print(f" Se detectaron {len(outliers_altos)} semanas con picos atípicos altos de casos (por encima de IQR).")

    # 5. Generar reporte de métricas descriptivas (Opcional del checklist)
    reporte['metricas_descriptivas'] = {
        "total_registros_semanales": len(df),
        "casos_totales_periodo": int(df['casos_ira_total'].sum()),
        "media_semanal": round(float(df['casos_ira_total'].mean()), 2),
        "mediana_semanal": round(float(df['casos_ira_total'].median()), 2),
        "desviacion_estandar": round(float(df['casos_ira_total'].std()), 2),
        "min_casos_semanales": int(df['casos_ira_total'].min()),
        "max_casos_semanales": int(df['casos_ira_total'].max())
    }
    
    print("\n--- RESUMEN DEL REPORTE DE CALIDAD ---")
    for metrica, valor in reporte['metricas_descriptivas'].items():
        print(f"   • {metrica}: {valor}")
        
    print("------------------------------------------\n")
    return reporte

if __name__ == "__main__":
    app()
