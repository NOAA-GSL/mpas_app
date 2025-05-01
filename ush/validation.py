from datetime import datetime
from typing import Literal

from pydantic import BaseModel, NonNegativeInt, PositiveInt

Model = Literal["GFS", "RAP"]


class ICs(BaseModel):
    external_model: Model
    offset_hours: NonNegativeInt


class LBCs(BaseModel):
    external_model: Model
    interval_hours: PositiveInt
    offset_hours: NonNegativeInt


class User(BaseModel):
    cycle_frequency: PositiveInt
    experiment_dir: str
    first_cycle: datetime
    ics: ICs
    last_cycle: datetime
    lbcs: LBCs
    mesh_label: str
    mpas_app: str
    platform: str
    workflow_blocks: list[str]


def validate(config: dict) -> None:
    assert User(**config)
