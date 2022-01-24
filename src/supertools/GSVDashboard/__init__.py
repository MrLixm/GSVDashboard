"""

"""
from __future__ import absolute_import

import Katana

from . import v1 as GSVDashboard


if GSVDashboard:

    PluginRegistry = [
        (
           'SuperTool',
           2,
           'GSVDashboard',
           (GSVDashboard.GSVDashboardNode, GSVDashboard.get_editor)
        )
    ]