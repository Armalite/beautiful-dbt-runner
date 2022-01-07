#!/usr/bin/env python3
# pylint: disable=too-many-public-methods, line-too-long, invalid-name, raise-missing-from, broad-except

""" Class representing a DBT pipeline object. This class contains all parameters and
control variables needed to prepare the DBT pipeline for execution """

import glob
import os
import shutil
import subprocess
import sys
import tarfile
from os import chmod

import boto3
import requests
from botocore.exceptions import ClientError

from src.classes.helpers import ChangeDir
from src.classes.logger import DBTLogger


class DBTPipeline:
    """
    Object representing a DBT Pipeline, which will run as part of a single container process.
    This class will contain all the variables necessary to run or test this pipeline
    """

    logger = None
    _package_path = "dbt_download"

    _env_vars = {}

    def get_dbt_artifactory(self) -> None:
        """Fetch the DBT package from Artifactory and unpackage it in the working directory"""
        self.logger.printlog(f"Fetching DBT package from Artifactory url: {self.dbt_package_url}")

        if self.dbt_package_url:

            try:
                # Fetch DBT package as a stream from Artifactory
                dbt_package = requests.get(self.dbt_package_url, stream=True)
            except requests.exceptions.Timeout as e:
                self.logger.printlog("ERROR: Request to fetch Artifactory package has timed out")
                raise SystemExit(e)
            except requests.exceptions.TooManyRedirects as e:
                self.logger.printlog("ERROR: Invalid Artifactory URL provided")
                raise SystemExit(e)
            except requests.exceptions.RequestException as e:
                self.logger.printlog("ERROR: Could not fetch Artifactory package")
                raise SystemExit(e)

            # Write the fetched package stream in chunks
            try:
                with open('dbt.tar.gz', 'wb') as f:
                    for chunk in dbt_package.iter_content(32 * 1024):
                        f.write(chunk)
            except Exception as e:
                self.logger.printlog(f"ERROR: Failed to save downloaded DBT Package: {e}")

            try:
                if os.stat('dbt.tar.gz').st_size > 0:
                    # Extract DBT package
                    with tarfile.open("dbt.tar.gz") as dbttar:
                        dbttar.extractall(f"{self.package_path}")
                        dbttar.close()
                        os.remove("dbt.tar.gz")
                        self.dbt_path = f"{self.package_path}/{self.dbt_path}"
                        self.logger.printlog(f"DBT project extracted from Artifactory package into {self.dbt_path}")
                else:
                    print("Artefact has no content")
            except Exception as e:
                self.logger.printlog(f"ERROR: Failed to extract contents of the tar.gz DBT package: {e}")
        else:
            self.logger.printlog(
                "Error: DBT_PACKAGE_TYPE set to 'artifactory' but artifactory URL not set in DBT_PACKAGE_URL")

    def get_dbt_s3(self) -> None:
        """Fetch DBT Package from S3"""
        self.logger.printlog(f"Fetching DBT package from S3 url: {self.dbt_package_url}")

    def get_dbt_github(self, branch: str) -> None:
        """Fetch DBT project from Github"""
        self.logger.printlog(f"Fetching DBT package from Github branch {branch} in repostiroy: {self.dbt_package_url}")

    def get_dbt_code(self) -> None:
        """Fetch DBT package based on the package type"""
        # Choose package fetch function based on package type (currently only Artifactory support)
        if self.dbt_package_type == "artifactory" and (self.dbt_package_url):
            self.get_dbt_artifactory()
        elif self.dbt_package_type == "s3" and (self.dbt_package_url):
            self.get_dbt_s3()
        elif self.dbt_package_type == "github" and (self.dbt_package_url) and (self.dbt_package_branch):
            self.get_dbt_s3(self.dbt_package_branch)
        else:
            self.logger.printlog(f"No DBT package type or URL specified. Assuming locally mounted in {self.dbt_path}/")

    def get_credentials(self) -> dict:
        """Obtain the service account credentials from AWS Secrets manager
        using the secret_arn provided. If DBT_PASS environment variable
        has been set, the secrets fetching step is ignored """

        if os.environ.get("DBT_PASS"):
            self.logger.printlog("""DBT_PASS already set. Skipping fetching secrets step""")
        else:
            if self.dbt_pass_secret_arn is None:
                self.logger.printlog("Either (DBT_PASS) or (DBT_PASS_SECRET_ARN) environment variables must be set")
                sys.exit(1)

            try:
                secretclient = boto3.client("secretsmanager", region_name=f"{self.aws_region}")
                password_val = secretclient.get_secret_value(
                    SecretId=f'{self.dbt_pass_secret_arn}'
                )
                self.dbt_pass = password_val["SecretString"]
                os.environ["DBT_USER"] = self.dbt_user
                os.environ["DBT_PASS"] = self.dbt_pass
                self.logger.printlog("Credentials obtained.")
                return password_val
            except ClientError as err:
                if err.response["Error"]["Code"] == "AccessDeniedException":
                    self.logger.printlog(f"Access Denied to Secrets Manager secrets: {self.dbt_pass_secret_arn}")
                else:
                    self.logger.printlog(f"Unexpected error: {err}")

    def run_dbt_command(self) -> None:
        """Run the specified DBT/shell command"""

        # Magically grant full access to the shell script(s) within the dbt folder
        try:
            for file in glob.glob(f'{self.dbt_path}/*.sh'):
                if file.endswith(".sh"):
                    chmod(file, 777)
        except FileNotFoundError as err:
            self.logger.printlog(
                f"Target dbt project folder not found. Please ensure DBT_PATH is set to the name of the project folder. Error: {err}")

        # Switch directory context to dbt folder and run the provided shell command/script
        try:
            with ChangeDir(f"{self.dbt_path}"):
                self.logger.printlog(f"Running DBT command: {self.dbt_command}")
                subprocess.call([f"{self.dbt_command}"], shell=True)
        except FileNotFoundError as err:
            self.logger.printlog(
                f"Target dbt project folder not found. Please ensure DBT_PATH is set to the name of the project folder. Error: {err}")

    def add_beautiful_dbt_macros(self) -> None:
        """Add custom DBT Macros to the DBT project folder"""
        if self.register_assets:
            self.logger.printlog(f"Adding custom DBT macros to the DBT Project folder {self.dbt_path}/")
            src = f"{os.getcwd()}/macros/"
            dest = f"{self.dbt_path}/macros/"
            src_files = os.listdir(src)
            try:
                for file_name in src_files:
                    full_file_name = os.path.join(src, file_name)
                    if os.path.isfile(full_file_name):
                        shutil.copy(full_file_name, dest)
            except FileNotFoundError as err:
                self.logger.printlog(f"Target dbt project folder not found to copy macros to. Error: {err}")
        else:
            self.logger.printlog("Asset registration disabled")

    @property
    def env_vars(self) -> dict:
        """Get the environment variable list"""
        return self._env_vars

    @env_vars.setter
    def env_vars(self, config: dict) -> None:
        """Get the environment variable list"""
        self._env_vars = config

    @property
    def dbt_package_url(self) -> str:
        """Get the DBT project folder URL"""
        return self._env_vars["DBT_PACKAGE_URL"]

    @dbt_package_url.setter
    def dbt_package_url(self, value: str) -> None:
        """Set the DBT project folder URL"""
        self._env_vars["DBT_PACKAGE_URL"] = value

    @property
    def dbt_package_type(self) -> str:
        """Get the DBT project folder URL type"""
        return self._env_vars["DBT_PACKAGE_TYPE"]

    @dbt_package_type.setter
    def dbt_package_type(self, value: str) -> None:
        """Set the DBT project folder URL type"""
        self._env_vars["DBT_PACKAGE_TYPE"] = value

    @property
    def dbt_command(self) -> str:
        """Get the bash command that will be executed to
        run the DBT pipeline"""
        return self._env_vars["DBT_COMMAND"]

    @dbt_command.setter
    def dbt_command(self, value: str) -> None:
        """Set the bash command that will be executed to
        run the DBT pipeline"""
        self._env_vars["DBT_PACKAGE_TYPE"] = value

    @property
    def dbt_path(self) -> str:
        """Get the DBT project folder location"""
        return self._env_vars["DBT_PATH"]

    @dbt_path.setter
    def dbt_path(self, value: str) -> None:
        """Set the DBT project folder location"""
        self._env_vars["DBT_PATH"] = value

    @property
    def dbt_user_secret_id(self) -> str:
        """Get the name of the AWS secret containing username of service account"""
        return self._env_vars["DBT_USER_SECRET_ID"]

    @dbt_user_secret_id.setter
    def dbt_user_secret_id(self, value: str) -> None:
        """Set the name of the AWS secret containing username of service account"""
        self._env_vars["DBT_USER_SECRET_ID"] = value

    @property
    def dbt_pass_secret_arn(self) -> str:
        """Get name of the AWS secret containing password of service account """
        return self._env_vars["DBT_PASS_SECRET_ARN"]

    @dbt_pass_secret_arn.setter
    def dbt_pass_secret_arn(self, value: str) -> None:
        """Set ARN of the AWS secret containing password of service account"""
        self._env_vars["DBT_PASS_SECRET_ARN"] = value

    @property
    def dbt_dbname(self) -> str:
        """Get the name of the Snowflake Database DBT will use as a target"""
        return self._env_vars["DBT_DBNAME"]

    @dbt_dbname.setter
    def dbt_dbname(self, value: str) -> None:
        """Set the name of the Snowflake Database DBT will use as a target"""
        self._env_vars["DBT_DBNAME"] = value

    @property
    def dbt_wh(self) -> str:
        """Get the name of the Snowfake Warehouse to be used"""
        return self._env_vars["DBT_WH"]

    @dbt_wh.setter
    def dbt_wh(self, value: str) -> None:
        """Set the name of the Snowfake Warehouse to be used"""
        self._env_vars["DBT_WH"] = value

    @property
    def dbt_schema(self) -> str:
        """Get the DBT default schema to be used"""
        return self._env_vars["DBT_SCHEMA"]

    @dbt_schema.setter
    def dbt_schema(self, value: str) -> None:
        """Set the DBT default schema to be used"""
        self._env_vars["DBT_SCHEMA"] = value

    @property
    def dbt_role(self) -> str:
        """Get the name of the Snowflake Role dbt will use"""
        return self._env_vars["DBT_ROLE"]

    @dbt_role.setter
    def dbt_role(self, value: str) -> None:
        """Set the name of the Snowflake Role dbt will use"""
        self._env_vars["DBT_ROLE"] = value

    @property
    def dbt_custom_schema_override(self) -> str:
        """Get the name custom schema override flag that indicates whether custom
        schemas should no longer be concatenated to the default DBT Schema"""
        return self._env_vars["DBT_CUSTOM_SCHEMA_OVERRIDE"]

    @dbt_custom_schema_override.setter
    def dbt_custom_schema_override(self, value: str) -> None:
        """Set the name custom schema override flag to indicate whether custom
        schemas should no longer be concatenated to the default DBT Schema"""
        self._env_vars["DBT_CUSTOM_SCHEMA_OVERRIDE"] = value

    @property
    def kotahi_id(self) -> str:
        """Get the Kotahi ID of the product this pipeline belongs to"""
        return self._env_vars["KOTAHI_ID"]

    @kotahi_id.setter
    def kotahi_id(self, value: str) -> None:
        """Set the Kotahi ID of the product this pipeline belongs to"""
        self._env_vars["KOTAHI_ID"] = value

    @property
    def classification(self) -> str:
        """Get the default Data Classification for this pipeline"""
        return self._env_vars["CLASSIFICATION"]

    @classification.setter
    def classification(self, value: str) -> None:
        """Set the default Data Classification for this pipeline"""
        self._env_vars["CLASSIFICATION"] = value

    @property
    def aws_region(self) -> str:
        """Get the AWS region"""
        return self._env_vars["AWS_REGION"]

    @aws_region.setter
    def aws_region(self, value: str) -> None:
        """Set the AWS region"""
        self._env_vars["AWS_REGION"] = value

    @property
    def dbt_user(self) -> str:
        """Get the DBT username of service account"""
        return self._env_vars["DBT_USER"]

    @dbt_user.setter
    def dbt_user(self, value: str) -> None:
        """Set the DBT username of service account"""
        self._env_vars["DBT_USER"] = value

    @property
    def dbt_pass(self) -> str:
        """Get the DBT password of service account"""
        return self._env_vars["DBT_PASS"]

    @dbt_pass.setter
    def dbt_pass(self, value: str) -> None:
        """Set the DBT password of service account"""
        self._env_vars["DBT_PASS"] = value

    @property
    def register_assets(self) -> str:
        """Get the value of REGSISTER_ASSETS flag"""
        return self._env_vars["REGISTER_ASSETS"]

    @register_assets.setter
    def register_assets(self, value: str) -> None:
        """Set the value of REGISTER_ASSETS flag"""
        self._env_vars["REGISTER_ASSETS"] = value

    @property
    def dbt_package_branch(self) -> str:
        """Get the value of DBT_PACKAGE_BRANCH flag"""
        return self._env_vars["DBT_PACKAGE_BRANCH"]

    @dbt_package_branch.setter
    def dbt_package_branch(self, value: str) -> None:
        """Set the value of DBT_PACKAGE_BRANCH flag"""
        self._env_vars["DBT_PACKAGE_BRANCH"] = value

    @property
    def package_path(self) -> str:
        """Get the parent path where downloaded packages will be extracted"""
        return self._package_path

    def __init__(
        self,
        config: dict
    ):
        self.logger = DBTLogger()
        self.logger.printlog("DBT Pipeline process started")
        self.env_vars = config
