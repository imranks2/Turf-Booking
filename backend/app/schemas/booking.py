from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BookingCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    turf_sport_id: str = Field(min_length=1)
    slot_ids: list[str] = Field(min_length=1, max_length=12)
    player_id: str | None = None


class BookingCancelSchema(BaseModel):
    reason: str | None = Field(default=None, max_length=512)
