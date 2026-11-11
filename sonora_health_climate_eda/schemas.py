"""Pydantic schemas for the datasets documented in ``references``."""

from datetime import date, datetime
from math import isnan
from numbers import Real
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    CVE_CONCATENADA: Optional[int] = Field(default=None, ge=0)
    CVE_ENT: Optional[int] = Field(default=None, ge=1)
    CVE_MUN: Optional[int] = Field(default=None, ge=1)
    fecha: Optional[str] = None
    categoria_sequia: Optional[str] = None
    Anio: Optional[int] = Field(default=None, ge=1900, le=2100)
    severidad_num: Optional[int] = Field(default=None, ge=0, le=5)

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

    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    clave: Optional[str] = None
    edo: Optional[str] = None
    est: Optional[str] = None
    temp_promedio: Optional[float] = Field(default=None, ge=-50.0, le=65.0)
    archivo_origen: Optional[str] = None
    anio: Optional[int] = Field(default=None, ge=1900, le=2100)
    mes: Optional[int] = Field(default=None, ge=1, le=12)
    fecha: Optional[date] = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_missing_and_sentinels(cls, value):
        if value is None or pd.isna(value):
            return None
        if str(value).strip().lower() in ["", "nan", "none", "null"]:
            return None
        try:
            val_num = float(value)
            if val_num in [-99.9, -999.0, -99.0]:
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


# -------------------------------------------------------------------------
# Esquema para Precipitación (Lluvia) CONAGUA
# -------------------------------------------------------------------------
class LluviaEstacionSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    clave: Optional[str] = None
    edo: Optional[str] = None
    estacion: Optional[str] = None
    precipitacion_mm: Optional[float] = Field(default=None, ge=0.0, le=3000.0)
    periodo: Optional[str] = None
    archivo_origen: Optional[str] = None
    anio: Optional[int] = Field(default=None, ge=1900, le=2100)
    mes: Optional[int] = Field(default=None, ge=1, le=12)
    fecha: Optional[date] = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_missing_and_sentinels(cls, value):
        if value is None or pd.isna(value):
            return None
        if str(value).strip().lower() in ["", "nan", "none", "null"]:
            return None
        try:
            val_num = float(value)
            if val_num in [-99.9, -999.0, -99.0]:
                return None
        except (ValueError, TypeError):
            pass
        return value

    @field_validator(
        "clave", "edo", "estacion", "periodo", "archivo_origen", mode="before"
    )
    @classmethod
    def clean_text_fields(cls, value):
        if value is None or pd.isna(value):
            return None
        return str(value).strip()

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_dates(cls, value):
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.date()
        if isinstance(value, str):
            return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
        return value


class MarginacionAgebSchema(DatasetSchema):
    """Schema for the CONAPO urban marginalization index at AGEB level (IMU 2020)."""

    CVE_AGEB: Optional[str] = Field(default=None, min_length=13, max_length=13)
    ENT: Optional[int] = Field(default=None, ge=1, le=32)
    NOM_ENT: Optional[str] = None
    MUN: Optional[str] = None
    NOM_MUN: Optional[str] = None
    LOC: Optional[str] = None
    NOM_LOC: Optional[str] = None
    AGEB: Optional[str] = None
    POB_TOTAL: Optional[int] = Field(default=None, ge=0)
    P6A14NAE: Optional[float] = Field(default=None, ge=0, le=100)
    SBASC: Optional[float] = Field(default=None, ge=0, le=100)
    PSDSS: Optional[float] = Field(default=None, ge=0, le=100)
    OVSDE: Optional[float] = Field(default=None, ge=0, le=100)
    OVSEE: Optional[float] = Field(default=None, ge=0, le=100)
    OVSAE: Optional[float] = Field(default=None, ge=0, le=100)
    OVPT: Optional[float] = Field(default=None, ge=0, le=100)
    OVSREF: Optional[float] = Field(default=None, ge=0, le=100)
    OVSINT: Optional[float] = Field(default=None, ge=0, le=100)
    OVSCEL: Optional[float] = Field(default=None, ge=0, le=100)
    OVHAC: Optional[float] = Field(default=None, ge=0, le=100)
    IM_2020: Optional[float] = None
    GM_2020: Optional[str] = None
    IMN_2020: Optional[float] = Field(default=None, ge=0, le=1)
    fn_CVE_AGEB: Optional[float] = None
    fn_AGEB: Optional[float] = None

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


__all__ = [
    "DatasetSchema",
    "SequiaSonoraSchema",
    "TemperaturaEstacionSchema",
    "LluviaEstacionSchema",
    "MarginacionAgebSchema",
]
