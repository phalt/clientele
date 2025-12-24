from ninja import NinjaAPI, Schema

api = NinjaAPI(title="Django Ninja Example", version="1.0.0", description="Example API for Clientele documentation")


class UserIn(Schema):
    username: str
    email: str
    age: int


class UserOut(Schema):
    id: int
    username: str
    email: str
    age: int


# In-memory storage for demo purposes
users_db = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "username": "bob", "email": "bob@example.com", "age": 25},
]


@api.get("/users", operation_id="list_users", response=list[UserOut])
def list_users(request):
    """List all users."""
    return users_db


@api.post("/users", operation_id="create_user", response=UserOut)
def create_user(request, user: UserIn):
    """Create a new user."""
    new_user = {
        "id": len(users_db) + 1,
        "username": user.username,
        "email": user.email,
        "age": user.age,
    }
    users_db.append(new_user)
    return new_user


@api.get("/users/{user_id}", operation_id="get_user", response=UserOut)
def get_user(request, user_id: int, include_posts: bool = False):
    """
    Get a specific user by ID.

    The include_posts parameter is for demonstration purposes.
    """
    for user in users_db:
        if user["id"] == user_id:
            return user
    return {"id": user_id, "username": "Not Found", "email": "", "age": 0}
