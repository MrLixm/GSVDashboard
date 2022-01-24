"""

"""
import logging

from Katana import (
    NodegraphAPI,
    Utils
)

from . import c

__all__ = ['upgrade']

logger = logging.getLogger("{}.Upgrade".format(c.name))


def upgrade(node):
    """


    Args:
        node(NodegraphAPI.Node): GSVDashboard node that need to be upgraded
    """

    Utils.UndoStack.DisableCapture()

    try:
        pass
        # This is where you would detect an out-of-date version:
        #    node.getParameter('version')
        # and upgrade the internal network.

    except Exception as exception:
        logger.exception(
            "[upgrade] Error upgrading {} node <{}>: {}"
            "".format(c.name, node.getName(), exception)
        )

    finally:
        Utils.UndoStack.EnableCapture()

    return
