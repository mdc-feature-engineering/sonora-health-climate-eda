# Nota de calidad de datos: unidades CLUES de Hermosillo sin coordenadas útiles

## Resumen

De las **103 unidades de salud** de Hermosillo que reportaron casos de IRA
(2010–2020) y aparecen en el catálogo CLUES
(`data/external/clues/clues_hermosillo_ira.csv`), **17 no traen
coordenadas útiles** y quedan fuera de cualquier análisis espacial
(notebook `3.6-analisis-marginacion-urbana.ipynb`):

- **13 unidades** traen coordenadas en la **Ciudad de México**
  (latitud ≈ 19.36–19.40, longitud ≈ −99.13 a −99.17), aunque el catálogo
  las registra en Hermosillo.
- **4 unidades** no tienen latitud ni longitud capturadas.

Las 17 son **consultorios de farmacias privadas** (`CLAVE DE LA
INSTITUCION = SMP`, "Servicios Médicos Privados"): 16 Farmacias Similares
y 1 Farmacias Benavides. El esquema `CluesHermosilloSchema`
(`sonora_health_climate_eda/schemas.py`) las rechaza porque exige que la
coordenada caiga en Sonora (latitud 26–33, longitud −116 a −108).

> **El error está en el catálogo maestro DGIS, no en el pipeline del
> proyecto.** Las mismas coordenadas erróneas/ausentes aparecen en el XLSX
> oficial `data/raw/clues/ESTABLECIMIENTO_SALUD_202610.xlsx`.

## Las 17 unidades

| CLUES | Unidad | Vialidad | Colonia | CP | Error | Última modif. | Casos IRA 2010–2020 |
|---|---|---|---|---|---|---|---:|
| SRSMP000770 | Farmacias Benavides | Seguro Social | Modelo | 83190 | sin coordenadas | 29/03/2016 | 1,312 |
| SRSMP001154 | Farmacias Similares | Monterrey Poniente | Centro | 83000 | coords en CDMX | 07/07/2016 | 14,487 |
| SRSMP001163 | Farmacias Similares | Monterrey | Hermosillo Centro | 83000 | coords en CDMX | 07/07/2016 | 1 |
| SRSMP001172 | Farmacias Similares | Guerrero | Hermosillo Centro | 83000 | coords en CDMX | 07/07/2016 | 237 |
| SRSMP001181 | Farmacias Similares | Plutarco Elías Calles | Hermosillo Centro | 83000 | coords en CDMX | 07/07/2016 | 989 |
| SRSMP001190 | Farmacias Similares | Periférico Oriente | Lomas Pitic | 83010 | coords en CDMX | 07/07/2016 | 5,404 |
| SRSMP001214 | Farmacias Similares | Solidaridad | Los Viñedos I | 83120 | sin coordenadas | 07/07/2016 | 44 |
| SRSMP001223 | Farmacias Similares | Leocadio Salcedo | Choyal | 83130 | coords en CDMX | 07/07/2016 | 1,539 |
| SRSMP001241 | Farmacias Similares | José María Mendoza | Balderrama | 83180 | coords en CDMX | 07/07/2016 | 7,847 |
| SRSMP001250 | Farmacias Similares | Juárez | Modelo | 83190 | coords en CDMX | 07/07/2016 | 1,669 |
| SRSMP001265 | Farmacias Similares | Reforma | Fracc. Bernard | 83260 | coords en CDMX | 07/07/2016 | 180 |
| SRSMP001274 | Farmacias Similares | Solidaridad | Villa Hermosa | 83280 | sin coordenadas | 07/07/2016 | 350 |
| SRSMP001283 | Farmacias Similares | Solidaridad | Las Villas | 83289 | sin coordenadas | 07/07/2016 | 213 |
| SRSMP001292 | Farmacias Similares | Mario Yeomans | Altares II | 83296 | coords en CDMX | 07/07/2016 | 118 |
| SRSMP001301 | Farmacias Similares | Berrendo | Renacimiento | 83296 | coords en CDMX | 07/07/2016 | 668 |
| SRSMP001310 | Farmacias Similares | I. Zaragoza | Miguel Alemán Centro | 83344 | coords en CDMX | 07/07/2016 | 480 |
| SRSMP001325 | Farmacias Similares | De Bahía de Kino | Miguel Alemán | 99999 | coords en CDMX | 07/07/2016 | 98 |

## ¿Por qué están mal registradas?

Las 16 Farmacias Similares comparten el mismo evento de actualización en
el catálogo: `ULTIMO MOVIMIENTO = MODIFICACION` del **07/07/2016** con la
observación *"ACTUALIZACION LOCALIDAD Y JURISDICCION"*. La Farmacias
Benavides fue modificada el 29/03/2016 (*"ACTUALIZACION DE DATOS"*) y
simplemente nunca tuvo coordenadas.

Los campos de domicilio de las 17 unidades (vialidad, colonia, código
postal 83xxx) **sí describen direcciones correctas en Hermosillo**; solo
las coordenadas están mal. Las 13 con coordenadas apuntan a un cluster en
el centro de CDMX, consistente con que la actualización masiva geocodificó
el **domicilio fiscal/corporativo de la cadena** (Farmacias Similares
tiene su matriz en CDMX) — o resolvió nombres de calle genéricos
("Monterrey", "Guerrero", "Juárez", "Reforma") contra la localidad
equivocada — en lugar de capturar la coordenada de cada sucursal.

**Es un problema sistémico de la cadena en todo el catálogo**, no solo de
Hermosillo. De las 4,292 unidades "Farmacias Similares" en
`ESTABLECIMIENTO_SALUD_202610.xlsx`:

- **1,238 (~29 %) no tienen coordenadas**.
- **275** están registradas fuera de CDMX pero traen coordenadas de CDMX.

En Hermosillo hay 134 unidades privadas (`SRSMP*`) en el catálogo: 111 con
coordenadas válidas en Sonora, 15 con coordenadas en CDMX, 7 sin
coordenadas y 1 con (0, 0). De esas 23 con problema, 17 reportaron IRA y
son las que aparecen en el extracto.

## Estatus

Las 17 unidades figuran **`EN OPERACION`** en el catálogo. No son clínicas
fantasma: operan y reportan casos reales — acumulan **35,636 casos de IRA
(1.6 % del total de Hermosillo)**, concentrados sobre todo en
SRSMP001154 (14,487), SRSMP001241 (7,847) y SRSMP001190 (5,404).

## Versionado del catálogo

La versión en uso (`202610`, octubre 2026) es **la más reciente publicada**
al 24-nov-2026 (`ESTABLECIMIENTO_SALUD_202611.xlsx` aún no existe en el
repositorio de catálogos DGIS). Cuando salga la siguiente:

```bash
# 1) actualizar la constante en sonora_health_climate_eda/config.py
CLUES_CATALOG_VERSION = "202611"
# 2) re-descargar y regenerar el extracto
python -m sonora_health_climate_eda.dataset download-clues-data --overwrite
```

Ojo: una versión nueva no garantiza que las coordenadas se corrijan — el
problema viene de cómo la cadena registró sus unidades en 2016 y persiste
en el catálogo actual.

## Opciones de corrección

Los domicilios declarados (vialidad + colonia + CP) son suficientes para
ubicar las sucursales — **excepto que ninguna trae número exterior**
(todas `"SIN NÚMERO"`), así que la precisión máxima es calle + colonia.
Alternativas, de mayor a menor precisión:

1. **Geocodificar el domicilio declarado** de cada sucursal (o buscar la
   sucursal por nombre en OSM/DENUE/Google Maps).
2. **Asignar el centroide de su colonia** (el análisis de 3.6 ya trabaja a
   ese nivel). — **aplicada**: las 15 unidades urbanas se corrigieron con
   esta opción (13 por colonia + 2 con coordenada exacta) y ya entran al
   spatial join de 3.6.
3. **Mantener la exclusión documentada**: los ~35.6 mil casos (1.6 %)
   quedan fuera del mapa de carga por colonia, aunque sí entran en el
   total municipal de Hermosillo.

### Resolución parcial por colonia declarada (opción 2)

`data/external/clues/clues_17_geocodificacion.csv` cruza el
`ASENTAMIENTO` + `CODIGO POSTAL` declarados contra las colonias de CONAPO
(`data/interim/marginacion/colonias_marginacion_hermosillo.gpkg`). Para
las resueltas, `LAT`/`LON` traen el `representative_point` de la colonia
(un punto garantizado dentro del polígono, apto para el `sjoin` de 3.6).

**El CSV no se versiona** (`data/` está en `.gitignore`): es un
complemento manual. Si falta, la libreta 3.6 corre igual sin las
correcciones (con un aviso y menor cobertura); esta nota documenta cómo
regenerarlo.

| ESTATUS | # | Significado |
|---|---|---|
| `auto` | 13 | Nombre y CP coinciden con la colonia CONAPO → usar LAT/LON del CSV (punto representativo de la colonia) |
| `manual` | 2 | Coordenada exacta de la sucursal, verificada a mano en mapa (SRSMP001214 en Viñedos; SRSMP001265 en Centenario — "Fracc. Bernard" declarado se refiere a la calle Casimiro Bernard, no a la colonia San Bernardino) |
| `rural` | 2 | No están en la ciudad: son sucursales de los **poblados costeros** del municipio — SRSMP001310 en Miguel Alemán (La Doce, ~28.84, −111.49) y SRSMP001325 en Bahía de Kino (28.828, −111.943). La cartografía de colonias de CONAPO no las cubre — **quedan correctamente fuera del mapa de colonias** y sus casos no pertenecen a ninguna colonia de la ciudad |

Las correcciones ya están aplicadas: la libreta
`3.6-analisis-marginacion-urbana.ipynb` (celda de carga de unidades)
sobreescribe `LATITUD`/`LONGITUD` del extracto con `LAT`/`LON` de este
CSV al leerlo (no se editó el catálogo raw). Con las 13 `auto` + las 2
`manual` se recuperaron ~35.1 mil de los 35.6 mil casos (98 %): la
cobertura pasó de 76 a 91 unidades dentro de una colonia y de 58 a 63
colonias con observatorio (94 % de los casos IRA de Hermosillo). Los
~578 casos restantes (las 2 `rural`) pertenecen a los poblados Miguel
Alemán y Bahía de Kino, fuera del área urbana — correctamente excluidos
del análisis intra-urbano aunque sí cuentan en el total municipal.
