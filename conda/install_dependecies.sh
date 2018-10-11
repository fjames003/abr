#!/bin/bash
# Stop on error
set -e

CONDA_ENV_PY3=abr-python3

SH_SCRIPT_DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

REQ_TXT_PY3=${SH_SCRIPT_DIR}/requirements_py3.txt

if which conda; then
  echo "=== Found Conda ($(conda --version))."
else
  echo "=== Conda does not exist on your system. Please install Conda first."
  echo "https://conda.io/docs/user-guide/install/index.html#regular-installation"
  exit 1
fi

if conda env list | grep -wq ${CONDA_ENV_PY3}; then
  echo "=== Pipeline's py3 Conda env (${CONDA_ENV_PY3}) already exists."
  echo "=== Please remove it first (uninstall_dependencies.sh)"
  exit 2
fi

echo "=== Installing packages for python3 env..."
conda create -n ${CONDA_ENV_PY3} --file ${REQ_TXT_PY3} -y -c bioconda -c conda-forge -c defaults -c r

echo "=== All done."
