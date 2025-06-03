from __future__ import annotations

from datetime import datetime  # noqa: TC003
from pathlib import Path  # noqa: TC003
from typing import Literal

from pydantic import BaseModel, NonNegativeInt, PositiveInt, root_validator

Model = Literal["GFS", "RAP"]


class Config(BaseModel):
    user: User


class ICs(BaseModel):
    external_model: Model
    offset_hours: NonNegativeInt


class LBCs(BaseModel):
    external_model: Model
    interval_hours: PositiveInt
    offset_hours: NonNegativeInt


class User(BaseModel):
    cycle_frequency: PositiveInt
    experiment_dir: Path
    first_cycle: datetime
    ics: ICs
    last_cycle: datetime
    lbcs: LBCs
    mesh_label: str
    platform: str
    workflow_blocks: list[str]

    @root_validator()
    def first_and_last_cycle(cls, values):
        first = values.get("first_cycle")
        last = values.get("last_cycle")
        if first and last and last < first:
            raise ValueError("last_cycle cannot precede first_cycle")
        return values


def validate(config: dict) -> Config:
    return Config(**config)

Config.update_forward_refs()
