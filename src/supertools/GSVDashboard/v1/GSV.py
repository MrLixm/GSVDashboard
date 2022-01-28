"""
"""
from collections import OrderedDict
import sys
import logging
# Python 2 ...
try:
    from typing import (
        Optional,
        List
    )
except ImportError:
    pass

import NodegraphAPI

from . import c


__all__ = ["GSVNode", "GSVScene", "GSVLocal"]

logger = logging.getLogger("{}.Node".format(c.name))

""" config_dict(dict)
Configure how the script behave

[lvl0]
[key=exclude:value](list):
    variable names that will be removed from result
[key=nodes:value](dict):
    List the node that make use of local GSVs.

[lvl1]
[key=nodes:value.key](str):  
    katana node type 
[key=nodes:value.key:value](dict):  
    parameters path on node that help build the GSV

[lvl2]
[key=nodes:value.key:value.key=name:value](str):  
    parameters path on node to get the variable name
[key=nodes:value.key:value.key=values:value](str):  
    parameters path on node to get the values the variable can take

"""

CONFIG = {
    "excluded": ["gafferState"],
    "nodes": {
        "VariableSwitch": {
            "action": "getter",
            "name": "variableName",
            "values": "patterns"
        },
        "VariableEnabledGroup": {
            "action": "getter",
            "name": "variableName",
            "values": "pattern"
        },
        "VariableSet": {
            "action": "setter",
            "name": "variableName",
            "values": "variableValue"
        }
    }
}

TIME = NodegraphAPI.GetCurrentTime()


class GSVNode(object):
    """
    A Katana node that use the GSV feature.

    Args:
        node(NodegraphAPI.Node):

    Attributes:
        node: Katana node
        type: Katana node type
        action: Action performed on GSV: setter or getter
        gsv_name: Name of the GSV
        gsv_values: Value(s) the GSV can take

    """

    __sources = CONFIG.get("nodes", dict())

    def __init__(self, node):

        self.node = node
        self.type = node.getType()
        self.action = None
        self.gsv_name = None
        self.gsv_values = None

        self.action = self.__sources[self.type]["action"]

        self.gsv_name = self.get_parameter(
            param_path=self.__sources[self.type]["name"]
        )[0]

        self.gsv_values = self.get_parameter(
            param_path=self.__sources[self.type]["values"]
        )

        logger.debug(
            "[GSVNode][__init__] Finished for node <{}>."
            "gsv_name={},gsv_values={}"
            "".format(node, self.gsv_name, self.gsv_values)
        )

        return

    def __str__(self):
        return "{}({})".format(self.node.getName(), self.type)

    def get_parameter(self, param_path):
        """

        Args:
            param_path(str): parameter path on node

        Returns:
            list: list of values holded by this parameter.

        Notes:
            TODO support case where given param has multiple nested param
        """

        param = self.node.getParameter(param_path)
        if not param:
            raise ValueError(
                "Parameter <{}> not found on node <{}>"
                "".format(param_path, self.node)
            )

        output = list()

        if param.getNumChildren() != 0:
            for index in range(0, param.getNumChildren()):
                output.append(param.getChildByIndex(index).getValue(TIME))
        else:
            output = [param.getValue(TIME)]

        return output


class GSVLocal(object):
    """
    Represent a GSV as a python object. Allow to know which node is using this
    gsv and what value it can take.

    A local GSV is considered as locked when it's value is set in the Nodegraph

    # TODO get the current value this GSV is potentially set to

    Args:
        name(str): gsv name used in the nodegraph
        scene(GSVScene): parent scene

    Attributes:
        name: Name of the local GSV
        scene: Parent scene this GSV can found in.
        nodes: LIst nodes that are using this GSV.
        values: List of value the GSV can take.
        locked: Value the GSV is currently set to or None if not set yet.

    """

    __instances = list()
    __excluded = CONFIG.get("excluded", list())

    def __new__(cls, *args, **kwargs):

        name = kwargs.get("name") or args[0]  # type: str
        scene = kwargs.get("scene") or args[1]  # type: GSVScene

        # If the variable name is specified as excluded return None
        if name in cls.__excluded:
            return None

        # try to find if an instance of this class with the same name and same
        # parented scene already exists.
        # If yes, return it instead of creating a new one.
        for instance in cls.__instances:
            if instance.name == name and instance.scene == scene:
                return instance  # type: GSVLocal

        new_instance = super(GSVLocal, cls).__new__(cls)
        cls.__instances.append(new_instance)
        return new_instance

    def __init__(self, name, scene):

        self.name = name
        self.scene = scene
        self.nodes = list()  # type: List[GSVNode]
        self.values = list()  # type: List[str]
        self.locked = None  # type: Optional[str]

    def __build_nodes(self):
        """
        Find all the nodes in the scene that use the current gsv name.
        This nodes are setter and getters.
        """

        self.nodes = list()

        for gsvnode in self.scene.nodes:

            if gsvnode.gsv_name == self.name:
                self.nodes.append(gsvnode)

            continue

        return

    def __build_values(self):
        """
        Get all the potential values this GSV can take by iterating through the
        nodes using it.
        """

        # reset self.value first
        self.values = list()

        # iterate through all the nodes (think to build it first !)
        for node in self.nodes:

            # the parameter holding the potential variables value might
            # have children (ex:VariableSwitch)
            if node.gsv_values:
                self.values.extend(map(str, node.gsv_values))

            continue

        # remove duplicates values
        self.values = list(OrderedDict.fromkeys(self.values))

        return

    def build(self):

        self.__build_nodes()
        self.__build_values()

        logger.debug(
            "[GSVLocal][build] Finished for name=<{}>".format(self.name)
        )
        return

    def todict(self):
        """
        Return a dictionnary representation of the class.
        """

        if not self.values:
            logger.warning("[GSVLocal][todict] self.values is empty")
        if not self.nodes:
            logger.warning("[GSVLocal][todict] self.nodes is empty")

        return {
            "name": self.name,
            "values": self.values,
            "nodes": map(str, self.nodes)
        }


class GSVScene(object):
    """
    A group of node associated with an arbitrary number of gsvs.
    """

    def __init__(self):

        self.nodes = list()  # type: List[GSVNode]
        self.gsvs = list()  # type: List[GSVLocal]

    def _build_nodes(self):
        """
        Find all the nodes in the nodegraph that use the gsv feature.
        """

        # reset self.nodes first
        self.nodes = list()

        for node_class, _ in GSVNode.__sources.items():

            nodes = NodegraphAPI.GetAllNodesByType(node_class)  # type: list
            for node in nodes:
                self.nodes.append(GSVNode(node))

            continue

        logger.debug(
            "[GSVLocal][_build_nodes] Finished. {} nodes found."
            "".format(len(self.nodes))
        )

        return

    def _build_gsvs(self):
        """
        From the node list find what gsv is used and build its object.
        """

        # reset self.gsvs first
        self.gsvs = list()

        for gsvnode in self.nodes:

            gsv = GSVLocal(gsvnode.gsv_name, self)
            # gsv might be excluded, so it returns None
            if not gsv:
                continue
            # avoid adding multiples times the same instance
            if gsv in self.gsvs:
                continue

            self.gsvs.append(gsv)
            continue

        # we don't forget to build the gsv object if we want to use its attributes
        for gsvlocal in self.gsvs:
            gsvlocal.build()

        logger.debug(
            "[GSVLocal][_build_gsvs] Finished. {} gsv found."
            "".format(len(self.gsvs))
        )

        return

    def build(self):

        self._build_nodes()
        self._build_gsvs()

        return

    def todict(self):
        return {"gsvs": list(map(lambda obj: obj.todict(), self.gsvs))}