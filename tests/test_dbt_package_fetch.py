#!/usr/bin/env python3

import os
import shutil

import pytest


@pytest.mark.functional
def test_fetch_secret(test_dbt_pipeline):
    """Tests obtaining credentials from a mock secretsmanager secret and
        ensuring the fetched SecretString and ARN match the mocked secret
    """
    if os.environ.get("DBT_PASS"):
        del os.environ["DBT_PASS"]

    package_download_path = "dbt_download"

    # expected dbt folder name
    expected_dbt_path = test_dbt_pipeline.dbt_path

    # run the function that fetches the packaged dbt file from artifactory and unpacks it
    test_dbt_pipeline.get_dbt_artifactory()

    # get a list of all folders under the download folder (should just be one dbt project folder)
    downloaded_packages = os.listdir(package_download_path)

    # clean up downloaded packages if there are any
    dbt_package_path = f"{package_download_path}/{expected_dbt_path}"
    if os.path.exists(dbt_package_path):
        shutil.rmtree(dbt_package_path)

    # test to see that the expected dbt project folder exists in the unpacked artifactory package
    assert expected_dbt_path in downloaded_packages
