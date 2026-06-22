from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MasterDataEntry(BaseModel):
    id: str | int
    name: str
    aliases: list[str] = Field(default_factory=list)


class MasterDataSet(BaseModel):
    schema_version: Literal[1] = 1
    dataset_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9._-]+$")
    entries: list[MasterDataEntry]

    @model_validator(mode="after")
    def validate_unique_match_values(self) -> "MasterDataSet":
        values: list[str] = []
        for entry in self.entries:
            values.append(entry.name)
            values.extend(entry.aliases)
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            raise ValueError(f"master data match values must be unique: {duplicates}")
        return self
