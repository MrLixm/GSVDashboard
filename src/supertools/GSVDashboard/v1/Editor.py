"""

"""
import json
import logging
from functools import partial

try:
    from typing import List
except ImportError:
    pass

from PyQt5 import (
    QtCore,
    QtWidgets,
    QtGui
)
from Katana import (
    Utils,
    UI4
)


from . import c
# import for type hints only
try:
    from .Node import GSVDashboardNode
    from .GSV import *
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

        self.__uibuild()

        return

    """------------------------------------------------------------------------
    Overrides
    """

    # We thaw/freeze the UI when it is shown/hidden.  This means that we aren't
    # wasting CPU cycles by listening and responding to events when the editor
    # is not active.
    def showEvent(self, event):
        """
        When the node is set to edit mode.
        """
        super(GSVDashboardEditor, self).showEvent(event)

        if not self.__frozen:
            return

        self.__frozen = False
        self.__setup_event_handlers(True)

        return

    def hideEvent(self, event):
        """
        When the node get out of edit mode.
        """
        super(GSVDashboardEditor, self).hideEvent(event)

        if self.__frozen:
            return

        self.__frozen = True
        self.__setup_event_handlers(False)

        return

    def __setup_event_handlers(self, enabled):
        """
        Associate an event in the Katana scene with a method on this class.

        Here we are updating the listWidget only for 3 events.

        Args:
            enabled(bool): Set if the even handler is enabled or not.
        """

        # these are the events that will update the listWidget (__lw_update())
        events4lwupdate = [
            "port_disconnect",
            "port_connect",
            "parameter_finalizeValue",
            "parameter_setValue",
        ]
        for event in events4lwupdate:
            Utils.EventModule.RegisterCollapsedHandler(
                self.__tw_update,
                event,
                enabled=enabled
            )
        return

    """------------------------------------------------------------------------
    Interactions
    """

    def __uibuild(self):

        # ==============
        # Create Layouts
        # ==============
        self.lyt_m = QtWidgets.QVBoxLayout()

        # ==============
        # Create Widgets
        # ==============
        self.ttlb_header = QTitleBar()
        self.tw1 = QtWidgets.QTreeWidget()
        self.mg_prop = QModMenu()
        self.ttlb_props_hd_locked = QTitleBar()
        self.ttlb_props_hd_reset = QTitleBar()
        self.ttlb_props_hd_edit = QTitleBar()
        self.ttlb_props_footer = QTitleBar()
        self.btn_reset = QtWidgets.QPushButton()  # TODO
        self.btn_edit = QtWidgets.QPushButton()  # TODO
        self.wgt_gsv_prop = GSVPropertiesWidget()  # TODO

        # ==============
        # Modify Widgets
        # ==============

        # treewidget
        self.tw1.setMinimumHeight(200)
        self.tw1.setHeaderHidden(True)
        self.tw1.setAlternatingRowColors(True)
        self.tw1.setSortingEnabled(True)
        self.tw1.setItemsExpandable(False)
        self.tw1.setUniformRowHeights(True)
        self.tw1.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tw1.itemSelectionChanged.connect(self.__tw_selection_changed)

        # QModeMenu
        self.mg_prop.set_content(self.mg_prop_content)
        mgprop_setup = {
            GSVPropertiesWidget.status_editable: [
                self.ttlb_props_hd_edit,
                self.ttlb_props_footer
            ],
            GSVPropertiesWidget.status_locked: [
                self.ttlb_props_hd_locked,
                self.ttlb_props_footer
            ],
            GSVPropertiesWidget.status_edited: [
                self.ttlb_props_hd_reset,
                self.ttlb_props_footer
            ],
        }
        for _status, _widgets in mgprop_setup.items():

            self.mg_prop.add_status(
                _status,
                replace_default=True,
                set_to_current=True
            )
            self.mg_prop.set_header_widget(_widgets[0])
            self.mg_prop.set_footer_widget(_widgets[1])
            continue

        # GSVPropertiesWidget
        self.wgt_gsv_prop.value_changed_sgn.connect(
            self.__gsv_set_value
        )
        # the QMenuGroup should have already the status built upon the ones
        # available in GSVPropertiesWidget so it's safe to do this
        self.wgt_gsv_prop.status_changed_sgn.connect(
            self.mg_prop.set_status_current
        )

        # ==============
        # Add to Layouts
        # ==============
        self.setLayout(self.lyt_m)
        self.lyt_m.addWidget(self.ttlb_header)
        self.lyt_m.addWidget(self.tw1)
        self.lyt_m.addWidget(self.mg_prop)

        return

    def __tw_update(self, data):
        """
        Args:
            data(list of list):
                event data from katana
                [ [ "event type", int, {event source} ], ... ]
        """
        logger.info(
            "[__lw_update]:\n{}"
            "".format(json.dumps(data, indent=4, default=str))
        )

        return

    def __tw_selection_changed(self):
        """
        When selection change, update the properties displayed.
        """

        gsv_data = self.__tw_selected_get_gsv_data()
        if not gsv_data:
            # TODO [optional] see what to do
            return

        # update the properties
        self.wgt_gsv_prop.set_data(gsv_data)
        # then update the idget status depending of the gsv data
        if gsv_data.is_locked():
            self.mg_prop.set_status_current(self.status_locked)
        # TODO find a way to set mg_prop status

        logger.info("[__lw_selection_changed]")
        return

    def __tw_selected_get_gsv_data(self):
        """
        Return the GSV class instance for the currently selected GSV in
        the treewidget

        Returns:
            GSVLocal or None:
        """
        selection = self.tw1.selectedItems()  # type: List[QtWidgets.QTreeWidgetItem]
        if not selection:
            return
        selection = selection[0]  # type: QtWidgets.QTreeWidgetItem

        gsv_data = selection.data(TODO)  # type: GSVLocal
        if not gsv_data:
            logger.error(
                "[GSVDashboardEditor][__tw_get_gsv_data] No gsv data found "
                "for the currently selected tree widget item <{}>. This is"
                "not supposed to happens ?!"
                "".format(selection)
            )
        return gsv_data

    def __gsv_set_value(self, gsv_object):
        pass


class GSVPropertiesWidget(QtWidgets.QWidget):
    """

    ::

        [gsv name ] [gsv value ▾]

        [ node1                 ]
        [ node2                 ]
        [ node3                 ]


    """

    value_changed_sgn = QtCore.pyqtSignal(str)
    status_changed_sgn = QtCore.pyqtSignal(str)

    status_editable = "editable"
    status_edited = "edited"
    status_locked = "locked"  # =read only

    def __init__(self):

        super(GSVPropertiesWidget, self).__init__()

        self.__status = self.status_locked  # default status is read only
        self.__data = None  # type: GSVLocal
        self.__edited = False

        return

    def __uibuild(self):

        # TODO build rest of ui

        self.cbb_value = QtWidgets.QComboBox()
        self.cbb_value.currentIndexChanged.connect(self.__value_changed)

        return

    def __value_changed(self):
        """
        To call when the user edit the value combobox.
        """
        self.__edited = True
        value = self.cbb_value.currentText()
        self.value_changed_sgn.emit(value)

        return

    def reset(self):
        """
        Reset the interface as it was never modified by the user
        """

        self.__uibuild()

        return

    def set_data(self, gsv_data):

        self.__data = gsv_data
        self.update_status()

        return

    def update_status(self):
        """
        Update __status attribute according to self data.
        """
        if not self.__data:
            self.__status = self.status_locked

        elif self.__data.is_locked():
            self.__status = self.status_locked

        elif self.__edited:
            self.__status = self.status_edited

        elif not self.__status:
            self.__status = self.status_editable

        else:
            # This should never happens
            raise ValueError(
                "Imposible to find a status for the GSVPropertiesWidget for"
                "the GSV <{}>".format(self.__data.name)
            )

        # emit the new status
        self.status_changed_sgn.emit(self.__status)

        return


class QTitleBar(QtWidgets.QWidget):

    border_radius = 4

    def __init__(self, parent=None, title=None):

        super(QTitleBar, self).__init__(parent)
        self.__title = title

        # must be in the instance else the mainWindow is not created yet
        self.mainwindow = UI4.App.MainWindow.GetMainWindow()
        self.palette = self.mainwindow.palette()

        return

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # build the background shape
        path = QtGui.QPainterPath()
        #
        brush = QtGui.QBrush()
        brush.setColor(
            self.palette.color(QtGui.QPalette.Normal, QtGui.QPalette.Shadow)
        )
        brush.setStyle(QtCore.Qt.SolidPattern)

        rect = QtCore.QRectF(event.rect())

        path.addRoundedRect(rect, self.border_radius, self.border_radius)

        painter.setBrush(brush)
        painter.fillPath(path, painter.brush())

        # build the text
        if self.__title:
            pen = QtGui.QPen()
            pen.setColor(
                self.palette.color(QtGui.QPalette.Disabled, QtGui.QPalette.Text)
            )
            font = self.mainwindow.font()

            painter.setFont(font)
            painter.setPen(pen)
            painter.drawText(rect, QtCore.Qt.AlignLeft, self.__title)

        return


class QModMenu(QtWidgets.QWidget):
    """
    Container widget with a header and a footer widget. In between you have a
    content widget.
    The widget can have multiple status that can be added on the fly.
    Each status store a different widget setup for header/footer.
    ::

        --[header widget]-------------------------------
        |
        |   content
        |
        --[footer widget]-------------------------------

    Header and footer should be horizontally shaped.
    The content and footer widget are optional.
    """

    def __init__(self, parent=None):

        super(QModMenu, self).__init__(parent)

        self.__content = None  # type: QtWidgets.QWidget
        self.__status = {
            "default": {
                "header": None,  # type: List[QtWidgets.QWidget]
                "footer": None,  # type: List[QtWidgets.QWidget]
            }
        }

        return

    def add_status(self, status_id, replace_default=False, set_to_current=True):
        """

        Args:
            status_id(any):
                object used to identify a status
            replace_default(bool):
                If true , it just delete the default key if it exists
            set_to_current(bool):
                If true, also change the current status to the newly added one.

        """
        pass

    def set_status_current(self, status_id):
        """

        Args:
            status_id(any): o
                object used to indentify the status

        Can only take on argument !!
        """
        pass

    def get_status_current(self):
        pass

    def get_status_list(self):
        pass

    def reset_status(self, status=None, reset_all=False):
        return

    def set_content(self, content_widget):
        pass

    def get_content(self):
        return self.__content

    def set_header_widget(self, widget, status=None):
        pass

    def set_footer_widget(self, widget, status=None):
        # Probably not implemented for GSVDashboard
        pass

