# Heat Index (índice de calor) — Rothfusz/NWS

Documento de referencia sobre el heat index usado en el panel integrado
para medir exposición a **calor húmedo** en Hermosillo.

## ¿Por qué existe?

La temperatura del aire (`temperature_2m_max`) sola no mide cómo le afecta
al calor al cuerpo humano. El cuerpo se refresca **evaporando el sudor**,
y la humedad relativa del aire frena esa evaporación:

- **Aire seco** (HR baja): el sudor se evapora rápido → el cuerpo se
  enfría → se siente *menos* caliente de lo que marca el termómetro.
- **Aire húmedo** (HR alta): el sudor no se evapora → el calor se acumula
  → se siente *más* caliente aunque la temperatura sea igual o menor.

Dos días con Tmax = 40 °C pueden ser fisiológicamente muy distintos:
uno con HR 30% (desértico) y otro con HR 70% (monzón).

## Historia

- **1980s — Modelo de Steadman**: Robert Steadman publicó un modelo
  fisiológico del cuerpo humano (transferencia de calor por radiación,
  convección y evaporación del sudor) que calculaba la "temperatura
  equivalente" para combinaciones de temperatura, humedad, viento y
  radiación solar. Era físicamente riguroso pero computacionalmente
  pesado para uso operativo.
- **1990 — Rothfusz**: Michael Rothfusz, del NWS (National Weather
  Service, EE.UU.), ajustó una **regresión polinomial** sobre miles de
  salidas del modelo de Steadman, reduciendo el cálculo a una fórmula
  algebraica de un solo paso — lo bastante simple para calculadoras de
  la época y pronósticos del tiempo.
- Desde entonces es el estándar operativo en meteorología de EE.UU.,
  Canadá y gran parte de Latinoamérica (incluido el SMN de México en
  algunos productos). En inglés se conoce como **Heat Index** o "feels
  like temperature" ("se siente como").

## La fórmula

Implementación Rothfusz completa (regresión sobre el modelo de
Steadman). T = temperatura en °F, HR = humedad relativa en %:

```
HI = -42.379 + 2.04901523·T + 10.14333127·HR
     - 0.22475541·T·HR - 0.00683783·T² - 0.05481717·HR²
     + 0.00122874·T²·HR + 0.00085282·T·HR²
     - 0.00000199·T²·HR²
```

El resultado `HI` está en °F y se convierte a °C.

En `panel.py` la función `_heat_index_c(tmax_c, rh_pct)` aplica esta
fórmula sobre Tmax y `relative_humidity_2m_mean` **diarios** de
Open-Meteo, y luego se agregan métricas mensuales.

## Rangos de referencia (NWS)

| Heat Index (°C) | Categoría NWS |
|-----------------|---------------|
| < 27 °C | Sin precaución especial |
| 27–32 °C | Precaución (exposición prolongada, actividad intensa) |
| 32–40 °C | Precaución extrema |
| 40–46 °C | Peligro (golpe de calor probable) |
| 46–51 °C | Peligro extremo |
| > 51 °C | Riesgo extremo / emergencia sanitaria |

En el proyecto se usa `HEAT_INDEX_DANGER_C = 40 °C` como umbral de
días con calor peligroso (`dias_heat_index_ge_40`) y rachas ≥3 días
consecutivos como olas de calor húmedo (`n_olas_calor_humedo`).

## Ejemplos

| Tmax | HR | HI (sensación) | Lectura |
|------|------|----------------|---------|
| 40 °C | 35 % | ~46 °C | Calor seco: incómodo pero manejable |
| 39 °C | 70 % | ~57 °C | **Peor aunque el termómetro marca menos** — el sudor no evapora |
| 36 °C | 70 % | ~54 °C | Un día "fresco" de verano húmedo ya es peligroso |
| 26 °C | 65 % | ~28 °C | Invierno: irrelevante para salud |

## Por qué es relevante en Hermosillo

Hermosillo tiene **dos regímenes de calor** marcados por la humedad:

- **Jun–jul (calor seco, pre-monzón)**: HR ~30–40%. El HI apenas supera
  a la Tmax. Son los meses de Tmax absoluta más alta (44–46 °C), pero
  fisiológicamente el cuerpo aún puede enfriarse.
- **Ago–oct (monzón)**: HR ~50–70%. El HI se dispara 10–25 °C por encima
  de la Tmax. Ejemplo real del panel: **sep-2017** tuvo Tmax 40.8 °C y
  HR ~53% → HI máximo de **70.8 °C** de sensación térmica.

Esto significa que meses que por temperatura sola parecen "menos
extremos" que junio pueden ser los más peligrosos para la salud —
justo el tipo de señal que la pregunta de investigación busca capturar.

## Limitaciones

- **Validado para T ≥ 27 °C y HR ≥ 40%** (condiciones del ajuste de
  Rothfusz). En desierto seco con HR < 30% puede sobrestimar la
  sensación real.
- Asume **persona a la sombra, con brisa ligera**; no considera vestimenta,
  edad, condición de salud ni exposición solar directa (para eso existen
  índices como el WBGT, más complejos).
- Es un **proxy fisiológico**, no una medición médica: útil como
  covariable de exposición, no como diagnóstico.

## Uso en el proyecto

- **Variables del panel** (`panel_hermosillo.parquet`):
  - `heat_index_max_mes`: HI máximo del mes.
  - `dias_heat_index_ge_40`: días con HI ≥ 40 °C.
  - `dias_ola_calor_humedo` / `n_olas_calor_humedo`: rachas ≥3 días con
    HI ≥ 40 °C (olas de calor húmedo).
  - `mes_calor_humedo`: flag mensual.
- **Complementa a las olas P95** (`n_olas_calor_p95`), que no usan
  humedad: juntas permiten comparar el calor seco vs. húmedo frente a
  las IRAs.
- Referencias: Rothfusz (1990), *NWS Technical Attachment SR 90-23*;
  Steadman (1979), *The Assessment of Sultriness Part I*.
