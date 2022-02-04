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
            print("{}: {}".format(event[0], event_source))

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
        # self.mmnu_props = QModMenu()
        # self.ttlb_props_hd_locked = QTitleBar()
        # self.ttlb_props_hd_reset = QTitleBar()
        # self.ttlb_props_hd_edit = QTitleBar()
        # self.ttlb_props_footer = QTitleBar()
        # self.btn_reset = QtWidgets.QPushButton()  # TODO
        # self.btn_edit = QtWidgets.QPushButton()  # TODO
        # self.gsv_props_wgt = GSVPropertiesWidget()  # TODO

        # ==============
        # Modify Widgets
        # ==============

        # treewidget
        # self.tw1.setHeaderHidden(True)
        self.tw1.setColumnCount(TreeWidgetGSVItem.column_number())
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
        self.tw1.setColumnWidth(0, TreeWidgetGSVItem.column_size(0)[0])
        self.tw1.setColumnWidth(1, TreeWidgetGSVItem.column_size(1)[0])
        self.tw1.setHeaderLabels(TreeWidgetGSVItem.column_labels())
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
        # # QModeMenu
        # self.mmnu_props.set_content(self.mmnu_props_content)
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
        # self.lyt_m.addWidget(self.mmnu_props)

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
            qtwi = TreeWidgetGSVItem(st_gsv=st_gsv, parent=self.tw1)

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
        # self.gsv_props_wgt.set_data(gsv_data)

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
        selection = self.tw1.selectedItems()  # type: List[TreeWidgetGSVItem]
        if not selection:
            logger.debug(
                "[GSVDashboardEditor][__tw_selected_get_gsv_data] Called but"
                "self.tw1.selectedItems() return None ?"
            )
            return

        # selection in the GUI can only be done on one item anyway
        selection = selection[0]  # type: TreeWidgetGSVItem

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


class TreeWidgetGSVItem(QtWidgets.QTreeWidgetItem):
    """
    Create and build a QTreeWidgetItem representing a GSV.

    Column 0 : Icon
    Column 1 : GSV name
    COlumn 2 : GSV values

    Args:
        st_gsv(SuperToolGSV):
        parent(QtWidgets.QTreeWidget):

    Attributes:
        gsv(SuperToolGSV): the GSV as a python object relative to the supertool
    """

    __status_config = {
        "colors": {
            SuperToolGSV.statuses.global_not_set: resources.Colors.yellow_global,
            SuperToolGSV.statuses.global_set: resources.Colors.yellow_global_disabled,
            SuperToolGSV.statuses.local_set_this: resources.Colors.edited,
            SuperToolGSV.statuses.local_set: resources.Colors.text_disabled
        },
        "icons": {
            SuperToolGSV.statuses.global_not_set: resources.Icons.status_g_viewed,
            SuperToolGSV.statuses.global_set: resources.Icons.status_g_locked,
            SuperToolGSV.statuses.local_set_this: resources.Icons.status_l_edited,
            SuperToolGSV.statuses.local_not_set: resources.Icons.status_l_viewed,
            SuperToolGSV.statuses.local_set: resources.Icons.status_l_locked,
        },
        "sorting": {
            SuperToolGSV.statuses.global_set: 0,
            SuperToolGSV.statuses.local_set: 1,
            SuperToolGSV.statuses.local_set_this: 2,
            SuperToolGSV.statuses.local_not_set: 3,
            SuperToolGSV.statuses.global_not_set: 4,
        }
    }

    __column_config = {
        "all": {
            "width": None,
            "height": 30,
        },
        0: {
            "label": "",
            "width": 0,
            "height": None,
        },
        1: {
            "label": "Name",
            "width": 200,
            "height": None,
        },
        2: {
            "label": "Values",
            "width": None,  # fill all the space left
            "height": None,
        }
    }

    def __init__(self, st_gsv, parent):

        super(TreeWidgetGSVItem, self).__init__(parent)
        self.gsv = st_gsv
        self.status = self.__status_config["sorting"].get(self.gsv.status)

        self.__build()

        return

    def __lt__(self, other):
        """
        Override < operator for sorting columns properly.

        Args:
            other(TreeWidgetGSVItem):

        Returns:
            bool: True if other is bigger than this instance.
        """

        tw = self.treeWidget()
        if not tw:
            sorted_column = 0
        else:
            sorted_column = tw.sortColumn()

        lt_this = self.__sorted_column_data(sorted_column)
        lt_other = other.__sorted_column_data(sorted_column)
        return lt_this < lt_other

    def __build(self):

        def list2str(list_obj):
            out = "[ "
            for item in list_obj:
                out += "{}, ".format(item)

            out = out[:-1][:-1]
            out += " ]"
            return out

        # column: icon
        column = 0
        self.setTextAlignment(column, QtCore.Qt.AlignCenter)
        self.setToolTip(column, "Status: {}".format(self.gsv.status))
        data = self.__status_config["sorting"].get(self.gsv.status, 0)
        self.setData(column, QtCore.Qt.UserRole, data)

        # column: gsv name
        column = 1
        self.setText(column, self.gsv.name)
        self.setTextAlignment(column, QtCore.Qt.AlignVCenter)
        self.setToolTip(column, "GSV Name")
        data = self.text(column)
        self.setData(column, QtCore.Qt.UserRole, data)

        # column: gsv values
        column = 2
        text = self.gsv.get_all_values()
        self.setText(column, list2str(text))
        self.setTextAlignment(column, QtCore.Qt.AlignLeft)
        self.setToolTip(column, "Values the GSV can take.")
        self.setTextAlignment(column, QtCore.Qt.AlignVCenter)
        data = len(text)
        self.setData(column, QtCore.Qt.UserRole, data)

        # all columns should be colored
        self.__update_columns_color([0, 1, 2])
        # only first column hold the icon
        self.__update_columns_icon([0])
        self.__update_size_hints()

        return

    def __update_size_hints(self):

        for column_index in range(self.column_number()):

            width, height = self.column_size(column_index)
            if width is not None and height is not None:
                self.setSizeHint(column_index, QtCore.QSize(width, height))
            continue

        return

    def __update_columns_color(self, columns):
        """
        Update text color for the given columns depending of the current
        GSV status.

        Args:
            columns (list of int): list of column index to update

        """
        color = self.__status_config["colors"].get(self.gsv.status)
        if not color:
            return

        for column in columns:

            self.setForeground(
                column,
                QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2]))
            )

        return

    def __update_columns_icon(self, columns, icon_size=None):
        """

        Args:
            columns (list of int): list of column index to update
            icon_size(int or None): height and width

        """

        for column in columns:

            iconpath = self.__status_config["icons"].get(self.gsv.status)

            qpixmap = QtGui.QPixmap(iconpath)
            if icon_size:
                qpixmap = qpixmap.scaled(
                    icon_size,
                    icon_size,
                    transformMode=QtCore.Qt.SmoothTransformation
                )
            qicon = QtGui.QIcon(qpixmap)
            self.setIcon(column, qicon)

        return

    def __sorted_column_data(self, column):
        """
        Return the value used for sorting different TreeWidgetGSVItem

        Args:
            column(int):

        Returns:
            object suporting the < operator. Type depends of the sorting
                function return value.
        """
        return self.data(column, QtCore.Qt.UserRole)

    @classmethod
    def column_size(cls, column):
        """
        Return the column size specified in __column_config for the given
        column or for "all" not None.

        Args:
            column(int):

        Returns:
            tuple[int or None, int or None]:
                tuple of width, height where both of them can be None.
        """

        column_data = cls.__column_config.get(column)
        if column_data is None:
            raise ValueError(
                "[TreeWidgetGSVItem][column_size] Column <{}> not found"
                " in __column_config".format(column)
            )

        # return the "all" key if not None first.
        width = cls.__column_config["all"]["width"] or column_data["width"]
        height = cls.__column_config["all"]["height"] or column_data["height"]
        return width, height

    @classmethod
    def column_number(cls):
        return len(cls.__column_config.keys()) - 1

    @classmethod
    def column_labels(cls):
        """
        Returns:
            list of str:
                list of labels to use for each column
        """
        out = list()
        for index in range(cls.column_number()):
            v = cls.__column_config[index]["label"]  # type: str
            out.append(v)
        return out


class GSVPropertiesWidget(QtWidgets.QWidget):
    """

    ::

        [gsv name ] [gsv value +]

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
        self.__data = None  # type: SuperToolGSV
        self.__edited = False

        self.lyt = None
        self.lyt_top = None
        self.lbl_name = None
        self.cbb_value = None
        self.tw_nodes = None

        self.__ui_cook()

        return

    def __ui_cook(self):

        # TODO build rest of ui

        # ==============
        # Create Layouts
        # ==============
        self.lyt = QtWidgets.QVBoxLayout()
        self.lyt_top = QtWidgets.QHBoxLayout()

        # ==============
        # Create Widgets
        # ==============
        self.lbl_name = QtWidgets.QLabel()
        self.cbb_value = QtWidgets.QComboBox()
        self.tw_nodes = QtWidgets.QTreeWidget()

        # ==============
        # Modify Widgets
        # ==============
        self.cbb_value.currentIndexChanged.connect(self.__value_changed)
        self.cbb_value.setEditable(False)
        # treewidget
        # self.tw1.setHeaderHidden(True)
        self.tw_nodes.setColumnCount(TreeWidgetGSVItem.column_number())
        self.tw_nodes.setMinimumHeight(150)
        self.tw_nodes.setAlternatingRowColors(True)
        self.tw_nodes.setSortingEnabled(True)
        self.tw_nodes.setUniformRowHeights(True)
        self.tw_nodes.setRootIsDecorated(False)
        self.tw_nodes.setItemsExpandable(False)
        # select only one row at a time
        self.tw_nodes.setSelectionMode(self.tw1.SingleSelection)
        # select only rows
        self.tw_nodes.setSelectionBehavior(self.tw1.SelectRows)
        # remove dotted border on columns
        self.tw_nodes.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tw_nodes.setColumnWidth(0, TreeWidgetGSVItem.column_size(0)[0])
        self.tw_nodes.setColumnWidth(1, TreeWidgetGSVItem.column_size(1)[0])
        self.tw_nodes.setHeaderLabels(TreeWidgetGSVItem.column_labels())
        tw_nodes_header = self.tw_nodes.header()
        # The user can resize the section
        tw_nodes_header.setSectionResizeMode(tw_nodes_header.Interactive)


        # ==============
        # Modify Layouts
        # ==============
        self.lyt_top.addWidget(self.lbl_name)
        self.lyt_top.addWidget(self.cbb_value)
        self.lyt.addLayout(self.lyt_top)
        self.lyt.addWidget(self.tw_nodes)
        self.setLayout(self.lyt)

        return

    def __ui_bake(self):
        """
        Fill the widgets with content base on __data attribute without having
        to recreate them.
        """

        if not self.__data:
            logger.error(
                "[GSVPropertiesWidget][__ui_cook] Called but "
                "self.__data is None."
            )
            return

        if self.__data.is_locked:
            self.setDisabled(True)
            # TODO see if child widgets also inherits this.

        self.lbl_name.setText(self.__data.name)
        self.cbb_value.clear()

        return

    def __update_status(self):
        """
        Update ``__status`` attribute according to instance attributes.
        Status depends of :

        * ``__data`` : if locked

        * ``__edited`` : if True or False

        """
        if not self.__data:
            logger.warning(
                "[GSVPropertiesWidget][update_status] Called but "
                "self.__data is None."
            )
            self.__status = self.status_locked
            # return without emitting signal
            return

        if self.__data.is_locked:
            self.__status = self.status_locked

        # The SuperTool already have a node that edit this GSV or this widget
        # is marked as edited :
        elif self.__data.is_edited or self.__edited:
            self.__status = self.status_edited

        elif not self.__edited:
            self.__status = self.status_editable

        else:
            # This should never happens
            raise ValueError(
                "Imposible to find a status for the GSVPropertiesWidget for"
                "the GSV <{}>".format(self.__data.name)
            )

        # emit the new status (can be the same as previous one emitted)
        self.status_changed_sgn.emit(self.__status)

        return

    def __value_changed(self):
        """
        To call when the user or the script edit the ``value combobox``.
        """
        self.__edited = True
        value = self.cbb_value.currentText()
        self.value_changed_sgn.emit(value)

        return

    def reset(self):
        """
        Reset the interface as it was never modified by the user.
        """

        self.__edited = False  # order is important
        self.__ui_bake()

        return

    def set_data(self, gsv_data):
        """
        Set the GSV data this widget represents.

        Args:
            gsv_data(SuperToolGSV):

        """

        self.__data = gsv_data
        self.__update_status()
        # update the ui with the new data
        self.reset()

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


# noinspection PyArgumentList
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

    Attributes:
        status(any):
            Currently active status.
            Can also be queried via get_status_current()
        __content(QtWidgets.QWidget): content widget
        __statuses(dict of dict): dict of possible statuses with their
            corresponding widgets.

    """

    __default_status = {
        "header": None,  # type: List[QtWidgets.QWidget]
        "footer": None,  # type: List[QtWidgets.QWidget]
    }

    def __init__(self, parent=None):

        super(QModMenu, self).__init__(parent)

        self.__content = None  # type: QtWidgets.QWidget
        self.__statuses = None
        self.status = None

        self.add_status("default")

        return

    """---
        UI
    """

    def build(self):

        self.lyt = QtWidgets.QVBoxLayout()
        self.lyt.setSpacing(0)

        header = self.get_header_widget()
        if header:
            self.lyt.addWidget(header)

        content = self.get_content()
        if content:
            self.lyt.addWidget(content)

        footer = self.get_footer_widget()
        if footer:
            self.lyt.addWidget(footer)

        self.setLayout(self.lyt)

        logger.debug(
            "[QModMenu][build] Finished for status=<{}>.".format(self.status)
        )
        return

    def set_content_hidden(self, hidden):
        """
        Args:
            hidden(bool):
                True to hide the content widget. False to make it visible.
        """
        self.get_content().setHidden(hidden)
        return

    """-----------
        Status API
    """

    def __check_status_exists_deco(func):
        """
        Hacky way to have a decorator in the class. Could be defined outside
        this class (without the __ prefix) but just cleaner to have it inside.
        """

        def wrapper(*args, **kwargs):

            self = args[0]
            status = kwargs.get("status_id") or args[1]
            self.is_status_existing(status, raise_error=True)
            return func(*args, **kwargs)

        return wrapper

    @__check_status_exists_deco
    def __reset_status(self, status_id):
        self.__statuses[status_id] = self.__default_status
        return

    @__check_status_exists_deco
    def __del_status(self, status_id):
        del self.__statuses[status_id]
        return

    @__check_status_exists_deco
    def set_status_current(self, status_id):
        """

        Args:
            status_id(any): o
                object used to indentify the status

        Devnote: Can only take on argument !!
        """
        self.status = status_id
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
        if replace_default:
            self.__del_status("default")

        self.__statuses[status_id] = self.__default_status

        if set_to_current:
            self.set_status_current(status_id=status_id)

        return

    def get_status_current(self):
        return self.status

    def get_status_list(self):
        return list(self.__statuses.keys())

    def is_status_existing(self, status_id, raise_error=False):
        """
        Args:
            status_id(any):
            raise_error(bool):
                If True raise an error if the status is not registered .

        Returns:
            bool: True if the status is registered else False.
        """
        result = status_id in self.get_status_list()
        if not result and raise_error:
            raise ValueError(
                "[is_status_existing] status_id argument <{}> passed is "
                "not registered in the available statuses.".format(status_id)
            )
        return result

    def remove_status(self, status_id=None, all_status=False):
        """
        Args:
            status_id(any or None): If None passed, use the current status.
            all_status(bool): True to reset all statuses.
        """

        # if no status_id passed use the current one
        if not status_id:
            status_id = self.get_status_current()
        status_id = [status_id]

        if all_status:
            status_id = self.get_status_list()

        for __status in status_id:
            self.__del_status(__status)

        # if we have removed all the statuses, add back the default one.
        if not self.get_status_list():
            self.add_status("default")

        return

    def reset_status(self, status_id=None, all_status=False):
        """
        Args:
            status_id(any or None): If None passed, use the current status.
            all_status(bool): True to reset all statuses.
        """

        # if no status_id passed use the current one
        if not status_id:
            status_id = self.get_status_current()
        status_id = [status_id]

        if all_status:
            status_id = self.get_status_list()

        for __status in status_id:
            self.__reset_status(__status)

        return

    def set_content(self, content_widget):
        """
        Content ils always the same, no matter the current status.

        Args:
            content_widget(QtWidgets.QWidget):
        """
        self.__content = content_widget
        return

    def get_content(self):
        """
        Returns:
            QtWidgets.QWidget:
                Widget used as content.
        """
        return self.__content

    def set_header_widget(self, widget, status_id=None):
        """
        Args:
            widget(QtWidgets.QWidget):
            status_id(any or None): If None, use the current status.
        """

        # if no status_id passed use the current one
        if not status_id:
            status_id = self.get_status_current()

        self.is_status_existing(status_id, raise_error=True)
        self.__statuses[status_id]["header"] = widget

        return

    def get_header_widget(self, status_id=None):
        """
        Args:
            status_id(any or None): If None, use the current status.
        """

        # if no status_id passed use the current one
        if not status_id:
            status_id = self.get_status_current()

        self.is_status_existing(status_id, raise_error=True)
        return self.__statuses[status_id]["header"]

    def set_footer_widget(self, widget, status_id=None):
        """
        Args:
            widget(QtWidgets.QWidget):
            status_id(any or None): If None, use the current status.
        """

        # if no status_id passed use the current one
        if not status_id:
            status_id = self.get_status_current()

        self.__statuses[status_id]["footer"] = widget

        return

    def get_footer_widget(self, status_id=None):
        """
        Args:
            status_id(any or None): If None, use the current status.
        """

        # if no status_id passed use the current one
        if not status_id:
            status_id = self.get_status_current()

        self.is_status_existing(status_id, raise_error=True)
        return self.__statuses[status_id]["footer"]
