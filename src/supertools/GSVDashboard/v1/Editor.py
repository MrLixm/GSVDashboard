"""

"""
import logging

try:
    from typing import List, Optional, Tuple, Union
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
from . import EditorResources as resources
from .EditorComponents import (
    QModMenu,
    TreeWidgetItemGSV,
    GSVPropertiesWidget,
    QTitleBar
)
# import for type hints only
try:
    from .Node import GSVDashboardNode, SuperToolGSV
    from .GSV import *
except:
    pass


__all__ = ['GSVDashboardEditor']

logger = logging.getLogger("{}.Editor".format(c.name))


class GSVDashboardEditor(QtWidgets.QWidget):
    """
    Args:
        node(GSVDashboardNode): SuperTool node
        parent(QtWidgets.QWidget or None): dd

    Attributes:
        __node(GSVDashboardNode): SuperTool node
        __frozen(bool): used for ui update handling
    """

    def __init__(self, parent, node):

        super(GSVDashboardEditor, self).__init__(parent)

        self.__node = node  # type: GSVDashboardNode
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
        self.__update_tw1 = False
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

        # these are the events that will update the treewidget
        events4twupdate = [
            "port_disconnect",
            "port_connect",
            "parameter_finalizeValue",
            "parameter_setValue",
            "node_setBypassed",
            "node_setName"
        ]
        for event in events4twupdate:
            Utils.EventModule.RegisterCollapsedHandler(
                self.__process_event,
                event,
                enabled=enabled
            )

        # this is once the events are finished, actually update tw1
        Utils.EventModule.RegisterCollapsedHandler(
            self.__idle_callback,
            "event_idle",
            enabled=enabled
        )
        return

    def __idle_callback(self, *args, **kwargs):
        """
        Called when an event is finished.
        Update ``tw1`` if ``__update_tw1`` is set to True.
        """

        # if self.__update_tw1:
        #     self.__tw_update()
        #     self.__update_tw1 = False

        return

    def __process_event(self, event_data):
        """
        Args:
            event_data(list of list):
                event data from katana
                [ [ "event type", int, {event source} ], ... ]
        """
        if self.__update_tw1:
            return

        for event in event_data:

            event_source = event[2]
            print("{}: {}".format(event[0], event_source))  # TODO remove

            self.__update_tw1 = True

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
        self.btn_update = QtWidgets.QPushButton()
        self.cbb_source = QtWidgets.QComboBox()
        self.tw1 = QtWidgets.QTreeWidget()
        self.mmnu_props = QModMenu()

        # self.ttlb_props_hd_locked = QTitleBar()
        # self.ttlb_props_hd_reset = QTitleBar()
        # self.ttlb_props_hd_edit = QTitleBar()
        # self.ttlb_props_footer = QTitleBar()
        # self.btn_reset = QtWidgets.QPushButton()  # TODO
        # self.btn_edit = QtWidgets.QPushButton()  # TODO
        self.gsv_props_wgt = GSVPropertiesWidget()  # TODO

        # ==============
        # Modify Widgets
        # ==============

        # treewidget
        # self.tw1.setHeaderHidden(True)
        self.tw1.setColumnCount(TreeWidgetItemGSV.column_number())
        self.tw1.setMinimumHeight(150)
        self.tw1.setAlternatingRowColors(True)
        self.tw1.setSortingEnabled(True)
        self.tw1.setUniformRowHeights(True)
        self.tw1.setRootIsDecorated(False)
        self.tw1.setItemsExpandable(False)
        # select only one row at a time
        self.tw1.setSelectionMode(self.tw1.SingleSelection)
        # select only rows
        self.tw1.setSelectionBehavior(self.tw1.SelectRows)
        # remove dotted border on columns
        self.tw1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tw1.setColumnWidth(0, TreeWidgetItemGSV.column_size(0)[0])
        self.tw1.setColumnWidth(1, TreeWidgetItemGSV.column_size(1)[0])
        self.tw1.setHeaderLabels(TreeWidgetItemGSV.column_labels())
        tw1_header = self.tw1.header()
        # The user can resize the section
        tw1_header.setSectionResizeMode(tw1_header.Interactive)

        # # QPushButton
        self.btn_update.setIcon(
            QtGui.QIcon(
                UI4.Util.IconManager.GetPixmap(
                    r"Icons\update_active20_hilite.png"
                )
            )
        )
        # self.btn_edit.setText("edit")
        # self.btn_reset.setText("reset")
        #
        # QModeMenu
        self.mmnu_props.set_content(self.gsv_props_wgt)
        self.mmnu_props.build()
        # mgprop_setup = {
        #     GSVPropertiesWidget.status_editable: [
        #         self.ttlb_props_hd_edit,
        #         self.ttlb_props_footer
        #     ],
        #     GSVPropertiesWidget.status_locked: [
        #         self.ttlb_props_hd_locked,
        #         self.ttlb_props_footer
        #     ],
        #     GSVPropertiesWidget.status_edited: [
        #         self.ttlb_props_hd_reset,
        #         self.ttlb_props_footer
        #     ],
        # }
        # for _status, _widgets in mgprop_setup.items():
        #
        #     self.mmnu_props.add_status(
        #         _status,
        #         replace_default=True,
        #         set_to_current=True
        #     )
        #     self.mmnu_props.set_header_widget(_widgets[0])
        #     self.mmnu_props.set_footer_widget(_widgets[1])
        #     continue

        # ==============
        # Add to Layouts
        # ==============
        self.setLayout(self.lyt_m)
        self.lyt_m.addWidget(self.btn_update)
        # self.lyt_m.addWidget(self.ttlb_header)
        self.lyt_m.addWidget(self.tw1)
        self.lyt_m.addWidget(self.mmnu_props)

        # ==============
        # Connections
        # ==============

        self.tw1.itemSelectionChanged.connect(self.__tw_selection_changed)
        self.btn_update.clicked.connect(self.__tw_update)
        # self.btn_reset.clicked.connect(self.gsv_props_wgt.reset)
        # self.btn_edit.clicked.connect(self.gsv_props_wgt.reset)
        #
        # # GSVPropertiesWidget
        # self.gsv_props_wgt.value_changed_sgn.connect(
        #     self.__gsv_set_value
        # )
        # # the QMenuGroup should have already the status built upon the ones
        # # available in GSVPropertiesWidget so it's safe to do this
        # self.gsv_props_wgt.status_changed_sgn.connect(
        #     self.mmnu_props.set_status_current
        # )

        return

    def __tw_update(self):
        """
        """

        parse_mode = "logical_upstream"  # TODO

        # clear teh treewidget before adding new entries
        self.tw1.clear()

        st_gsvs = self.__node.get_gsvs(mode=parse_mode)
        for st_gsv in st_gsvs:
            qtwi = TreeWidgetItemGSV(st_gsv=st_gsv, parent=self.tw1)

        self.__tw_selection_changed()
        logger.debug(
            "[GSVDashboardEditor][__tw_update] Finished."
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
        self.gsv_props_wgt.set_data(gsv_data)

        logger.debug(
            "[GSVDashboardEditor][__lw_selection_changed] Finished."
            "SuperToolGSV found is <{}>.".format(gsv_data)
        )
        return

    def __tw_selected_get_gsv_data(self):
        """
        Return the SuperToolGSV instance for the currently selected GSV in
        the treewidget.

        Returns:
            SuperToolGSV or None:
        """
        selection = self.tw1.selectedItems()  # type: List[TreeWidgetItemGSV]
        if not selection:
            logger.debug(
                "[GSVDashboardEditor][__tw_selected_get_gsv_data] Called but"
                "self.tw1.selectedItems() return None ?"
            )
            return

        # selection in the GUI can only be done on one item anyway
        selection = selection[0]  # type: TreeWidgetItemGSV

        gsv_data = selection.gsv  # type: SuperToolGSV
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


