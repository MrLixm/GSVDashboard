"""
"""
import NodegraphAPI

# error on Python2, for comments only anyway
try:
    from typing import Tuple, Optional
except ImportError:
    pass

__all__ = [
    "SceneParser",
    "ParseSettings"
]


class ParseSettings(dict):
    """
    A regular dictionary object with a fixed structure. Structure is verified
    through ``validate()`` method.

    Used to configure the output result of the scene parsing.

    [include_groups](bool)
         If True, before visiting its content, include the group node in the output
    [excluded.asGroupsNodeType](list of str):
        list of node type that should not be considered as groups and children
        are as such not processed.
    [logical](bool):
        True to process only logical connections between nodes.
        (ex: Switch node only have 1 logical connection)
    """

    __default = {
        "include_groups": False,
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

    @property
    def include_groups(self):
        return self["include_groups"]

    @include_groups.setter
    def include_groups(self, include_groups_value):
        self["include_groups"] = include_groups_value

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

        assert isinstance(self.get("include_groups"), bool),\
            pre + "Missing key <include_groups> or value is not <bool>."

        return


class SceneParser(object):
    """
    Attributes:

        __buffer(set of NodegraphAPI.Node):
            list of visited node in "pseudo-order" after a parsing operation.
            Must be returned by the parsing function and reset after.

        visited_ports (list of NodegraphAPI.Port):
            we keep a list of the port we progressively visit to avoid visiting
            them multiples times.

        settings(ParseSettings):
            Options for the scene parsing
    """

    def __init__(self, source=None):

        self.source = source
        self.__buffer = list()
        self.settings = ParseSettings()

        return

    def __get_upstream_nodes(self, source):
        """
        From a given node, find all upstream nodes connected.

        Groups node themself are not included in the output but their children are
        processed (unless contrary specified in settings).

        Args:
            source(NodegraphAPI.Node or NodegraphAPI.Port):
                object to start the parsing from.

        """

        if isinstance(source, NodegraphAPI.Port):
            source_port = source
            source_node = source.getNode()
        elif isinstance(source, NodegraphAPI.Node):
            source_port = None
            source_node = source
        else:
            raise TypeError(
                "Submited source argument <{}> is not supported."
                "Must be Port or Node."
                "".format(source)
            )

        # When we got a groupNode we need to also parse what's inside (unless
        # the node it is excluded). To do so we swap the passed inputPort/node
        # of the group by the ones from the first children in the group.
        # (i): A groupNode is passed as arg when going in and going out of a group
        if isinstance(
            source_node,
            NodegraphAPI.GroupNode
        ) and (
            source_node.getType() not in self.settings.exluded_asGroupsNodeType
        ):

            # If specified we add the groupNode to the buffer, but only
            # if we are sure there is no input else it would be added multiple
            #  time to the buffer (going in and out) and would stop the script.
            # If there is input it is added only when goign out.
            if self.settings.include_groups and not source_node.getInputPorts():
                self.__buffer.append(source_node)

            # if we passed a port we can just find what child node is connected
            if source_port:
                # at first we assume we a going inside the group = return port
                __port = source_node.getReturnPort(source_port.getName())

                if not __port:
                    # we are going out of a group so find the group input port
                    __port = source_node.getInputPort(source_port.getName())
                    # the group was not added when going in so add it now
                    if self.settings.include_groups:
                        self.__buffer.append(source_node)

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

        self.__buffer.append(source_node)

        # We need to find a list of port connected to this node
        connected_ports = node_get_connections(
            node=source_node,
            logical=self.settings.logical
        )
        # Node doesn't have any inputs so return it.
        if not connected_ports:
            return

        # now process all the input of this node
        for connected_port in connected_ports:

            # avoid processing multiples times the same node/port
            if connected_port.getNode() in self.__buffer:
                continue

            self.__get_upstream_nodes(
                source=connected_port
            )

            continue

        return

    def __reset(self):
        """
        Operations done after a parsing to reset the instance before the next
        parsing.
        """
        self.visited_ports = list()
        self.settings = ParseSettings()
        return

    def get_upstream_nodes(self, source=None):
        """
        Make sure the settings attributes is set accordingly before calling.

        Args:
            source(NodegraphAPI.Node or NodegraphAPI.Port):
                source nodegraph object from where to start the upstream parsing

        Returns:
            set of NodegraphAPI.Node:
        """
        source = source or self.source
        if not source:
            raise ValueError(
                "[get_upstream_nodes] Source argument is nul. Set the class "
                "source attribute or pass a source argument to this method."
            )
        self.__get_upstream_nodes(source=source)
        out = self.__buffer  # save the buffer before reseting it
        self.__reset()

        return out


def node_get_connections(node, logical=True):
    """
    From a given node return a set of the connected output ports .

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
    """

    # we avoid visiting GT nodes content.
    setting_dict = {
        "include_groups": True,
        "excluded": {
            "asGroupsNodeType": ["GafferThree"]
        },
        "logical": False
    }
    excluded_ntype = ["Dot"]

    sel = NodegraphAPI.GetAllSelectedNodes()  # type: list

    scene = SceneParser()
    scene.settings = ParseSettings(setting_dict)
    result = scene.get_upstream_nodes(sel[0])

    # removed nodes of unwanted type
    result = filter(lambda node: node.getType() not in excluded_ntype, result)
    # convert nodes objects to string
    result = map(lambda obj: obj.getName(), result)
    # result.sort()  # break the visited order ! but nicer for display

    import pprint
    pprint.pprint(result)

    return
