# 🧬 GraphQL Client

Clientele provides a specialized `GraphQLClient` for building GraphQL integrations following the same decorator pattern as the standard `APIClient`.

## Basic Query

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Repository(BaseModel):
    name: str
    stargazerCount: int

class RepositoryQueryData(BaseModel):
    repository: Repository

class RepositoryQueryResponse(BaseModel):
    data: RepositoryQueryData

@client.query("""
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            name
            stargazerCount
        }
    }
""")
def get_repo(owner: str, name: str, result: RepositoryQueryResponse) -> Repository:
    return result.data.repository

repo = get_repo(owner="phalt", name="clientele")
print(repo.name)  # "clientele"
print(repo.stargazerCount)  # 100
```

How it works:

- The GraphQL query string is passed to the `@client.query()` decorator.
- Function parameters (excluding `result` and `response`) become GraphQL variables.
- The `result` parameter is auto-hydrated to the specified Pydantic model matching GraphQL's response structure.
- GraphQL wraps all responses in `{"data": {...}}`, so your models should reflect this nested structure.

## Basic Mutation

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Issue(BaseModel):
    id: str
    title: str

class CreateIssueData(BaseModel):
    issue: Issue

class CreateIssueMutationData(BaseModel):
    createIssue: CreateIssueData

class CreateIssueMutationResponse(BaseModel):
    data: CreateIssueMutationData

@client.mutation("""
    mutation($title: String!, $body: String!) {
        createIssue(input: {title: $title, body: $body}) {
            issue {
                id
                title
            }
        }
    }
""")
def create_issue(title: str, body: str, result: CreateIssueMutationResponse) -> Issue:
    return result.data.createIssue.issue

issue = create_issue(title="Bug report", body="Something is broken")
print(issue.id)  # "123"
print(issue.title)  # "Bug report"
```

## Optional Parameters

GraphQL variables that are optional (nullable) should use Python's `| None` type annotation. When a parameter is `None`, it will be omitted from the variables object following GraphQL best practices.

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Repository(BaseModel):
    name: str
    language: str | None = None

class RepositoriesQueryData(BaseModel):
    repositories: list[Repository]

class RepositoriesQueryResponse(BaseModel):
    data: RepositoriesQueryData

@client.query("""
    query($owner: String!, $language: String) {
        repositories(owner: $owner, language: $language) {
            name
            language
        }
    }
""")
def search_repos(owner: str, language: str | None, result: RepositoriesQueryResponse) -> list[Repository]:
    return result.data.repositories

# Call without optional parameter - language is omitted from variables
repos = search_repos(owner="phalt")

# Call with optional parameter - language is included
python_repos = search_repos(owner="phalt", language="Python")
```

**Note**: Passing `None` omits the variable entirely rather than sending `null`, which is the recommended GraphQL pattern for optional variables.

## Async Support

Both queries and mutations support async operations. Simply define your decorated function as `async def`:

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Repository(BaseModel):
    name: str
    stargazerCount: int

class RepositoryQueryData(BaseModel):
    repository: Repository

class RepositoryQueryResponse(BaseModel):
    data: RepositoryQueryData

@client.query("""
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            name
            stargazerCount
        }
    }
""")
async def get_repo(owner: str, name: str, result: RepositoryQueryResponse) -> Repository:
    return result.data.repository

# Use with await
repo = await get_repo(owner="phalt", name="clientele")
```

### Async Mutations

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Issue(BaseModel):
    id: str
    title: str

class CreateIssueData(BaseModel):
    issue: Issue

class CreateIssueMutationData(BaseModel):
    createIssue: CreateIssueData

class CreateIssueMutationResponse(BaseModel):
    data: CreateIssueMutationData

@client.mutation("""
    mutation($title: String!, $body: String) {
        createIssue(input: {title: $title, body: $body}) {
            issue {
                id
                title
            }
        }
    }
""")
async def create_issue(title: str, body: str | None, result: CreateIssueMutationResponse) -> Issue:
    return result.data.createIssue.issue

# Use with await
issue = await create_issue(title="Bug report", body=None)
```

## Inspecting the Response

You can access the raw HTTP response by adding a `response` parameter:

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient
from clientele.http import Response

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Repository(BaseModel):
    name: str

class RepositoryQueryData(BaseModel):
    repository: Repository

class RepositoryQueryResponse(BaseModel):
    data: RepositoryQueryData

@client.query("""
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            name
        }
    }
""")
def get_repo(owner: str, name: str, result: RepositoryQueryResponse, response: Response) -> Repository:
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    return result.data.repository

repo = get_repo(owner="phalt", name="clientele")
```

## Working with Raw Dicts

If you prefer not to use Pydantic models for the response structure, you can still use `result: dict` and work with raw dictionaries:

```python
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

@client.query("""
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            name
            stargazerCount
        }
    }
""")
def get_repo(owner: str, name: str, result: dict) -> dict:
    return result["data"]["repository"]

repo = get_repo(owner="phalt", name="clientele")
print(repo["name"])  # "clientele"
print(repo["stargazerCount"])  # 100
```

However, using Pydantic models for the `result` parameter provides type safety and auto-hydration, which is the recommended approach.

## Configuration

The `GraphQLClient` inherits from `APIClient` and supports all the same configuration options:

```python
from clientele.graphql import GraphQLClient
from clientele.api import BaseConfig

config = BaseConfig(
    base_url="https://api.github.com/graphql",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
)

client = GraphQLClient(config=config)
```

You can also close clients when done:

```python
# Sync
client.close()

# Async
await client.aclose()
```
