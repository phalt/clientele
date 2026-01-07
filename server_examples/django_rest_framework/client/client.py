from __future__ import annotations

from clientele import api as clientele_api
from server_examples.django_rest_framework.client import config, schemas

client = clientele_api.APIClient(config=config.Config())


@client.get("/api/users/")
def list_users(result: schemas.ListUsers200Response) -> schemas.ListUsers200Response:
    return result


@client.post("/api/users/")
def create_user(data: schemas.UserRequest, result: schemas.User) -> schemas.User:
    return result


@client.get("/api/users/{id}/")
def get_user(id: int, result: schemas.User) -> schemas.User:
    return result


@client.put("/api/users/{id}/")
def users_update(id: int, data: schemas.User, result: schemas.User) -> schemas.User:
    return result


@client.patch("/api/users/{id}/")
def users_partial_update(id: int, data: schemas.PatchedUser, result: schemas.User) -> schemas.User:
    return result


@client.delete("/api/users/{id}/")
def users_destroy(id: int, result: None) -> None:
    return result
