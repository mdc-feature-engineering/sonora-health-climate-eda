# Índice de notebooks — Sonora Health-Climate EDA

> **TODO CRÍTICO del equipo:** tres de las cinco capas de datos del protocolo
> están **pendientes** y bloquean el análisis integrado. Ver
> `docs/docs/protocolo_eda.md` para el detalle metodológico.

## Estado de las capas de datos

| Capa | Notebook | Estado | Responsable |
|------|----------|--------|-------------|
| 1. Marginación | `01_ingesta/1.3-indice-marginacion.ipynb` (template) + `pendientes/marginacion/` | ⚠️ **TODO CRÍTICO** — descarga implementada; falta geometría AGEB y validación | Compañeros |
| 2. Clima (temp/lluvia) | `01_ingesta/1.0-conagua-temperatura.ipynb`, `1.1-conagua-lluvia.ipynb` | ✅ Implementado | — |
| 3. Sequía | `01_ingesta/1.2-monitor-sequia.ipynb` | ✅ Implementado | — |
| 4. Calidad del aire | `01_ingesta/1.4-calidad-aire.ipynb` | 🔴 **TODO CRÍTICO** — fuente sin confirmar (SINAICA / datos abiertos Sonora) | Compañeros |
| 5. Salud respiratoria | `01_ingesta/1.5-enfermedades-respiratorias.ipynb` | 🔴 **TODO CRÍTICO** — fuente y granularidad sin confirmar (SINAVE / SSA) | Compañeros |

## Orden de ejecución sugerido

### `01_ingesta/` — Fase A (ETL)
| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `1.0-conagua-temperatura.ipynb` | Descarga e ingesta de temperatura media por estación (SMN/CONAGUA) | ✅ |
| `1.1-conagua-lluvia.ipynb` | Descarga e ingesta de precipitación por estación (SMN/CONAGUA) | ✅ |
| `1.2-monitor-sequia.ipynb` | Monitor de Sequía CONAGUA → formato tidy por año | ✅ |
| `1.3-indice-marginacion.ipynb` | Índice de marginación — **template TODO** (trabajo parcial en `pendientes/marginacion/`) | ⚠️ TODO |
| `1.4-calidad-aire.ipynb` | PM2.5, PM10, O3 por estación — **esqueleto** | 🔴 TODO |
| `1.5-enfermedades-respiratorias.ipynb` | IRAs, asma, EPOC, neumonías — **esqueleto** | 🔴 TODO |
| `pendientes/marginacion/1.3-indice-marginacion.ipynb` | Marginación municipal/AGEB — **en desarrollo** | ⚠️ TODO |

### `02_eda/` — Fases B y C
| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `2.0-integracion-espacial.ipynb` | Panel integrado: claves INEGI, spatial joins AGEB↔estaciones | 🔴 Bloqueado por capas pendientes |
| `2.1-univariado.ipynb` | Series temporales, estacionalidad, mapas coropléticos | 🔴 Bloqueado |
| `2.2-bivariado-ccf.ipynb` | Pearson/Spearman + función de correlación cruzada (rezagos) | 🔴 Bloqueado |
| `2.3-espacial-coropletico.ipynb` | Mapas marginación × morbilidad × exposición | 🔴 Bloqueado |

### `03_modelado/` — Fase D
| Notebook | Descripción | Estado |
|----------|-------------|--------|
| `3.0-glm-respiratorio.ipynb` | GLM Poisson/NB con rezagos e interacciones marginación×exposición | 🔴 Bloqueado |

## Cómo retomar una capa pendiente

1. Confirmar la fuente en `sonora_health_climate_eda/config.py`
   (`AIR_QUALITY_SOURCES`, `HEALTH_DATA_SOURCES`, `MARGINACION_AGEB_URL`).
2. Implementar el comando de descarga en `dataset.py` (ver los stubs como
   ejemplo) o documentar la descarga manual en el notebook.
3. Llenar el notebook esqueleto correspondiente en `01_ingesta/`.
4. Generar el diccionario de datos en `references/<capa>/`.
