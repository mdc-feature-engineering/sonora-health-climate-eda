# Fuentes de datos primarias

Descripción de cada fuente, su enlace y la fecha en que se descargó el
archivo que usa el proyecto (fecha de descarga de los archivos en
`data/raw/`, que no se versionan en Git).

| Capa | Fuente y descripción | Enlace | Fecha de descarga | Cómo se obtiene |
|------|----------------------|--------|-------------------|-----------------|
| Índice de marginación | CONAPO / INEGI — índice de marginación municipal 2015 y 2020 (Excel) | https://coespo.sonora.gob.mx/ (portal COESPO Sonora) | 13-nov-2026 | Notebook `01_ingesta/1.3` |
| Marginación por colonia | STCONAPO — cartografía nacional de marginación urbana por colonia 2020 (SHP, ~45 MB) | https://repodatos.atdt.gob.mx/CONAPO/indices_marginacion/colonias_imc2020_shp.zip | 16-nov-2026 | **Descarga con navegador** (el servidor bloquea clientes automáticos); ver notebook `01_ingesta/1.3` |
| Temperatura (SMN) | CONAGUA/SMN — resúmenes mensuales de temperatura media, máxima y mínima por estación | https://smn.conagua.gob.mx/tools/RESOURCES/com_archivo_datos_resumenes/ | 15-nov-2026 | `download-temperature-data` y `download-temperature-extremes-data` |
| Temperatura diaria | Open-Meteo Archive API — Tmax, Tmin y humedad relativa diarias de Hermosillo, 1991–2020 | https://archive-api.open-meteo.com/v1/archive | 13-nov-2026 | `download-openmeteo-data` |
| Índice de sequía | CONAGUA/SMN — Monitor de Sequía en México, quincenal por municipio | https://smn.conagua.gob.mx/tools/RESOURCES/Monitor%20de%20Sequia%20en%20Mexico/MunicipiosSequia.xlsx | 15-nov-2026 | `download-drought-data` |
| Calidad del aire | RUOA-UNAM, observatorio ERNO Hermosillo — PM2.5, PM10, O3 horarios, un CSV por mes. Ojo: los CSV crudos también traen SO2, NO2, NO y CO, pero con mala cobertura (NOx muere en 2017, CO y PM2.5 en 2019); la estación de Hermosillo en SINAICA es el mismo observatorio ERNO, no una fuente independiente | https://ruoa.unam.mx/caire/erno/hora/ | 14-nov-2026 | `download-air-quality-data` |
| Catálogo CLUES | SS/DGIS — catálogo maestro de establecimientos de salud (XLSX nacional, ~26 MB). Ojo: 17 de 103 unidades de Hermosillo traen coordenadas erróneas (en CDMX) o ausentes en el catálogo fuente — ver `salud/nota_calidad_clues_coordenadas.md` | https://gobi.salud.gob.mx/gobi/catalogos/catalogosmaestros/ESTABLECIMIENTO_SALUD_202610.xlsx | 16-nov-2026 | `download-clues-data` |
| Enfermedades respiratorias | SS/DGIS, SINAIS (formato SUIVE) — casos confirmados de IRA, Sonora 2010–2020 | **Archivo manual** (no se descarga): pedir al equipo | Recibido 10-nov-2026 | `data/raw/salud/enf_resp_sonora_2010_2020.csv` |

Los diccionarios de cada conjunto están en este mismo directorio
(`climate/`, `marginacion/`, `aire/`, `salud/`).
