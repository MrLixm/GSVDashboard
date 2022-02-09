"""

"""
import logging
import pprint

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
    QTitleBar,
    ResetButton,
    EditButton,
    GSVTreeWidget,
    UpdateButton
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

        self.__uicook()

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

    def __uicook(self):

        # ==============
        # Create Layouts
        # ==============
        self.lyt_m = QtWidgets.QVBoxLayout()

        # ==============
        # Create Widgets
        # ==============
        self.ttlb_header = QTitleBar(title="GSVs")
        self.btn_update = UpdateButton()
        self.cbb_source = QtWidgets.QComboBox()
        self.tw1 = GSVTreeWidget()
        self.mmnu_props = QModMenu()

        self.ttlb_props_hd_locked = QTitleBar(title="Properties")
        self.ttlb_props_hd_reset = QTitleBar(title="Properties")
        self.ttlb_props_hd_edit = QTitleBar(title="Properties")
        self.ttlb_props_footer = QTitleBar()
        self.btn_reset = ResetButton()
        self.btn_edit = EditButton()
        self.gsv_props_wgt = GSVPropertiesWidget()

        # ==============
        # Modify Widgets
        # ==============

        # # QPushButton
        self.btn_update.setToolTip("Manually update the GSV list.")
        self.btn_edit.setText("edit")
        self.btn_edit.setToolTip(
            "Create a VariableSet to edit the selected GSV."
        )
        self.btn_reset.setText("reset")
        self.btn_reset.setToolTip(
            "Delete the modified value for the selected GSV. "
            "This GSV is no more "
            "edited by this super tool."
        )
        # QToolBars
        self.ttlb_header.add_widget(self.btn_update)
        self.ttlb_props_hd_locked.set_icon(resources.Icons.status_l_locked)
        self.ttlb_props_hd_reset.set_icon(resources.Icons.status_l_edited)
        self.ttlb_props_hd_reset.add_widget(self.btn_reset)
        self.ttlb_props_hd_edit.set_icon(resources.Icons.status_l_viewed)
        self.ttlb_props_hd_edit.add_widget(self.btn_edit)

        # QModeMenu
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
        for __status, _widgets in mgprop_setup.items():
            self.mmnu_props.add_status(
                __status,
                replace_default=True,
                set_to_current=True
            )
            self.mmnu_props.set_header_widget(_widgets[0])
            self.mmnu_props.set_footer_widget(_widgets[1])
            continue
        self.mmnu_props.set_content(self.gsv_props_wgt)
        self.mmnu_props.update()

        # ==============
        # Add to Layouts
        # ==============
        self.setLayout(self.lyt_m)
        self.lyt_m.setSpacing(8)
        self.lyt_m.addWidget(self.ttlb_header)
        # self.lyt_m.addWidget(self.ttlb_header)
        self.lyt_m.addWidget(self.tw1)
        self.lyt_m.addWidget(self.mmnu_props)

        # ==============
        # Connections
        # ==============

        self.tw1.itemSelectionChanged.connect(self.__tw_selection_changed)
        self.btn_update.clicked.connect(self.__tw_update)
        self.btn_reset.clicked.connect(self.gsv_props_wgt.set_unedited)
        self.btn_edit.clicked.connect(self.gsv_props_wgt.set_edited)
        # GSVPropertiesWidget
        self.gsv_props_wgt.value_changed_sgn.connect(
            self.__gsv_set_value
        )
        self.gsv_props_wgt.status_changed_sgn.connect(
            self.__props_status_changed
        )
        self.gsv_props_wgt.unedited_sgn.connect(
            self.__gsv_remove_edit
        )

        return

    def __tw_update(self):
        """
        """
        parse_mode = "logical_upstream"  # TODO
        logger.debug(
            "[{}][__tw_update] Started with mode: <{}>."
            "".format(self.__class__.__name__, parse_mode)
        )

        # clear the treewidget before adding new entries
        self.tw1.clear()

        st_gsvs = self.__node.get_gsvs(mode=parse_mode)
        qtwi = None
        for st_gsv in st_gsvs:
            qtwi = TreeWidgetItemGSV(st_gsv=st_gsv, parent=self.tw1)

        self.__tw_select_last_selected()
        self.__tw_selection_changed()
        logger.debug(
            "[{}][__tw_update] Finished.".format(self.__class__.__name__)
        )
        return

    def __tw_select_last_selected(self):
        """
        When updating the tw we loose the selection, select back the last
        item that was selected if possible.
        """
        gsv_name = self.tw1.last_selected
        if not gsv_name:
            return

        to_select = None
        for twitem in self.tw1.get_all_items():
            if twitem.gsv.name == gsv_name:
                to_select = twitem

        if to_select:
            self.tw1.setCurrentItem(to_select)

        return

    def __tw_selection_changed(self):
        """
        When selection change, update the properties displayed.
        """

        gsv_data = self.tw1.get_selected_gsv_data()
        if not gsv_data:
            # TODO [optional] see what to do, but should "never" happens.
            return

        # self.tw1.last_selected = gsv_data.name

        # update the properties
        self.gsv_props_wgt.set_data(gsv_data)

        logger.debug(
            "[{}][__tw_selection_changed] Finished."
            "SuperToolGSV found is <{}>."
            "".format(self.__class__.__name__, gsv_data)
        )
        return

    def __props_status_changed(self, new_status, previous_status):
        """
        Called by signals when status is changed on the GSVPropertiesWidget.

        Args:
            new_status(str):
            previous_status(str):
        """
        # Change the QMenuGroup status based on the GSVPropertiesWidget's one.
        # (the QMenuGroup should have already the status built upon the ones
        # available in GSVPropertiesWidget so it's safe to do this)
        self.mmnu_props.set_status_current(new_status)
        logger.debug(
            "[{}][__props_status_changed] Finished. new_status=<>,"
            "previous_status=<{}>"
            "".format(self.__class__.__name__, new_status, previous_status)
        )
        return

    def __gsv_set_value(self, stgsv, new_value):
        """
        Called by signals from GSVPropertiesWidget.
        Asked to the SuperTool node to edit the given GSV.

        Args:
            stgsv(SuperToolGSV):
            new_value(str):
        """
        if new_value is None:
            logger.debug(
                "[{}][__gsv_set_value] new_value arg passed is None. Returning."
                "".format(self.__class__.__name__)
            )
            return

        self.__node.edit_gsv(name=stgsv.name, value=new_value)
        self.__tw_update()
        return

    def __gsv_remove_edit(self, stgsv):
        """
        Args:
            stgsv(SuperToolGSV):
        """
        self.__node.unedit_gsv(stgsv.name)
        self.__tw_update()
        return
