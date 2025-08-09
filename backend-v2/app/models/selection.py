from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


# Param binding in a source: either a fixed value or coming from request args
class ParamBindingFixed(BaseModel):
    type: Literal["fixed"]
    value: Union[str, int, float, bool]


class ParamBindingArg(BaseModel):
    type: Literal["arg"]


ParamBinding = Union[ParamBindingFixed, ParamBindingArg]


class SourceItem(BaseModel):
    endpoint: str
    fields: List[str]
    params: Dict[str, ParamBinding] = Field(default_factory=dict)

    @field_validator("fields")
    @classmethod
    def non_empty_fields(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("fields must not be empty")
        return v


class Constraints(BaseModel):
    winsor: Optional[List[float]] = None
    zscore_axis: Optional[str] = None


class ParamDecl(BaseModel):
    type: Literal["string", "number", "boolean", "date"]
    required: bool = False
    default: Optional[Union[str, int, float, bool]] = None
    enum: Optional[List[Union[str, int, float, bool]]] = None


class SelectionSpec(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    join_keys: List[str]
    sources: List[SourceItem]
    constraints: Optional[Constraints] = None
    params_schema: Dict[str, ParamDecl] = Field(default_factory=dict)

    @field_validator("slug")
    @classmethod
    def slug_safe(cls, v: str) -> str:
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
        s = v.lower()
        if not s or any(c not in allowed for c in s):
            raise ValueError("slug must be lowercase slug [a-z0-9-_]")
        return s

    @field_validator("join_keys")
    @classmethod
    def non_empty_join_keys(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("join_keys must not be empty")
        return v

    @field_validator("sources")
    @classmethod
    def non_empty_sources(cls, v: List[SourceItem]) -> List[SourceItem]:
        if not v:
            raise ValueError("sources must not be empty")
        return v
