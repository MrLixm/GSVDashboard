"""

"""
import logging
from contextlib import (
    contextmanager
)

from Katana import (
    NodegraphAPI,
    Utils
)

from . import c

__all__ = ['GSVDashboardNode']

logger = logging.getLogger("{}.Node".format(c.name))


@contextmanager
def undo_ctx(name, post_actions=None):
    """
    Use to register a group of action as one in the undo stack.
    Replace the ``try/finally`` syntax usually used.
    Can be used as a decorator on methods or like this :
    ::

        with undox_ctx("Action A"):
            NodegraphAPI.CreateNode("Group", root)

    Args:
        name(str): Name of the action in the Undo stack.
        post_actions(list or None):
            list of functions to call in the <finally> statement after the
            UndoStack is closed.

    """
    post_actions = post_actions if post_actions else list()

    Utils.UndoStack.OpenGroup(name)

    try:
        yield
    finally:
        Utils.UndoStack.CloseGroup()
        for post_action in post_actions:
            post_action()


def upgrade(node):
    """
    If the passed node is from an older version, upgrade it without
    breaking the setup.

    TODO [upgrade] Not implemented yet.

    Args:
        node(GSVDashboardNode): GSVDashboard node that need to be upgraded
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


class GSVDashboardNode(NodegraphAPI.SuperTool):

    _hints = {}

    def __init__(self):

        self.hideNodegraphGroupControls()
        self.addInputPort('input')
        self.addOutputPort('output')

        # Hidden version parameter to detect out-of-date internal networks
        # and upgrade it.
        self.getParameters().createChildNumber('version', c.version)

        self.__build_default_network()

        return

    """------------------------------------------------------------------------
    SuperTool methods override
    """

    def __build_default_network(self):
        pass

    def addParameterHints(self, attrName, inputDict):
        """
        This function will be called by Katana to allow you to provide hints
        to the UI to change how parameters are displayed.
        """
        inputDict.update(self._hints.get(attrName, {}))
        return

    def upgrade(self):
        """
        Use the Upgrade module to update the node content to the latest version
        if needed.
        """

        if self.isLocked():
            logger.warning(
                "[GSVDashboardNode][upgrade] Cannot updgrade node <{}>: "
                "is locked.".format(self)
            )

        upgrade(self)

        return

    """------------------------------------------------------------------------
    Actual API
    """

    def add_gsv(self, name):
        with undo_ctx(
                "Add edit options for GSV <{}> on node <{}>"
                "".format(name, self.getname())
        ):
            pass
        return

    def delete_gsv(self, name):
        with undo_ctx(
                "Delete edit options for GSV <{}> on node <{}>"
                "".format(name, self.getname())
        ):
            pass
        return



