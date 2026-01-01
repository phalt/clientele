from __future__ import annotations

import typing

import clientele

client = clientele.Client(config=config.Config())


@client.get("/api/users")
def list_users() -> schemas.Response:  # type: ignore[return]
    """List Users

    List all users.
    """
    ...


@client.post("/api/users")
def create_user(data: schemas.UserIn) -> schemas.UserOut:  # type: ignore[return]
    """Create User

    Create a new user.
    """
    ...


@client.get("/api/users/{user_id}")
def get_user(user_id: int, include_posts: typing.Optional[bool] = None) -> schemas.UserOut:  # type: ignore[return]
    """Get User

        Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """
    ...
