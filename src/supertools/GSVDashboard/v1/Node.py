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
from . import GSV

__all__ = ['GSVDashboardNode', "SuperToolGSV"]

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
    """
    The supertool node in the nodegraph.
    """

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
        """
        Default network is just connecting the 2 inner ports.
        """

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

    def __build_internal_network(self):
        """
        Using the WireInlineNodes, connect all the nodes insides to themself
        and to the SuperTool Return/Sender ports.
        """
        try:
            PackageSuperToolAPI.NodeUtils.WireInlineNodes(
                self,
                self.getChildren(),
                0,
                50
            )
        except Exception as excp:
            # TODO see if it's safe to raise an error
            raise RuntimeError(
                "[{}][__build_internal_network] WireInlineNodes exceptions:\n"
                "{}".format(self.__class__.__name__, excp)
            )
        return

    def edit_gsv(self, name, value):
        """
        Args:
            name(str): Name of the GSV to edit
            value(str): Value to give to the GSV
        """

        # check if we are not already editing the variable inside
        node = None
        for gsvname, edited_node in self.get_edited_gsvs().items():
            if name == gsvname:
                node = edited_node
                break

        with undo_ctx(
                "Add edit options for GSV <{}> on node <{}>"
                "".format(name, self.getname())
        ):
            if not node:
                node = NodegraphAPI.CreateNode("VariableSet", self)

            node.getParameter("variableValue").setValue(value)
            node.setName("VariableSet_{}_{}".format(name, value))
            self.__build_internal_network()

        logger.debug(
            "[GSVDashboardNode][edit_gsv] Finished with name<{}>, value<{}>"
            "".format(name, value)
        )
        return

    def get_edited_gsvs(self):
        """
        Return a dict of {GSV Name : Katana node} where the node is the
        VariableSet node used inside teh SuperTool to edit the GSV of the
        corresponding name.
        Can return an empty dict.

        Returns:
            dict of str|NodegraphAPI.Node:
        """
        out = {}
        for child in self.getChildren():
            gsv_name = child.getParameter("variableName")
            gsv_name = gsv_name.getValue(NodegraphAPI.GetCurrentTime())
            out[gsv_name] = child

        return out

    def unedit_gsv(self, name):
        """
        Remove the VariableSet the SuperTool is using to edit the given GSV.
        Passing a GSV that is not edited yet will just return and log an error.

        Args:
            name(str): name of the GSV to stop editing.
        """

        # check if we are editing the GSV with the given name inside
        node = None
        for gsvname, edited_node in self.get_edited_gsvs().items():
            if name == gsvname:
                node = edited_node
                break
        # if not found exit and log error (this shouldn't have been called)
        if not node:
            logger.error(
                "[{}][unedit_gsv] No current node is editing the GSV <{}>."
                "".format(self.__class__.__name__, name)
            )
            return

        with undo_ctx(
                "Delete edit options for GSV <{}> on node <{}>"
                "".format(name, self.getname())
        ):
            node.delete()
            self.__build_internal_network()

        logger.debug(
            "[GSVDashboardNode][unedit_gsv] Finished with name<{}>."
            "".format(name)
        )
        return

    def get_gsvs(self, mode="logical_upstream"):
        """
        Parse the scene to find all the GSV used.

        Args:
            mode(str): See GSV.GSVSettings for supported modes.

        Returns:
            list of SuperToolGSV:
        """
        output = list()  # type: List[SuperToolGSV]
        # dict will use the default build
        settings = GSV.GSVSettings()

        if mode not in settings.get_expected("parsing.mode"):
            raise ValueError(
                "<mode> argument <{}> is not supported.".format(mode)
            )

        settings["parsing"]["mode"] = mode
        # use this katana node as the source for upstream nodes parsing.
        settings["parsing"]["source"] = self

        gsvscene = GSV.GSVScene(settings=settings)
        gsvscene.build()
        # Convert the GSVLocals to SuperToolGSV instances
        for gsvlocal in gsvscene.gsvs:
            stgsv = SuperToolGSV(data=gsvlocal)

            # check if the super tool already edit this variable
            if stgsv.name in self.get_edited_gsvs().keys():
                stgsv.set_edit_node(self)

            output.append(stgsv)
            continue

        logger.debug(
            "[GSVDashboardNode][get_gsvs] Finished with mode<{}>."
            "".format(mode)
        )
        return output


class SuperToolGSVStatus:

    global_not_set = "global"
    global_set = "global set locally"
    local_not_set = "local not set"
    local_set = "local set locally"
    local_set_this = "local set by the supertool"


class SuperToolGSV(object):
    """
    Object describing a GSV in the Katana scene relative to this super tool.
    Used in the Editor context.

    Attributes:
        __knode(NodegraphAPI.Node or None): a VariableSet node.
        __data(GSV.GSVObject): GSV as a python object

    Args:
        data (GSV.GSVObject): GSV as a python object
    """

    statuses = SuperToolGSVStatus

    def __init__(self, data):

        self.__data = data  # type: GSV.GSVObject
        self.__knode = None  # type: NodegraphAPI.Node

        return

    def __str__(self):
        return "SuperToolGSV(<{}><{}>)".format(self.name, self.status)

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
        Is the gsv set localy by this supertool.

        Returns:
            bool: True if the SuperTool has a node created for this GSV.
        """
        return True if self.__knode else False

    @property
    def is_local(self):
        return self.__data.is_local

    @property
    def is_global(self):
        return self.__data.is_global

    @property
    def is_locked(self):
        """
        Is the gsv set localy in the nodegraph.

        Returns:
            bool: True if the GSV can't be modified.
        """
        return True if self.__data.locked else False

    @property
    def status(self):
        """
        Combine all the above properties into a more convenient status string.
        See SuperToolGSVStatus.

        Returns:
            str: current status
        """

        if self.is_global and (self.is_edited or self.is_locked):
            return self.statuses.global_set

        if self.is_global:
            return self.statuses.global_not_set

        if self.is_local and self.is_locked:
            return self.statuses.local_set

        if self.is_local and self.is_edited:
            return self.statuses.local_set_this

        if self.is_local:
            return self.statuses.local_not_set

        raise RuntimeError(
            "SuperToolGSV <{}> was not built properly and a status cannot "
            "be found.".format(self.name)
        )

    def get_current_value(self):
        """
        Last value the GSV has been set to. Including by this supertool.

        TODO last value is hard to determine so consider the result
         an approximation for now.

        Returns:
            str or None: Current value the GSV is set to or None.
        """

        # if there is an associated variableSet return it's value.
        if self.__knode:
            output = self.__knode.getParameter("variableValue")
            output = output.getValue(NodegraphAPI.GetCurrentTime())
            return str(output)

        # this should be the last value set by the top-most GSV setter node.
        if self.is_locked:
            return self.__data.locked  # type: str

        return None

    def get_all_values(self):
        """
        Returns:
            list of str:
                List of values the GSV can take.
        """
        return self.__data.values

    def get_nodes(self):
        """
        Returns:
            list of GSVNode:
                List of nodes that are using this GSV. List content depends
                    of parsing settings passed to the super-tool.
        """
        return self.__data.nodes

    def set_edit_node(self, node):
        """
        Set the __knode attribute, i.e. the node used by the super tool to
        edit the gsv.
        Unset it by passing None.

        Args:
            node(NodegraphApi.Node or None):

        """
        self.__knode = node
        return