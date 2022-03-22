"""
Configure scene parsing settings from parameters in the scene.

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
import logging
try:
    from typing import Optional, List
except ImportError:
    pass

from . import c
from . import GSV

from Katana import NodegraphAPI

__all__ = [
    "get_parse_settings"
]

logger = logging.getLogger("{}.config".format(c.name))


def __get_settings_from_param(sparam):
    """
    Parse the given parameter and generate Settings from it.
    Child parameters excepted are :

    - excluded_gsv_names(str): comma separated list
        - gsvdb_excluded_gsv_names: same as above
    - excluded_as_grpnode_type(str): comma separated list
        - gsvdb_excluded_as_grpnode_type: same as above

    Args:
        sparam(NodegraphAPI.Parameter): param to get the child from

    Returns:
        GSV.GSVSettings or None:
            None if no parameter found to configure the settings.
    """

    time = NodegraphAPI.GetCurrentTime()
    settings = GSV.GSVSettings()
    # to determine if the settings was modified at least one time
    _set = False

    setting1 = (
            sparam.getChild("excluded_gsv_names") or
            sparam.getChild("gsvdb_excluded_gsv_names")
    )
    if setting1:
        value = setting1.getValue(time)  # type: Optional[str]
        value = value if value else ""
        value = value.replace(" ", "").split(",")  # type: List[str]
        settings["excluded"] = value
        _set = True

    setting1 = (
            sparam.getChild("excluded_as_grpnode_type") or
            sparam.getChild("gsvdb_excluded_as_grpnode_type")
    )
    if setting1:
        value = setting1.getValue(time)  # type: Optional[str]
        value = value if value else ""
        value = value.replace(" ", "").split(",")  # type: List[str]
        settings["parsing"]["excluded"]["asGroupsNodeType"] = value
        _set = True

    return settings if _set else None


def __get_from_node(node):
    """

    Args:
        node(NodegraphAPI.Node): node with the user parameters for
            settings config.

    Returns:
        GSV.GSVSettings or None:
            see __get_settings_from_param doctsring
    """

    if not node:
        return None

    prm_user = node.getParameter("user")
    settings = __get_settings_from_param(prm_user)

    logger.debug(
        "[__get_from_node] Finished with settings <{}>".format(settings)
    )
    return settings


def __get_from_project():
    """

    Returns:
        GSV.GSVSettings or None:
           see __get_settings_from_param doctsring

    """

    time = NodegraphAPI.GetCurrentTime()

    # let first check if the node exists
    node = NodegraphAPI.GetNode("GSVDB_config")
    if node:
        logger.debug(
            "[__get_from_project] Returned. Found node <GSVDB_config>"
        )
        return __get_from_node(node)

    # then parse project.user parameters
    uprm_proj = NodegraphAPI.GetRootNode().getParameter("user")
    if not uprm_proj:
        return None

    # if a config node is specified return its settings
    uprm_gsvdb_node = uprm_proj.getChild("gsvdb_config_node")
    if uprm_gsvdb_node:
        node_name = uprm_gsvdb_node.getValue(time)
        node = NodegraphAPI.GetNode(node_name)
        if not node:
            logger.error(
                "[config][__get_from_node] Given node name <{}> doesn't exists."
                "Check <project.user.gsvdb_config_node> parameter is correct."
                "".format(node_name)
            )
        logger.debug(
            "[__get_from_project] Returned. Found node <{}>".format(node_name)
        )
        return __get_from_node(node)

    # parse the user parameter and generate settings from them
    settings = __get_settings_from_param(uprm_proj)
    logger.debug(
        "[__get_from_project] Finished with settings <{}>".format(settings)
    )
    return settings


def get_parse_settings():
    """
    Parse scene for parameter used to configure the GSVSettings.
    Generate a default one if nothing found.

    Settings that can't be modified here (overiden later):
    - settings["parsing"]["mode"]
    - settings["parsing"]["source"]

    Returns:
        GSV.GSVSettings:
    """
    settings = __get_from_project()

    if not settings:
        settings = GSV.GSVSettings()
        settings["excluded"] = ["gafferState"]
        settings["parsing"]["excluded"]["asGroupsNodeType"] = [
            "GafferThree",
            "Importomatic",
            "LookFileLightAndConstraintActivator",
            "LookFileMultiBake",
            "LookFileManager",
            "NetworkMaterials",
            "ShadingGroup",
        ]

    return settings