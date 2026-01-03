from __future__ import annotations

import decimal
import enum
import inspect
import typing

import pydantic


class AnotherModel(pydantic.BaseModel):
    key: str


class ComplexModelResponse(pydantic.BaseModel):
    a_dict_response: dict[str, typing.Any]
    a_enum: "ExampleEnum"
    a_list_of_enums: list["ExampleEnum"]
    a_list_of_numbers: list[int]
    a_list_of_other_models: list["AnotherModel"]
    a_list_of_strings: list[str]
    a_number: int
    a_string: str
    a_decimal: decimal.Decimal
    a_float: float
    another_model: "AnotherModel"


class DeleteResponse(pydantic.BaseModel):
    pass


class ExampleEnum(str, enum.Enum):
    ONE = "ONE"
    TWO = "TWO"


class HeadersResponse(pydantic.BaseModel):
    x_test: str


class HTTPValidationError(pydantic.BaseModel):
    detail: list["ValidationError"]


class OptionalParametersResponse(pydantic.BaseModel):
    optional_parameter: typing.Optional[str] = None
    required_parameter: str


class ParameterResponse(pydantic.BaseModel):
    your_input: str


class RequestDataAndParameterResponse(pydantic.BaseModel):
    my_input: str
    path_parameter: str


class RequestDataRequest(pydantic.BaseModel):
    my_input: str
    my_decimal_input: decimal.Decimal


class RequestDataResponse(pydantic.BaseModel):
    my_input: str


class SecurityRequiredResponse(pydantic.BaseModel):
    token: str


class SimpleQueryParametersResponse(pydantic.BaseModel):
    your_query: str


class OptionalQueryParametersResponse(pydantic.BaseModel):
    your_query: str


class SimpleResponse(pydantic.BaseModel):
    status: str


class ValidationError(pydantic.BaseModel):
    loc: list[str | int]
    msg: str
    type_: str = pydantic.Field(alias="type")

    model_config = pydantic.ConfigDict(populate_by_name=True)


class HeaderRequestHeaderRequestGetHeaders(pydantic.BaseModel):
    x_test: typing.Any = pydantic.Field(serialization_alias="x-test")


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
