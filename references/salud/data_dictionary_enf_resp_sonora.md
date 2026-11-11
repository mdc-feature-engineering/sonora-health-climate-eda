# Diccionario de Datos: Enfermedades respiratorias — Sonora (SUIVE/Salud Sonora)

## Descripción general

Casos **confirmados** de enfermedades respiratorias reportados por la
Secretaría de Salud del Estado de Sonora (formato SUAVE / Sistema Único de
Información para la Vigilancia Epidemiológica, SUIVE). Cobertura:
**2010–2020**, granularidad **semanal epidemiológica × municipio × sexo ×
grupo de edad × unidad de salud (CLUES)**.

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
| `clave_enfermedad` | str | Grupo de diagnóstico **CIE-10** del formato SUIVE (ver sección siguiente). En este archivo solo aparece `J00-J06, J20, J21 EXCEPTO J02.0 Y J03.0` = **Infecciones respiratorias agudas (IRA)**. Equivale al `cve_diagno = 16` de `config.RESPIRATORY_DIAGNOSIS_IDS`. |
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

> ⚠️ **Pendiente de validación contra fuente oficial.** Este diccionario se
> construyó a partir de los datos recibidos (sin diccionario propio) y de la
> estructura conocida del formato SUIVE. Los siguientes puntos son
> **inferidos** y deben confirmarse con quien compartió los archivos o con
> la Secretaría de Salud de Sonora:
>
> - La consulta/criterio exacto que generó los CSV.

**Supuesto del proyecto:** `casos` se interpreta como **casos
confirmados** de IRA (inferido; no confirmado por la fuente).

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
  oficial DGIS/SSA (`ESTABLECIMIENTO_SALUD_202610.xlsx`). Extracto
  guardado en `data/external/clues/clues_hermosillo_ira.csv` con
  domicilio, tipo de establecimiento, estatus y coordenadas
  (LATITUD/LONGITUD) — 90 consulta externa + 13 hospitalización. El
  catálogo permite georreferenciar las unidades a nivel colonia/AGEB en
  trabajo futuro.
