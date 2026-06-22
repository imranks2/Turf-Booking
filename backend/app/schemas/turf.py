from __future__ import annotations

import datetime as _dt
import re
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}


class DayHours(BaseModel):
    open: str
    close: str

    @field_validator("open", "close")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return v

    @field_validator("close")
    @classmethod
    def _close_after_open(cls, v: str, info) -> str:
        open_v = info.data.get("open")
        if open_v and v <= open_v:
            raise ValueError("close must be after open")
        return v


class TurfCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=255)
    address: str = Field(min_length=2, max_length=512)
    city: str = Field(min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    description: str | None = None
    amenities: list[str] = Field(default_factory=list)
    operating_hours: dict[str, DayHours]

    @field_validator("operating_hours")
    @classmethod
    def _valid_days(cls, v: dict[str, DayHours]) -> dict[str, DayHours]:
        invalid = set(v) - _WEEKDAYS
        if invalid:
            raise ValueError(f"Invalid weekday keys: {sorted(invalid)}")
        if not v:
            raise ValueError("operating_hours must define at least one day")
        return v


class TurfUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = Field(default=None, min_length=2, max_length=512)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    description: str | None = None
    amenities: list[str] | None = None
    operating_hours: dict[str, DayHours] | None = None
    is_active: bool | None = None

    @field_validator("operating_hours")
    @classmethod
    def _valid_days(cls, v: dict[str, DayHours] | None) -> dict[str, DayHours] | None:
        if v is None:
            return v
        invalid = set(v) - _WEEKDAYS
        if invalid:
            raise ValueError(f"Invalid weekday keys: {sorted(invalid)}")
        return v


class TurfSportCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sport_name: str = Field(min_length=1, max_length=100)
    sport_id: str | None = None
    icon_url: str | None = None
    price_per_hour: float = Field(gt=0)
    advance_deposit_percentage: int = Field(default=50, ge=0, le=100)
    min_players: int = Field(default=1, ge=1)
    max_players: int = Field(default=22, ge=1)
    default_duration_minutes: int = Field(default=60, ge=15, le=240)


class TurfSportUpdateSchema(BaseModel):
    price_per_hour: float | None = Field(default=None, gt=0)
    advance_deposit_percentage: int | None = Field(default=None, ge=0, le=100)
    min_players: int | None = Field(default=None, ge=1)
    max_players: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class GenerateSlotsSchema(BaseModel):
    turf_sport_id: str
    days: int = Field(default=14, ge=1, le=60)


class CalendarQuerySchema(BaseModel):
    turf_id: str
    sport_id: str
    date: date


class DiscoveryQuerySchema(BaseModel):
    city: str | None = None
    sport: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    radius: float | None = Field(default=None, gt=0, le=500)
    amenities: list[str] = Field(default_factory=list)
    date: _dt.date | None = None
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class AvailableSlotsQuerySchema(BaseModel):
    date: date
    sport_id: str


class SlotBlockSchema(BaseModel):
    turf_sport_id: str
    slot_date: date
    start_time: str
    end_time: str
    reason: str
    notes: str | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return v


class SlotUnblockSchema(BaseModel):
    slot_id: str


class BulkBlockSchema(BaseModel):
    turf_sport_id: str
    start_date: date
    end_date: date
    days_of_week: list[int] = Field(min_length=1)
    start_time: str
    end_time: str
    reason: str
    notes: str | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError("Time must be in HH:MM 24-hour format")
        return v

    @field_validator("days_of_week")
    @classmethod
    def _valid_days(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("days_of_week must be 0 (Mon) .. 6 (Sun)")
        return v
