SHELL=/bin/bash -e -o pipefail
bold := $(shell tput bold)
sgr0 := $(shell tput sgr0)

.PHONY: help install check lint pyright test hooks install-hooks
.SILENT:

deployer_image_name = "beautiful-dbt-runner-deployer"
output_location = "output"
tf_root = "terraform"
tf_bucket = "beautiful-$(env)-$(aws_region)-terraform"
tf_key = "dbt-runner/terraform-dbt-runner.tfstate"
dbt_tester_artifactory_url = ""
dbt_tester_artifactory_user = "beautiful_dbt_runner_deployer"
dbt_tester_package_name = "beautiful-data-vault-test"
dbt_runner_image:="dbt-runner:latest"

MAKEFLAGS += --warn-undefined-variables
.DEFAULT_GOAL := help

## display help message
help:
	@awk '/^##.*$$/,/^[~\/\.0-9a-zA-Z_-]+:/' $(MAKEFILE_LIST) | awk '!(NR%2){print $$0p}{p=$$0}' | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

venv = .venv
pip := $(venv)/bin/pip

$(pip):
	# create empty virtualenv containing pip
	$(if $(value VIRTUAL_ENV),$(error Cannot create a virtualenv when running in a virtualenv. Please deactivate the current virtual env $(VIRTUAL_ENV)),)
	python3 -m venv --clear $(venv)
	cp pip.conf $(venv)
	$(pip) install pip==21.3.1 setuptools==58.5.3 wheel==0.37.0

$(venv): setup.py $(pip)
	$(pip) install -e '.[dev]'
	touch $(venv)

# delete the venv
clean:
	rm -rf $(venv)

## create venv and install this package and hooks
install: $(venv) node_modules $(if $(value CI),,install-hooks)

node_modules: package.json
	npm install --no-save
	touch node_modules

## format all code
format: $(venv)
	$(venv)/bin/autopep8 --in-place .
	$(venv)/bin/isort .

## pyright type check
pyright: node_modules $(venv)
# activate venv so pyright can find dependencies
	PATH="$(venv)/bin:$$PATH" node_modules/.bin/pyright

## run pre-commit git hooks on all files
hooks: $(venv)
	$(venv)/bin/pre-commit run --show-diff-on-failure --color=always --all-files --hook-stage push

## lint using flake8
lint: $(venv)
	$(venv)/bin/flake8

## lint and type check
check: lint pyright


install-hooks: .git/hooks/pre-commit .git/hooks/pre-push

.git/hooks/pre-commit: $(venv)
	$(venv)/bin/pre-commit install -t pre-commit

.git/hooks/pre-push: $(venv)
	$(venv)/bin/pre-commit install -t pre-push

###############################################################################
# Local Development Targets
#
###############################################################################

dev-publish-dbt-package:
	$(eval pkgtag=$(shell date +%s))
	$(eval pkgurl=$(dbt_tester_artifactory_url)/beautiful-data-vault-test-$(pkgtag))
	./scripts/tar_my_dbt.sh -c . -s dbt_tester
	curl -u $(dbt_tester_artifactory_user):${ARTI_PASS} -T dbt_tester.tar.gz $(pkgurl)
	echo "DBT Package published to $(pkgurl)"

build-dbt-runner-image:
	docker build -t dbt-runner:latest .

# This example fetches dbt package from artifactory and passes in several parameters (uses profiles.yml provided by the image)
run-dbt-artifactory:
	$(eval pwd:=$(shell pwd))
	docker run -it \
			-v $(pwd)/src:/src  \
			-v $(pwd)/dbt_download:/dbt_download \
			-e DBT_USER	\
			-e DBT_PASS	\
			-e DBT_PATH="dbt_tester"	\
			-e DBT_COMMAND="./run_dbt.sh"	\
			-e DBT_PACKAGE_TYPE="artifactory"	\
			-e DBT_PACKAGE_URL="" \
			dbt-runner:latest	\
			$(SHELL)

# This example fetches dbt package from artifactory, uses custom profiles.yml and fetches password secret
run-dbt-artifactory-sa:
	$(eval pwd:=$(shell pwd))
	docker run -it \
			-v $(pwd)/src:/src	\
			-e DBT_PASS_SECRET_ARN="" 	\
			-e DBT_COMMAND="dbt run --profiles-dir ."	\
			-e DBT_PACKAGE_TYPE="artifactory"	\
			-e DBT_PACKAGE_URL="" \
			dbt-runner:latest \
			$(SHELL)

# This example mounts the local dbt project (dbt_tester) into the container under dbt/
run-dbt-mounted:
	$(eval pwd:=$(shell pwd))
	docker run -it \
			-p 443:443 \
			-v $(pwd)/src:/src \
			-v $(pwd)/dbt_tester:/dbt_tester \
			-e DBT_PATH="dbt_tester" \
			-e DBT_TARGET="dev" \
			-e DBT_COMMAND="dbt deps --profiles-dir . && dbt compile --profiles-dir ."	\
			dbt-runner:latest	\
			$(SHELL)

# This kicks off a Make test by mounting the entire repo in the container
test-container-mounted: build-dbt-runner-image
	$(eval pwd:=$(shell pwd))
	docker run --rm -it \
			-v $(pwd):/runner \
			-w /runner \
			-e ARTI_PASS \
			--entrypoint "make" \
			$(dbt_runner_image)	\
			test

# This kicks off a Make test using the app that is installed in the container image (see Dockerfile)
test-container: build-dbt-runner-image
	$(eval pwd:=$(shell pwd))
	docker run --rm -it \
			-e ARTI_PASS \
			--entrypoint "make" \
			$(dbt_runner_image)	\
			test

###############################################################################
# Deployment targets
#
###############################################################################
build-deployer-image: **/* #
	echo "$(bold)=== Building Docker Image ===$(sgr0)"
	@docker build -t beautiful_dbt_runner_deployer:latest .

publish-docker-images: build-deployer-image
	echo "$(artifactory_password)" | docker login -u beautiful_dbt_runner_deployer --password-stdin beautiful-dbt-runner-deployer-docker-common.artifactory.beautiful-repo.com
	docker tag beautiful_dbt_runner_deployer beautiful-dbt-runner-deployer-docker-common.artifactory.beautiful-repo.com/beautiful_dbt_runner_deployer:"$(tag)"
	docker push beautiful-dbt-runner-deployer-docker-common.artifactory.beautiful-repo.com/beautiful_dbt_runner_deployer:"$(tag)"
	docker logout

###############################################################################
# Tests
#
###############################################################################
test: test-functional
	echo "$(bold)=== Run all tests ===$(sgr0)"

unit-tests:
	echo "$(bold)=== Running unit tests ===$(sgr0)"
	#pytest --capture=no --doctest-modules -m unit --user=$(user) --password=$(password) --account=$(account) --prefix=$(prefix) --environment=$(env) tests/

test-functional:
	echo "$(bold)=== Running functional tests ===$(sgr0)"
	pytest --capture=tee-sys --doctest-modules -m functional tests/

end-to-end-tests:
	echo "$(bold)=== Running end-to-end tests ===$(sgr0)"
	#pytest --capture=no --doctest-modules -m end_to_end --user=$(user) --password=$(password) --account=$(account) --prefix=$(prefix) --environment=$(env) tests/

pre-deployment-tests:
	echo "$(bold)=== Running pre-deployment tests ===$(sgr0)"
	#pytest --capture=no --doctest-modules -m pre_deployment --user=$(user) --password=$(password) --account=$(account) --prefix=$(prefix) --environment=$(env) tests/

post-deployment-tests:
	echo "$(bold)=== Running post-deployment tests ===$(sgr0)"
	#pytest --capture=no --doctest-modules -m post_deployment --user=$(user) --password=$(password) --account=$(account) --prefix=$(prefix) --environment=$(env) tests/
