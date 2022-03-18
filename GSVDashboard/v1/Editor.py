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
import logging
import os
import re
import time

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
from UI4.FormMaster import CreateParameterPolicy as CreateParameterPolicy
from UI4.FormMaster.KatanaFactory import ParameterWidgetFactory as ParameterWidgetFactory

from . import c
from . import EditorResources as resources
from .EditorComponents import (
    TreeWidgetItemGSV,
    QTitleBar,
    GSVTreeWidget,

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
        self.__update_tw1 = False

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
        self.__setup_event_handlers(True)
        self.__tw_update()
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

        Here we are updating the treeWidget when specific events happened.

        Args:
            enabled(bool): Set if the even handler is enabled or not.
        """
        # this is once the events are finished, actually update tw1
        Utils.EventModule.RegisterCollapsedHandler(
            self.__idle_callback,
            "event_idle",
            enabled=enabled
        )

        # these are the events that will update the treewidget
        events4twupdate = [
            "port_disconnect",
            "port_connect",
            "parameter_finalizeValue",
            "parameter_setValue",
            "parameter_setKey",  # don't know why/if needed ?
            "parameter_replaceXML",  # don't know why/if needed ?
            "parameter_removeKey",  # don't know why/if needed ?
            "node_setBypassed",
            "node_setName",
            "undo_openGroup",
        ]
        for event in events4twupdate:
            Utils.EventModule.RegisterCollapsedHandler(
                self.__process_event,
                event,
                enabled=enabled
            )

        return

    def __idle_callback(self, *args, **kwargs):
        """
        Called when an event is finished.
        Update ``tw1`` if ``__update_tw1`` is set to True.

        !! While the node is edited this is run indefinitively. Don't log/run
        anything that is not in a condition.
        """
        if self.__update_tw1:
            try:
                self.__tw_update()
            finally:
                self.__update_tw1 = False

        return

    def __process_event(self, event_data):
        """
        Filter actions that need to performed depending of the event.
        In our case ther eis no special case, all events, no matter the source
        node led to an update of the tw.

        Args:
            event_data(list of list):
                event data from katana
                [ [ "event type", int, {event source} ], ... ]
        """
        if self.__update_tw1:
            return
        # uncomment the under for debuging
        # for event in event_data:
        #     event_source = event[2]
        #     print("{}: {}".format(event[0], event_source))
        self.__update_tw1 = True

        return

    """------------------------------------------------------------------------
    Interactions
    """

    def __uicook(self):
        """
        Called once on node's instancing
        """

        # ==============
        # Create Layouts
        # ==============
        self.lyt_m = QtWidgets.QVBoxLayout()

        # ==============
        # Create Widgets
        # ==============

        # -- Create Widgets from parameters ----
        # Honestly I don't know why they are private attributes

        self.__pp_parsing_mode = CreateParameterPolicy(
            parentPolicy=None,
            param=self.__node.getParameter('parsing_mode')
        )
        self.__pp_filters_grp = CreateParameterPolicy(
            parentPolicy=None,
            param=self.__node.getParameter('Filters')
        )
        self.__pp_view_type = CreateParameterPolicy(
            parentPolicy=None,
            param=self.__node.getParameter('Filters.view_type')
        )
        self.__pp_match_names = CreateParameterPolicy(
            parentPolicy=None,
            param=self.__node.getParameter('Filters.match_names')
        )
        self.__pp_match_value = CreateParameterPolicy(
            parentPolicy=None,
            param=self.__node.getParameter('Filters.match_values')
        )

        self.cbb_mode = ParameterWidgetFactory.buildWidget(
            parent=self,
            policy=self.__pp_parsing_mode
        )  # type: QtWidgets.QWidget

        self.grp_filters = ParameterWidgetFactory.buildWidget(
            parent=self,
            policy=self.__pp_filters_grp
        )  # type: QtWidgets.QWidget

        self.ttlb_header = QTitleBar()
        self.btn_update = UI4.Widgets.ToolbarButton(
            toolTip="",
            parent=self,
            normalPixmap=UI4.Util.IconManager.GetPixmap(
                os.path.join("Icons", "update_active20_hilite.png")
            )

        )
        self.tw1 = GSVTreeWidget()

        # ==============
        # Modify Widgets
        # ==============
        self.ttlb_header.set_icon(resources.Icons.logo, 24)
        self.ttlb_header.set_icon_tooltip(
            "GSVDb v{}.{}.{}-{}.{}"
            "".format(c.v_major, c.v_minor, c.v_patch, c.v_dev, c.v_published)
        )
        self.ttlb_header.set_icon_link("https://github.com/MrLixm/GSVDashboard")

        # ==============
        # Add to Layouts
        # ==============
        self.setLayout(self.lyt_m)
        self.lyt_m.setSpacing(8)
        self.lyt_m.addWidget(self.ttlb_header)
        self.lyt_m.addWidget(self.tw1)
        self.lyt_m.addWidget(self.grp_filters)

        self.ttlb_header.add_widget(self.cbb_mode)
        self.ttlb_header.add_widget(self.btn_update)

        # ==============
        # Connections
        # ==============

        # note: we doesn't need to set Node's parameters callback to update
        # the tw as we already have call backs when any parameter is finalized
        # (see __setup_event_handlers)

        self.tw1.edited_sgn.connect(self.__gsv_set_value)
        self.tw1.reset_sgn.connect(self.__gsv_remove_edit)
        self.btn_update.clicked.connect(self.__tw_update)

        return

    def __tw_update(self, *args, **kwargs):
        """
        Re-build the tree widget from scratch.
        """
        s_time = time.clock()

        parse_mode = self.__pp_parsing_mode.getValue()
        if not parse_mode:
            raise ValueError(
                "[__tw_update] Parse mode queried from QComboBox return nul."
            )

        logger.debug(
            "[{}][__tw_update] Started with mode: <{}>."
            "".format(self.__class__.__name__, parse_mode)
        )

        # clear the treewidget before adding new entries
        self.tw1.clear()

        st_gsvs = self.__node.get_gsvs(mode=parse_mode)
        for st_gsv in st_gsvs:
            self.__tw_create_item_from(st_gsv)

        self.__tw_select_last_selected()

        s_time = time.clock() - s_time
        logger.info(
            "[{}][__tw_update] Finished in {}s."
            "".format(self.__class__.__name__, s_time)
        )
        return

    def __tw_create_item_from(self, stgsv):
        """
        Create a tree widget item from the given SuperToolGSV except if this
        item doesn't pass the user-specified filters.

        Args:
            stgsv(SuperToolGSV):

        Returns:
            TreeWidgetItemGSV or None: TreeWidgetItemGSV created or None if not.
        """
        filters_dict = self.__get_filters()
        if filters_dict["global"] and stgsv.is_global:
            return
        if filters_dict["local"] and stgsv.is_local:
            return
        if filters_dict["not_edited"] and not stgsv.is_edited:
            return
        if filters_dict["locked"] and not stgsv.is_editable:
            return

        f = filters_dict["match_names"]
        if f and not re.search(f, stgsv.name):
            return

        f = filters_dict["match_values"]
        skip = True
        for v in stgsv.get_all_values():
            if f and re.search(f, v):
                skip = False
                break
        if f and skip:
            return

        return TreeWidgetItemGSV(parent=self.tw1, st_gsv=stgsv)

    def __tw_select_last_selected(self):
        """
        When updating the tw we loose the selection, select back the last
        item that was selected if possible.
        """
        gsv_name = self.tw1.last_selected
        if not gsv_name:
            # select a "random" treeW item instead
            all_items = self.tw1.get_all_items()
            # no widgets in tw, just return
            if not all_items:
                return
            self.tw1.setCurrentItem(all_items[0])
            return

        to_select = None
        for twitem in self.tw1.get_all_items():
            if twitem.gsv.name == gsv_name:
                to_select = twitem

        if to_select:
            self.tw1.setCurrentItem(to_select)

        return

    def __gsv_set_value(self, stgsv, new_value):
        """
        Called by signals from GSVPropertiesWidget.
        Asked to the SuperTool node to edit the given GSV.

        Args:
            stgsv(SuperToolGSV):
            new_value(str): can be an empty string ""
        """

        if new_value is None:
            logger.debug(
                "[{}][__gsv_set_value] new_value arg passed is None. Returning."
                "".format(self.__class__.__name__)
            )
            return

        # weirdly on Katana 4.0 signal seems to passe something that was
        # not a string. Issue was not there on Katana 4.5
        new_value = str(new_value)
        if new_value == "":
            new_value = str(stgsv.get_all_values()[0])

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

    def __get_filters(self):
        """
        Return the interface user defined filter as a dictionnary.

        Returns:
            dict:
        """

        filter_dict = {
            "global": True,
            "local": True,
            "not_edited": True,
            "locked": True,
            "match_names": None,
            "match_values": None
        }

        v = self.__pp_view_type.getValue()  # type: str
        v = v.split(", ")  # type: List[str]
        if "Global" in v:
            filter_dict["global"] = False
        if "Local" in v:
            filter_dict["local"] = False
        if "Locked" in v:
            filter_dict["locked"] = False
        if "Not-Edited" in v:
            filter_dict["not_edited"] = False

        v = self.__pp_match_names.getValue()  # type: str
        v = None if v == "" else v
        filter_dict["match_names"] = v

        v = self.__pp_match_value.getValue()  # type: str
        v = None if v == "" else v
        filter_dict["match_values"] = v

        return filter_dict