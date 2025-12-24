from __future__ import annotations

import typing  # noqa

from server_examples.fastapi.client import http, schemas  # noqa


def list_users() -> schemas.ResponseListUsers:
    """Get Users

    List all users.
    """

    response = http.get(url="/users")
    return http.handle_response(list_users, response)


def create_user(data: schemas.CreateUserRequest) -> schemas.HTTPValidationError | schemas.UserResponse:
    """Create User

    Create a new user.
    """

    response = http.post(url="/users", data=data.model_dump())
    return http.handle_response(create_user, response)


def get_user(
    user_id: int, include_posts: typing.Optional[bool] = None
) -> schemas.HTTPValidationError | schemas.UserResponse:
    """Get User

        Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """

    response = http.get(url=f"/users/{user_id}?include_posts={include_posts}")
    return http.handle_response(get_user, response)
