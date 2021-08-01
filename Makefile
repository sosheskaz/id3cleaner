PYTHON_INTERPRETER?=python3
PYTHON_INSTALL_ARGS?=--force
TWINE_REPOSITORY_URL?=
DOCKER_OWNER?=ericdmiller

PRODUCT_NAME=$(shell ${PYTHON_INTERPRETER} setup.py --name)
PRODUCT_VERSION=$(shell ${PYTHON_INTERPRETER} setup.py --version)

devenv:
	test ! -z "$$VIRTUAL_ENV" || ${PYTHON_INTERPRETER} -m pip install virtualenv
	test ! -z "$$VIRTUAL_ENV" || ${PYTHON_INTERPRETER} -m virtualenv venv
	venv/bin/pip install setuptools wheel twine pylint autopep8 -r requirements.txt

clean:
	${PYTHON_INTERPRETER} setup.py clean -a
	rm -rf build/ dist/ *.egg-info

build-sdist: clean
	${PYTHON_INTERPRETER} setup.py sdist
build-wheel: clean
	${PYTHON_INTERPRETER} setup.py bdist_wheel
build-docker: clean
	docker build -t ericdmiller/${PRODUCT_NAME}:${PRODUCT_VERSION} .
build: clean build-sdist build-wheel build-docker

install:
	${PYTHON_INTERPRETER} setup.py install ${PYTHON_INSTALL_ARGS}

upload-local: build-sdist build-wheel
	test ! -z "${TWINE_REPOSITORY_URL}"
	twine upload -r "${TWINE_REPOSITORY_URL}" dist/*
