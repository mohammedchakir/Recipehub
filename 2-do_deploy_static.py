#!/usr/bin/python3
"""
Fabric script that distributes an archive to your web servers
"""
from fabric.api import env, run, put
import os
from datetime import datetime

env.hosts = ['34.202.159.64']
env.user = 'ubuntu'
env.key_filename = ['~/.ssh/school']


def do_deploy(archive_path):
    """Distributes an archive to both of webservers 01 & 02.

    Args:
        archive_path (str): Path of archive to distribute.
    Returns:
        If the file doesn't exist at archive_path or an error apears - False.
        Otherwise - True.
    """
    if os.path.isfile(archive_path) is False:
        return False
    file = archive_path.split("/")[-1]
    name = file.split(".")[0]

    if put(archive_path, "/tmp/{}".format(file)).failed is True:
        return False
    if run("rm -rf /data/static/releases/{}/".
           format(name)).failed is True:
        return False
    if run("mkdir -p /data/static/releases/{}/".
           format(name)).failed is True:
        return False
    if run("tar -xzf /tmp/{} -C /data/static/releases/{}/".
           format(file, name)).failed is True:
        return False
    if run("rm /tmp/{}".format(file)).failed is True:
        return False
    if run("mv /data/static/releases/{}/static/* "
           "/data/static/releases/{}/".format(name, name)).failed is True:
        return False
    if run("rm -rf /data/static/releases/{}/static".
           format(name)).failed is True:
        return False
    if run("rm -rf /data/static/current").failed is True:
        return False
    if run("ln -s /data/static/releases/{}/ /data/static/current".
           format(name)).failed is True:
        return False
    return True
