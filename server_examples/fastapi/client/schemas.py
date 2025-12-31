from __future__ import annotations

import inspect
import typing

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


def get_subclasses_from_same_file() -> list[typing.Type[pydantic.BaseModel]]:
    """
    Due to how Python declares classes in a module,
    we need to update_forward_refs for all the schemas generated
    here in the situation where there are nested classes.
    """
    calling_frame = inspect.currentframe()
    if not calling_frame:
        return []
    else:
        calling_frame = calling_frame.f_back
    module = inspect.getmodule(calling_frame)

    subclasses = []
    for _, c in inspect.getmembers(module):
        if inspect.isclass(c) and issubclass(c, pydantic.BaseModel) and c != pydantic.BaseModel:
            subclasses.append(c)

    return subclasses


subclasses: list[typing.Type[pydantic.BaseModel]] = get_subclasses_from_same_file()
for c in subclasses:
    c.model_rebuild()
