#!/usr/bin/env python3

"""
Fixtures representing the DBTPipeline
"""

import pytest


@pytest.fixture(scope='session', name='test_dbt_pipeline')
def dbt_pipeline(test_secret, test_artifactory_package):
    from src.classes.pipeline import DBTPipeline
    secret = test_secret["secret"]
    secret_arn = secret["ARN"]
    test_config = {
        "DBT_PACKAGE_URL": test_artifactory_package["artifactory_package_url"],
        "DBT_PACKAGE_TYPE": "artifactory",
        "DBT_COMMAND": "dbt run --profiles-dir .",
        "DBT_PATH": test_artifactory_package["dbt_path"],
        "DBT_PASS_SECRET_ARN": secret_arn,
        "DBT_CUSTOM_SCHEMA_OVERRIDE": None,
        "KOTAHI_ID": None,
        "CLASSIFICATION": "C5",
        "DBT_CUSTOM_PROFILE": None,
        "AWS_REGION": "us-east-1",
        "DBT_DBNAME": None,
        "DBT_WH": None,
        "DBT_SCHEMA": None,
        "DBT_ROLE": None,
        "DBT_USER": "adeeb.rahman",
        "DBT_PASS": None,
        "DBT_PRIVATE_KEY": None,
        "DBT_TARGET": None,
        "REGISTER_ASSETS": None,
    }
    test_dbt_pipeline = DBTPipeline(test_config)
    yield test_dbt_pipeline
