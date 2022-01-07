""" Helper classes to be used by the DBT Runner Application """

import os


class ChangeDir:
    """Context manager for changing the current working directory"""

    saved_path = None
    new_path = None

    def __init__(self, new_path: str) -> None:
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self) -> None:
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype: str, value: str, traceback: str) -> None:
        os.chdir(self.saved_path)
