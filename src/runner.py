#!/usr/bin/python

""" Main DBT Runner app """

import os
from src.classes.logger import DBTLogger
from src.classes.pipeline import DBTPipeline

default_config = {
    "DBT_PACKAGE_URL": None,
    "DBT_PACKAGE_TYPE": None,
    "DBT_COMMAND": "dbt run",
    "DBT_PATH": "dbt",
    "DBT_PASS_SECRET_ARN": None,
    "DBT_CRED_TYPE": "password",
    "DBT_KEY_NAME": "private.key",
    "DBT_CUSTOM_SCHEMA_OVERRIDE": None,
    "DBT_CUSTOM_PROFILE": None,
    "AWS_REGION": "us-east-1",
    "DBT_DBNAME": None,
    "DBT_WH": None,
    "DBT_SCHEMA": None,
    "DBT_ROLE": None,
    "DBT_USER": None,
    "DBT_PASS": None,
    "DBT_PRIVATE_KEY": None,
    "DBT_TARGET": None,
    "REGISTER_ASSETS": None,
    "DBT_PACKAGE_BRANCH": None,
}

def read_env_vars() -> dict:
    """Read all supported container environment variables into the app"""

    runner_logger = DBTLogger()
    runner_logger.printlog("Reading environment variables...")
    config = default_config
    for key in config:
        try:
            if os.environ.get(f"{key}"):
                config[key] = os.environ.get(f"{key}")
            if key not in ["DBT_PASS"]:
                if config[key]:
                    runner_logger.printlog(f"{key} set to: {config[key]}")
        except KeyError:
            runner_logger.printlog(f"Environment variable not set: {key}")
    return config

def main() -> None:
    """ DBT Runner app main function """

    # Generate a config based on supported environment variables
    config = read_env_vars()

    # Create a DBT Pipeline object
    runner = DBTPipeline(config)

    # Fetch DBT pipeline code/package
    runner.get_dbt_code()

    # Get service account credentials
    runner.get_credentials()

    # Run the specified bash command
    runner.run_dbt_command()

if __name__ == "__main__":
    main()