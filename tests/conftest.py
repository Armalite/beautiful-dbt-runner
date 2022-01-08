#!/usr/bin/env python3

"""
Fixtures for all the tests
"""

pytest_plugins = [
    "tests.fixtures.aws_mock_fixtures",
    "tests.fixtures.dbt_pipeline_fixtures",
]
