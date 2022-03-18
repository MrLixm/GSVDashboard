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
from __future__ import absolute_import

from .Node import GSVDashboardNode
from . import c


__all__ = ["GSVDashboardNode", "get_editor"]


version = "v{}.{}.{}-{}.{}".format(
    c.v_major, c.v_minor, c.v_patch, c.v_dev, c.v_published
)


def get_editor():
    """
    Return the SuperTool interface class for registering in Katana.
    """

    from .Editor import GSVDashboardEditor

    return GSVDashboardEditor