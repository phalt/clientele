from httpx import Client, Response

client = Client()


def _get(url: str) -> Response:
    client.get(url)
