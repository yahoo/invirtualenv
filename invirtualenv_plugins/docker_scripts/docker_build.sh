#!/usr/bin/env bash
set -e

INVIRTUALENV_DIR="/var/lib/invirtualenv"
INSTALLVENV="/var/lib/invirtualenv/installvenv"
VENV_COMMAND="virtualenv"
PYTHON="python3"

if [ "$LANG" = "" ]; then
    export LANG="en_US.UTF-8"
fi

function header {
    echo "========================================================================"
    echo "$1"
    echo "========================================================================"
    
}

function init_directories {
    mkdir -p "/var/lib/virtualenvs"
    mkdir -p "${INVIRTUALENV_DIR}"
}

function init_alpine {
    header "Configuring container for alpine packaging"
    apk add python3 python3-dev coreutils zip gcc libxml2 libxslt musl-dev libxslt-dev linux-headers make
    VENV_COMMAND="python3 -m venv"
}

function init_debian {
    header "Configuring container for debian packaging"
    DEBIAN_FRONTEND="noninteractive"
    export DEBIAN_FRONTEND
    apt-get update
    apt-get upgrade -y
    
    apt-get install -y python3-dev python3-venv build-essential || RC="$?"
    if [ "$RC" != "0" ]; then
        apt-get install -y python-dev python-pip python-virtualenv build-essential
        VENV_COMMAND="virtualenv"
    else
        VENV_COMMAND="python3 -m venv"
    fi
}

function init_rpm {
    header "Configuring container for rpm packaging"
    VENV_COMMAND="virtualenv"
    # yum upgrade -y
    yum clean all
    yum install -y apr apr-util autoconf automake \
        bison byacc \
        cscope ctags \
        diffstat doxygen \
        flex \
        gcc gcc-gfortran \
        indent intltool \
        libtool \
        patchutils \
        rcs \
        subversion swig \
        python3-devel python3 python3-virtualenv || RC="$?"
    yum clean all
    if [ "$RC" != "0" ]; then
        echo "Unable to bootstrap python3, switching to python2"
        yum install -y apr apr-util autoconf automake \
            bison byacc \
            cscope ctags \
            diffstat doxygen \
            flex \
            gcc gcc-gfortran \
            indent intltool \
            libtool \
            patchutils \
            rcs \
            subversion swig \
            python-devel python-virtualenv && yum clean all
    fi
}

function install_invirtualenv {
    header "Bootstrapping the invirtualenv package"
    $VENV_COMMAND "${INSTALLVENV}"
    source "${INSTALLVENV}/bin/activate"
    venv_pip="${INSTALLVENV}/bin/pip"

    ${venv_pip} install -U setuptools
    ${venv_pip} install -U wheel virtualenv
    ${venv_pip} install "pip<19.0"
    ${venv_pip} install -U invirtualenv
    deactivate || true
}

function deploy {
    header "Deploying application virtualenv"
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

if [ -e "/usr/bin/yum" ]; then
    header "Cleaning up yum metadata"
    yum clean all
fi
exit 0
