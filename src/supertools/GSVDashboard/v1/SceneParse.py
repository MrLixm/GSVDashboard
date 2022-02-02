"""
"""
import NodegraphAPI

# error on Python2, for comments only anyway
try:
    from typing import Tuple, Optional
except ImportError:
    pass

__all__ = [
    "get_upstream_nodes",
    "ParseSettings"
]


class ParseSettings(dict):
    """
    A regular dictionary object with a fixed structure. Structure is verified
    through ``validate()`` method.

    Used to configure the output result of the scene parsing.

    [excluded.asGroupsNodeType](list of str):
        list of node type that should not be considered as groups and children
        are as such not processed.
    [logical](bool):
        True to process only logical connections between nodes.
        (ex: Switch node only have 1 logical connection)
    """

    __default = {
        "excluded": {
            "asGroupsNodeType": []
        },
        "logical": True
    }

    def __init__(self, *args, **kwargs):

        if not args and not kwargs:
            super(ParseSettings, self).__init__(self.__default)
        else:
            super(ParseSettings, self).__init__(*args, **kwargs)
            self.validate()

        return

    def __setitem__(self, *args, **kwargs):
        super(ParseSettings, self).__setitem__(*args, **kwargs)
        self.validate()

    # Defined some properties to set/get values. Allow to use autocompletion.

    @property
    def exluded_asGroupsNodeType(self):
        return self["excluded"]["asGroupsNodeType"]

    @exluded_asGroupsNodeType.setter
    def exluded_asGroupsNodeType(self, value):
        self["excluded"]["asGroupsNodeType"] = value

    @property
    def logical(self):
        return self["logical"]

    @logical.setter
    def logical(self, logical_value):
        self["logical"] = logical_value

    def validate(self):
        """
        Raises:
            AssertionError: if self is not built properly.
        """
        pre = "[{}] ".format(self.__class__.__name__)

        assert self.get("excluded"),\
            pre + "Missing key <excluded>"

        assert isinstance(self["excluded"].get("asGroupsNodeType"), list),\
            pre + "Missing key <excluded.asGroupsNodeType>"

        assert isinstance(self.get("logical"), bool),\
            pre + "Missing key <logical> or value is not <bool>."

        return


def get_upstream_nodes(source_node, source_port, settings):
    """
    From a given node, find all upstream nodes connected.

    Groups node themself are not included in the output but their children are
    processed (unless contrary specified in settings).

    Args:
        source_node(NodegraphAPI.Node):
            first index is always a node, second an optional source port.
            Port should be on the same node as the passed node.
        source_port(NodegraphAPI.Port or None):
        settings(ParseSettings):
            a regular dict with a fixed structure. See ParseSettings docstring.

    Returns:
        list of NodegraphAPI.Node:
            list of visited node in order. In the case of a merge, the first
                branch (index 0) is visited first and recursively to the top,
                and then the second branch, ...
    """

    buffer = list()
    if source_port and source_port.getNode() != source_node:
        raise TypeError(
            "Submited source_port argument doesn't belong to the submited "
            " source_node argument: source_node=<{}>, source_port's node=<{}>"
            "".format(source_node, source_port.getNode())
        )

    # When we got a groupNode we need to also parse what's inside (unless
    # the node it is excluded)
    # A groupNode is passed when going in and going out of a group
    if isinstance(source_node, NodegraphAPI.GroupNode) and (
            source_node.getType() not in settings.exluded_asGroupsNodeType
    ):

        # if we passed a port we can just find what child node is connected
        if source_port:
            # at first we assume we a going inside the group = return port
            __port = source_node.getReturnPort(source_port.getName())

            if not __port:
                # we are going out of a group so find the group input port
                __port = source_node.getInputPort(source_port.getName())

            source_port = __port.getConnectedPorts()[0]
            # replace the group node with its last connected child
            source_node = source_port.getNode()

        else:
            # if no port supplied we assume the group only have one output
            source_port = source_node.getOutputPortByIndex(0)
            # and if he doesn't even have an output port ...
            if not source_port:
                raise TypeError(
                    "The given source_obj[0] is a GroupNode with no output "
                    "port which is not currently supported."
                )
            source_port = source_node.getReturnPort(source_port.getName())
            source_port = source_port.getConnectedPorts()[0]
            source_node = source_port.getNode()

    else:
        pass

    buffer.append(source_node)

    # We need to find a list of port connected to this node
    connected_ports = node_get_connections(
        node=source_node,
        logical=settings.logical
    )
    # Node doesn't have any inputs so return it.
    if not connected_ports:
        return buffer

    for connected_port in connected_ports:
        buffer.extend(
            get_upstream_nodes(
                source_node=connected_port.getNode(),
                source_port=connected_port,
                settings=settings
            )
        )
        continue

    return buffer


def node_get_connections(node, logical=True):
    """
    From a given node return a list of the coonected output ports .

    If logical is set to True only port's nodes contributing to building
    the scene as returned. For example, in the case of a VariableSwitch,
    return only the connected port active.

    Works for any node type even with only one input or no input.

    Args:
        logical(bool): True to return only logical connections.
        node(NodegraphAPI.Node):

    Returns:
        set of NodeGraphAPI.Port: set of ports connected to the passed node
    """

    output = set()
    in_ports = node.getInputPorts()

    for in_port in in_ports:
        # we assume input port can only have one connection
        connected_port = in_port.getConnectedPort(0)
        if not connected_port:
            continue

        if logical:
            # Having a GraphState means the node is evaluated.
            if connected_port.getNode().getGraphState():
                output.add(connected_port)
        else:
            output.add(connected_port)

    return output


def __test():
    """
    Example use case of the above functions.
    # TODO remove this function before publish
    """

    # we avoid visiting GT nodes content.
    setting_dict = {
        "excluded": {
            "asGroupsNodeType": ["GafferThree"]
        },
        "logical": True
    }
    excluded_ntype = ["Dot"]

    sel = NodegraphAPI.GetAllSelectedNodes()  # type: list

    result = get_upstream_nodes(
        source_node=sel[0],
        source_port=None,
        settings=ParseSettings(setting_dict),
    )
    # removed nodes of unwanted type
    result = filter(lambda node: node.getType() not in excluded_ntype, result)
    # convert nodes objects to string
    result = map(lambda obj: obj.getName(), result)
    # result.sort()  # break the visited order ! but nicer for display

    import pprint
    pprint.pprint(result)

    return
