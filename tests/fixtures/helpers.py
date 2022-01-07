# pylint: disable=too-few-public-methods, invalid-name
"""
Helper functions
"""

import os.path
import tarfile


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
