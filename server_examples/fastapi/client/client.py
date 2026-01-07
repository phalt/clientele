from __future__ import annotations

import typing

from clientele import api as clientele_api
from server_examples.fastapi.client import config, schemas

client = clientele_api.APIClient(config=config.Config())


@client.get("/users")
def list_users(result: schemas.ResponseListUsers) -> schemas.ResponseListUsers:
    """Get Users

    List all users.
    """
    return result


@client.post("/users", response_map={200: schemas.UserResponse, 422: schemas.HTTPValidationError})
def create_user(
    data: schemas.CreateUserRequest, result: schemas.HTTPValidationError | schemas.UserResponse
) -> schemas.HTTPValidationError | schemas.UserResponse:
    """Create User

    Create a new user.
    """
    return result


@client.get("/users/{user_id}", response_map={200: schemas.UserResponse, 422: schemas.HTTPValidationError})
def get_user(
    user_id: int,
    result: schemas.HTTPValidationError | schemas.UserResponse,
    include_posts: typing.Optional[bool] = None,
) -> schemas.HTTPValidationError | schemas.UserResponse:
    """Get User

        Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """
    return result
