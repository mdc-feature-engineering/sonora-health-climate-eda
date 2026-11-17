# Catálogo de datos procesados para el panel

Describe las tablas que salen del procesamiento (`notebooks/02_procesamiento/`) y que se integran en el panel de Hermosillo (`03_eda/3.0`). Para cada capa se indica de dónde viene, qué columnas tiene y qué hay que tomar en cuenta al usarla.

Ventana del panel: **ene-2015 a dic-2020** (`PANEL_START_YEAR` y `PANEL_END_YEAR` en `config.py`). Hay dos versiones del panel: **mensual** (72 meses, llave `fecha_mes`) y **semanal** (313 semanas epidemiológicas de domingo a sábado, llave `fecha_semana`).

> Estado revisado el 15-nov-2026. Si cambia `panel.py` o algún notebook 2.x, actualizar este archivo.

## Resumen

| # | Capa | Fuente | Notebook | Función en el paquete | Mensual | Semanal |
|---|------|--------|----------|-----------------------|---------|---------|
| 1 | Temperatura SMN | CONAGUA/SMN, 3 estaciones | 2.0 | `panel.climate_hermosillo()` | ✅ | ❌ (solo existe por mes) |
| 2 | Calor extremo diario | Open-Meteo (reanálisis) | 2.1 | `panel.openmeteo_hermosillo_monthly()` / `_weekly()` | ✅ | ✅ |
| 3 | Sequía | Monitor de Sequía CONAGUA | 2.2 | `panel.drought_hermosillo()` / `_weekly()` | ✅ | ✅ |
| 4 | Marginación | CONAPO (censos 2015 y 2020) | 2.3 | `panel.marginacion_hermosillo()` | ✅ | ✅ (cada semana toma el valor de su mes) |
| 5 | Calidad del aire | RUOA-UNAM, estación ERNO | 2.4 | `aire.build_weekly()` / `build_monthly()` | ✅ | ✅ |
| 6 | Casos de IRA | Salud Sonora (SUIVE) | 2.5 | `panel.health_ira_monthly()` / `_weekly()` | ✅ | ✅ |

**Llaves de tiempo**

- `fecha_mes`: primer día del mes (`2015-01-01`).
- `fecha_semana`: domingo con el que empieza la semana epidemiológica (`2015-01-04`). La semana 1 del año es la que contiene el 4 de enero.

---

## 1. Temperatura SMN

**Qué es:** temperatura media, máxima y mínima **mensual** de Hermosillo, como promedio de las estaciones `HM2SO`, `HMNSO` y `MMHO` (`config.CLIMATE_STATION_IDS`).

| Columna | Descripción | Unidad |
|---------|-------------|--------|
| `fecha_mes` | Mes | fecha |
| `temp_media_c` | Temperatura media mensual | °C |
| `temp_max_media_c` | Promedio mensual de la temperatura máxima | °C |
| `temp_min_media_c` | Promedio mensual de la temperatura mínima | °C |

**A tomar en cuenta**

- **dic-2015, dic-2016 y dic-2017 son `NaN`.** El SMN publicó archivos dañados (mismo valor en media, máxima y mínima).
- **No todos los meses tienen las 3 estaciones.** `MMHO` solo tiene 36 de 72 meses y `HMNSO` 70. Hay 36 meses con 3 estaciones, 34 con 2 y 2 con 1.
- **Solo existe por mes**, así que no entra al panel semanal.
- Con `temp_max_media_c` se calcula la bandera `mes_calor_extremo` (≥ 38 °C). En el panel semanal, `semana_calor_extremo` usa `tmax_media_sem` de Open-Meteo.

## 2. Calor extremo diario (Open-Meteo)

**Qué es:** métricas de calor calculadas con datos **diarios** de Open-Meteo (1991–2020) para el centro de Hermosillo, resumidas por mes o por semana. Los años 1991–2014 solo sirven de línea base para los percentiles.

Las dos tablas tienen las mismas columnas; cambia la llave (`fecha_mes` / `fecha_semana`) y el sufijo (`_mes` / `_sem`).

| Columna | Descripción |
|---------|-------------|
| `tmax_max_mes` / `_sem` | Tmax del día más caliente (°C) |
| `tmax_media_mes` / `_sem` | Promedio de las Tmax diarias (°C) |
| `tmin_min_mes` / `_sem` | Tmin más baja (°C) |
| `humedad_rel_media` | Humedad relativa promedio (%) |
| `dias_tmax_ge_35` | Días con Tmax ≥ 35 °C |
| `dias_ola_calor` | Días dentro de una ola **fija** (Tmax ≥ 35 °C, ≥ 3 días seguidos) |
| `dias_ola_calor_p95` | Días dentro de una ola **P95** (Tmax y Tmin sobre su P95 del mes calendario, ≥ 3 días seguidos) |
| `heat_index_max_mes` / `_sem` | Heat index (sensación térmica) más alto (°C) |
| `dias_heat_index_ge_40` | Días con heat index ≥ 40 °C |
| `dias_ola_calor_humedo` | Días dentro de una ola **húmeda** (heat index ≥ 40 °C, ≥ 3 días seguidos) |
| `n_olas_calor`, `n_olas_calor_p95`, `n_olas_calor_humedo` | Número de olas que **empiezan** en el periodo |

**A tomar en cuenta**

- **Cada ola se cuenta una sola vez, en el periodo de su primer día.** Por eso un mes puede tener días en ola pero `n_olas_* = 0` (la ola empezó el mes anterior).
- **La ola fija y la húmeda cubren casi todo el verano** (94 % de los días de junio y 97–98 % de julio–agosto), así que distinguen poco. La **P95** es la métrica principal, pero solo hay **5 olas** en 2015–2020.
- **El heat index está sobreestimado** (llega a 70.8 °C) porque combina la Tmax con la humedad *promedio* del día. Sirve para comparar días, no como valor absoluto. Pendiente con el equipo.
- **Open-Meteo marca ~2.2 °C menos que el SMN** (correlación 0.994). Para la temperatura mensual se usa el SMN.
- **La última semana (27-dic-2020) tiene 5 días**, porque la serie termina el 31 de diciembre.

## 3. Sequía

**Qué es:** el Monitor de Sequía publica una categoría por municipio **cada quincena** (2 registros por mes). Se resume por mes o por semana.

| Columna | Descripción |
|---------|-------------|
| `fecha_mes` / `fecha_semana` | Periodo |
| `severidad_sequia` | Promedio de la severidad de las quincenas del periodo, de 0 a 5: Normal/Sin sequía = 0, D0 = 1, D1 = 2, D2 = 3, D3 = 4, D4 = 5 |
| `categoria_sequia` | Categoría más frecuente (moda) del periodo: Normal, D0 … D4 |

**A tomar en cuenta**

- **Mensual:** 72 meses: 31 Normal, 21 D0, 9 D1, 7 D2 y 4 D3.
- **Sin sequía, la fuente deja la categoría vacía:** se rellena como "Normal" (severidad 0) en las dos versiones.
- **Empates en la moda:** 16 meses tienen dos quincenas con categorías distintas; en un empate gana la categoría **más severa**.
- **Semanal:** como la fuente es quincenal, cada semana repite el **último registro vigente**. La primera semana (4-ene-2015) queda en `NaN` porque no hay un registro anterior.
- Con `severidad_sequia` se calcula la bandera `mes_sequia` / `semana_sequia` (≥ 2, es decir D1 o peor).

## 4. Marginación

**Qué es:** índice de marginación municipal de CONAPO (serie DP2, comparable entre censos). Solo se mide en los censos 2015 y 2020; los meses intermedios se **interpolan** con una línea recta.

| Columna | Descripción (todas en %) |
|---------|--------------------------|
| `fecha_mes` | Mes |
| `ANALF` | Población de 15 años o más analfabeta |
| `SBASC` | Población de 15 años o más sin educación básica |
| `OVSDE` | Ocupantes en viviendas sin drenaje ni excusado |
| `OVSEE` | Ocupantes en viviendas sin energía eléctrica |
| `OVSAE` | Ocupantes en viviendas sin agua entubada |
| `OVPT` | Ocupantes en viviendas con piso de tierra |
| `VHAC` | Viviendas con hacinamiento |
| `PL.5000` | Población en localidades de menos de 5,000 habitantes |
| `PO2SM` | Población ocupada con ingresos de hasta 2 salarios mínimos |
| `IM` | Índice de marginación (adimensional). Un valor **más alto** parece indicar **menos** marginación |

**A tomar en cuenta**

- **Son estimaciones, no datos publicados.** Entre ene-2015 y ene-2020 el valor avanza en línea recta; todo 2020 tiene el valor del censo 2020.
- **`IMN` se eliminó** porque CONAPO lo normaliza con una escala distinta cada año y no sirve para comparar en el tiempo.
- **`PO2SM` salta de 20 % a 47 %** entre 2015 y 2020 en todo Sonora. Probablemente cambió cómo se mide (el salario mínimo subió mucho en 2019–2020); no interpretarlo como empeoramiento real.
- **Panel semanal:** cada semana toma el valor del mes de su domingo de inicio.
- Es un **solo valor para todo el municipio**. La comparación intra-urbana se hace con la **marginación por colonia 2020** (cartografía CONAPO, SHP con geometría + índice + población) en el notebook `3.6-analisis-marginacion-urbana`.
- Diccionario completo: `references/marginacion/data_dictionary_conapo_IM.md`.

## 5. Calidad del aire

**Qué es:** PM2.5, PM10 y O3 del observatorio ERNO (RUOA-UNAM), la única estación de Hermosillo. Se limpia hora por hora, se promedia por día con criterio de suficiencia (75 %) y se resume por semana o mes. Diccionario completo al final del notebook 2.4.

| Columna | Descripción |
|---------|-------------|
| `pm25_ugm3`, `pm10_ugm3` | Promedio de los promedios diarios de 24 h (µg/m³) |
| `pm25_max_diario_ugm3`, `pm10_max_diario_ugm3` | Promedio de 24 h del peor día (µg/m³) |
| `o3_ppb` | Promedio de los promedios diarios de O3 (ppb) |
| `o3_max8h_ppb` | Promedio del máximo diario de 8 h (ppb); métrica normada de O3 |
| `o3_max8h_max_ppb` | Máximo de 8 h del peor día (ppb) |
| `*_dias_excede_nom` | Días sobre la NOM (PM2.5 45, PM10 75 µg/m³; O3 70 ppb) |
| `*_categoria_peor_dia` | Categoría AIRE Y SALUD del peor día (Buena … Extremadamente mala) |
| `*_dias_aceptable_o_peor` | Días en categoría Aceptable o peor |
| `*_dias_validos` | Días medidos que cumplen la suficiencia |
| `*_interpolado` | `True` si el promedio se rellenó por interpolación |
| `pm10_o3_*` | Lo mismo para la peor de PM10 y O3 de cada día |

`*` = `pm25`, `pm10` u `o3`. La tabla semanal trae además `anio`, `semana` y `n_dias`, que `panel.py` quita al unir.

**A tomar en cuenta**

- **PM2.5 no tiene datos desde junio de 2018.** Para 2019–2020 usar PM10 como indicador de partículas.
- **Jun–nov de 2018 no tiene ningún contaminante** (la estación se apagó).
- **Solo se interpolan huecos cortos** (≤ 2 semanas o 1 mes), marcados en `*_interpolado`. Los huecos largos quedan en `NaN`; no se rellenan con promedios.
- **Cobertura semanal:** PM10 91 %, O3 89 %, PM2.5 55 %.
- **Temporadas:** PM10 empeora de octubre a enero; O3 en primavera (abril–mayo).
- Se guarda en CSV (no parquet): `data/processed/aire/aire_hermosillo_{semanal,mensual}.csv`.

## 6. Casos de IRA

**Qué es:** casos confirmados de infecciones respiratorias agudas (CIE-10 J00–J06, J20, J21, menos J02.0 y J03.0) de Hermosillo, por semana epidemiológica. Se suman todos los sexos, edades y clínicas.

| Tabla | Columna | Descripción |
|-------|---------|-------------|
| Semanal | `fecha_semana`, `anio`, `semana` | Semana epidemiológica |
| Semanal | `casos_ira_total` | Casos **de la semana** |
| Mensual | `fecha_mes` | Mes (cada semana se asigna al mes de su domingo de inicio) |
| Mensual | `casos_ira` | Casos **del mes** (suma de sus semanas) |
| Mensual | `n_semanas` | Semanas que suma el mes (4 o 5) |
| Mensual | `casos_ira_por_semana` | Casos **promedio por semana** del mes (`casos_ira / n_semanas`) |

**A tomar en cuenta**

- **Los meses tienen 4 o 5 semanas.** Para comparar meses, usar `casos_ira_por_semana`, no la suma.
- **2020 es atípico:** los casos caen ~70 % por la COVID-19 (cambió la notificación, no la enfermedad). La bandera `anio_atipico` lo marca; no usar 2020 como si fuera un año normal. En el panel semanal marca 53 semanas: la SE1 de 2020 empieza el 29-dic-2019.
- **Semanas epidemiológicas por año:** 2015–2019 tienen 52 y 2020 tiene 53. Ojo: `processing.construir_panel_temporal()` (notebook 2.5) cuenta semanas ISO, que empiezan en lunes, y por eso crea una "semana 53 de 2015" con 0 casos que no existe en el calendario epidemiológico. Revisar con el equipo.
- **La semana es de notificación, no de inicio de síntomas.** Puede haber rezago administrativo de días o semanas entre la consulta y el registro, y no todas las clínicas reportan con la misma puntualidad — relevante al interpretar rezagos cortos (0–2 semanas) contra exposiciones.
- **Depende del catálogo CLUES.** `health_ira_weekly()` ahora lee `data/interim/salud_ira_hermosillo.csv`, que genera el notebook 2.5 al unir los casos con `data/external/clues/clues_hermosillo_ira.csv`. Ese catálogo no está en el repositorio: hay que pedirlo al equipo.

---

## Banderas que agrega el panel

`build_panel_monthly()` y `build_panel_weekly()` agregan columnas de sí/no (`mes_*` en la mensual, `semana_*` en la semanal):

| Bandera | Se activa cuando |
|---------|------------------|
| `*_calor_extremo` | Tmax media ≥ 38 °C: `temp_max_media_c` (SMN) en la mensual, `tmax_media_sem` (Open-Meteo, ~2.2 °C más bajo) en la semanal |
| `*_sequia` | `severidad_sequia` ≥ 2 (D1 o peor) |
| `*_extremo_conjunto` | Calor extremo **y** sequía |
| `*_ola_calor` | Hubo al menos una ola fija |
| `*_ola_calor_p95` | Hubo al menos una ola P95 |
| `*_ola_calor_p95_y_sequia` | Ola P95 **y** sequía |
| `*_calor_humedo` | Hubo al menos una ola húmeda |
| `anio_atipico` | El año (epidemiológico, en la semanal) es 2020 |

**Ojo con `*_calor_extremo`:** el panel mensual y el semanal no usan la misma fuente, porque el SMN solo existe por mes. Con el mismo umbral de 38 °C, Open-Meteo marca menos calor que el SMN (~2.2 °C de diferencia): por mes, el SMN da 24 meses y Open-Meteo solo 15. En el panel semanal se marcan 62 de 313 semanas. Se decidió conservar el umbral de 38 °C en los dos paneles (15-nov-2026); un mes "extremo" en el panel mensual puede no tener semanas "extremas" en el semanal. Con 36 °C, Open-Meteo daría 22 meses y 100 semanas, más parecido al SMN.

## Cómo se arma el panel

Cada notebook 2.x guarda su capa en `data/processed/` en su celda **"Guardar salida"**, y `03_eda/3.0` las une con `build_panel_monthly()` y `build_panel_weekly()`. Hay que ejecutar primero los notebooks 2.0–2.5 (al menos esa celda) y después el 3.0.

| Capa | Notebook | Archivo que lee el panel |
|------|----------|--------------------------|
| SMN | 2.0 | `data/processed/climate_hermosillo.parquet` (solo mensual) |
| Open-Meteo | 2.1 | `data/processed/openmeteo_hermosillo_monthly.parquet` y `openmeteo_hermosillo_weekly.parquet` |
| Sequía | 2.2 | `data/processed/drought_hermosillo.parquet` y `drought_hermosillo_weekly.parquet` |
| Marginación | 2.3 | `data/processed/marginacion_hermosillo.parquet` (la semanal se arma desde la mensual) |
| Aire | 2.4 | `data/processed/aire/aire_hermosillo_mensual.csv` y `aire_hermosillo_semanal.csv` |
| IRA | 2.5 | `data/processed/health_ira_monthly.parquet` y `health_ira_weekly.parquet` |

**Resultado** (15-nov-2026, con las 6 capas): panel mensual de **72 meses × 66 columnas** y panel semanal de **313 semanas × 62 columnas** (4-ene-2015 a 27-dic-2020, todas en domingo), sin columnas vacías. Los únicos faltantes son los esperados: los 3 diciembres del SMN, los huecos de calidad del aire (sobre todo PM2.5 desde junio de 2018 y jun–nov de 2018; ver capa 5) y la sequía de la primera semana.

## Pendientes

- **Catálogo CLUES:** el notebook 2.5 necesita `data/external/clues/clues_hermosillo_ira.csv`, que no está en el repositorio pero se genera con `python -m sonora_health_climate_eda.dataset download-clues-data` (extracto del catálogo DGIS/SSA). Sin él no se generan los parquet de IRA.
- **Notebook 2.5:** llama a `health_ira_weekly(location=True)` y `health_ira_monthly(location=True)`, una opción que `panel.py` todavía no tiene.
- **Semana 53 de 2015:** `processing.construir_panel_temporal()` cuenta semanas ISO (ver capa 6).
- **Heat index sobreestimado:** decidir con el equipo (ver capa 2).
