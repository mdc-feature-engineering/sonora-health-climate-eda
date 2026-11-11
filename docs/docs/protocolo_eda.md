# Protocolo de Investigación y Propuesta Metodológica (EDA)

## Título del Proyecto
**Análisis Exploratorio y Modelado Espacio-Temporal de la Vulnerabilidad Socioeconómica y Climática ante Enfermedades Respiratorias en Hermosillo, Sonora**

---

## 1. Preguntas de Investigación

**Pregunta general:**

> ¿Cómo inciden el calor extremo, la sequía y la contaminación del aire en la incidencia de enfermedades respiratorias en Hermosillo?

**Pregunta específica (hipótesis de vulnerabilidad diferencial):**

> ¿Las zonas más marginadas de Hermosillo son las más afectadas por las enfermedades respiratorias durante olas de calor y sequía?

*(Versión original de trabajo: "¿De qué manera la población marginalizada en
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
Para llevar a cabo este análisis, se integrarán cinco capas de información clave, homologadas a nivel espacial y temporal:

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

---

## 3. Estructura Metodológica del EDA (Análisis Exploratorio de Datos)

### Fase A: Ingesta, Limpieza e Integración de Datos (ETL)
* **Análisis de datos faltantes:** cuantificación del porcentaje de faltantes por variable, identificación de patrones temporales (días/temporadas completas ausentes, p.ej. mantenimiento de estaciones) y definición de la estrategia de imputación por variable (interpolación temporal, media por estación, forward-fill o exclusión justificada). *(Libreta: `02_eda/2.4-datos-faltantes.ipynb`)*
* Estandarización de claves geoespaciales (INEGI GEOID) y uniones espaciales (*spatial joins*) entre AGEBs y estaciones de medición.

### Fase B: Análisis Univariado
* **Distribución temporal:** Análisis de estacionalidad y tendencias en series temporales diarias de temperatura, calidad del aire y picos de consultas respiratorias.
* **Distribución espacial:** Mapas coropléticos de Hermosillo cruzando grados de marginación urbana con la incidencia acumulada de morbilidad respiratoria.
* **Detección de anomalías (outliers):** aplicación de **al menos dos técnicas** — regla IQR/Z-score (univariado e interpretable), Isolation Forest y Local Outlier Factor (multivariado, sobre variables estandarizadas) — con comparación de resultados. Los outliers se clasifican como *eventos reales* (olas de calor, picos de contaminación, brotes epidemiológicos) o *errores de datos*, y se documenta la decisión de tratamiento para cada uno. *(Libreta: `02_eda/2.5-outliers.ipynb`)*

### Fase C: Análisis Bivariado y Correlaciones Cruzadas
* **Correlaciones de Pearson/Spearman:** Evaluación de la relación lineal entre días con mala calidad del aire ($PM_{2.5}/PM_{10}$ elevados) y el incremento de consultas respiratorias, con heatmaps de correlación entre todas las variables numéricas, correlación específica con la variable de respuesta y prueba de significancia estadística. *(Libretas: `02_eda/2.6-correlacion.ipynb` y `02_eda/2.2-bivariado-ccf.ipynb`)*
* **Visualización de relaciones:** scatter plots y matrices de dispersión (*pairplot*) de las variables con correlación más fuerte.
* **Función de Correlación Cruzada (CCF):** Identificación empírica del número óptimo de días de rezago entre la exposición ambiental y la respuesta médica.
* **Reducción de dimensionalidad para visualización:** proyección del panel a 2-3 dimensiones con **PCA** (scree plot, loadings, scatter coloreado por marginación/estación) y **t-SNE** (estructura de clusters no lineal), para explorar si los AGEBs/periodos se agrupan por nivel de marginación, estación del año o intensidad de exposición. *(Libreta: `02_eda/2.7-reduccion-dimensionalidad.ipynb`)*

### Fase D: Análisis Multivariado y Modelado Estadístico (GLM)
* Implementación de Modelos Lineales Generalizados (GLM) con distribución de **Poisson** o **Binomial Negativa** (ideales para conteo de casos médicos):
  $$\log(\mathbb{E}[Y_t]) = \beta_0 + \beta_1 \text{Temp}_t + \beta_2 \text{Temp}_{t-1} + \beta_3 \text{PM}_{2.5, t-2} + \beta_4 \text{Marginación} + \text{Tendencia}$$
* Inclusión de términos de interacción para evaluar si el impacto del calor/contaminación es estadísticamente mayor en zonas de alta marginación.

---

## 4. Manejo de Rezagos Temporales (*Lag Effects*)

En epidemiología ambiental, los efectos de la exposición ambiental no son instantáneos; la inhalación de partículas o el estrés térmico provocan inflamación y debilitamiento que se manifiestan días después.

### Tipos de Rezagos a Considerar:
* **Temperatura y Calor Extremo:** Efectos agudos rápidos (0 a 3 días), aunque el agravamiento respiratorio por aire caliente y seco suele verse reflejado entre las 24 y 72 horas.
* **Contaminación Atmosférica ($PM_{2.5}$, $PM_{10}$):** Los efectos inflamatorios en las vías aéreas se acumulan y se reflejan desde el mismo día (**Lag 0**) hasta 4 o 5 días después (**Lag 4**, **Lag 5**).

### Implementación en Python con `pandas`:
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

### Modelado Avanzado Opcional:
Para un nivel superior de posgrado, se pueden integrar **Distributed Lag Models (DLM)** o **Distributed Lag Non-Linear Models (DLNM)** para estimar curvas de retardo-respuesta no lineales a lo largo del tiempo.

---

## 5. Entregables del Proyecto

### 5.1 Auto-EDA (primer análisis rápido)

Una libreta de **auto-EDA** que genere un reporte exploratorio automático y
rápido sobre el dataset integrado, visualizable como parte de la página del
proyecto en GitHub.

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
| Distribuciones univariadas (temporal y espacial) | `2.1-univariado.ipynb` |
| Bivariado, correlación y rezagos (CCF) | `2.2-bivariado-ccf.ipynb` |
| Mapas coropléticos marginación × morbilidad × exposición | `2.3-espacial-coropletico.ipynb` |
| Datos faltantes | `2.4-datos-faltantes.ipynb` |
| Anomalías/outliers (≥2 técnicas) | `2.5-outliers.ipynb` |
| Correlación entre variables | `2.6-correlacion.ipynb` |
| Reducción de características (PCA, t-SNE) | `2.7-reduccion-dimensionalidad.ipynb` |

### 5.3 Consulta con los usuarios durante la exploración

El proceso de exploración es **iterativo y se consulta con el equipo/usuarios
en los puntos de decisión**, no es un flujo lineal:

- **Checkpoint 1 — Calidad de datos:** revisión del análisis de faltantes y
  outliers; se decide qué variables/periodos se conservan, se imputan o se
  excluyen.
- **Checkpoint 2 — Hallazgos exploratorios:** revisión de correlaciones,
  rezagos (CCF) y estructura multivariada (PCA/t-SNE) para decidir qué
  relaciones se profundizan en el modelado GLM.
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