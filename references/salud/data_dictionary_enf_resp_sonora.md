# Diccionario de Datos: Enfermedades respiratorias — Sonora (SS/DGIS, SINAIS / formato SUIVE)

## Descripción general

Casos **confirmados** de enfermedades respiratorias. **Autor y fuente
institucional:** Secretaría de Salud, a través de la **Dirección General de
Información en Salud (DGIS)**, sistema **SINAIS** (Sistema Nacional de
Información en Salud); los datos se recibieron en formato **SUIVE**
(Sistema Único de Información para la Vigilancia Epidemiológica) por
conducto de la Secretaría de Salud del Estado de Sonora. Cobertura:
**2010–2020**, granularidad **semanal epidemiológica × municipio × sexo ×
grupo de edad × unidad de salud (CLUES)**.

> **Fuente: SS/DGIS, SINAIS (SUIVE), 2010–2020.**

Archivo fuente: `data/raw/salud/enf_resp_sonora_2010_2020.csv`
(~1.7 M filas, 72 municipios de Sonora).

Archivo complementario: `data/raw/salud/enf_resp_hmo_2010_2020.csv`
(~320 K filas, desagregado por CLUES, sin columnas de municipio). Es el
recorte de Hermosillo (`clave_municipio = 30`) del archivo de Sonora
(confirmado por quien compartió los datos; los totales coinciden:
2,206,617 casos). El panel usa el archivo de Sonora.

## Variables

| Columna | Tipo | Descripción |
|---|---|---|
| `clave_municipio` | int | Clave municipal del Estado de Sonora (1–72). **Hermosillo = 30**, equivalente a INEGI `26030`. |
| `municipio` | str | Nombre del municipio en mayúsculas (ej. `HERMOSILLO`). |
| `clave_entidad` | int | Clave de entidad federativa INEGI (`26` = Sonora). |
| `anio` | int | Año de la semana epidemiológica (2010–2020). |
| `semana` | int | Semana epidemiológica (SE) del año, 1–53. |
| `genero` | str | `Masculino` / `Femenino`. |
| `grupo_edad` | str | Grupo quinquenal de edad (ej. `De 00 años`, `De 05 a 09 años`). |
| `clave_enfermedad` | str | Grupo de diagnóstico **CIE-10** del formato SUIVE (ver sección siguiente). En este archivo solo aparece `J00-J06, J20, J21 EXCEPTO J02.0 Y J03.0` = **Infecciones respiratorias agudas (IRA) VIRUS**. Equivale al `cve_diagno = 16` de `config.RESPIRATORY_DIAGNOSIS_IDS`. |
| `clues` | str | Clave Única de Establecimientos de Salud (unidad notificante). |
| `casos` | int | **Casos confirmados** de IRA en el periodo/unidad. |

## `clave_enfermedad`: códigos CIE-10

La CIE-10 (Clasificación Internacional de Enfermedades, 10ª revisión, OMS)
es el estándar con el que la SSA codifica los diagnósticos médicos. En el
formato SUIVE cada enfermedad notificable se agrupa bajo un rango o
conjunto de códigos CIE-10.

Único grupo presente en estos archivos:

```
J00-J06, J20, J21 EXCEPTO J02.0 Y J03.0
```

| Código CIE-10 | Diagnóstico |
|---|---|
| `J00`–`J06` | Infecciones de las vías aéreas superiores: resfriado común, faringitis, laringitis, traqueítis |
| `J20` | Bronquitis aguda |
| `J21` | Bronquiolitis aguda |
| `J02.0` | Laringitis obstructiva aguda — **excluida** del grupo |
| `J03.0` | Amigdalitis aguda estreptocócica — **excluida** del grupo |

Es decir, el dataset contiene únicamente **infecciones respiratorias
agudas (IRA)**. Otros diagnósticos respiratorios del protocolo
(`config.RESPIRATORY_DIAGNOSIS_IDS`: asma `J45`, EPOC `J44`,
tuberculosis `A15`–`A19`, etc.) **no están presentes** en los archivos
recibidos; si se requieren, hay que solicitar a Salud Sonora los
desagregados de las demás claves del formato SUIVE.

## Notas

> **Advertencias sobre el registro de casos.**
> - Retraso en la captura (Reporting lag): El día que aparece registrado el dato no siempre es el día real en que la persona fue a consulta; a veces los reportes se actualizan días o semanas después.
> - El "efecto vacaciones": Cuidado con las caídas repentinas de casos en periodos vacacionales o fines de semana largos. Muchas veces baja la asistencia a los consultorios, pero eso no significa necesariamente que la gente esté más sana, sino que acuden menos a revisarse.
> - Sesgo por clínicas privadas: Gran parte de la atención ocurre en consultorios particulares, cuyas dinámicas y tiempos de reporte son distintos a los del sistema público.
> - El factor COVID: Hay que tener presente que las olas o picos de la pandemia alteraron fuertemente la forma en que la gente buscaba atención médica y cómo se saturaban (o evitaban) las clínicas, lo que puede distorsionar la tendencia general.

### Confirmado con quien compartió los datos

- `enf_resp_hmo_2010_2020.csv` es el recorte de Hermosillo del archivo de
  Sonora.
- El municipio es el de la **unidad médica**, no la residencia del
  paciente.

### Número de casos de Hermosillo (lo que usa el análisis)

El análisis usa el **número total de casos de IRA de Hermosillo** por
semana o por mes: se suman `casos` sobre `genero`, `grupo_edad` y
`clues`. Notas que afectan ese total:

- **Semanas → meses:** semanas epidemiológicas de domingo a sábado; SE1
  es la que contiene el 4 de enero (inferido: los datos traen SE53 en 2014
  y 2020 y solo 52 en 2015). Cada semana se asigna al mes en que inicia,
  así que un mes suma 4 o 5 semanas (`n_semanas`): comparar meses con
  `casos_ira_por_semana`.
- **Total anual estable:** ~190–230 mil casos por año en 2010–2019.
  **2020 tiene ~117 mil** (≈ la mitad, efecto COVID; `anio_atipico`).
- **Más unidades reportando desde 2017** (de ~45 a ~95, casi todas
  consultorios de farmacia), pero el total anual no sube: los casos se
  redistribuyen entre unidades. No afecta el total de Hermosillo.
- **Semanas sin reporte:** no hay filas con `casos = 0`; si una unidad no
  aparece, se cuenta como 0. Las unidades grandes casi no faltan (11 de
  313 semanas en 2015–2020 con alguna de las 10 mayores ausente), por lo
  que el efecto en el total es menor.
- **Casos de fuera:** al contarse por unidad médica, el total incluye
  pacientes de otros municipios atendidos en Hermosillo (p. ej. Hospital
  Infantil del Estado). Limitación a mencionar en el reporte.
- **Instituciones:** incluye Secretaría de Salud, IMSS, ISSSTESON,
  IMSS-Bienestar y consultorios privados.
- Solo hay un grupo de enfermedad respiratoria (IRA). Asma, EPOC,
  neumonías y tuberculosis **no** están en estos archivos.
- **Cruce CLUES verificado (2026-11):** las 103 unidades únicas que
  reportaron IRA en Hermosillo (2010–2020) se encontraron en el catálogo
  oficial DGIS/SSA (`ESTABLECIMIENTO_SALUD_202610.xlsx`). El extracto
  `data/external/clues/clues_hermosillo_ira.csv` lo genera
  `python -m sonora_health_climate_eda.dataset download-clues-data`
  (con domicilio, tipo de establecimiento, estatus y coordenadas
  LATITUD/LONGITUD — 90 consulta externa + 13 hospitalización). El
  catálogo permite georreferenciar las unidades a nivel colonia/AGEB en
  trabajo futuro.
  **Fuente del extracto CLUES: SS/DGIS, catálogo ESTABLECIMIENTO_SALUD,
  actualización 2026-10.**
