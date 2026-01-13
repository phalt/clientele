from io import StringIO
from pathlib import Path

import pytest
from mypy.__main__ import main as mypy_main
from pydantic import BaseModel

from clientele.api import APIClient


class CreateUserRequest(BaseModel):
    name: str


class User(BaseModel):
    id: int
    name: str


FILE = Path(__file__).absolute()
PWD = FILE.parent.absolute()

client = APIClient(base_url="http://example.com")


@client.post("/users")
def create_user(data: CreateUserRequest, result: User) -> User:
    return result


def example_usage_with_pydantic_model() -> None:
    user = create_user(data=CreateUserRequest(name="Charlie"))
    assert user.name == "Charlie"


def example_usage_with_dict() -> None:
    user = create_user(data={"name": "Charlie"})
    assert user.name == "Charlie"


def example_usage_with_errors() -> None:
    user = create_user(data={"name": "Charlie"}, non_existent_param="value")
    assert user.non_existent_attribute == "Charlie"


def test_mypy_plugin() -> None:
    print(FILE)
    stdout = StringIO()
    stderr = StringIO()
    with pytest.raises(SystemExit):
        mypy_main(
            args=["--config-file", f"{PWD}/mypy_plugin_test_config.ini", str(FILE)],
            clean_exit=True,
            stdout=stdout,
            stderr=stderr,
        )
    # no errors on mypy execution (not check results)
    assert stderr.getvalue().strip() == ""

    mypy_output = stdout.getvalue()
    # check for expected errors but nothing else
    assert 'error: Unexpected keyword argument "non_existent_param" for "create_user"' in mypy_output
    assert 'error: "User" has no attribute "non_existent_attribute' in mypy_output
    assert "Found 2 errors in 1 file (checked 1 source file)" in mypy_output
