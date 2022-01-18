import functools
from unittest.mock import patch

from velo_action.octopus.client import OctopusClient


def mock_client_requests(registered_responses: list = None):
    """
    Decorator for mocking requests against the Octopus server

    Usage:
    @mock_client_requests(list_of_requests)

    Where list_of_requests consists of (method, path, response_body)

    Example:
    @mock_client_requests(["get", "api/project/Project-123", {"ID: Project-123"}])
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if callable(registered_responses):
                # Decorator used without arguments
                responses = []
            else:
                # Local copy to prevent side effects
                responses = list(registered_responses)

            def perform_request(_self, method, path, _data=None):
                nonlocal responses
                for i, req in enumerate(responses):
                    if req[0] == method and req[1] == path:
                        responses.pop(i)
                        return req[2]
                raise RuntimeError(
                    f"No request found for '{method}' '{path}'. \""
                    f'Add it to @mock_client_requests([]):\n("{method}", "{path}", {{}}),'
                )

            with patch.object(
                target=OctopusClient, attribute="_request", new=perform_request
            ):
                result = func(*args, **kwargs)

            if responses:
                raise RuntimeError(
                    f"Not all client responses have been used. Remaining: {responses}"
                )

            return result

        return wrapper

    if callable(registered_responses):
        return decorator(registered_responses)
    else:
        return decorator
