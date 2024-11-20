from collections.abc import Iterable
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel, ValidationError


def iter_direct_subdirs(path: Path) -> Iterable[Path]:
    """
    Get an iterable of the direct subdirectories of a given path.

    :param path: The given path
    :return: The iterable of the direct subdirectories of the given path
    :raises: ValueError if the given path is not a directory
    """
    if not path.is_dir():
        raise ValueError(f"The given path is not a directory: {path}")
    return (p for p in path.iterdir() if p.is_dir())


# Note: this function is copied from the dandi/dandisets-linkml-status-tools repo
def pydantic_validate(data: Union[dict[str, Any], str], model: type[BaseModel]) -> str:
    """
    Validate the given data against a Pydantic model

    :param data: The data, as a dict or JSON string, to be validated
    :param model: The Pydantic model to validate the data against
    :return: A JSON string that specifies an array of errors encountered in
        the validation (The JSON string returned in a case of any validation failure
        is one returned by the Pydantic `ValidationError.json()` method. In the case
        of no validation error, the empty array JSON expression, `"[]"`, is returned.)
    """
    if isinstance(data, str):
        validate_method = model.model_validate_json
    else:
        validate_method = model.model_validate

    try:
        validate_method(data)
    except ValidationError as e:
        return e.json()

    return "[]"
