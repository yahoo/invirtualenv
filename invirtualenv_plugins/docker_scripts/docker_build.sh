#!/usr/bin/env bash
set -e

INVIRTUALENV_DIR="/var/lib/invirtualenv"
INSTALLVENV="/var/lib/invirtualenv/installvenv"
VENV_COMMAND="virtualenv"
PYTHON="python3"

function init_directories {
    mkdir -p "/var/lib/virtualenvs"
    mkdir -p "${INVIRTUALENV_DIR}"
}

function init_alpine {
    echo "Configuring container for alpine packaging"
    apk add python3 python3-dev coreutils zip gcc libxml2 libxslt musl-dev libxslt-dev linux-headers make
    VENV_COMMAND="python3 -m venv"
}

function init_debian {
    echo "Configuring container for debian packaging"
    DEBIAN_FRONTEND="noninteractive"
    export DEBIAN_FRONTEND
    apt-get update
    apt-get upgrade -y
    
    set +e
    apt-get install -y python3-dev python3-venv build-essential
    RC="$?"
    set -e
    if [ "$RC" != "0" ]; then
        apt-get install -y python-dev python-pip python-virtualenv build-essential
        VENV_COMMAND="virtualenv"
    else
        VENV_COMMAND="python3 -m venv"
    fi
}

function init_rpm {
    echo "Configuring container for rpm packaging"
    VENV_COMMAND="virtualenv"
    # yum upgrade -y
    yum groupinstall -y 'development tools'
    set +e
    yum install -y python3-devel python3 python3-virtualenv
    RC="$?"
    set -e
    if [ "$RC" != "0" ]; then
        yum install -y python-devel python-virtualenv
    fi
}

function install_invirtualenv {
    echo "Bootstrapping the invirtualenv package"
    $VENV_COMMAND "${INSTALLVENV}"
    venv_pip="${INSTALLVENV}/bin/pip"

    ${venv_pip} install -U setuptools
    ${venv_pip} install -U wheel virtualenv
    ${venv_pip} install "pip<19.0"
    ${venv_pip} install -U invirtualenv
}

function deploy {
    echo "Deploying application virtualenv"
    cwd="`pwd`"
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

if [ -e "/sbin/apk" ]; then
    init_alpine
fi

install_invirtualenv
deploy

exit 0
