import os
import sys
from typing import Generator, Iterator

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


@pytest.fixture
def clear_dandischema_modules_and_set_env_vars(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """
    This fixture clears all `dandischema` modules from `sys.modules` and sets
    environment variables for configuring `config.CONFIG` which configures the
    `dandischema` modules.

    With this fixture, tests can import `dandischema` modules cleanly in an environment
    defined by the provided values for the environment variables.

    This fixture expects values for the environment variables to be passed indirectly
    from the calling test function using `request.param`. `request.param` should be a
    dictionary containing the following keys for setting environment variables of
    the same respective names in upper case and prefixed with "DANDI_SCHEMA_".
        `"id_pattern"`
        `"dandi_schema_datacite_doi_id_pattern"`

    Example usage:
    ```python
    @pytest.mark.parametrize(
        "clear_dandischema_modules_and_set_env_vars",
        [
            {
                "id_pattern": "DANDI",
                "dandi_schema_datacite_doi_id_pattern": "48324",
            },
            {
                "id_pattern": "EMBER",
                "dandi_schema_datacite_doi_id_pattern": "60533",
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
    params = ["id_pattern", "dandi_schema_datacite_doi_id_pattern"]
    modules = sys.modules
    modules_original = modules.copy()

    # Remove all dandischema modules from sys.modules
    for name in list(modules):
        if name.startswith("dandischema.") or name == "dandischema":
            del modules[name]

    # Monkey patch environment variables to configure `config.CONFIG`
    for param in params:
        monkeypatch.setenv(f"DANDI_SCHEMA_{param.upper()}", request.param[param])

    yield

    # Restore the original modules
    for name in list(modules):
        if name not in modules_original:
            del modules[name]
    modules.update(modules_original)
