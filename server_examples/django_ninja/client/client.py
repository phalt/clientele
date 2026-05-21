from __future__ import annotations

import typing

from clientele import api as clientele_api
from server_examples.django_ninja.client import config, schemas

client = clientele_api.APIClient(config=config.Config())


@client.get("/api/users")
def list_users(result: schemas.Response) -> schemas.Response:
    """List Users

    List all users.
    """
    return result


@client.post("/api/users")
def create_user(result: schemas.UserOut, data: schemas.UserIn) -> schemas.UserOut:
    """Create User

    Create a new user.
    """
    return result


@client.get("/api/users/{user_id}")
def get_user(result: schemas.UserOut, user_id: int, include_posts: typing.Optional[bool] = None) -> schemas.UserOut:
    """Get User

        Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """
    return result
