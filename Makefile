PYTHON_INTERPRETER:=python3
PYTHON_INSTALL_ARGS:=--force
TWINE_REPOSITORY_URL:=

clean:
	${PYTHON_INTERPRETER} setup.py clean -a
	rm -rf build/ dist/ *.egg-info

build: clean
	${PYTHON_INTERPRETER} setup.py bdist_wheel

install:
	${PYTHON_INTERPRETER} setup.py install ${PYTHON_INSTALL_ARGS}

upload-local: build
	test ! -z "${TWINE_REPOSITORY_URL}"
	twine upload -r "${TWINE_REPOSITORY_URL}" dist/*
