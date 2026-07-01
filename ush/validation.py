from __future__ import annotations

from datetime import datetime  # noqa: TC003
from pathlib import Path  # noqa: TC003
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)
from uwtools.api.driver import yaml_keys_to_classes

Model = Literal["GFS", "RAP", "RRFS"]
MIN_WIDTH_HEIGHT = 80


class Config(BaseModel):
    user: User


class ICs(BaseModel):
    external_model: Model
    offset_hours: NonNegativeInt


class LBCs(BaseModel):
    external_model: Model
    interval_hours: PositiveInt
    offset_hours: NonNegativeInt


class TrackerInfo(BaseModel):
    trkrinfo: TrkrInfo


class TrackerNamelist(BaseModel):
    trackerinfo: TrackerInfo


class TrkrInfo(BaseModel):
    eastbd: NonNegativeFloat
    westbd: NonNegativeFloat
    northbd: NonNegativeFloat
    southbd: NonNegativeFloat

    @model_validator(mode="after")
    def east_west_order(self):
        if self.eastbd < self.westbd:
            msg = (
                "East and west bounds are probably switched. East bound "
                f"({self.eastbd}) < west bound ({self.westbd})."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def east_west_size(self):
        if self.eastbd < (self.westbd + MIN_WIDTH_HEIGHT):
            msg = (
                f"East and west bounds ({self.eastbd}, {self.westbd}) are "
                f"close together. Recommend at least {MIN_WIDTH_HEIGHT} points."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def north_south_order(self):
        if self.northbd < self.southbd:
            msg = (
                "North and south bounds are probably switched. North bound"
                f"({self.northbd}) < south bound ({self.southbd})."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def north_south_size(self):
        if self.northbd < (self.southbd + MIN_WIDTH_HEIGHT):
            msg = (
                f"North and south bounds ({self.northbd}, {self.southbd}) "
                f"are close together. Recommend at least {MIN_WIDTH_HEIGHT} points."
            )
            raise ValueError(msg)
        return self


class User(BaseModel):
    cycle_frequency: PositiveInt
    driver_validation_blocks: list[str] = Field(default_factory=list)
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
        valid_drivers = yaml_keys_to_classes().keys()
        for key_path in self.driver_validation_blocks:
            driver = key_path.split(".")[-1]
            if driver not in valid_drivers:
                msg = (
                    f"Unsupported driver in 'driver_validation_blocks': '{driver}'."
                    f"Supported drivers are: {valid_drivers}."
                )
                raise ValueError(msg)
        return self


def validate(config: dict) -> Config:
    return Config(**config)
