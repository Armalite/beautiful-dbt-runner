#!/usr/bin/env python3

"""
Fixtures representing the DBT project packaged in Artifactory
"""

import os
import time

import pytest
import requests

from tests.fixtures.helpers import make_tarfile


@pytest.fixture(scope='session', name='test_artifactory_package')
def generate_test_artifactory_package():

    epoch_time = int(time.time())
    arti_pass = os.environ.get("ARTI_PASS")
    dbt_path = "dbt_tester"
    dbt_tester_package_path = "tests/fixtures/data/dbt_tester.tar.gz"
    make_tarfile(dbt_tester_package_path, "tests/fixtures/data/dbt_tester")
    arti_package_url = f"https://artifactory.beautiful-repo.com/dbt-test-generic-common/beautiful-data-vault-test-{epoch_time}"
    tar_data = open("tests/fixtures/data/dbt_tester.tar.gz", 'rb')
    if os.environ.get("ARTI_PASS"):
        requests.put(arti_package_url,
                                data=tar_data,
                                auth=('beautiful_dbt_runner_deployer', arti_pass),
                     )

        artifactory_package = {
            "artifactory_package_url": arti_package_url,
            "artifactory_package_binary": tar_data,
            "dbt_path": dbt_path,
        }
        tar_data.close()
        yield artifactory_package

        if os.path.exists(dbt_tester_package_path):
            os.remove(dbt_tester_package_path)
        else:
            print("Can not delete the file as it doesn't exists")
    else:
        print("[ERROR] - Artifactory test fixture - Must set env var ARTI_PASS with your Artifactory password")
