from __future__ import annotations

import pytest
from pydantic import BaseModel

from clientele.graphql import GraphQLClient
from clientele.http import Response
from clientele.testing import ResponseFactory, configure_client_for_testing


class Repository(BaseModel):
    name: str
    stargazerCount: int


class RepositoryQueryData(BaseModel):
    repository: Repository


class RepositoryQueryResponse(BaseModel):
    data: RepositoryQueryData


class Issue(BaseModel):
    id: str
    title: str


class CreateIssueData(BaseModel):
    issue: Issue


class CreateIssueMutationData(BaseModel):
    createIssue: CreateIssueData


class CreateIssueMutationResponse(BaseModel):
    data: CreateIssueMutationData


def test_graphql_query_sync():
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(data={"data": {"repository": {"name": "clientele", "stargazerCount": 100}}}),
    )

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
    assert repo["name"] == "clientele"
    assert repo["stargazerCount"] == 100

    request = fake_backend.requests[0]
    assert request["method"] == "POST"
    assert request["url"] == ""
    assert "query" in request["kwargs"]["json"]
    assert request["kwargs"]["json"]["variables"] == {"owner": "phalt", "name": "clientele"}

    client.close()


def test_graphql_mutation_sync():
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(
            data={
                "data": {
                    "createRepository": {"repository": {"name": "new-repo", "url": "https://github.com/phalt/new-repo"}}
                }
            }
        ),
    )

    @client.mutation("""
        mutation($name: String!, $description: String!) {
            createRepository(input: {name: $name, description: $description}) {
                repository {
                    name
                    url
                }
            }
        }
    """)
    def create_repo(name: str, description: str, result: dict) -> dict:
        return result["data"]["createRepository"]["repository"]

    repo = create_repo(name="new-repo", description="A new repository")
    assert repo["name"] == "new-repo"
    assert repo["url"] == "https://github.com/phalt/new-repo"

    request = fake_backend.requests[0]
    assert request["method"] == "POST"
    assert request["url"] == ""
    assert "query" in request["kwargs"]["json"]
    assert request["kwargs"]["json"]["variables"] == {"name": "new-repo", "description": "A new repository"}

    client.close()


@pytest.mark.asyncio
async def test_graphql_query_async():
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(data={"data": {"repository": {"name": "clientele", "stargazerCount": 100}}}),
    )

    @client.query("""
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                name
                stargazerCount
            }
        }
    """)
    async def get_repo(owner: str, name: str, result: dict) -> dict:
        return result["data"]["repository"]

    repo = await get_repo(owner="phalt", name="clientele")
    assert repo["name"] == "clientele"
    assert repo["stargazerCount"] == 100

    request = fake_backend.requests[0]
    assert request["method"] == "POST"
    assert request["url"] == ""
    assert "query" in request["kwargs"]["json"]
    assert request["kwargs"]["json"]["variables"] == {"owner": "phalt", "name": "clientele"}

    await client.aclose()


@pytest.mark.asyncio
async def test_graphql_mutation_async():
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(
            data={
                "data": {
                    "createRepository": {"repository": {"name": "new-repo", "url": "https://github.com/phalt/new-repo"}}
                }
            }
        ),
    )

    @client.mutation("""
        mutation($name: String!, $description: String!) {
            createRepository(input: {name: $name, description: $description}) {
                repository {
                    name
                    url
                }
            }
        }
    """)
    async def create_repo(name: str, description: str, result: dict) -> dict:
        return result["data"]["createRepository"]["repository"]

    repo = await create_repo(name="new-repo", description="A new repository")
    assert repo["name"] == "new-repo"
    assert repo["url"] == "https://github.com/phalt/new-repo"

    request = fake_backend.requests[0]
    assert request["method"] == "POST"
    assert request["url"] == ""
    assert "query" in request["kwargs"]["json"]
    assert request["kwargs"]["json"]["variables"] == {"name": "new-repo", "description": "A new repository"}

    await client.aclose()


def test_graphql_query_sync_with_response():
    """Test sync query that inspects and returns the response object."""
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(data={"data": {"repository": {"name": "clientele", "stargazerCount": 100}}}),
    )

    @client.query("""
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                name
                stargazerCount
            }
        }
    """)
    def get_repo(owner: str, name: str, result: dict, response: Response) -> dict:
        # Can inspect the response object before returning
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        return result["data"]["repository"]

    repo = get_repo(owner="phalt", name="clientele")
    assert repo["name"] == "clientele"
    assert repo["stargazerCount"] == 100

    client.close()


@pytest.mark.asyncio
async def test_graphql_mutation_async_with_response():
    """Test async mutation that inspects and returns the response object."""
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(
            data={
                "data": {
                    "createRepository": {"repository": {"name": "new-repo", "url": "https://github.com/phalt/new-repo"}}
                }
            }
        ),
    )

    @client.mutation("""
        mutation($name: String!, $description: String!) {
            createRepository(input: {name: $name, description: $description}) {
                repository {
                    name
                    url
                }
            }
        }
    """)
    async def create_repo(name: str, description: str, result: dict, response: Response) -> dict:
        # Can inspect the response object before returning
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        return result["data"]["createRepository"]["repository"]

    repo = await create_repo(name="new-repo", description="A new repository")
    assert repo["name"] == "new-repo"
    assert repo["url"] == "https://github.com/phalt/new-repo"

    await client.aclose()


def test_graphql_query_with_optional_arguments():
    """Test query with optional (None-able) arguments."""
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    # Test with None value
    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(data={"data": {"repositories": [{"name": "repo1"}, {"name": "repo2"}]}}),
    )

    @client.query("""
        query($owner: String!, $language: String) {
            repositories(owner: $owner, language: $language) {
                name
            }
        }
    """)
    def search_repos(owner: str, language: str | None, result: dict) -> dict:
        return result["data"]["repositories"]

    # Call with None for optional parameter
    repos = search_repos(owner="phalt", language=None)
    assert len(repos) == 2
    assert repos[0]["name"] == "repo1"

    request = fake_backend.requests[0]
    # GraphQL best practice: None values should be omitted from variables
    assert request["kwargs"]["json"]["variables"] == {"owner": "phalt"}

    # Test with actual value
    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(data={"data": {"repositories": [{"name": "python-repo"}]}}),
    )

    repos = search_repos(owner="phalt", language="python")
    assert len(repos) == 1
    assert repos[0]["name"] == "python-repo"

    request = fake_backend.requests[1]
    assert request["kwargs"]["json"]["variables"] == {"owner": "phalt", "language": "python"}

    client.close()


@pytest.mark.asyncio
async def test_graphql_mutation_with_optional_arguments():
    """Test async mutation with optional (None-able) arguments."""
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(
            data={"data": {"createIssue": {"issue": {"id": "123", "title": "Bug report", "body": None}}}}
        ),
    )

    @client.mutation("""
        mutation($title: String!, $body: String) {
            createIssue(input: {title: $title, body: $body}) {
                issue {
                    id
                    title
                    body
                }
            }
        }
    """)
    async def create_issue(title: str, body: str | None, result: dict) -> dict:
        return result["data"]["createIssue"]["issue"]

    # Call with None for optional parameter
    issue = await create_issue(title="Bug report", body=None)
    assert issue["id"] == "123"
    assert issue["title"] == "Bug report"
    assert issue["body"] is None

    request = fake_backend.requests[0]
    # GraphQL best practice: None values should be omitted from variables
    assert request["kwargs"]["json"]["variables"] == {"title": "Bug report"}

    await client.aclose()


def test_graphql_query_with_pydantic_hydration():
    """Test that result is hydrated to Pydantic model when annotated."""
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(data={"data": {"repository": {"name": "clientele", "stargazerCount": 100}}}),
    )

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
    assert isinstance(repo, Repository)
    assert repo.name == "clientele"
    assert repo.stargazerCount == 100

    client.close()


@pytest.mark.asyncio
async def test_graphql_mutation_with_pydantic_hydration():
    """Test that async mutation result is hydrated to Pydantic model when annotated."""
    client = GraphQLClient(base_url="https://api.github.com/graphql")
    fake_backend = configure_client_for_testing(client)

    fake_backend.queue_response(
        path="",
        response_obj=ResponseFactory.ok(
            data={"data": {"createIssue": {"issue": {"id": "123", "title": "Bug report"}}}}
        ),
    )

    @client.mutation("""
        mutation($title: String!) {
            createIssue(input: {title: $title}) {
                issue {
                    id
                    title
                }
            }
        }
    """)
    async def create_issue(title: str, result: CreateIssueMutationResponse) -> Issue:
        return result.data.createIssue.issue

    issue = await create_issue(title="Bug report")
    assert isinstance(issue, Issue)
    assert issue.id == "123"
    assert issue.title == "Bug report"

    await client.aclose()
