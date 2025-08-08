from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ParamBindingFixed(BaseModel):
    type: Literal["fixed"]
    value: Union[str, int, float, bool]


class ParamBindingRequestArg(BaseModel):
    type: Literal["request_arg"]
    name: str


class ParamBindingDerived(BaseModel):
    type: Literal["derived"]
    rule: str = Field(description="Name of the derived rule, MVP placeholder")


ParamBinding = Union[ParamBindingFixed, ParamBindingRequestArg, ParamBindingDerived]


class SelectionItem(BaseModel):
    endpoint: str
    fields: List[str]
    param_binding: Dict[str, ParamBinding] = Field(default_factory=dict)
    join_keys: List[str]

    @field_validator("fields")
    @classmethod
    def non_empty_fields(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("fields must not be empty")
        return v

    @field_validator("join_keys")
    @classmethod
    def non_empty_join_keys(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("join_keys must not be empty")
        return v


class CodeContract(BaseModel):
    signature: str
    data_keys: List[str]


class Constraints(BaseModel):
    winsor: Optional[List[float]] = None
    zscore_axis: Optional[str] = None


class SelectionSpec(BaseModel):
    factor_slug: str
    title: str
    output_index: List[str]
    selection: List[SelectionItem]
    alignment: List[dict] = Field(default_factory=list)
    constraints: Optional[Constraints] = None
    code_contract: CodeContract

    @field_validator("factor_slug")
    @classmethod
    def slug_safe(cls, v: str) -> str:
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
        s = v.lower()
        if not s or any(c not in allowed for c in s):
            raise ValueError("factor_slug must be lowercase slug [a-z0-9-_]")
        return s

    @field_validator("output_index")
    @classmethod
    def non_empty_index(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("output_index must not be empty")
        return v
