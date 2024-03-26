#!/usr/bin/python3
"""
Fabric script that creates and distributes an archive to your web servers
"""
import re
import tarfile
import os.path
from fabric.api import *
from datetime import datetime

env.user = 'ubuntu'
env.hosts = ['34.202.159.64']
env.key_filename = "~/.ssh/school"


def do_pack():
    """Create a tar gzipped archive of the directory static."""
    target = local("mkdir -p ./versions")
    name = str(datetime.now()).replace(" ", '')
    opt = re.sub(r'[^\w\s]', '', name)
    tar = local('tar -cvzf versions/static_{}.tgz static'.format(opt))
    if os.path.exists("./versions/static_{}.tgz".format(opt)):
        return os.path.normpath("./versions/static_{}.tgz".format(opt))
    else:
        return None


def do_deploy(archive_path):
    """Distributes an archive to both of webservers 01 & 02.

    Args:
        archive_path (str): Path of archive to distribute.
    Returns:
        If the file doesn't exist at archive_path or an error apears - False.
        Otherwise - True.
    """
    if os.path.exists(archive_path) is False:
        return False
    try:
        arc = archive_path.split("/")
        base = arc[1].strip('.tgz')
        put(archive_path, '/tmp/')
        sudo('mkdir -p /data/static/releases/{}'.format(base))
        main = "/data/static/releases/{}".format(base)
        sudo('tar -xzf /tmp/{} -C {}/'.format(arc[1], main))
        sudo('rm /tmp/{}'.format(arc[1]))
        sudo('mv {}/static/* {}/'.format(main, main))
        sudo('rm -rf /data/static/current')
        sudo('ln -s {}/ "/data/static/current"'.format(main))
        return True
    except Exception as e:
        return False


def deploy():
    """Create and distribute an archive to a web server."""
    path = do_pack()
    if path is None:
        return False
    result = do_deploy(path)
    return result
