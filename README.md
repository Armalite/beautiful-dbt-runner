WARNING: This repository and instructions are a work in progress and may not operate 100%

# Beautiful DBT Runner
This repository contains the Beautiful DBT Runner application source code, which can run a DBT pipeline project that has been packaged and stored in Artifactory. The application runs within a container and this repository generates the Beautiful Managed DBT Image that contains this application. Teams that wish to execute DBT pipelines on Beautiful should use this image to execute their dbt pipelines. The container runtime accepts a set of parameters to allow Snowflake connectivity and fetching the DBT package from Artifactory. This is in line with the example architecture outlined for the Beautiful Batch Transform service

# Beautiful DBT Runner - Image Location
The Beautiful DBT Runner image will be located in the following repository: <TBD>


# DBT Runner Container Usage
The DBT Runner container operates based on environment variables being passed into it. This can be done within any container runtime, such as using `docker run` or within a Kubernetes deployment that passes in environment variables. To get an idea of how environment variables can be used, you can view the Makefile local development targets that perform some 'dummy' runs of the container. There are multiple targets, each starting the container with a different set of environment variables that gets handled in different ways e.g. One target pulls a dummy dbt project package from Artifactory, unpackages and then attempts to run it. Another target does not specify an artifactory url, so the DBT runner assumes that you have mounted or 'baked' your dbt project onto the container.

## Dummy DBT Project mounted into Container
This test run of the DBT runner mounts a local dbt project folder directly into the container at runtime. The local dbt project available in this repo is in the dbt_tester folder.
 1. Run `make run-dbt-mounted`
 2. View the Makefile to see what environment variables are passed into the container at runtime

# Local App Usage (Containerless)
There is a test dbt project located in this repo in the dbt_tester folder. You can run the DBT Runner application outside of a docker container by specifying the path to this dbt_tester folder in your local DBT_PATH environment variable. You will also need to update the profiles.yml file in the dbt_tester folder to include your credentials. The dev target in this profiles.yml file is structured for web browser auth.

 1. To set the dbt path to the test dbt folder: `export DBT_PATH=dbt_tester`
 2. To set dbt target to dev, so that it uses web browser auth: `export DBT_TARGET=dev`
 3. To run the DBT Runner app locally: `python3 -m src.runner`

# CONTRIBUTING
## Local Development
For local development, please fork or create a branch named feature/<issue_number>_short_description

To setup your local development environment:
 1. Clone repo and checkout your feature branch
 2. In your terminal run `make install` to set up the venv and git commit hooks
 3. Grab a coffee
 4. Write some awesome code

## Running Tests
You can run the available pytests using make targets.
 1. To run all tests run `make test`
 2. To run functional tests only `make test-functional`
 3. View the Makefile for additional test targets

