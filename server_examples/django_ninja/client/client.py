from __future__ import annotations

import typing  # noqa

from server_examples.django_ninja.client import http, schemas  # noqa


def list_users() -> schemas.Response:
    """List Users

    List all users.
    """

    response = http.get(url="/api/users")
    return http.handle_response(list_users, response)


def create_user(data: schemas.UserIn) -> schemas.UserOut:
    """Create User

    Create a new user.
    """

    response = http.post(url="/api/users", data=data.model_dump())
    return http.handle_response(create_user, response)


def get_user(user_id: int, include_posts: typing.Optional[bool] = None) -> schemas.UserOut:
    """Get User

        Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """

    response = http.get(url=f"/api/users/{user_id}?include_posts={include_posts}")
    return http.handle_response(get_user, response)
