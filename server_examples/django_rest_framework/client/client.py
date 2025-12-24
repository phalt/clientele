from __future__ import annotations

import typing  # noqa

from server_examples.django_rest_framework.client import http, schemas  # noqa


def list_users() -> schemas.ListUsers200Response:
    response = http.get(url="/api/users/")
    return http.handle_response(list_users, response)


def create_user(data: schemas.UserRequest) -> schemas.User:
    response = http.post(url="/api/users/", data=data.model_dump())
    return http.handle_response(create_user, response)


def get_user(id: int) -> schemas.User:
    response = http.get(url=f"/api/users/{id}/")
    return http.handle_response(get_user, response)


def users_update(id: int, data: schemas.User) -> schemas.User:
    response = http.put(url=f"/api/users/{id}/", data=data.model_dump())
    return http.handle_response(users_update, response)


def users_partial_update(id: int, data: schemas.PatchedUser) -> schemas.User:
    response = http.patch(url=f"/api/users/{id}/", data=data.model_dump())
    return http.handle_response(users_partial_update, response)


def users_destroy(id: int) -> None:
    response = http.delete(url=f"/api/users/{id}/")
    return http.handle_response(users_destroy, response)
