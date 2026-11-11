# Reporte Final — Análisis Exploratorio de Datos

> **Template del reporte final (rúbrica del proyecto).**
> Llenar cada sección con los hallazgos reales una vez completado el EDA.
> Extensión máxima: **3 páginas** (más portada si aplica). Guardar como
> `reports/reporte_final.md` al entregar.

---

## 1. Nombre del proyecto

**Análisis Exploratorio y Modelado Espacio-Temporal de la Vulnerabilidad
Socioeconómica y Climática ante Enfermedades Respiratorias en Hermosillo,
Sonora**

---

## 2. Equipo e integrantes

**Equipo:** _[Nombre del equipo — opcional]_

| Integrante | Rol | Correo | LinkedIn / contacto |
|------------|-----|--------|---------------------|
| _Nombre Apellido_ | _Ej. análisis de datos_ | _correo@universidad.edu_ | _linkedin.com/in/..._ |
| _Nombre Apellido_ | _Ej. visualización_ | _correo@universidad.edu_ | _linkedin.com/in/..._ |
| _Nombre Apellido_ | _Ej. modelado_ | _correo@universidad.edu_ | _linkedin.com/in/..._ |

---

## 3. Resumen de hallazgos

> _1–2 párrafos con los hallazgos más importantes, escritos de forma directa.
> Redactar al final, cuando el EDA esté completo. Debe responder: ¿qué
> relación se encontró entre la exposición ambiental (calor, sequía,
> contaminación) y la morbilidad respiratoria?, y ¿la marginación modula esa
> relación?_**

_Párrafo 1 — hallazgo principal._

_Párrafo 2 — hallazgos secundarios / implicaciones._

---

## 4. Hallazgo más importante (figura representativa)

![Descripción de la figura](figures/NOMBRE_DE_LA_FIGURA.png)

_Figura X — _[Descripción: qué muestra, ejes, unidades, fuente de datos]._

---

## 5. Detalle de los hallazgos

### 5.1 Datos y cobertura

- _[Capas de datos usadas, periodo temporal y cobertura espacial analizados.
  Mencionar limitaciones: granularidad temporal de salud, estaciones de
  monitoreo disponibles, etc.]_

### 5.2 Datos faltantes y calidad

- _[Principales huecos encontrados (variables, periodos, estaciones) y
  estrategia de tratamiento aplicada. Referir a `2.1-datos-faltantes.ipynb`.]_

### 5.3 Anomalías (outliers)

- _[Resumen de outliers detectados con las técnicas aplicadas (IQR/Z-score,
  Isolation Forest, LOF), cuáles se interpretaron como eventos reales
  (olas de calor, picos de contaminación, brotes) y cuáles como errores.
  Referir a `2.2-outliers.ipynb`.]_

### 5.4 Relaciones entre variables

- _[Principales relaciones observadas en las visualizaciones: temperatura–
  morbilidad, PM2.5/PM10–morbilidad, marginación–exposición. Referir a
  `2.3-relaciones-visualizacion.ipynb`.]_

### 5.5 Correlación

- _[Correlaciones más fuertes (Pearson/Spearman) con la variable de
  respuesta y significancia. Referir a `2.4-correlacion.ipynb`.]_

### 5.6 Estructura multivariada (PCA / t-SNE)

- _[Clusters o gradientes encontrados en el espacio reducido: ¿se agrupan
  AGEBs por marginación, estaciones del año o intensidad de exposición?
  Varianza explicada por componentes PCA. Referir a
  `2.5-reduccion-dimensionalidad.ipynb`.]_

### 5.7 Distribución espacial

- _[Patrones espaciales en Hermosillo: marginación × morbilidad × exposición.
  Referir a `2.0-integracion-espacial.ipynb` (mapas por AGEB: plan).]_

### 5.8 Conclusiones y trabajo futuro

- _[Síntesis de hallazgos, respuesta a la pregunta de investigación y
  posibles extensiones (modelos GLM, alertas, producto de datos).]_

---

## 6. Bibliografía

> _Formato sugerido: APA 7.ª edición. Incluir las fuentes de datos
> (CONAPO, INEGI, SMN/CONAGUA, SINAICA, SINAVE/SSA, datos abiertos Sonora)
> y la literatura metodológica citada en el análisis._

- Autor, A. A. (Año). *Título del trabajo*. Revista/Editorial. DOI/URL
- CONAPO. (2020). *Índice de Marginación Urbana 2020*. Recuperado de ...
- INEGI. (2020). *Cartografía Geoestadística — AGEB*. Recuperado de ...
- SMN/CONAGUA. (s.f.). *Monitor de Sequía en México*. Recuperado de ...
- _[Completar con las fuentes efectivamente usadas]_ 

---

## 7. Repositorio y reproducibilidad

- **Repositorio:** _[URL del GitHub del proyecto]_
- **Libretas:** `notebooks/00_auto_eda/` (auto-EDA), `01_ingesta/` (ETL),
  `02_eda/` (integración y análisis).
- **Reporte automático:** `reports/auto_eda_report.html`.
- **Datos:** `data/raw/` (crudos), `data/interim/` (intermedios),
  `data/processed/` (panel integrado).

---

<!--
NOTAS PARA EL EQUIPO (borrar antes de entregar):
- El rúbrica pide MÁXIMO 3 páginas: condensar secciones 5.x si es necesario.
- La figura de la sección 4 debe ser el hallazgo MÁS importante (la que mejor
  responda la pregunta de investigación), no necesariamente la más vistosa.
- Verificar que todos los integrantes tengan correo y al menos un contacto
  adicional (LinkedIn, GitHub, etc.).
- Exportar a PDF desde el editor de Markdown (VS Code: "Markdown PDF",
  o pandoc) si el formato de entrega lo requiere.
-->
