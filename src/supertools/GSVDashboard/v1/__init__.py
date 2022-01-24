"""

"""
from __future__ import absolute_import

from .Node import GSVDashboardNode


__all__ = ["GSVDashboardNode", "get_editor"]


def get_editor():
    """
    Return the SuperTool interface class for registering in Katana.
    """

    from .Editor import GSVDashboardEditor

    return GSVDashboardEditor