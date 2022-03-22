"""

[LICENSE]

    Copyright 2022 Liam Collod
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
       http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
import pprint
import re
from collections import OrderedDict
import sys
import logging
# Python 2 ...
from types import NoneType

try:
    from typing import (
        Optional,
        List
    )
except ImportError:
    pass

import NodegraphAPI

from . import c
from .SceneParse import (
    SceneParser,
    ParseSettings
)


__all__ = ["GSVNode", "GSVScene", "GSVObject", "GSVSettings"]

logger = logging.getLogger("{}.Node".format(c.name))


def _get_parameter(knode, param_path):
    """
    Return the parameter values in the given node.

    Args:
        knode(NodegraphAPI.Node):
        param_path(str): parameter path on node

    Returns:
        list: list of values holded by this parameter.

    Notes:
        Parameters are considered as not multi-sampled.
        TODO support case where given param has multiple nested param
    """

    param = knode.getParameter(param_path)
    if not param:
        raise ValueError(
            "Parameter <{}> not found on node <{}>"
            "".format(param_path, knode)
        )

    output = list()

    if param.getNumChildren() != 0:
        for index in range(0, param.getNumChildren()):
            output.append(param.getChildByIndex(index).getValue(0))
    else:
        output = [param.getValue(0)]

    return output


def gsv_get_opscript_structure(knode):
    """
    Args:
        knode(NodegraphAPI.Node):

    Returns:
        dict of str:
    """
    out = dict()

    lua_script = _get_parameter(knode, "script.lua")
    lua_script = lua_script[0]
    for match in re.finditer(
            r"Interface.GetGraphStateVariable\(\"(.+)\"\)",
            lua_script
    ):
        out[match.group(1)] = ["*"]

    return out


def gsv_get_variabledelete_structure(knode):
    """
    Args:
        knode(NodegraphAPI.Node):

    Returns:
        dict of str:
    """
    gsvname = _get_parameter(knode, "variableName")
    gsvname = gsvname[0]
    return {
        gsvname: ["DELETED"]
    }


def gsv_get_variableset_structure(knode):
    """
    Args:
        knode(NodegraphAPI.Node):

    Returns:
        dict of str:
    """
    gsvname = _get_parameter(knode, "variableName")
    gsvname = gsvname[0]
    return {
        gsvname: _get_parameter(knode, "variableValue")
    }


def gsv_get_variablegroup_structure(knode):
    """
    Args:
        knode(NodegraphAPI.Node):

    Returns:
        dict of str:
    """
    gsvname = _get_parameter(knode, "variableName")
    gsvname = gsvname[0]
    return {
        gsvname: _get_parameter(knode, "pattern")
    }


def gsv_get_variableswitch_structure(knode):
    """
    Args:
        knode(NodegraphAPI.Node):

    Returns:
        dict of str:
    """
    gsvname = _get_parameter(knode, "variableName")
    gsvname = gsvname[0]
    return {
        gsvname: _get_parameter(knode, "patterns")
    }


class GSVSettings(dict):
    """
    A regular dictionary object with a fixed structure. Structure is verified
    through ``validate()`` method.

    Used to configure the output result of the scene parsing.

    [nodes.X.name](str or callable):
        callable must return a list of string: list of GSV names
    [nodes.X.values](str or callable):
        callable must return a list of string: list of GSV values

    [excluded.asGroupsNodeType](list of str):
        list of node type that should not be considered as groups and children
        are as such not processed.

    """

    __default = {
        "excluded": [],
        "nodes": {
            "VariableSwitch": {
                "action": "getter",
                "structure": gsv_get_variableswitch_structure,
            },
            "VariableEnabledGroup": {
                "action": "getter",
                "structure": gsv_get_variablegroup_structure,
            },
            "VariableSet": {
                "action": "setter",
                "structure": gsv_get_variableset_structure
            },
            "VariableDelete": {
                "action": "setter",
                "structure": gsv_get_variabledelete_structure
            },
            "OpScript": {
                "action": "getter",
                "structure": gsv_get_opscript_structure
            }

        },
        "parsing": {
            "mode": "logical_upstream",
            "source": None,
            "excluded": {
                "asGroupsNodeType": []
            },
        }
    }

    __expected = {
        "excluded": list(),
        "nodes": {
            "template": {
                "action": ["getter", "setter"],
                "structure": callable,
            }
        },
        "parsing": {
            # first index is default
            "mode": ["logical_upstream", "all_scene", "upstream"],
            "source": None,
            "excluded": {
                "asGroupsNodeType": list()
            }
        }
    }

    def __init__(self, *args, **kwargs):

        if not args and not kwargs:
            super(GSVSettings, self).__init__(self.__default)
        else:
            super(GSVSettings, self).__init__(*args, **kwargs)
            self.validate()

        return

    def __setitem__(self, *args, **kwargs):
        super(GSVSettings, self).__setitem__(*args, **kwargs)
        self.validate()

    def validate(self):
        """
        Raises:
            AssertionError: if self is not built properly.
        """
        pre = "[{}] ".format(self.__class__.__name__)
        node_key_list = list(self.get_expected("nodes.template").keys())

        # check root keys
        for rk, rv in self.__expected.items():

            assert isinstance(
                self.get(rk), type(rv)
            ), pre + "Missing key <{}>".format(rk)

        # check the "nodes" key
        for nkey, nvalue in self["nodes"].items():

            assert isinstance(
                nvalue, dict
            ), pre + "Value for Key <{}> is not a dict but <>"\
                     "".format(nkey, type(nvalue))

            for nvkey, nvvalue in nvalue.items():

                assert nvkey in node_key_list, \
                    pre + "Key <{}> is not supported: must be one of <{}>" \
                          "".format(nvkey, node_key_list)

                if nvkey == "structure":
                    assert callable(nvvalue), \
                        pre + "Key <{}> has an invalid value type: " \
                              "must be a callable.".format(nvkey)

        # check parsing.mode
        parsing_mode = self["parsing"].get("mode")
        assert parsing_mode in self.get_expected("parsing.mode"), \
            pre + "parsing.mode key unsuported value <{}>".format(parsing_mode)

        # check parsing.source (value can be None)
        assert isinstance(
            self["parsing"].get("source", str()), (NoneType, NodegraphAPI.Node)
        ), pre + "Missing key <parsing.source>"

        # check parsing.excluded
        assert isinstance(
            self["parsing"].get("excluded"),
            type(self.get_expected("parsing.excluded"))
        ), pre + "Missing key <parsing.excluded>"

        # check parsing.excluded.asGroupsNodeType
        assert isinstance(
            self["parsing"]["excluded"].get("asGroupsNodeType"),
            type(self.get_expected("parsing.excluded.asGroupsNodeType"))
        ), pre + "Missing key <parsing.excluded.asGroupsNodeType>"

        return

    @classmethod
    def get_expected(cls, keypath):
        """
        Args:
            keypath(str): path to nested key, using "." as a key seperator.

        Returns:
            any: type depends of key's value.
        """

        # access nested keys:value pairs using the "." separator
        keypath = keypath.split(".")  # type: list
        value = cls.__expected
        for key in keypath:
            value = value[key]

        return value


class GSVNode(object):
    """
    A Katana node that use the GSV feature.
    You must make sure the node use the GSV feature before instancing the class

    Args:
        node(NodegraphAPI.Node):
        scene(GSVScene): parent scene this node was generated from.

    Attributes:
        node(NodegraphAPI.Node): Katana node
        type(str): Katana node type
        gsv_action(str):
            Action performed on GSV: setter or getter.
            Used by the corresponding properties method.
        gsvs(dict of str):
            dictionary of gsv names with their asociated list of value
            {"gsvname": [value1, ...], ...}


    """
    action_getter = "getter"
    action_setter = "setter"

    def __init__(self, node, scene):

        self.scene = scene  # type: GSVScene
        self.node = node
        self.type = node.getType()

        self.gsv_action = None
        self.gsv_action = self.scene.settings["nodes"][self.type]["action"]

        self.gsvs = self.scene.settings["nodes"][self.type]["structure"]  # type: callable
        self.gsvs = self.gsvs(node)  # type: dict

        logger.debug(
            "[GSVNode][__init__] Finished for node <{}> // "
            "{} gsvs found."
            "".format(node, len(self.gsvs))
        )

        return

    def __str__(self):
        return "{}({})".format(self.node.getName(), self.type)

    @property
    def node_name(self):
        """
        Returns:
            str: Name of the Katana node.
        """
        return self.node.getName()

    @property
    def is_setter(self):
        """
        Returns:
            bool: True if the node set a GSV
        """
        return self.gsv_action == "setter"

    @property
    def is_getter(self):
        """
        Returns:
            bool: True if the node use a GSV without setting it.
        """
        return self.gsv_action == "getter"

    def select_edit(self):
        """
        Select and set the katana node to edited in the UI.
        """
        NodegraphAPI.SetAllSelectedNodes([self.node])
        NodegraphAPI.SetNodeEdited(self.node, True, exclusive=True)
        return


class GSVObject(object):
    """
    Represent a GSV as a python object. Allow to know which node is using this
    gsv and what value it can take.

    A GSV is considered as locked when it's value is set locally
    in the Nodegraph.

    a GSV can be local or global (see Katana doc).

    Args:
        name(str): gsv name used in the nodegraph
        scene(GSVScene): parent scene

    Attributes:
        name: Name of the local GSV
        scene: Parent scene this GSV can found in.
        nodes: List of nodes that are using this GSV.
        values: List of value the GSV can take.
        type: If the gsv is global/local. Used by the corresponding properties.

    """

    __instances = list()

    global_type = "global"
    local_type = "local"

    def __new__(cls, *args, **kwargs):

        name = kwargs.get("name") or args[0]  # type: str
        scene = kwargs.get("scene") or args[1]  # type: GSVScene

        # If the variable name is specified as excluded return None
        if name in scene.settings["excluded"]:
            return None

        # try to find if an instance of this class with the same name and same
        # parented scene already exists.
        # If yes, return it instead of creating a new one.
        for instance in cls.__instances:
            if instance.name == name and instance.scene == scene:
                return instance  # type: GSVObject

        new_instance = super(GSVObject, cls).__new__(cls)
        cls.__instances.append(new_instance)
        return new_instance

    def __init__(self, name, scene):

        self.name = name  # type: str
        self.scene = scene  # type: GSVScene
        self.nodes = list()  # type: List[GSVNode]
        self.values = list()  # type: List[str]
        self.type = None  # type: str

    def __build_nodes(self):
        """
        Find all the nodes in the scene that use the current gsv name.
        This nodes are setter and getters.
        """

        # node order must be maintained
        self.nodes = list()

        for gsvnode in self.scene.nodes:

            if isinstance(gsvnode.gsvs.get(self.name), list):
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
            v = node.gsvs.get(self.name)
            if v:
                # make sure every item inside is a str with map()
                self.values.extend(map(str, v))

            continue

        # remove duplicates values
        self.values = list(OrderedDict.fromkeys(self.values))

        return

    def __set_type(self):
        """
        Find if the GSV name is in global GSV and set type attribute to global
         or local accordingly.
        """

        global_gsv_param = NodegraphAPI.GetRootNode().getParameter('variables')
        global_gsvs = [
            param.getName() for param in global_gsv_param.getChildren()
        ]

        if self.name in global_gsvs:
            self.type = self.global_type
        else:
            self.type = self.local_type

        return

    @property
    def locked(self):
        """
        Last value the GSV has been set to or None if it has never been set.
        "Set" also mean "deleted" (VariableDelete)

        TODO last value is hard to determine so consider the result
         an approximation for now.

        Returns:
            None or str:
        """

        value = None

        # self.nodes should be ordered by the nodegraph flow, meaning the last
        # setter node we find is the one used to set the value
        for node in self.nodes:
            if node.is_setter:
                # gsv_values return a list but for setter nodes this list will
                # always have one index anyway.
                value = node.gsvs.get(self.name, list())[0]

        return value

    @property
    def is_global(self):
        return self.type == self.global_type

    @property
    def is_local(self):
        return self.type == self.local_type

    def build(self):

        self.__build_nodes()
        self.__build_values()
        self.__set_type()

        logger.debug(
            "[GSVObject][build] Finished for name=<{}>".format(self.name)
        )
        return

    def todict(self):
        """
        Return a dictionnary representation of the class.
        """

        if not self.values:
            logger.warning("[GSVObject][todict] self.values is empty")
        if not self.nodes:
            logger.warning("[GSVObject][todict] self.nodes is empty")

        return {
            "type": self.type,
            "name": self.name,
            "values": self.values,
            "nodes": map(str, self.nodes),
            "locked": self.locked
        }


class GSVScene(object):
    """
    A group of node associated with an arbitrary number of gsvs.
    Disabled nodes are considered as excluded.

    Attributes:
        nodes(List[GSVNode]): list of GSVnodes
        gsvs(List[GSVObject]): list of GSVObject build from <nodes>

    Args:
        settings(GSVSettings):
    """

    def __init__(self, settings):

        self.settings = settings  # type: GSVSettings
        self.nodes = list()  # type: List[GSVNode]
        self.gsvs = list()  # type: List[GSVObject]

    def __parse_all(self):
        """
        Build the <nodes> attribute.
        """
        # node order must be maintained

        for node_class in self.settings["nodes"].keys():

            nodes = NodegraphAPI.GetAllNodesByType(
                node_class,
                sortByName=False
            )  # type: list
            for node in nodes:

                self.nodes.append(GSVNode(node, scene=self))

            continue

        self.__parse_post_actions()
        return

    def __parse_upstream(self, logical):
        """
        Build the <nodes> attribute.

        Args:
            logical(bool):
                True to process only logical connections between nodes.
        """
        # node order must be maintained
        # if not logical:
        #     raise NotImplementedError(
        #         "__parse_upstream is not implemented yet."
        #     )

        source = self.settings["parsing"]["source"]
        if not source:
            # By safety but this should never happens
            raise ValueError(
                "Can't perform __parse_logical_upstream as"
                "no source has been submitted through settings"
            )

        settings = ParseSettings()
        settings.include_groups = True
        settings.logical = logical
        settings.exluded_asGroupsNodeType = self.settings[
            "parsing"]["excluded"]["asGroupsNodeType"]

        # list of all upstream logical nodes, need to be filtered after
        scene = SceneParser()
        scene.settings = settings
        upstream_nodes = scene.get_upstream_nodes(source)

        for knode in upstream_nodes:

            # filter nodes using nodeTypes specified in settings
            if knode.getType() not in self.settings["nodes"].keys():
                continue

            gsvnode = GSVNode(node=knode, scene=self)
            self.nodes.append(gsvnode)
            continue

        self.__parse_post_actions()
        return

    def __parse_post_actions(self):
        """
        Actions that need to be perforemed post parsing methods execution.
        """
        # remove nodes that are disabled
        self.nodes = filter(
            lambda gsvnode: not gsvnode.node.isBypassed(), self.nodes
        )

        return

    def __build_nodes(self):
        """
        Find all the nodes in the nodegraph that use the gsv feature depending
        of the mode specified in self.settings.
        """

        # reset self.nodes first
        self.nodes = list()

        mode = self.settings["parsing"]["mode"]

        if mode == "all_scene":
            self.__parse_all()

        elif mode == "logical_upstream":
            self.__parse_upstream(logical=True)

        elif mode == "upstream":
            self.__parse_upstream(logical=False)

        else:
            raise ValueError(
                "Unsuported mode <{}> in settings passed.".format(mode)
            )

        logger.debug(
            "[GSVObject][__build_nodes] Finished. {} nodes found."
            "".format(len(self.nodes))
        )

        return

    def __build_gsvs(self):
        """
        From the node list find what gsv is used and build its object.
        """

        # reset self.gsvs first
        self.gsvs = list()

        for gsvnode in self.nodes:

            for gsvname in gsvnode.gsvs.keys():

                gsv = GSVObject(gsvname, self)  # can return None !
                # gsv might be excluded, so it returns None
                if not gsv:
                    continue
                # avoid adding multiples times the same instance
                if gsv in self.gsvs:
                    continue

                self.gsvs.append(gsv)
                continue

            continue

        # TODO why this is not in the above loop ?
        # we don't forget to build the gsv object if we want to use its attributes
        for gsvlocal in self.gsvs:
            gsvlocal.build()

        logger.debug(
            "[GSVScene][_build_gsvs] Finished. {} gsv found."
            "".format(len(self.gsvs))
        )

        return

    def build(self):
        """
        Scene is empty until you build it. Can also be used to update it.
        Fill the <nodes> and <gsvs> instance attributes.
        """

        self.__build_nodes()
        self.__build_gsvs()

        return

    def todict(self):
        return {"gsvs": list(map(lambda obj: obj.todict(), self.gsvs))}
