from fabric import local
from datetime import date
from time import strftime


def do_pack():
    """
    Creates a .tgz archive from the contents of the static folder
    """
    file = strftime("%Y%m%d%H%M%S")
    try:
        local("mkdir -p versions")
        local("tar -czvf versions/static_{}.tgz static/"
              .format(file))

        return "versions/static_{}.tgz".format(file)
    except Exception as e:
        return None
