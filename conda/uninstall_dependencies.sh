#!/bin/bash
# Stop on error
set -e

CONDA_ENV_PY3=abr-python3

if which conda; then
  echo "=== Found Conda ($(conda --version))."
else
  echo "=== Conda does not exist on your system. Please install Conda first."
  echo "https://conda.io/docs/user-guide/install/index.html#regular-installation"
  exit 1
fi

if conda env list | grep -wq ${CONDA_ENV_PY3}; then
  echo "=== Removing pipeline's py3 Conda env (${CONDA_ENV_PY3})..."
  conda env remove -n ${CONDA_ENV_PY3} -y
else
  echo "=== Pipeline's py3 Conda env (${CONDA_ENV_PY3}) does not exist or has already been removed."
fi
