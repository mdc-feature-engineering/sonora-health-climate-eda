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
* Manejo de valores faltantes en series temporales climáticas y de calidad del aire.
* Estandarización de claves geoespaciales (INEGI GEOID) y uniones espaciales (*spatial joins*) entre AGEBs y estaciones de medición.

### Fase B: Análisis Univariado
* **Distribución temporal:** Análisis de estacionalidad y tendencias en series temporales diarias de temperatura, calidad del aire y picos de consultas respiratorias.
* **Distribución espacial:** Mapas coropléticos de Hermosillo cruzando grados de marginación urbana con la incidencia acumulada de morbilidad respiratoria.

### Fase C: Análisis Bivariado y Correlaciones Cruzadas
* **Correlaciones de Pearson/Spearman:** Evaluación de la relación lineal entre días con mala calidad del aire ($PM_{2.5}/PM_{10}$ elevados) y el incremento de consultas respiratorias.
* **Función de Correlación Cruzada (CCF):** Identificación empírica del número óptimo de días de rezago entre la exposición ambiental y la respuesta médica.

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