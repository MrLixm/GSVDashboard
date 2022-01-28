"""

"""
import logging
from contextlib import (
    contextmanager
)
try:
    from typing import (
        List
    )
except ImportError:
    pass

from Katana import (
    NodegraphAPI,
    Utils,
)
import PackageSuperToolAPI

from . import c
from .GSV import *

__all__ = ['GSVDashboardNode', "GSVNode"]

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
        # TODO

        # get inner input port
        port_in = self.getSendPort(
            self.getInputPortByIndex(0).getName()
        )
        # get inner output port
        port_out = self.getReturnPort(
            self.getOutputPortByIndex(0).getName()
        )
        # connect them
        port_out.connect(port_in)

        return

    def addParameterHints(self, attrName, inputDict):
        """
        This function will be called by Katana to allow you to provide hints
        to the UI to change how parameters are displayed.
        """
        inputDict.update(self._hints.get(attrName, {}))
        return

    def upgrade(self):
        """
        Update the node content to the latest version if needed.
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

    def edit_gsv(self, name, value):
        with undo_ctx(
                "Add edit options for GSV <{}> on node <{}>"
                "".format(name, self.getname())
        ):
            pass
        # TODO
        return

    def get_edited_gsvs(self):
        # TODO
        pass

    def unedit_gsv(self, name):
        with undo_ctx(
                "Delete edit options for GSV <{}> on node <{}>"
                "".format(name, self.getname())
        ):
            pass
        # TODO
        return

    def get_gsvs(self, all_scene=False):
        """

        Args:
            all_scene(bool):
                If False only return the GSVs from the upstream node flow.
                If True from all the scene.

        """
        # TODO
        output = list()  # type: List[GSVNode]
        return output


class GSVNode(object):
    """
    Object describing a GSV in the Katana scene relative to this super tool.

    Attributes:
        __knode(NodegraphAPI.Node or None): a VariableSet node.
    """

    def __init__(self, data):

        # TODO see how __data and __knode is set

        self.__data = None  # type: GSVLocal
        self.__knode = None  # type: NodegraphAPI.Node

        return

    @property
    def name(self):
        """
        Returns:
            str: Name of the GSV represented.
        """
        return self.__data.name

    @property
    def is_edited(self):
        """

        Returns:
            bool: True if the SuperTool has a node created for this GSV.
        """
        return True if self.__knode else False

    @property
    def is_locked(self):
        """
        Returns:
            bool: True if the GSV can't be modified.
        """
        return self.__data.is_locked()

    def get_current_value(self):
        """
        Returns:
            str or None: Current value the GSV is set to or None.
        """

        # if there is an associated variableSet return it's value.
        if self.__knode:
            output = self.__knode.getParameter("variableValue")
            output = output.getValue(NodegraphAPI.GetCurrentTime())
            return str(output)

        if self.__data.locked:
            pass

        return None

    def get_all_values(self):
        pass
