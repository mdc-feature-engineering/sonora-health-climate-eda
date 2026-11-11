# Protocolo de Investigación y Propuesta Metodológica (EDA)

## Título del Proyecto

**Análisis Exploratorio y Modelado Espacio-Temporal de la Vulnerabilidad Socioeconómica y Climática ante Enfermedades Respiratorias en Hermosillo, Sonora**

---

## 1. Preguntas de Investigación

**Pregunta general:**

> ¿Cómo inciden el calor extremo, la sequía y la contaminación del aire en la incidencia de enfermedades respiratorias en Hermosillo?

**Pregunta específica (hipótesis de vulnerabilidad diferencial):**

> ¿Las zonas más marginadas de Hermosillo son las más afectadas por las enfermedades respiratorias durante olas de calor y sequía?

*(Versión original de trabajo: "¿De qué manera la población marginizada en
Hermosillo presenta una mayor exposición y vulnerabilidad a enfermedades
asociadas al calor extremo y la sequía, mediada por la calidad del aire y los
efectos de rezago temporal?")*

## 1.1 Objetivo del proyecto (EDA)

Explorar a profundidad la relación entre la exposición ambiental (calor
extremo, sequía y contaminación del aire) y la morbilidad respiratoria en
Hermosillo, para definir los alcances posibles del producto de datos final:

- **Corto plazo:** sistema de alerta por condiciones climáticas y de aire.
- **Mediano plazo:** modelo predictivo de incidencia por AGEB que incorpore
  la vulnerabilidad socioeconómica (marginación).
- **Largo plazo:** herramienta de planeación en salud pública dirigida a
  zonas de alta marginación.

---

## 2. Definición y Homologación de Fuentes de Datos

Para llevar a cabo este análisis, se integrarán cinco capas de información
clave, homologadas a nivel espacial y temporal:

1. **Índice de Marginación:**
   * *Nivel:* AGEB urbana (Áreas Geoestadísticas Básicas) o Localidad (CONAPO / INEGI). Permite una granularidad fina intra-urbana en Hermosillo.
   * *Variables:* Porcentaje de población en pobreza, carencia de servicios básicos (agua, drenaje), y tipos de vivienda.
2. **Temperatura y Clima:**
   * *Nivel:* Estaciones de monitoreo atmosférico en Hermosillo (REDNAMEC / unidades locales) o modelos gridados de reanálisis.
   * *Variables:* Temperatura media y máxima diaria, anomalías térmicas y olas de calor.
3. **Índice de Sequía:**
   * *Nivel:* Municipal (Monitor de Sequía en México / SMN).
   * *Variables:* Categorías de sequía y déficit hídrico acumulado, actuando como un factor estructural de fondo (suelos secos y suspensión de polvo).
4. **Calidad del Aire:**
   * *Nivel:* Estaciones de monitoreo atmosférico diarias.
   * *Variables:* Concentraciones de partículas suspendidas ($PM_{2.5}$, $PM_{10}$) y ozono ($O_3$).
5. **Enfermedades Respiratorias (Variable de Respuesta):**
   * *Nivel:* Jurisdicción sanitaria o unidades médicas georeferenciadas por AGEB de residencia del paciente (Secretaría de Salud / SINAVE).
   * *Variables:* Conteo diario de casos de infecciones respiratorias agudas (IRAs), asma, EPOC y neumonías.

### 2.1 Cómo quedó el panel en la práctica

El protocolo original planteaba cinco capas de datos. El panel que
realmente se construyó (`data/processed/panel_hermosillo.parquet`)
adapta ese diseño a lo que fue posible obtener. Esta sección explica
qué contiene, de dónde sale cada cosa y sus limitaciones.

#### Qué contiene el panel

- **Periodo:** enero 2015 a diciembre 2020 (72 meses), a nivel
  municipio (Hermosillo, `CVE_MUN=26030`). La ventana está
  parametrizada en `config.py` (`PANEL_START_YEAR`/`PANEL_END_YEAR`)
  para poder extenderla a 2010–2020.
- **Desenlace (salud):** casos **confirmados de IRA** — infecciones
  respiratorias agudas, código CIE-10 `J00-J06, J20, J21` (excepto
  `J02.0` y `J03.0`). Fuente: datos semanales de Salud Sonora
  (SUIVE/SINAVE) agregados a mes. Asma, EPOC y neumonías **no están
  disponibles** en la fuente abierta; el análisis se hace solo con IRA.
  Un mes agrupa 4 o 5 semanas epidemiológicas (`n_semanas`);
  `casos_ira_por_semana` permite comparar meses sin que los de 5 semanas
  parezcan tener más casos.

#### De dónde sale cada capa

| Capa | Fuente | Transformación aplicada |
|------|--------|------------------------|
| Temperatura | Resúmenes mensuales SMN/CONAGUA | Ya vienen mensuales; se promedian las estaciones de Hermosillo |
| Sequía | Monitor de Sequía SMN/CONAGUA | De quincenal a mensual: severidad promedio + categoría más frecuente |
| Marginación | CONAPO/INEGI (archivos ya depurados en `data/interim/`) | La marginación solo existe por censo (2015, 2020): se interpola linealmente mes a mes |
| Calor extremo diario | Open-Meteo Archive (reanalysis) | Serie diaria 1991–2020 de Tmax, Tmin y humedad → agregados mensuales |
| Calidad del aire | **Sin fuente todavía** | No está en el panel; sigue pendiente |

#### Cómo medimos el calor extremo

Un mes con temperatura promedio alta no es lo mismo que un mes con
**olas de calor** reales. Por eso se usan datos **diarios** (Open-Meteo)
y se definen olas de calor de dos formas:

- **Ubral fijo (`n_olas_calor`):** ≥3 días seguidos con Tmax ≥ 35 °C.
  Es la convención estándar, pero en Hermosillo casi todo el verano la
  cumple — sirve de referencia, no discrimina mucho.
- **Ubral adaptado (`n_olas_calor_p95`) — métrica principal:** el P95
  (percentil 95) de Tmax y Tmin **de cada mes calendario**, calculado
  con la historia 1991–2020. Un día "extremo" es aquel donde **tanto la
  máxima como la mínima** superan su P95 del mes, y una ola son ≥3 días
  seguidos así. Esto detecta calor **anómalo para la época** — por
  ejemplo, una semana de 38 °C en marzo cuenta como ola aunque no
  alcance los 45 °C de agosto.
- **Calor húmedo (heat index, Rothfusz):** la temperatura sola no
  basta — si el aire está húmedo, el cuerpo no se refresca bien aunque
  haga menos calor. El heat index convierte (Tmax + humedad) en
  "temperatura de sensación". En Hermosillo separa el calor seco de
  junio–julio (HR ~30–40%) del calor húmedo del monzón agosto–octubre
  (HR ~50–70%), donde la sensación puede llegar a 60–70 °C en meses con
  Tmax "normal" (sep-2017: Tmax 40.8 °C + HR 53% → HI 70.8 °C).
  Métricas: `heat_index_max_mes`, `dias_heat_index_ge_40`,
  `n_olas_calor_humedo`. Es la fórmula del NWS de EE.UU. (1990);
  detalle completo en [`heat_index.md`](heat_index.md).

Además hay flags mensuales listos para el análisis: `mes_calor_extremo`,
`mes_sequia`, `mes_extremo_conjunto`, `mes_ola_calor_p95` y
`mes_ola_calor_p95_y_sequia` (ola adaptada + sequía a la vez).

#### Problemas de los datos que hay que recordar

- **Dic-2015, dic-2016 y dic-2017:** los archivos de temperatura del
  SMN vienen corruptos en la fuente (valores idénticos e
  imposibles para diciembre). El panel los deja en blanco (NaN).
- **2020 es un año atípico:** los casos de IRA colapsaron ~70% por la
  disrupción de COVID-19 en la notificación epidemiológica. El clima
  de 2020 sí es válido. La columna `anio_atipico` marca esos 12 meses
  para excluirlos o tratarlos con una variable indicadora.
- **Las unidades de salud están georreferenciadas:** las 103 clínicas
  que reportaron IRA en Hermosillo fueron cruzadas con el catálogo
  DGIS/SSA y tienen domicilio y coordenadas en
  `data/external/clues/clues_hermosillo_ira.csv` — habilita análisis a
  nivel unidad médica en el futuro.

#### Limitaciones que se documentarán en el reporte

- La marginación es **interpolada** (se supone cambio lineal entre
  censos), no observada mes a mes.
- La sequía pasa de quincenal a mensual por promedios — se pierde
  detalle de eventos cortos.
- La semana epidemiológica se asigna al mes de su fecha de inicio.
- **No hay datos de calidad del aire** — la primera pregunta de
  investigación solo podrá responderse parcialmente.

---

## 3. Estructura Metodológica del EDA (Análisis Exploratorio de Datos)

> **Alcance actual:** por ahora el proyecto cubre solo la **ingesta e
> integración** de las capas (Fase A) y los templates de datos faltantes,
> outliers, relaciones por visualización, correlación y reducción de
> dimensionalidad. El resto (secciones 3.2 y 4) queda como **plan**
> y se hará cuando estén completos los datos (calidad del aire y geometría
> AGEB).

### 3.1 Implementado: ingesta, integración y calidad de datos

#### Fase A: Ingesta, limpieza e integración (ETL)

* **Análisis de datos faltantes:** cuantificación del porcentaje de
  faltantes por variable, identificación de patrones temporales (días o
  temporadas completas ausentes, p.ej. mantenimiento de estaciones) y
  definición de la estrategia de imputación por variable (interpolación
  temporal, media por estación, forward-fill o exclusión justificada).
  *(Libreta: `02_eda/2.1-datos-faltantes.ipynb`)*
* Estandarización de claves geoespaciales (INEGI GEOID) y uniones
  espaciales (*spatial joins*) entre AGEBs y estaciones de medición.
* **Detección de anomalías (outliers):** aplicación de **al menos dos
  técnicas** — regla IQR/Z-score (univariado e interpretable), Isolation
  Forest y Local Outlier Factor (multivariado, sobre variables
  estandarizadas) — con comparación de resultados. Los outliers se
  clasifican como *eventos reales* (olas de calor, picos de
  contaminación, brotes epidemiológicos) o *errores de datos*, y se
  documenta la decisión de tratamiento para cada uno.
  *(Libreta: `02_eda/2.2-outliers.ipynb`)*
* **Relaciones por visualización:** series de casos vs. exposición,
  scatter por estación, pairplot y boxplots en meses con y sin ola de
  calor o sequía.
  *(Libreta: `02_eda/2.3-relaciones-visualizacion.ipynb`)*
* **Correlaciones de Pearson/Spearman:** heatmaps de correlación entre
  todas las variables numéricas del panel, correlación con la variable de
  respuesta (casos de IRA) y prueba de significancia; scatter plots de
  las relaciones más fuertes.
  *(Libreta: `02_eda/2.4-correlacion.ipynb`)*
* **Reducción de dimensionalidad para visualización:** **PCA** (scree
  plot, loadings) y **t-SNE** para explorar si los meses se agrupan por
  estación del año, marginación o intensidad de exposición.
  *(Libreta: `02_eda/2.5-reduccion-dimensionalidad.ipynb`)*

### 3.2 Plan: próximos pasos (sin libreta todavía)

#### Fase B: Análisis univariado

* **Distribución temporal:** estacionalidad y tendencias en las series
  de temperatura, calidad del aire y consultas respiratorias.
* **Distribución espacial:** mapas de Hermosillo cruzando marginación
  con incidencia acumulada de morbilidad respiratoria.

#### Fase C: Rezagos

* **Panel semanal:** construir un panel por semana epidemiológica
  (domingo a sábado, ~313 semanas en 2015–2020) con los casos de IRA
  semanales, Open-Meteo diario agregado a semana, la sequía del último
  registro quincenal vigente y la marginación del mes (la temperatura SMN
  es mensual y no entraría). Permite estimar rezagos de 0–3 semanas que en
  el panel mensual se diluyen.
* **Función de Correlación Cruzada (CCF):** identificar empíricamente el
  rezago óptimo entre la exposición ambiental y los casos.
* **Relación calidad del aire–casos:** días con $PM_{2.5}/PM_{10}$
  elevados frente a casos de IRA, cuando exista la fuente de aire.

#### Fase D: Modelado estadístico (GLM)

* Modelos Lineales Generalizados (GLM) con distribución de **Poisson** o
  **Binomial Negativa** (adecuados para conteo de casos médicos):

  $$\log(\mathbb{E}[Y_t]) = \beta_0 + \beta_1 \text{Temp}_t + \beta_2 \text{Temp}_{t-1} + \beta_3 \text{PM}_{2.5, t-2} + \beta_4 \text{Marginación} + \text{Tendencia}$$

* Términos de interacción para evaluar si el impacto del calor o la
  contaminación es mayor en zonas de alta marginación.
* En el panel mensual, usar `log(n_semanas)` como *offset* para
  compensar los meses de 4 vs. 5 semanas epidemiológicas.

---

## 4. Plan: Manejo de Rezagos Temporales (*Lag Effects*)

> Pendiente; no implementado todavía (ver sección 3.2).

En epidemiología ambiental, los efectos de la exposición no son
instantáneos: la inhalación de partículas o el estrés térmico provocan
inflamación y debilitamiento que se manifiestan días después.

### Tipos de rezagos a considerar

* **Temperatura y calor extremo:** efectos agudos rápidos (0 a 3 días);
  el agravamiento respiratorio por aire caliente y seco suele verse entre
  las 24 y 72 horas.
* **Contaminación atmosférica ($PM_{2.5}$, $PM_{10}$):** los efectos
  inflamatorios se reflejan desde el mismo día (**lag 0**) hasta 4 o 5
  días después (**lag 4**, **lag 5**).

### Implementación en Python con `pandas`

```python
import pandas as pd

# Suponiendo un DataFrame diario ordenado por fecha
df['temp_max'] = df['temperatura_maxima']
df['pm25'] = df['pm25_promedio']

# Creación de variables con rezagos de 1 a 4 días
for lag in range(1, 5):
    df[f'temp_max_lag{lag}'] = df['temp_max'].shift(lag)
    df[f'pm25_lag{lag}'] = df['pm25'].shift(lag)

# Promedios móviles para exposición acumulada (ej. últimos 3 días)
df['pm25_ma3'] = df['pm25'].rolling(window=3).mean()
```

### Modelado avanzado opcional

Para un nivel superior, se pueden integrar **Distributed Lag Models
(DLM)** o **Distributed Lag Non-Linear Models (DLNM)** para estimar
curvas de retardo-respuesta no lineales a lo largo del tiempo.

---

## 5. Entregables del Proyecto

### 5.1 Auto-EDA (primer análisis rápido)

Una libreta de **auto-EDA** que genere un reporte exploratorio automático
y rápido sobre el dataset integrado, visualizable como parte de la página
del proyecto en GitHub.

- *Herramienta:* `ydata-profiling` (reporte HTML interactivo con
  estadísticas, distribuciones, correlaciones y faltantes).
- *Entrada:* panel integrado `data/processed/panel_hermosillo.parquet`
  (salida de `02_eda/2.0-integracion-espacial.ipynb`).
- *Salida:* `reports/auto_eda_report.html` (commiteado y enlazado desde
  `README.md`).
- *Libreta:* `notebooks/00_auto_eda/0.0-auto-eda.ipynb`.

### 5.2 Libretas de análisis exploratorio

Las libretas de `notebooks/02_eda/` cubren los aspectos del análisis
exploratorio (ver el mapa aspecto → libreta en `notebooks/README.md`):

| Aspecto | Libreta |
|---------|---------|
| Integración espacial/temporal del panel | `2.0-integracion-espacial.ipynb` |
| Datos faltantes | `2.1-datos-faltantes.ipynb` |
| Anomalías/outliers (≥2 técnicas) | `2.2-outliers.ipynb` |
| Relaciones entre variables por visualización | `2.3-relaciones-visualizacion.ipynb` |
| Correlación entre variables | `2.4-correlacion.ipynb` |
| Reducción de características (PCA, t-SNE) | `2.5-reduccion-dimensionalidad.ipynb` |

Univariado, rezagos (CCF), mapas coropléticos y GLM quedan
como plan (sección 3.2) y todavía no tienen libreta.

### 5.3 Consulta con los usuarios durante la exploración

El proceso de exploración es **iterativo y se consulta con el equipo en
los puntos de decisión**, no es un flujo lineal:

- **Checkpoint 1 — Calidad de datos:** revisión del análisis de faltantes
  y outliers; se decide qué variables o periodos se conservan, se imputan
  o se excluyen.
- **Checkpoint 2 — Hallazgos exploratorios:** revisión de correlaciones
  para decidir qué relaciones se profundizan en las fases del plan
  (rezagos, GLM).
Cada libreta de `02_eda/` termina con una celda *Consulta con el equipo*
para registrar fecha, participantes, hallazgo presentado y decisión.

- **Checkpoint 3 — Interpretación:** validación de que los hallazgos
  responden las preguntas de investigación antes de redactar el reporte.

### 5.4 Reporte final

Al concluir el EDA se integra un **reporte final** (markdown; `pdf`/`html`
según formato de entrega) con la siguiente estructura, en este orden:

1. **Nombre del proyecto.**
2. **Equipo e integrantes:** nombre del equipo (opcional) y nombres de los
   integrantes con su información de contacto (correo, LinkedIn, etc.).
3. **Resumen** de uno o dos párrafos con los hallazgos más importantes,
   escritos de forma directa.
4. **Gráfica o imagen representativa** del hallazgo más importante.
5. **Detalle de los hallazgos** (máximo 3 páginas), incluyendo bibliografía
   y gráficas.

*Template:* `reports/reporte_final_template.md`.
