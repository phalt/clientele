from __future__ import annotations

from clientele import api as clientele_api
from server_examples.django_rest_framework.client import config, schemas

client = clientele_api.APIClient(config=config.Config())


@client.get("/api/users/")
def list_users(result: schemas.ListUsers200Response) -> schemas.ListUsers200Response:

    return result


@client.post("/api/users/")
def create_user(result: schemas.User, data: schemas.UserRequest) -> schemas.User:

    return result


@client.get("/api/users/{id}/")
def get_user(result: schemas.User, id: int) -> schemas.User:

    return result


@client.put("/api/users/{id}/")
def users_update(result: schemas.User, data: schemas.User, id: int) -> schemas.User:

    return result


@client.patch("/api/users/{id}/")
def users_partial_update(result: schemas.User, data: schemas.PatchedUser, id: int) -> schemas.User:

    return result


@client.delete("/api/users/{id}/")
def users_destroy(result: None, id: int) -> None:

    return result
