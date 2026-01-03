from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="FastAPI Example",
    description="Example API for Clientele documentation",
    version="1.0.0",
)


class User(BaseModel):
    id: int
    name: str
    email: str


class CreateUserRequest(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


# In-memory storage for demo purposes
users_db = [
    User(id=1, name="Alice", email="alice@example.com"),
    User(id=2, name="Bob", email="bob@example.com"),
]


@app.get("/users", operation_id="list_users", response_model=list[UserResponse])
def get_users():
    """List all users."""
    return users_db


@app.post("/users", operation_id="create_user", response_model=UserResponse)
def create_user(user: CreateUserRequest):
    """Create a new user."""
    new_user = User(
        id=len(users_db) + 1,
        name=user.name,
        email=user.email,
    )
    users_db.append(new_user)
    return new_user


@app.get("/users/{user_id}", operation_id="get_user", response_model=UserResponse)
def get_user(user_id: int):
    """
    Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """
    for user in users_db:
        if user.id == user_id:
            return user
    return UserResponse(id=user_id, name="Not Found", email="")
