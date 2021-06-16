from invirtualenv.config import get_configuration
from invirtualenv.deploy import link_deployed_bin_files



def main():
    config = get_configuration()
    link_bin_files = config['docker_container'].get('link_bin_files', '')
    if link_bin_files:
        link_bin_files = config['docker_container'].getboolean('link_bin_files')
    else:
        link_bin_files = config['docker_container'].getboolean('link_bin_files')
    if not link_bin_files:
        return 0

    bin_dir = config['docker_container'].get('bin_dir', '')
    if not bin_dir:
        bin_dir = config['global'].get('bin_dir', '/usr/bin')

    link_deployed_bin_files(venv_directory, bin_dir)



if __name__ == '__main__':
    main()
