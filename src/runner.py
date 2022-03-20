#!/usr/bin/python

""" Main DBT Runner app """

import os

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
    "GITHUB_ACCESS_TOKEN": None,
}


def read_env_vars() -> dict:
    """Read all supported container environment variables into the app"""
    runner_logger = DBTLogger()
    runner_logger.printlog("[Beautiful DBT Runner] Reading environment variables...")
    config = default_config

    for key in config:
        try:
            if os.environ.get(f"{key}"):
                config[key] = os.environ.get(f"{key}")
            if key not in ["DBT_PASS"]:
                if config[key]:
                    runner_logger.printlog(f"[Beautiful DBT Runner] {key} set to: {config[key]}")
        except KeyError:
            runner_logger.printlog(f"[Beautiful DBT Runner] Environment variable not set: {key}")

    return config


def main() -> None:
    """ DBT Runner app main function """
    # Initialize the pipeline object

    config = read_env_vars()

    runner = DBTPipeline(config)

    # Fetch DBT pipeline code/package
    runner.get_dbt_code()

    # Get service account credentials
    # self.get_credentials()

    # Add required custom macros to DBT project
    # runner.add_custom_macros()

    # Run the specified bash command
    runner.run_dbt_command()

    # Output the DBT logs
    # runner.output_dbt_logs()

    # Clean up all packages
    #runner.cleanup_packages()


if __name__ == "__main__":
    main()
