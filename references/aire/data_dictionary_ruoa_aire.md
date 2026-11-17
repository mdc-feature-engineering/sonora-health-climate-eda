# Diccionario de Datos: Calidad del aire — Hermosillo (RUOA-UNAM, ERNO)

## Descripción general

PM2.5, PM10 y O3 del **observatorio ERNO** (Red Universitaria de
Observatorios Atmosféricos, RUOA-UNAM; 29.0814 N, 110.9706 W, 154 m), la
única estación de calidad del aire de Hermosillo. Resolución original:
**horaria** (hora local UTC-7; Hermosillo no usa horario de verano).

Archivos fuente: un CSV público por mes en
`data/raw/aire/ruoa_erno/AAAA-MM-ERNO_hora_L1_caire.csv`
(`https://ruoa.unam.mx/caire/erno/hora/`). Se descarga con
`python -m sonora_health_climate_eda.dataset download-air-quality-data`.

Cadena de procesamiento (comandos `python -m sonora_health_climate_eda.aire
<horario|diario|semanal|mensual>`, equivalentes a los notebooks 1.4 y 2.4):

1. **Horario** → `data/interim/aire/aire_hermosillo_horario.csv`.
2. **Diario** → `data/interim/aire/aire_hermosillo_diario.csv`: promedio de
   24 h con criterio de suficiencia (≥ 75 % de horas válidas) y categoría
   AIRE Y SALUD por día (`pm25_categoria`, `pm10_categoria`,
   `o3_categoria`, `pm10_o3_categoria`; NOM-172-SEMARNAT-2019).
3. **Semanal** → `data/processed/aire/aire_hermosillo_semanal.csv`
   (semana epidemiológica, domingo a sábado).
4. **Mensual** → `data/processed/aire/aire_hermosillo_mensual.csv`.

Las tablas semanal y mensual tienen las mismas métricas; cambia la llave de
tiempo.

## Variables

| Columna | Descripción |
|---------|-------------|
| `fecha_semana` | (semanal) Domingo de inicio de la semana epidemiológica |
| `anio`, `semana` | (semanal) Año y semana epidemiológicos, como en los casos de IRA |
| `n_dias` | (semanal) Días de la semana dentro de la serie: 7, salvo la SE 53 de 2020 (5) |
| `fecha_mes` | (mensual) Primer día del mes |
| `pm25_ugm3`, `pm10_ugm3` | Media de los promedios diarios de 24 h (µg/m³) |
| `pm25_max_diario_ugm3`, `pm10_max_diario_ugm3` | Promedio de 24 h del peor día del periodo (µg/m³) |
| `o3_ppb` | Media de los promedios diarios de 24 h de O3 (ppb) |
| `o3_max8h_ppb` | Media del máximo diario del promedio móvil de 8 h (ppb); **métrica normada de O3** |
| `o3_max8h_max_ppb` | Máximo de 8 h del peor día del periodo (ppb) |
| `*_dias_excede_nom` | Días sobre el límite diario de la NOM (PM2.5 45, PM10 75 µg/m³; O3 70 ppb) |
| `*_categoria_peor_dia` | Categoría AIRE Y SALUD (NOM-172-SEMARNAT-2019) del peor día: Buena, Aceptable, Mala, Muy mala o Extremadamente mala |
| `*_dias_aceptable_o_peor` | Días del periodo en categoría Aceptable o peor |
| `*_dias_validos` | Días medidos con la métrica normada válida; decide la suficiencia |
| `*_interpolado` | `True` si los promedios del periodo se interpolaron (hueco de ≤ 2 semanas o de 1 mes) |
| `pm10_o3_categoria_peor_dia`, `pm10_o3_dias_aceptable_o_peor`, `pm10_o3_dias_validos` | Lo mismo para la peor de PM10 y O3 de cada día; cuentan solo días con los dos contaminantes |

`*` = `pm25`, `pm10` u `o3`.

## Notas

- **PM2.5 no tiene datos válidos desde junio de 2018.** Para 2019–2020 usar
  PM10 como indicador de partículas.
- **Jun–nov de 2018 no tiene ningún contaminante** (la estación se apagó).
- **Solo se interpolan huecos cortos** (≤ 2 semanas o 1 mes), marcados en
  `*_interpolado`. Los huecos largos quedan en `NaN`; no se rellenan con
  promedios. Un periodo sin suficiencia conserva `*_dias_validos` para saber
  por qué faltó.
- **Cobertura semanal:** PM10 91 %, O3 89 %, PM2.5 55 %.
- **Temporadas:** PM10 empeora de octubre a enero; O3 en primavera
  (abril–mayo).
- Las bandas del Índice AIRE Y SALUD usadas son las de la
  NOM-172-SEMARNAT-2019 (`config.AIR_QUALITY_INDEX_BANDS`): coinciden con
  las normas vigentes en el periodo de análisis 2015–2020.
