from __future__ import annotations

import pydantic


class CreateUserRequest(pydantic.BaseModel):
    name: str
    email: str


class HTTPValidationError(pydantic.BaseModel):
    detail: list["ValidationError"]


class UserResponse(pydantic.BaseModel):
    id: int
    name: str
    email: str


class ValidationError(pydantic.BaseModel):
    loc: list[str | int]
    msg: str
    type_: str = pydantic.Field(alias="type")

    model_config = pydantic.ConfigDict(populate_by_name=True)


ResponseListUsers = list[UserResponse]
