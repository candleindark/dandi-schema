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
    """
    modules = sys.modules
    modules_original = modules.copy()

    # Remove all dandischema modules from sys.modules
    for name in modules:
        if name.startswith("dandischema.") or name == "dandischema":
            del modules[name]

    # Monkey patch environment variables to configure `config.CONFIG`
    monkeypatch.setenv("DANDI_SCHEMA_ID_PATTERN", request.param["id_pattern"])
    monkeypatch.setenv(
        "DANDI_SCHEMA_DATACITE_DOI_ID_PATTERN",
        request.param["dandi_schema_datacite_doi_id_pattern"],
    )

    yield

    # Restore the original modules
    for name in modules:
        if name not in modules_original:
            del modules[name]
    modules.update(modules_original)
