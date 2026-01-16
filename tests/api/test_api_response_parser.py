from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.api import APIClient
from clientele.http import response as http_response

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


class CustomResponseParserResponse(BaseModel):
    name: str
    other_value: str


@pytest.mark.respx(base_url=BASE_URL)
def test_accepts_response_parser_and_uses_it_to_return_response(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}, headers={"x-source": "mock"})
    )

    def my_response_parser(response: http_response.Response) -> CustomResponseParserResponse:
        data = response.json()
        return CustomResponseParserResponse(name=data["name"], other_value="other value")

    @client.get("/users/{user_id}", response_parser=my_response_parser)
    def get_user_custom_response(user_id: int, result: CustomResponseParserResponse) -> str:
        return result.other_value

    custom_response = get_user_custom_response(1)

    assert custom_response == "other value"
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/1"


@pytest.mark.respx(base_url=BASE_URL)
def test_response_parser_handles_simple_response_types(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}, headers={"x-source": "mock"})
    )

    def my_response_parser(response: http_response.Response) -> dict:
        return {"other_value": "other value"}

    @client.get("/users/{user_id}", response_parser=my_response_parser)
    def get_user_custom_response(user_id: int, result: dict) -> str:
        return result["other_value"]

    custom_response = get_user_custom_response(1)

    assert custom_response == "other value"
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/1"


def test_errors_when_parser_return_types_do_not_match_result_types(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    def my_response_parser(response: http_response.Response) -> CustomResponseParserResponse:
        data = response.json()
        return CustomResponseParserResponse(name=data["name"], other_value="other value")

    with pytest.raises(
        TypeError,
        match="The return type of the response_parser for function 'get_user': "
        r"\[CustomResponseParserResponse\] does not match the type\(s\) of the 'result' parameter: "
        r"\[User\]\.",
    ):

        @client.get("/users/{user_id}", response_parser=my_response_parser)
        def get_user(user_id: int, result: User) -> int:
            return result.id


def test_raises_when_both_response_map_and_response_parser_are_provided(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    def my_response_parser(response: http_response.Response) -> CustomResponseParserResponse:
        return CustomResponseParserResponse(name="name", other_value="other value")

    with pytest.raises(
        TypeError,
        match="Function 'get_raises_with_both' cannot have both 'response_map' and 'response_parser' defined.",
    ):

        @client.get(
            "/users/{user_id}", response_parser=my_response_parser, response_map={200: CustomResponseParserResponse}
        )
        def get_raises_with_both(user_id: int, result: CustomResponseParserResponse) -> str:
            return result.name
