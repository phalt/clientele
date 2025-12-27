# 🔗 References in OpenAPI

Clientele fully supports OpenAPI's `$ref` mechanism for reusing schema definitions across your API specification. This page explains how references work and what Clientele does when generating clients with them.

## What are `$ref`s?

In OpenAPI, `$ref` (short for "reference") lets you define a schema, parameter, or response once and reuse it throughout your specification.

Here's a simple example:

```json
{
  "components": {
    "schemas": {
      "User": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "name": { "type": "string" }
        }
      },
      "UserList": {
        "type": "object",
        "properties": {
          "users": {
            "type": "array",
            "items": { "$ref": "#/components/schemas/User" }
          }
        }
      }
    }
  }
}
```

Instead of duplicating the `User` schema definition everywhere you need it, you use `$ref` to reference it.

## How Clientele handles references

Clientele resolves all `$ref` declarations in your OpenAPI schema and generates properly-typed Python code using [Pydantic](https://docs.pydantic.dev/latest/) models.

## Types of references supported

Clientele handles `$ref` in all the places the OpenAPI specification allows:

### 1. Schema properties

When a property references another schema:

```json
{
  "Response": {
    "properties": {
      "user": { "$ref": "#/components/schemas/User" }
    }
  }
}
```

Generates:

```python
class User(pydantic.BaseModel):
    id: int
    name: str

class Response(pydantic.BaseModel):
    user: "User" 
```

### 2. Array items

When array items reference a schema:

```json
{
  "UserList": {
    "properties": {
      "users": {
        "type": "array",
        "items": { "$ref": "#/components/schemas/User" }
      }
    }
  }
}
```

Generates:

```python
class UserList(pydantic.BaseModel):
    users: list[User]
```

### 3. Enum references

References to enum schemas work just as you'd expect:

```json
{
  "Status": {
    "type": "string",
    "enum": ["active", "inactive"]
  },
  "Response": {
    "properties": {
      "status": { "$ref": "#/components/schemas/Status" }
    }
  }
}
```

Generates:

```python
class Status(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Response(pydantic.BaseModel):
    status: "Status"
```

### 4. Response references

OpenAPI lets you define reusable responses in `components/responses`:

```yaml
components:
  responses:
    ErrorResponse:
      description: Standard error response
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
  schemas:
    Error:
      type: object
      properties:
        message:
          type: string

paths:
  /users:
    get:
      responses:
        '400':
          $ref: '#/components/responses/ErrorResponse'
```

Clientele resolves the response reference and generates the corresponding schema just once:

```python
class Error(pydantic.BaseModel):
    message: str
```

### 5. Parameter references

You can define reusable parameters:

```yaml
components:
  parameters:
    PageNumber:
      name: page
      in: query
      schema:
        type: integer

paths:
  /users:
    get:
      parameters:
        - $ref: '#/components/parameters/PageNumber'
```

Clientele includes these in the generated function signatures or header classes.

### 6. Composed schemas (allOf)

OpenAPI's `allOf` lets you compose schemas from multiple references:

```yaml
components:
  schemas:
    BaseUser:
      type: object
      properties:
        id:
          type: integer
    UserDetails:
      type: object
      properties:
        email:
          type: string
    FullUser:
      allOf:
        - $ref: '#/components/schemas/BaseUser'
        - $ref: '#/components/schemas/UserDetails'
```

Generates a single merged schema:

```python
class FullUser(pydantic.BaseModel):
    id: int       # From BaseUser
    email: str    # From UserDetails
```

## Nested references

Clientele handles deeply nested references without any issues:

```json
{
  "Comment": {
    "properties": {
      "author": { "$ref": "#/components/schemas/User" }
    }
  },
  "Post": {
    "properties": {
      "comments": {
        "type": "array",
        "items": { "$ref": "#/components/schemas/Comment" }
      }
    }
  }
}
```

Generates properly typed nested structures:

```python
class User(pydantic.BaseModel):
    id: int
    name: str

class Comment(pydantic.BaseModel):
    author: User

class Post(pydantic.BaseModel):
    comments: list[Comment]
```

## Working with generated code

The generated code using references works seamlessly at runtime:

```python
from my_api import schemas

# Create a user
user = schemas.User(id=1, name="Alice")

# Use in a response
response = schemas.Response(user=user)

# Type checking works!
reveal_type(response.user)  # Revealed type is "User"

# IDE auto-completion works too
response.user.name  # ← Your IDE suggests 'id' and 'name'
```

## Real-world example

Here's a complete example showing multiple reference types working together:

### OpenAPI Schema

```json
{
  "components": {
    "schemas": {
      "UserRole": {
        "type": "string",
        "enum": ["admin", "user", "guest"]
      },
      "User": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "name": { "type": "string" },
          "role": { "$ref": "#/components/schemas/UserRole" }
        }
      },
      "TeamResponse": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "members": {
            "type": "array",
            "items": { "$ref": "#/components/schemas/User" }
          },
          "owner": { "$ref": "#/components/schemas/User" }
        }
      }
    }
  }
}
```

### Generated Code

```python
import enum
import pydantic

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(pydantic.BaseModel):
    id: int
    name: str
    role: UserRule

class TeamResponse(pydantic.BaseModel):
    name: str
    members: list[User]
    owner: User
```

### Usage

```python
from my_api import schemas

# Create users with enum roles
admin = schemas.User(
    id=1, 
    name="Alice", 
    role=schemas.UserRole.ADMIN
)
member = schemas.User(
    id=2, 
    name="Bob", 
    role=schemas.UserRole.USER
)

# Create a team response
team = schemas.TeamResponse(
    name="Engineering",
    members=[admin, member],
    owner=admin
)

# Everything is properly typed
assert isinstance(team.owner, schemas.User)
assert team.owner.role == schemas.UserRole.ADMIN
```

## Summary

Clientele handles all forms of `$ref` in OpenAPI schemas:

| Reference Type | Location | Supported | Example |
|----------------|----------|-----------|---------|
| Schema in property | `properties.user.$ref` | ✅ | `user: "User"` |
| Schema in array | `items.$ref` | ✅ | `list["User"]` |
| Enum reference | `properties.status.$ref` | ✅ | `status: "Status"` |
| Response reference | `responses.400.$ref` | ✅ | Schema generated |
| Parameter reference | `parameters.$ref` | ✅ | Included in functions |
| allOf composition | `allOf[n].$ref` | ✅ | Merged into one schema |
