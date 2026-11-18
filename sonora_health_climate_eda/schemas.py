"""Pydantic schemas for the datasets documented in ``references``."""

from datetime import date, datetime
from math import isnan
from numbers import Real
from typing import Any, Literal

import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class DatasetSchema(BaseModel):
    """Common configuration for schemas loaded from tabular or GIS data."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_missing_values(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, Real) and isnan(value):
            return None
        return value


class SequiaSonoraSchema(DatasetSchema):
    """Schema for the tidy CONAGUA drought dataset for Sonora."""

    model_config = ConfigDict(extra="ignore")

    CVE_CONCATENADA: int | None = Field(default=None, ge=0)
    CVE_ENT: int | None = Field(default=None, ge=1)
    CVE_MUN: int | None = Field(default=None, ge=1)
    fecha: str | None = None
    categoria_sequia: str | None = None
    Anio: int | None = Field(default=None, ge=1900, le=2100)
    severidad_num: int | None = Field(default=None, ge=0, le=5)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_missing_values(cls, value):
        # If it is None, an empty string, or pandas NaN, convert it to None
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        return value

    @field_validator("fecha", "categoria_sequia", mode="before")
    @classmethod
    def convert_text_fields(cls, value):
        if value is None or pd.isna(value):
            return None
        return str(value).strip()

    @field_validator(
        "CVE_CONCATENADA", "CVE_ENT", "CVE_MUN", "Anio", "severidad_num", mode="before"
    )
    @classmethod
    def convert_numeric_fields(cls, value):
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        try:
            return int(float(value))  # float() in case it comes with .0 from pandas
        except (ValueError, TypeError):
            return None


# -------------------------------------------------------------------------
# Esquema para Temperatura Media CONAGUA
# -------------------------------------------------------------------------
class TemperaturaEstacionSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    clave: str | None = None
    edo: str | None = None
    est: str | None = None
    temp_promedio: float | None = Field(default=None, ge=-50.0, le=65.0)
    archivo_origen: str | None = None
    anio: int | None = Field(default=None, ge=1900, le=2100)
    mes: int | None = Field(default=None, ge=1, le=12)
    fecha: date | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_missing_and_sentinels(cls, value, info):
        if value is None or pd.isna(value):
            return None
        if str(value).strip().lower() in ["", "nan", "none", "null"]:
            return None
        # Los valores centinela solo aplican a la temperatura, no a lon/lat
        if info.field_name == "temp_promedio":
            try:
                if float(value) in [-99.9, -999.0, -99.0]:
                    return None
            except (ValueError, TypeError):
                pass
        return value

    @field_validator("clave", "edo", "est", "archivo_origen", mode="before")
    @classmethod
    def convert_text_fields(cls, value):
        if value is None or pd.isna(value):
            return None
        return str(value).strip()

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_date(cls, value):
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.date()
        if isinstance(value, str):
            return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
        return value


class MarginacionAgebSchema(DatasetSchema):
    """Schema for the CONAPO urban marginalization index at AGEB level (IMU 2020)."""

    CVE_AGEB: str | None = Field(default=None, min_length=13, max_length=13)
    ENT: int | None = Field(default=None, ge=1, le=32)
    NOM_ENT: str | None = None
    MUN: str | None = None
    NOM_MUN: str | None = None
    LOC: str | None = None
    NOM_LOC: str | None = None
    AGEB: str | None = None
    POB_TOTAL: int | None = Field(default=None, ge=0)
    P6A14NAE: float | None = Field(default=None, ge=0, le=100)
    SBASC: float | None = Field(default=None, ge=0, le=100)
    PSDSS: float | None = Field(default=None, ge=0, le=100)
    OVSDE: float | None = Field(default=None, ge=0, le=100)
    OVSEE: float | None = Field(default=None, ge=0, le=100)
    OVSAE: float | None = Field(default=None, ge=0, le=100)
    OVPT: float | None = Field(default=None, ge=0, le=100)
    OVSREF: float | None = Field(default=None, ge=0, le=100)
    OVSINT: float | None = Field(default=None, ge=0, le=100)
    OVSCEL: float | None = Field(default=None, ge=0, le=100)
    OVHAC: float | None = Field(default=None, ge=0, le=100)
    IM_2020: float | None = None
    GM_2020: str | None = None
    IMN_2020: float | None = Field(default=None, ge=0, le=1)
    fn_CVE_AGEB: float | None = None
    fn_AGEB: float | None = None

    @field_validator(
        "CVE_AGEB",
        "NOM_ENT",
        "MUN",
        "NOM_MUN",
        "LOC",
        "NOM_LOC",
        "AGEB",
        "GM_2020",
        mode="before",
    )
    @classmethod
    def convert_text_fields(cls, value):
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        return str(value).strip()

    @field_validator("ENT", "POB_TOTAL", mode="before")
    @classmethod
    def convert_int_fields(cls, value):
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    @field_validator(
        "P6A14NAE",
        "SBASC",
        "PSDSS",
        "OVSDE",
        "OVSEE",
        "OVSAE",
        "OVPT",
        "OVSREF",
        "OVSINT",
        "OVSCEL",
        "OVHAC",
        "IM_2020",
        "IMN_2020",
        "fn_CVE_AGEB",
        "fn_AGEB",
        mode="before",
    )
    @classmethod
    def convert_float_fields(cls, value):
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        try:
            return float(str(value).replace(",", "").strip())
        except (ValueError, TypeError):
            return None


class InfeccionesRespiratoriasSonoraSchema(DatasetSchema):
    """Schema for the SUIVE epidemiological respiratory dataset for Sonora."""

    model_config = ConfigDict(extra="ignore")

    clave_municipio: int | None = Field(default=None, ge=1, le=72)
    municipio: str | None = None
    clave_entidad: int | None = Field(default=None, ge=1)
    anio: int | None = Field(default=None, ge=2010, le=2020)
    semana: int | None = Field(default=None, ge=1, le=53)
    genero: str | None = None
    grupo_edad: str | None = None
    clave_enfermedad: str | None = None
    clues: str | None = None
    casos: int | None = Field(default=None, ge=0)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_missing_values(cls, value):
        # Si es None, NaN de pandas o string vacío, retorna None
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        return value

    @field_validator(
        "municipio", "genero", "grupo_edad", "clave_enfermedad", "clues", mode="before"
    )
    @classmethod
    def convert_text_fields(cls, value):
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        # Opcional: estandarizar municipio a mayúsculas si lo deseas
        cleaned = str(value).strip()
        if cls.__name__ == "municipio":
            return cleaned.upper()
        return cleaned

    @field_validator("clave_municipio", "clave_entidad", "anio", "semana", "casos", mode="before")
    @classmethod
    def convert_numeric_fields(cls, value):
        if value is None or pd.isna(value) or str(value).strip() == "":
            return None
        try:
            return int(
                float(value)
            )  # Maneja valores decimales residuales tipo "30.0" desde pandas
        except (ValueError, TypeError):
            return None


# -------------------------------------------------------------------------
# Esquema para Open-Meteo diario (data/raw/openmeteo_hermosillo_daily_1991_2020.csv)
# -------------------------------------------------------------------------
class OpenMeteoDiarioSchema(DatasetSchema):
    """Un día de la serie Open-Meteo de Hermosillo (rangos físicos plausibles)."""

    fecha: date
    tmax_c: float = Field(ge=-10.0, le=55.0)
    tmin_c: float = Field(ge=-15.0, le=40.0)
    humedad_rel_pct: float = Field(ge=0.0, le=100.0)

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_date(cls, value):
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.date()
        return value

    @model_validator(mode="after")
    def tmax_no_menor_que_tmin(self):
        if self.tmax_c < self.tmin_c:
            raise ValueError("tmax_c es menor que tmin_c")
        return self


# -------------------------------------------------------------------------
# Esquema para calidad del aire horaria RUOA-ERNO
# (data/interim/aire/aire_hermosillo_horario.csv, sin limpiar)
# -------------------------------------------------------------------------
BanderaRUOA = Literal["OK", "BDL", "OR", "OS"]


class AireHorarioSchema(DatasetSchema):
    """Una hora de RUOA-ERNO tal como viene (antes de la limpieza de 2.4).

    Los valores pueden ser absurdos cuando la bandera es ``OR`` (fuera de
    rango), así que solo se exige coherencia entre valor y bandera:
    ``OK`` debe traer un valor no negativo y ``OS`` (fuera de servicio) no
    debe traer valor.
    """

    fecha_hora: datetime
    pm25_ugm3: float | None = None
    pm25_bandera: BanderaRUOA
    pm10_ugm3: float | None = None
    pm10_bandera: BanderaRUOA
    o3_ppb: float | None = None
    o3_bandera: BanderaRUOA

    @model_validator(mode="after")
    def valor_coherente_con_bandera(self):
        for pol, valor_col in (("pm25", "pm25_ugm3"), ("pm10", "pm10_ugm3"), ("o3", "o3_ppb")):
            valor = getattr(self, valor_col)
            bandera = getattr(self, f"{pol}_bandera")
            if bandera == "OK" and (valor is None or valor < 0):
                raise ValueError(f"{pol}: bandera OK con valor vacío o negativo ({valor})")
            if bandera == "OS" and valor is not None:
                raise ValueError(
                    f"{pol}: bandera OS (fuera de servicio) pero trae valor ({valor})"
                )
        return self


# -------------------------------------------------------------------------
# Esquema para marginación municipal CONAPO
# (data/interim/marginacion/marginacion_municipal_AAAA.csv)
# -------------------------------------------------------------------------
GradoMarginacion = Literal["Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"]


class MarginacionMunicipalSchema(DatasetSchema):
    """Un municipio de Sonora en el índice de marginación municipal (IMM)."""

    CVE_ENT: int = Field(ge=26, le=26)
    CVE_MUN: int = Field(ge=26001, le=26072)
    NOM_MUN: str
    POB_TOT: int = Field(ge=0)
    ANALF: float = Field(ge=0, le=100)
    SBASC: float = Field(ge=0, le=100)
    OVSDE: float = Field(ge=0, le=100)
    OVSEE: float = Field(ge=0, le=100)
    OVSAE: float = Field(ge=0, le=100)
    OVPT: float = Field(ge=0, le=100)
    VHAC: float = Field(ge=0, le=100)
    PO2SM: float = Field(ge=0, le=100)
    IM: float
    GM: GradoMarginacion
    IMN: float = Field(ge=0, le=1)


# -------------------------------------------------------------------------
# Esquema para la capa de colonias CONAPO 2020 (atributos, sin geometría)
# (data/interim/marginacion/colonias_marginacion_hermosillo.gpkg)
# -------------------------------------------------------------------------
class ColoniaMarginacionSchema(DatasetSchema):
    """Una colonia de Hermosillo de la cartografía de marginación urbana 2020."""

    CVE_COL: str
    CVE_MUN: Literal["26030"]
    COLONIA: str | None = None
    POBTOT: int = Field(ge=0)
    IMN_2020: float = Field(ge=0, le=1)
    GM_2020: GradoMarginacion

    @field_validator("CVE_COL", "CVE_MUN", mode="before")
    @classmethod
    def to_text(cls, value):
        return None if value is None else str(value).strip()


# -------------------------------------------------------------------------
# Esquema para el extracto del catálogo CLUES
# (data/external/clues/clues_hermosillo_ira.csv)
# -------------------------------------------------------------------------
class CluesHermosilloSchema(DatasetSchema):
    """Una unidad de salud de Hermosillo del catálogo CLUES (DGIS).

    Las coordenadas deben caer en Sonora; una unidad con coordenadas vacías
    o fuera del estado no se puede ubicar en una colonia (notebook 3.6).
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    CLUES: str = Field(pattern=r"^[A-Z]{5}\d{6}$")
    clave_municipio: int = Field(alias="CLAVE DEL MUNICIPIO", ge=30, le=30)
    LATITUD: float = Field(ge=26.0, le=33.0)
    LONGITUD: float = Field(ge=-116.0, le=-108.0)


def validate_dataframe(
    df: pd.DataFrame, schema: type[BaseModel]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida cada fila de ``df`` con ``schema``.

    Devuelve ``(validas, errores)``: las filas que pasaron, ya normalizadas
    por el esquema, y una tabla con una fila por fila rechazada (índice
    original, campo y mensaje del primer error).
    """
    validas, errores = [], []
    for idx, record in zip(df.index, df.to_dict("records")):
        try:
            validas.append(schema.model_validate(record).model_dump())
        except ValidationError as e:
            primero = e.errors()[0]
            errores.append(
                {
                    "fila": idx,
                    "campo": ".".join(str(p) for p in primero["loc"]) or "(fila)",
                    "error": primero["msg"],
                    "valor": primero.get("input") if primero["loc"] else None,
                }
            )
    return pd.DataFrame(validas), pd.DataFrame(
        errores, columns=["fila", "campo", "error", "valor"]
    )


__all__ = [
    "AireHorarioSchema",
    "CluesHermosilloSchema",
    "ColoniaMarginacionSchema",
    "DatasetSchema",
    "InfeccionesRespiratoriasSonoraSchema",
    "MarginacionAgebSchema",
    "MarginacionMunicipalSchema",
    "OpenMeteoDiarioSchema",
    "SequiaSonoraSchema",
    "TemperaturaEstacionSchema",
    "validate_dataframe",
]
