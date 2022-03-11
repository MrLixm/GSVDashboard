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
import os.path

__all__ = [
    "Colors",
    "Icons"
]


class Colors:
    """

    """

    """"rgb(237, 195, 44)"""
    yellow_global = (237, 195, 44)
    """"rgb(157, 128, 24)"""
    yellow_global_disabled = (157, 128, 24)
    """"rgb(82, 153, 82)"""
    edited = (82, 153, 82)
    """rgb(104, 91, 186)"""
    viewed = (104, 91, 186)
    """rgb(140, 140, 140)"""
    text_disabled = (140, 140, 140)
    """rgb(57, 217, 121)"""
    edit = (57, 217, 121)  # used by edit button
    """rgb(114, 114, 114)"""
    reset = (114, 114, 114)  # used by reset button


class Icons:
    """

    """

    __root = os.path.join(os.path.dirname(__file__), "icons")

    status_g_locked = os.path.join(__root, "status_g_locked.svg")
    status_g_viewed = os.path.join(__root, "status_g_viewed.svg")
    status_g_edited = os.path.join(__root, "status_g_edited.svg")
    status_l_edited = os.path.join(__root, "status_l_edited.svg")
    status_l_locked = os.path.join(__root, "status_l_locked.svg")
    status_l_viewed = os.path.join(__root, "status_l_viewed.svg")
    status_node_getter = os.path.join(__root, "status_node_getter.svg")
    status_node_setter = os.path.join(__root, "status_node_setter.svg")
    info = os.path.join(__root, "info.svg")
    logo = os.path.join(__root, "gsvdb-logo.svg")
