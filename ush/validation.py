from __future__ import annotations

from datetime import datetime  # noqa: TC003
from pathlib import Path  # noqa: TC003
from typing import Literal

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt, model_validator
from uwtools.api.driver import yaml_keys_to_classes

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
    driver_validation_blocks: list[str] | None = Field(default=None)
    experiment_dir: Path
    first_cycle: datetime
    ics: ICs
    last_cycle: datetime
    lbcs: LBCs
    mesh_label: str
    platform: str
    workflow_blocks: list[str]

    @model_validator(mode="after")
    def first_and_last_cycle(self):
        if self.last_cycle < self.first_cycle:
            msg = "last_cycle cannot precede first_cycle"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_driver_blocks(self):
        valid_drivers = set(yaml_keys_to_classes().keys())
        for key_path in self.driver_validation_blocks or []:
            driver = key_path.rsplit(".", 1)[-1]
            if driver not in valid_drivers:
                msg = (
                    f"Unsupported driver in 'driver_validation_blocks': '{driver}'. "
                    f"Supported drivers are: {valid_drivers}."
                )
                raise ValueError(msg)
        return self


def validate(config: dict) -> Config:
    return Config(**config)
