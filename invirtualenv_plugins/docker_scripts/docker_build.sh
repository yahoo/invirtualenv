#!/usr/bin/env bash

INVIRTUALENV_DIR="/var/lib/invirtualenv"
INSTALLVENV="/var/lib/invirtualenv/installvenv"

function init_directories {
    mkdir -p "/var/lib/virtualenvs"
    mkdir -p "${INVIRTUALENV_DIR}"
}

function init_debian {
    echo "Configuring container for debian packaging"
    DEBIAN_FRONTEND="noninteractive"
    export DEBIAN_FRONTEND
    apt-get update
    apt-get upgrade -y
    apt-get install -y python-dev python-pip python-virtualenv
}

function init_rpm {
    echo "Configuring container for rpm packaging"
    yum upgrade -y
    yum install -y python-devel python-virtualenv
}

function install_invirtualenv {
    virtualenv "${INSTALLVENV}"
    venv_pip="${INSTALLVENV}/bin/pip"

    ${venv_pip} install -U setuptools
    ${venv_pip} install -U pip wheel virtualenv
    ${venv_pip} install -U invirtualenv
}

function deploy {
    cwd=`pwd`
    cd "${INVIRTUALENV_DIR}"
    cat deploy.conf
    ${INSTALLVENV}/bin/deploy_virtualenv
    cd ${cwd}
}


# Main code starts here
init_directories

if [ -e "/usr/bin/apt-get" ]; then
    init_debian
fi

if [ -e "/usr/bin/yum" ]; then
    init_rpm
fi

install_invirtualenv
deploy

exit 0
