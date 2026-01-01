from __future__ import annotations

import clientele

from . import config, schemas

client = clientele.Client(config=config.Config())


@client.get("/api/users/")
def list_users() -> schemas.ListUsers200Response:  # type: ignore[return]
    ...


@client.post("/api/users/")
def create_user(data: schemas.UserRequest) -> schemas.User:  # type: ignore[return]
    ...


@client.get("/api/users/{id}/")
def get_user(id: int) -> schemas.User:  # type: ignore[return]
    ...


@client.put("/api/users/{id}/")
def users_update(id: int, data: schemas.User) -> schemas.User:  # type: ignore[return]
    ...


@client.patch("/api/users/{id}/")
def users_partial_update(id: int, data: schemas.PatchedUser) -> schemas.User:  # type: ignore[return]
    ...


@client.delete("/api/users/{id}/")
def users_destroy(id: int) -> None:  # type: ignore[return]
    ...
