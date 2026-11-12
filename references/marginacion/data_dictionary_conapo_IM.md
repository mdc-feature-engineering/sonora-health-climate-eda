# Diccionario de Datos: Índice de Marginación Municipal - Hermosillo, Sonora (CONAPO)

## Descripción general

Este diccionario describe las variables del archivo `data/interim/marginacion/marginacion_municipal_hermosillo_2010_2020.csv`, generado en el notebook `1.3-indice-marginacion.ipynb`. Contiene el índice de marginación del municipio de Hermosillo (clave INEGI `26030`) para los años 2010, 2015 y 2020. Cada renglón corresponde a un año censal (3 filas en total) y las variables están organizadas en columnas (19 columnas).

**Fuente:** Índice de marginación por municipio, CONAPO (estimaciones con base en el INEGI), calculado con el método de distancia P2 (DP2). Archivos originales: `IMM_DP2_2010.xlsx`, `IMM_DP2_2015.xlsx` e `IMM_2020.xlsx`, publicados en la página de CONAPO "Índices de marginación 2020".

**Archivos relacionados** (misma carpeta): `marginacion_municipal_{2010,2015,2020}.csv` contienen los 72 municipios de Sonora, uno por año, sin las columnas `AÑO` ni `CVE_MUN_5D`.

**Fuentes de las definiciones:**
1. Diccionario de datos del dataset "Índice de marginación por municipio" del portal de datos abiertos de Sonora (`datos.sonora.gob.mx`, COESPO), que describe las variables de la serie 2020.
2. Diccionario CONAPO "Índice de marginación por entidad federativa 1990-2015", usado para contrastar con la serie histórica.

Las columnas `AÑO` y `CVE_MUN_5D` no pertenecen a las fuentes: se crearon en el notebook.

## Grado de marginación (`GM`)

| Grado | Descripción |
| :--- | :--- |
| **Muy bajo** | Menor nivel de marginación |
| **Bajo** | Nivel de marginación bajo |
| **Medio** | Nivel de marginación intermedio |
| **Alto** | Nivel de marginación alto |
| **Muy alto** | Mayor nivel de marginación |

Los cinco grados se obtienen estratificando el índice; los puntos de corte los define CONAPO y no se reproducen aquí. En Hermosillo el grado observado es **Muy bajo** en los tres años.

## Estructura de variables

| Variable | Tipo de dato | Formato | Unidad de medida | Descripción | Obligatoriedad | Catálogo de referencia | Identificador de valores nulos | Ejemplo de dato |
|---|---|---|---|---|---|---|---|---|
| `AÑO` | Numérico | `int` | `AAAA` | Año del cálculo del índice. Columna agregada en el notebook (el archivo de 2020 no la trae). | No especificado | — | Sin nulos | `2010` |
| `CVE_MUN_5D` | Numérico | `int` (`NNNNN`) | — | Clave INEGI de 5 dígitos del municipio (entidad + municipio). Columna auxiliar creada en el notebook para filtrar; su valor coincide con `CVE_MUN`. | No especificado | Catálogo INEGI | Sin nulos | `26030` |
| `CVE_ENT` | Numérico | `int` (`NN`) | 1 a 32 (clasificación INEGI) | Clave de la entidad federativa. | No especificado | Catálogo INEGI | Sin nulos | `26` |
| `NOM_ENT` | Texto | Texto | — | Nombre de la entidad. | No especificado | Catálogo INEGI | Sin nulos | `Sonora` |
| `CVE_MUN` | Numérico | `int` (`NNNNN`) | Clasificación INEGI | Clave del municipio. En este archivo es la clave de 5 dígitos (entidad + municipio). El diccionario de Sonora indica formato `nnn`, pero su propio ejemplo (`26048`) y los datos usan 5 dígitos. | No especificado | Catálogo INEGI | Sin nulos | `26030` |
| `NOM_MUN` | Texto | Texto | — | Nombre del municipio. | No especificado | Catálogo INEGI | Sin nulos | `Hermosillo` |
| `POB_TOT` | Numérico | `int` | personas | Población total. | No especificado | — | Sin nulos | `784342` |
| `ANALF` | Numérico | `float` | porcentaje (%) | Porcentaje de población de 15 años o más analfabeta. | No especificado | — | Sin nulos | `2.105482` |
| `SBASC` | Numérico | `float` | porcentaje (%) | Porcentaje de población de 15 años o más sin educación básica. Sustituye a `SPRIM` (sin primaria completa) de la serie histórica; no son equivalentes. | No especificado | — | Sin nulos | `26.204042` |
| `OVSDE` | Numérico | `float` | porcentaje (%) | Porcentaje de ocupantes en viviendas particulares sin drenaje ni excusado. | No especificado | — | Sin nulos | `0.831793` |
| `OVSEE` | Numérico | `float` | porcentaje (%) | Porcentaje de ocupantes en viviendas particulares sin energía eléctrica. | No especificado | — | Sin nulos | `0.724452` |
| `OVSAE` | Numérico | `float` | porcentaje (%) | Porcentaje de ocupantes en viviendas particulares sin agua entubada. | No especificado | — | Sin nulos | `1.928271` |
| `OVPT` | Numérico | `float` | porcentaje (%) | Porcentaje de ocupantes en viviendas particulares con piso de tierra. | No especificado | — | Sin nulos | `4.715866` |
| `VHAC` | Numérico | `float` | porcentaje (%) | Porcentaje de viviendas particulares con hacinamiento. | No especificado | — | Sin nulos | `31.274788` |
| `PL.5000` | Numérico | `float` | porcentaje (%) | Porcentaje de población en localidades con menos de 5 000 habitantes. En el archivo histórico se llama `PL<5000`. | No especificado | — | Sin nulos | `4.126006` |
| `PO2SM` | Numérico | `float` | porcentaje (%) | Porcentaje de población ocupada con ingresos menores a 2 salarios mínimos (diccionario de Sonora). El diccionario CONAPO 1990-2015 dice "hasta 2 salarios mínimos". Ver notas. | No especificado | — | Sin nulos | `19.240435` |
| `IM` | Numérico | `float` | adimensional (índice) | Índice de marginación (método DP2). En los archivos originales aparece como `IM_2020` (o equivalente por año). El diccionario de Sonora lo clasifica como "Porcentaje" sin unidad definida; aquí se trata como índice adimensional. | No especificado | — | Sin nulos | `37.772798` |
| `GM` | Texto | Categórico | Muy bajo; Bajo; Medio; Alto; Muy alto | Grado de marginación. En el archivo original de 2020 aparece como `GM_2020`. | No especificado | Ver tabla de grados | Sin nulos | `Muy bajo` |
| `IMN` | Numérico | `float` | adimensional (0 a 1) | Índice de marginación normalizado. En el archivo original de 2020 aparece como `IMN_2020`. El diccionario de Sonora lo clasifica como "Porcentaje", pero los valores observados están entre 0 y 1. | No especificado | — | Sin nulos | `0.92227` |

## Variables de la serie 1990-2015 que no se incluyen

Estas variables existen en los archivos de CONAPO con el método anterior (o solo en el archivo de 2020) y no tienen equivalente directo en la serie 2010-2020; se eliminaron al unificar los archivos.

| Variable | Descripción | Motivo de exclusión |
| :--- | :--- | :--- |
| `SPRIM` | Porcentaje de población de 15 años o más sin primaria completa | No equivale a `SBASC` (mide otra carencia) |
| `OVSD` / `OVSDSE` | Ocupantes en viviendas sin drenaje ni servicio sanitario exclusivo | Solo existe en el archivo 1990-2015 |
| `IND0A100` | Índice en escala 0 a 100 | Solo existe en el archivo 1990-2015 |
| `LUGAR_NAC` / `LUGAR_EST` | Lugar que ocupa en el contexto nacional / estatal | Solo existe en el archivo 1990-2015 |
| `POSICION` | Lugar que ocupa en el contexto nacional (archivo de 2020) | Solo existe en 2020; corresponde conceptualmente a `LUGAR_NAC` |
| `VP`, `CVEE_MUN` | Sin definición en los diccionarios consultados | Solo existe en el archivo 1990-2015 |

## Notas de calidad y tipado

- **Comparabilidad.** Los valores de 2010, 2015 y 2020 se calcularon con el mismo método (DP2) y son comparables entre sí. CONAPO señala que las estimaciones DP2 de 2010 y 2015 sirven como referencia para las de 2020 y no reemplazan oficialmente a las publicadas en su momento. **No son comparables con el `IM` del archivo histórico 1990-2015** (método anterior, escala distinta).
- **Cobertura de las definiciones.** El diccionario de Sonora describe las variables del archivo de 2020 (con sufijo `_2020` en `IM`, `GM` e `IMN`). Para 2010 y 2015 se asume que los indicadores con el mismo nombre tienen la misma definición.
- **Dirección y escala del índice (sin confirmar en la documentación).** Los diccionarios consultados no indican en qué sentido crece el índice. Los datos sugieren que en esta serie un valor mayor de `IM` e `IMN` corresponde a **menor** marginación: en Hermosillo ambos suben de 2010 a 2020 mientras el grado sigue en "Muy bajo", y el ejemplo del diccionario (Puerto Peñasco, `IM_2020` = 58.6, grado "Muy bajo") es coherente con ello. En el índice histórico 1990-2015 ocurre lo contrario. Confirmar en la nota técnico-metodológica de CONAPO antes de interpretar tendencias.
- **`SBASC` frente a `SPRIM`.** Miden carencias distintas (sin educación básica frente a sin primaria completa). No deben unirse en una sola serie.
- **Salto en `PO2SM`.** El indicador pasa de 19.9 % (2015) a 47.2 % (2020) mientras los demás indicadores mejoran o se mantienen. La redacción también difiere entre diccionarios ("hasta 2" frente a "menores a 2 salarios mínimos"), y los valores de 2020 de otros municipios de Sonora son igual de altos (por ejemplo, 66.9 % en Aconchi, 75.7 % en Álamos, 81.1 % en Agua Prieta y 82.6 % en Puerto Peñasco). Esto apunta a un posible cambio de definición del indicador y no a un fenómeno propio de Hermosillo, pero **no está confirmado**. No interpretar como tendencia real sin revisar la nota metodológica.
- **Interpolación mensual.** `panel.py` interpola linealmente entre 2015 y 2020 para construir el panel mensual. Esos valores mensuales son estimaciones, no datos publicados por CONAPO.
- **Valores nulos.** No se observaron valores nulos en las 3 filas de Hermosillo. El archivo histórico 1990-2015 usa el guion `-` para indicadores no disponibles; en este archivo no aparece.
- **Columnas redundantes.** `CVE_MUN` y `CVE_MUN_5D` contienen el mismo valor (`26030`). `CVE_MUN_5D` es auxiliar y puede omitirse en análisis.
- **Nombres de columnas.** El notebook quita el sufijo de año de los nombres originales (`IM_2020` → `IM`, `GM_2020` → `GM`, `IMN_2020` → `IMN`) para que los tres años compartan columnas. El indicador de localidades pequeñas aparece como `PL.5000` en esta serie y como `PL<5000` en el archivo histórico.
