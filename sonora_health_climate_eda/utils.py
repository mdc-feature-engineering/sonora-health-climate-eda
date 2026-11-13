from loguru import logger
import pandas as pd
import typer

from sonora_health_climate_eda.config import INTERIM_DATA_DIR, REFERENCES_DIR

app = typer.Typer(help="Comandos para generar los diccionarios de datos del proyecto.")

REF_DIR = REFERENCES_DIR


def make_sequia_conagua_data_dictionary():
    REF_DIR.mkdir(parents=True, exist_ok=True)
    output_md = REF_DIR / "climate" / "data_dictionary_conagua_sequia.md"
    output_md.parent.mkdir(parents=True, exist_ok=True)

    sample_files = list(INTERIM_DATA_DIR.glob("**/sonora_sequia_*.csv"))

    descriptions = {
        "Cve_Entidad": "Clave oficial de la entidad federativa.",
        "Entidad": "Nombre oficial de la entidad federativa.",
        "Cve_Municipio": "Clave oficial del municipio (INEGI).",
        "Municipio": "Nombre oficial del municipio.",
        "CVE_CONCATENADA": ("Clave concatenada única del municipio (Entidad + Municipio)."),
        "CVE_ENT": "Clave de la entidad federativa en formato estandarizado.",
        "CVE_MUN": "Clave del municipio en formato estandarizado.",
        "NOMBRE_MUN": "Nombre oficial del municipio en mayúsculas.",
        "ORG_CUENCA": "Organismo de Cuenca donde se localiza el municipio.",
        "CLV_OC": "Clave de Organismo de Cuenca.",
        "CON_CUENCA": "Consejo de Cuenca donde se localiza el municipio.",
        "CVE_CONC": "Clave de Consejo de Cuenca.",
        "fecha": "Fecha correspondiente a la quincena de evaluación del monitor.",
        "categoria_sequia": ("Clasificación oficial de sequía (Sin Sequía, D0 a D4)."),
        "Anio": "Año extraído de la fecha de evaluación.",
        "severidad_num": ("Escala numérica de severidad asignada (0 = Sin Sequía hasta 5 = D4)."),
    }

    if sample_files:
        print(f"-> Leyendo estructura del archivo modelo: {sample_files[0].name}")
        df_sample = pd.read_csv(sample_files[0])
        column_dtypes = {col: str(df_sample[col].dtype) for col in df_sample.columns}
    else:
        print(
            "[AVISO] No se encontraron archivos procesados. Usando estructura"
            " estándar predefinida..."
        )
        default_columns = [
            "Cve_Entidad",
            "Entidad",
            "Cve_Municipio",
            "Municipio",
            "CVE_CONCATENADA",
            "CVE_ENT",
            "CVE_MUN",
            "NOMBRE_MUN",
            "ORG_CUENCA",
            "CLV_OC",
            "CON_CUENCA",
            "CVE_CONC",
            "fecha",
            "categoria_sequia",
            "Anio",
            "severidad_num",
        ]
        column_dtypes = {
            col: ("int64" if "Cve" in col or col == "Anio" or col == "severidad_num" else "object")
            for col in default_columns
        }

    lines = [
        "# Diccionario de Datos: Monitor de Sequía CONAGUA - Sonora\n",
        "## Descripción General",
        "Este documento detalla las variables del dataset transformado a formato largo (Tidy Data) para el análisis de sequía por municipio en Sonora, basado en los reportes del Monitor de Sequía en México de CONAGUA.\n",
        "## Clasificación de Sequía (Monitor de Sequía)",
        "| Categoría | Descripción | Escala Numérica (`severidad_num`) |",
        "| :--- | :--- | :---: |",
        "| **Sin Sequía** | Condición normal sin afectación | `0` |",
        "| **D0** | Anormalmente Seco (preparación para sequía) | `1` |",
        "| **D1** | Sequía Moderada | `2` |",
        "| **D2** | Sequía Severa | `3` |",
        "| **D3** | Sequía Extrema | `4` |",
        "| **D4** | Sequía Excepcional | `5` |\n",
        "## Estructura de Variables del Dataset",
        "| Columna | Tipo de Dato | Descripción / Metadato Oficial |",
        "| :--- | :--- | :--- |",
    ]

    for col, dtype in column_dtypes.items():
        desc = descriptions.get(col, "Variable de metadatos o procesamiento.")
        lines.append(f"| `{col}` | `{dtype}` | {desc} |")

    output_md.write_text("\n".join(lines), encoding="utf-8")
    logger.success(f"Diccionario de sequía generado con éxito en: {output_md.resolve()}")


@app.command()
def sequia_dictionary():
    """Genera el diccionario de datos de CONAGUA (Sequía)."""
    make_sequia_conagua_data_dictionary()


@app.command()
def all():
    """Genera todos los diccionarios del proyecto."""
    make_sequia_conagua_data_dictionary()


if __name__ == "__main__":
    app()
