from datetime import datetime

from pydantic import BaseModel


class ICs(BaseModel):
    external_model: str
    offset_hours: int


class LBCs(BaseModel):
    external_model: str
    interval_hours: int
    offset_hours: int


class User(BaseModel):
    cycle_frequency: int
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
