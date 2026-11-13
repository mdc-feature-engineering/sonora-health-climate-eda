"""Pydantic schemas for the datasets documented in ``references``."""

from datetime import date, datetime
from math import isnan
from numbers import Real
from typing import Any

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


__all__ = [
    "DatasetSchema",
    "MarginacionAgebSchema",
    "SequiaSonoraSchema",
    "TemperaturaEstacionSchema",
]
