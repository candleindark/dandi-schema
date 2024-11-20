from collections.abc import Iterable
from pathlib import Path


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
