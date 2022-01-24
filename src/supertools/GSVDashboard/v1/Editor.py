"""

"""
import logging

from PyQt5 import (
    QtCore,
    QtWidgets
)
from Katana import (
    Utils
)


from . import c
# import for type hints only
try:
    from .Node import GSVDashboardNode
except:
    pass


__all__ = ['GSVDashboardEditor']

logger = logging.getLogger("{}.Editor".format(c.name))


class GSVDashboardEditor(QtWidgets.QWidget):
    """
    Args:
        parent(QtWidgets.QWidget or None):
        node(GSVDashboardNode):
    """

    def __init__(self, parent, node):

        super(GSVDashboardEditor, self).__init__(parent)

        self.__node = node
        self.__node.upgrade()
        self.__frozen = True

        return

    """------------------------------------------------------------------------
    Overrides
    """

    # We thaw/freeze the UI when it is shown/hidden.  This means that we aren't
    # wasting CPU cycles by listening and responding to events when the editor
    # is not active.
    def showEvent(self, event):
        """
        When this Widget is showed.
        """
        super(GSVDashboardEditor, self).showEvent(event)

        if not self.__frozen:
            return

        self.__frozen = False
        self.__setup_event_handlers(True)

        return

    def hideEvent(self, event):
        """
        When this Widget is hidden.
        """
        super(GSVDashboardEditor, self).hideEvent(event)

        if self.__frozen:
            return

        self.__frozen = True
        self.__setup_event_handlers(False)

        return

    def __setup_event_handlers(self, enabled):
        """
        Args:
            enabled(bool): Set if the even handler is enabled or not.
        """
        Utils.EventModule.RegisterEventHandler(
            self.__idle_callback,
            'event_idle',
            enabled=enabled
        )
        Utils.EventModule.RegisterCollapsedHandler(
            self.__updateCB,
            'port_connect',
            enabled=enabled
        )
        Utils.EventModule.RegisterCollapsedHandler(
            self.__updateCB,
            'port_disconnect',
            enabled=enabled
        )
        Utils.EventModule.RegisterCollapsedHandler(
            self.__updateCB,
            'parameter_finalizeValue',
            enabled=enabled
        )

        return

