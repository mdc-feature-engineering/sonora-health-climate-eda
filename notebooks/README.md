# Índice de notebooks — Sonora Health-Climate EDA

> **Estado:** paneles integrados mensual (`panel_hermosillo.parquet`, 72
> meses) y semanal (`panel_eda_semanal.parquet`, 313 semanas
> epidemiológicas) con las 5 capas. El nivel intra-urbano se cubrió con
> la capa de **colonias** (CONAPO 2020) en `3.6`; el nivel AGEB ya no es
> necesario. Ver `docs/docs/protocolo_eda.md` para el detalle metodológico.

## Auto-EDA (primer análisis rápido)

| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `00_auto_eda/0.0-auto-eda.ipynb` | Reporte automático con `ydata-profiling` → `reports/auto_eda_report.html` | 📝 Template (requiere panel integrado) |

## Estado de las capas de datos

| Capa | Notebook | Estado | Responsable |
|------|----------|--------|-------------|
| 1. Marginación | `01_ingesta/1.3-indice_-marginacion.ipynb` | ✅ Implementado — IMM municipal 2015/2020 (CSV en `data/interim/marginacion/`, usados por el panel) y cartografía por colonia 2020 (`colonias_marginacion_hermosillo.gpkg`, la usa `3.6`) | Compañeros |
| 2. Clima (temperatura) | `01_ingesta/1.0-conagua-temperatura.ipynb` | ✅ Implementado | — |
| 3. Sequía | `01_ingesta/1.2-monitor-sequia.ipynb` | ✅ Implementado | — |
| 4. Calidad del aire | `01_ingesta/1.4-calidad-aire.ipynb` | ✅ Implementado — RUOA-UNAM, observatorio ERNO (horario 2015–2020) → diario → semanal y mensual en `02_procesamiento/2.4`; ya integrada al panel | Compañeros |
| 5. Salud respiratoria | `01_ingesta/1.5-enfermedades-respiratorias.ipynb` | ✅ Implementado — casos confirmados de IRA (Salud Sonora 2010–2020), semanal → mensual vía `panel.health_ira_monthly()` | — |

## Orden de ejecución sugerido

### `01_ingesta/` — Fase A (ETL)
| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `1.0-conagua-temperatura.ipynb` | Descarga e ingesta de temperatura media por estación (SMN/CONAGUA) | ✅ |
| `1.2-monitor-sequia.ipynb` | Monitor de Sequía CONAGUA → formato tidy por año | ✅ |
| `1.3-indice_-marginacion.ipynb` | Índice de marginación municipal (CONAPO) + descarga y recorte de la cartografía por colonia 2020 | ✅ |
| `1.4-calidad-aire.ipynb` | PM2.5, PM10, O3 horarios de RUOA-ERNO → tabla horaria sin limpiar | ✅ |
| `1.5-enfermedades-respiratorias.ipynb` | IRAs confirmadas (Salud Sonora) → mensual Hermosillo | ✅ |

### `02_procesamiento/` — Limpieza y agregación por capa

El número menor coincide con la libreta de ingesta de la misma capa (`2.1`
es el complemento diario de clima, sin libreta de ingesta propia). Cada
libreta revisa las transformaciones que aplica `panel.py` —las mismas que
ejecuta `3.0`— y termina con una tabla de **decisiones de procesamiento**;
un cambio decidido aquí se implementa en `panel.py` para que llegue al panel.

| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `2.0-procesamiento-temperatura-smn.ipynb` | TMed/TMax/TMin por estación → serie mensual de Hermosillo; centinelas, coherencia física, meses corruptos (dic-2015/16/17) | 📝 Template |
| `2.1-procesamiento-calor-openmeteo.ipynb` | Open-Meteo diario → olas de calor (≥35 °C, P95, heat index) y métricas mensuales; contraste con SMN | 📝 Template |
| `2.2-procesamiento-sequia.ipynb` | Monitor de Sequía quincenal → mensual (severidad media + moda); categorías sin mapeo y empates | 📝 Template |
| `2.3-procesamiento-marginacion.ipynb` | IMM 2010/2015/2020: homologación de columnas e interpolación mensual | 📝 Template |
| `2.4-procesamiento-calidad-aire.ipynb` | Limpieza horaria (banderas, BDL, artefactos) → diario → mensual (suficiencia 75 %, O3 8 h, días sobre la NOM) | ✅ |
| `2.5-procesamiento-salud-ira.ipynb` | IRA semanal → mensual: calidad de registros, semanas faltantes, `n_semanas`, 2020 atípico | 📝 Template |

### `03_eda/` — Integración y templates del rúbrica
| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `3.0-integracion-espacial.ipynb` | Panel mensual integrado (`panel.build_panel()` → `panel_hermosillo.parquet`) | ✅ (nivel municipal; intra-urbano por colonia en `3.6`) |
| `3.1-datos-faltantes.ipynb` | % faltantes, missingno, patrones temporales, imputación | 📝 Template (rúbrica: datos faltantes) |
| `3.2-outliers.ipynb` | Outliers con ≥2 técnicas: IQR/Z-score, Isolation Forest, LOF | 📝 Template (rúbrica: anomalías) |
| `3.3-relaciones-visualizacion.ipynb` | Series, scatter, pairplot y boxplots casos vs. exposición | 📝 Template (rúbrica: relaciones por visualización) |
| `3.4-correlacion.ipynb` | Heatmaps Pearson/Spearman, correlación con variable objetivo | 📝 Template (rúbrica: correlación) |
| `3.5-reduccion-dimensionalidad.ipynb` | PCA (scree, loadings) + t-SNE para visualización | 📝 Template (rúbrica: reducción de características) |
| `3.6-analisis-marginacion-urbana.ipynb` | Marginación por colonia (CONAPO SHP) × carga de IRA por ubicación de unidad CLUES | ✅ |

Cada notebook de `03_eda/` termina con una celda **Consulta con el equipo**
(rúbrica: consulta con los usuarios):

| Checkpoint | Notebooks | Qué se decide |
|------------|-----------|---------------|
| 1 — Calidad de datos | `3.1`, `3.2` | Qué variables/periodos se conservan, imputan o excluyen |
| 2 — Hallazgos exploratorios | `3.3`, `3.4`, `3.5` | Qué relaciones se profundizan en el plan |
| 3 — Interpretación | reporte final | Si los hallazgos responden las preguntas de investigación |

### Plan (cuando estén todos los datos)

No tienen notebook todavía; el detalle está en la sección 3 de
`docs/docs/protocolo_eda.md`:

- Análisis univariado (series, estacionalidad).
- Rezagos exposición → casos: panel semanal por semana epidemiológica y
  correlación cruzada (CCF).
- ~~Mapas por AGEB (marginación × morbilidad × exposición)~~ → hecho a nivel
  **colonia** en `3.6-analisis-marginacion-urbana.ipynb` (la cartografía de
  colonias CONAPO ya trae índice + población, sin necesidad del marco
  geoestadístico INEGI).
- GLM Poisson/Binomial Negativo con rezagos e interacciones.

## Cómo retomar una capa pendiente

1. Confirmar la fuente en `sonora_health_climate_eda/config.py`
   (`AIR_QUALITY_SOURCES`, `HEALTH_DATA_SOURCES`, `MARGINACION_AGEB_URL`,
   `MARGINACION_COLONIA_URL`).
2. Implementar el comando de descarga en `dataset.py` (ver los stubs como
   ejemplo) o documentar la descarga manual en el notebook.
3. Llenar el notebook esqueleto correspondiente en `01_ingesta/`.
4. Generar el diccionario de datos en `references/<capa>/`.
