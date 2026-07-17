from __future__ import annotations


class Query:
    """Marks a decorated function parameter as an HTTP query parameter with a wire-format alias.

    Use via ``typing.Annotated`` when the Python parameter name (e.g. to satisfy naming
    conventions such as ruff's N803) differs from the query parameter name expected by the API.

    Example:
    ```python
    from typing import Annotated

    from clientele import api

    client = api.APIClient(base_url="https://pokeapi.co/api/v2/")


    @client.get("/pokemon/")
    def get_pokemon_page(result: dict, order_by: Annotated[str, api.Query(alias="orderBy")]) -> dict:
        return result
    ```
    """

    __slots__ = ("alias",)

    def __init__(self, *, alias: str) -> None:
        self.alias = alias

    def __repr__(self) -> str:
        return f"Query(alias={self.alias!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Query) and self.alias == other.alias

    def __hash__(self) -> int:
        return hash(("clientele.api.Query", self.alias))
