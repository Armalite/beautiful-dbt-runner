#!/usr/bin/env python3

import os

import pytest


@pytest.mark.functional
def test_fetch_secret(test_dbt_pipeline, test_secret):
    """Tests obtaining credentials from a mock secretsmanager secret and
        ensuring the fetched SecretString and ARN match the mocked secret
    """
    if os.environ.get("DBT_PASS"):
        del os.environ["DBT_PASS"]

    expected_arn = test_secret["expected_arn"]
    expected_secretstring = test_secret["expected_secretstring"]
    secretresponse = test_dbt_pipeline.get_credentials()
    secretstring = secretresponse["SecretString"]
    arn = secretresponse["ARN"]
    assert arn == expected_arn
    assert secretstring == expected_secretstring


@pytest.mark.functional
def test_fetch_secret_and_store_creds(test_dbt_pipeline, test_secret):
    """Tests the setting of the dbt_pass private variable in the DBTPipeline Object
    as well as the DBT_PASS environment variable. Asserts check that these are being
    set correctly to the value of the SecretString that is set in the mock secret
    """

    if os.environ.get("DBT_PASS"):
        del os.environ["DBT_PASS"]

    expected_secretstring = test_secret["expected_secretstring"]
    test_dbt_pipeline.get_credentials()
    dbt_pass = test_dbt_pipeline.dbt_pass
    dbt_pass_env_var = os.environ.get("DBT_PASS")

    assert dbt_pass == expected_secretstring
    assert dbt_pass_env_var == expected_secretstring
