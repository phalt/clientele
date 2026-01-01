from __future__ import annotations

import typing

from clientele import framework as clientele_framework
from server_examples.django_ninja.client import config, schemas

client = clientele_framework.Client(config=config.Config())


@client.get("/api/users")
def list_users(result: schemas.Response) -> schemas.Response:
    """List Users

    List all users.
    """
    return result


@client.post("/api/users")
def create_user(
    data: schemas.UserIn,
    result: schemas.UserOut,
) -> schemas.UserOut:
    """Create User

    Create a new user.
    """
    return result


@client.get("/api/users/{user_id}")
def get_user(user_id: int, result: schemas.UserOut, include_posts: typing.Optional[bool] = None) -> schemas.UserOut:
    """Get User

        Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """
    return result
