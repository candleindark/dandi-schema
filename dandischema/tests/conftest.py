import os
import sys
from typing import Generator, Iterator

from pydantic import TypeAdapter, ValidationError
import pytest


@pytest.fixture(scope="session", autouse=True)
def disable_http() -> Iterator[None]:
    if os.environ.get("DANDI_TESTS_NONETWORK"):
        with pytest.MonkeyPatch().context() as m:
            m.setenv("http_proxy", "http://127.0.0.1:9/")
            m.setenv("https_proxy", "http://127.0.0.1:9/")
            yield
    else:
        yield


_ENV_DICT_ADAPTER = TypeAdapter(dict[str, str])


@pytest.fixture
def clear_dandischema_modules_and_set_env_vars(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """
    This fixture clears all `dandischema` modules from `sys.modules` and sets
    environment variables.

    With this fixture, tests can import `dandischema` modules cleanly in an environment
    defined by the provided values for the environment variables.

    This fixture expects values for the environment variables to be passed indirectly
    from the calling test function using `request.param`. `request.param` should be a
    `dict[str, str]`. Each value in the dictionary will be used to set an environment
    variable with the name that is the same as its key but in upper case and prefixed
    with "DANDI_SCHEMA_".

    Example usage:
    ```python
    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [
            {
                "id_pattern": "DANDI",
                "datacite_doi_id_pattern": r"(48324|80507)",
            },
            {
                "id_pattern": "EMBER",
                "datacite_doi_id_pattern": r"(60533|82754)",
            }
        ],
        indirect=True,
    )
    def test_foo(clear_dandischema_modules_and_set_env_vars):
        # Your test code here
        ...
    ```

    Note
    ----
    When this fixture is torn down, it restores the original `sys.modules` and undo
    the environment variable changes made.

    The user of this fixture needs to ensure that no other threads besides a calling
    thread of this fixture are modifying `sys.modules` during the execution of this
    fixture, which should be a common situation.
    """
    # Check if the calling test has passed valid `indirect` arguments
    ev = ValueError(
        "The calling test must use the `indirect` parameter to pass "
        "a `dict[str, str]` for setting environment variables."
    )
    if not hasattr(request, "param"):
        raise ev
    try:
        _ENV_DICT_ADAPTER.validate_python(request.param, strict=True)
    except ValidationError as e:
        raise ev from e

    modules = sys.modules
    modules_original = modules.copy()

    # Remove all dandischema modules from sys.modules
    for name in list(modules):
        if name.startswith("dandischema.") or name == "dandischema":
            del modules[name]

    # Monkey patch environment variables with arguments from the calling test
    for k, v in request.param.items():
        monkeypatch.setenv(f"DANDI_SCHEMA_{k.upper()}", v)

    yield

    # Restore the original modules
    for name in list(modules):
        if name not in modules_original:
            del modules[name]
    modules.update(modules_original)
