# clientele/graphql/client.py
from __future__ import annotations

import functools
import inspect
import typing

from clientele.api import APIClient, requests

_F = typing.TypeVar("_F", bound=typing.Callable[..., typing.Any])


class GraphQLClient(APIClient):
    """
    Specialized client for GraphQL APIs.
    """

    def query(
        self,
        query_string: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
    ) -> typing.Callable[[_F], _F]:
        """
        Decorator for GraphQL queries.

        Args:
            query_string: GraphQL query with variable placeholders
            response_map: Optional mapping of HTTP status codes to response models

        Example:
            ```python
            @client.query('''
                query($owner: String!, $name: String!) {
                    repository(owner: $owner, name: $name) {
                        name
                        stargazerCount
                    }
                }
            ''')
            def get_repo(owner: str, name: str, result: RepositoryData) -> Repository:
                return result.repository
            ```
        """
        return self._create_graphql_decorator("POST", query_string, response_map=response_map)

    def mutation(
        self,
        mutation_string: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
    ) -> typing.Callable[[_F], _F]:
        """
        Decorator for GraphQL mutations.

        Args:
            mutation_string: GraphQL mutation with variable placeholders
            response_map: Optional mapping of HTTP status codes to response models

        Example:
            ```python
            @client.mutation('''
                mutation($title: String!) {
                    createIssue(input: {title: $title}) {
                        issue { id title }
                    }
                }
            ''')
            def create_issue(title: str, result: IssueData) -> Issue:
                return result.createIssue.issue
            ```
        """
        return self._create_graphql_decorator("POST", mutation_string, response_map=response_map)

    def _create_graphql_decorator(
        self,
        method: str,
        graphql_string: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
    ) -> typing.Callable[[_F], _F]:
        """
        Create a GraphQL decorator using Clientele's existing decorator machinery.
        """

        def decorator(func: _F) -> _F:
            context = requests.build_request_context(
                method=method,
                path="",  # GraphQL uses a single endpoint
                func=func,
                response_map=response_map,
            )

            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                    return await self._execute_graphql_async(context, graphql_string, args, kwargs)

                async_wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
                return typing.cast(_F, async_wrapper)

            @functools.wraps(func)
            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                return self._execute_graphql_sync(context, graphql_string, args, kwargs)

            wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
            return typing.cast(_F, wrapper)

        return decorator

    def _execute_graphql_sync(
        self,
        context: requests.RequestContext,
        graphql_string: str,
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
    ) -> typing.Any:
        """Execute a synchronous GraphQL request."""
        variables = self._extract_variables(context, args, kwargs)

        payload = {
            "query": graphql_string,
            "variables": variables,
        }

        response = self._send_request(
            method=context.method,
            url=context.path_template,
            query_params=None,
            data_payload=payload,
            headers_override=kwargs.get("headers") if "headers" not in context.signature.parameters else None,
            response_map=context.response_map,
        )

        parsed_result = self._parse_response(
            response=response,
            annotation=context.type_hints.get("result", inspect._empty),
            response_map=context.response_map,
        )

        bound = context.signature.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        call_args = dict(bound.arguments)

        if "result" in context.signature.parameters:
            call_args["result"] = parsed_result
        if "response" in context.signature.parameters:
            call_args["response"] = response

        return context.func(**call_args)

    async def _execute_graphql_async(
        self,
        context: requests.RequestContext,
        graphql_string: str,
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
    ) -> typing.Any:
        """Execute an asynchronous GraphQL request."""
        variables = self._extract_variables(context, args, kwargs)

        payload = {
            "query": graphql_string,
            "variables": variables,
        }

        response = await self._send_request_async(
            method=context.method,
            url=context.path_template,
            query_params=None,
            data_payload=payload,
            headers_override=kwargs.get("headers") if "headers" not in context.signature.parameters else None,
            response_map=context.response_map,
        )

        parsed_result = self._parse_response(
            response=response,
            annotation=context.type_hints.get("result", inspect._empty),
            response_map=context.response_map,
        )

        bound = context.signature.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        call_args = dict(bound.arguments)

        if "result" in context.signature.parameters:
            call_args["result"] = parsed_result
        if "response" in context.signature.parameters:
            call_args["response"] = response

        return await context.func(**call_args)

    def _extract_variables(
        self,
        context: requests.RequestContext,
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        """
        Extract GraphQL variables from function arguments.

        Excludes 'result', and 'response' which are special parameters.
        Filters out None values to follow GraphQL best practices.
        """
        bound = context.signature.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        variables = {}
        for param_name, param_value in bound.arguments.items():
            if param_name not in ("result", "response", "self"):
                # Only include non-None values to follow GraphQL conventions
                if param_value is not None:
                    variables[param_name] = param_value

        return variables
