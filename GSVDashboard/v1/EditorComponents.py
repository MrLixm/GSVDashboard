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
from abc import abstractmethod

try:
    from typing import List, Optional, Tuple, Union
except ImportError:
    pass

from PyQt5 import (
    QtCore,
    QtWidgets,
    QtGui
)

from . import c
from . import EditorResources as resources
from .Node import SuperToolGSV
from .GSV import GSVNode


__all__ = [
    "TreeWidgetItemGSV",
    "QTitleBar",
    "ResetButton",
    "EditButton",
    "GSVTreeWidget",
]

logger = logging.getLogger("{}.EditorComponents".format(c.name))


def list2str(list_obj):
    """
    Args:
        list_obj(list):

    Returns:
        str: List converted to a prettier string than the default str(list).
    """
    out = "[ "
    for item in list_obj:
        out += "{}, ".format(item)

    out = out[:-1][:-1]
    out += " ]"
    return out


""" ---------------------------------------------------------------------------
    UI: TreeWidget stuff
    
"""


class TreeWidgetItemBase(QtWidgets.QTreeWidgetItem):
    """
    Base subclass of QTreeWidgetItem. More convenient.

    [Specify what each column reprsents here]

    Args:
        parent(QtWidgets.QTreeWidget):

    Attributes:
        status(any): Object used to define a status for the item.

    Think to override the bottom class attributes.
    """

    _status_config = {
        "colors": {},
        "icons": {},
        "sorting": {}
    }

    _column_config = {
        "all": {
            "width": None,
            "height": None,
        },
        0: {
            "label": None,
            "width": None,
            "height": None,
        },
    }

    def __init__(self, parent):

        super(TreeWidgetItemBase, self).__init__(parent)
        self.status = None

        return

    def __lt__(self, other):
        """
        Override < operator for sorting columns properly.

        Args:
            other(TreeWidgetItemBase):

        Returns:
            bool: True if other is bigger than this instance.
        """

        tw = self.treeWidget()
        if not tw:
            sorted_column = 0
        else:
            sorted_column = tw.sortColumn()

        lt_this = self._sorted_column_data(sorted_column)
        lt_other = other._sorted_column_data(sorted_column)
        return lt_this < lt_other

    @abstractmethod
    def __cook(self):
        # each column must implement a QtCore.Qt.UserRole data attribute !
        # Used for sorting ! The value should be supported by the < operator.
        raise NotImplementedError(
            "[{}][__build] Not overriden !".format(self.__class__.__name__)
        )

    def _update_size_hints(self):

        for column_index in range(self.column_number()):

            width, height = self.column_size(column_index)
            if (width is not None) and (height is not None):
                self.setSizeHint(column_index, QtCore.QSize(width, height))
            continue

        return

    def _update_columns_color(self, columns):
        """
        Update text color for the given columns depending of the current
        status.

        Args:
            columns (list of int): list of column index to update

        """
        color = self._status_config["colors"].get(self.status)
        if not color:
            return

        for column in columns:

            self.setForeground(
                column,
                QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2]))
            )

        return

    def _update_columns_icon(self, columns, icon_size=None):
        """

        Args:
            columns (list of int): list of column index to update
            icon_size(int or None): height and width

        """

        for column in columns:

            iconpath = self._status_config["icons"].get(self.status)

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

    def _sorted_column_data(self, column):
        """
        Return the value used for sorting different TreeWidgetItemBase

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
        Return the column size specified in _column_config for the given
        column or for "all" not None.

        Args:
            column(int):

        Returns:
            tuple[int or None, int or None]:
                tuple of width, height where both of them can be None.
        """

        column_data = cls._column_config.get(column)
        if column_data is None:
            raise ValueError(
                "[{}][column_size] Column <{}> not found"
                " in _column_config".format(cls.__name__, column)
            )
        # return the "all" key if not None first.
        width = (
            cls._column_config["all"]["width"] or column_data["width"]
        )  # type: Optional[int]
        height = (
            cls._column_config["all"]["height"] or column_data["height"]
        )  # type: Optional[int]
        return width, height

    @classmethod
    def column_number(cls):
        # -1 cause there is the "all" key
        return len(cls._column_config.keys()) - 1

    @classmethod
    def column_labels(cls):
        """
        Returns:
            list of (str or None):
                list of labels to use for each column
        """
        out = list()
        for index in range(cls.column_number()):
            v = cls._column_config[index]["label"]  # type: Optional[str]
            out.append(v)
        return out


class TreeWidgetItemGSV(TreeWidgetItemBase):
    """
    Create and build a QTreeWidgetItem representing a GSV.

    Column 0 : Icon
    Column 1 : GSV name
    COlumn 2 : GSV values

    Data per item using UserRole is used to sort the item's column in the
    parent treewidget.

    Args:
        st_gsv(SuperToolGSV):
        parent(GSVTreeWidget):

    Attributes:
        parent(GSVTreeWidget):
        status(str): gsv status
        gsv(SuperToolGSV): the GSV as a python object relative to the supertool
        cbb_values(QtWidgets.QComboBox):
        btn(QtWidgets.QPushButton):
    """

    _status_config = {
        "colors": {
            SuperToolGSV.statuses.global_not_set: resources.Colors.yellow_global,
            SuperToolGSV.statuses.global_set: resources.Colors.yellow_global_disabled,
            SuperToolGSV.statuses.local_set_this: resources.Colors.edited,
            SuperToolGSV.statuses.local_set: resources.Colors.text_disabled,
            SuperToolGSV.statuses.global_set_this: resources.Colors.yellow_global
        },
        "icons": {
            SuperToolGSV.statuses.global_not_set: resources.Icons.status_g_viewed,
            SuperToolGSV.statuses.global_set: resources.Icons.status_g_locked,
            SuperToolGSV.statuses.local_set_this: resources.Icons.status_l_edited,
            SuperToolGSV.statuses.local_not_set: resources.Icons.status_l_viewed,
            SuperToolGSV.statuses.local_set: resources.Icons.status_l_locked,
            SuperToolGSV.statuses.global_set_this: resources.Icons.status_g_edited,
        },
        "sorting": {
            SuperToolGSV.statuses.local_set_this: 0,
            SuperToolGSV.statuses.global_set_this: 1,
            SuperToolGSV.statuses.local_not_set: 2,
            SuperToolGSV.statuses.global_not_set: 3,
            SuperToolGSV.statuses.local_set: 4,
            SuperToolGSV.statuses.global_set: 5,
        }
    }

    _column_config = {
        "all": {
            "width": None,
            "height": 32,
        },
        0: {
            "label": "",
            "width": 0,
            "height": None,
        },
        1: {
            "label": "Name",
            "width": 185,
            "height": None,
        },
        2: {
            "label": "Values",
            "width": 200,
            "height": None,
        },
        3: {
            "label": "Action",
            "width": None,
            "height": None,
        }
    }

    def __init__(self, parent, st_gsv):

        super(TreeWidgetItemGSV, self).__init__(parent)
        self.parent = parent
        self.gsv = st_gsv
        self.status = self.gsv.status
        self.cbb_values = None  # type: QtWidgets.QComboBox
        self.btn = None  # type: QtWidgets.QPushButton

        self.__cook()

        return

    def __cook(self):

        # column: icon
        column = 0
        self.setTextAlignment(column, QtCore.Qt.AlignCenter)
        self.setToolTip(column, "Status: {}".format(self.status))
        data = self._status_config["sorting"].get(self.status, 0)
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
        data = len(text)
        self.setData(column, QtCore.Qt.UserRole, data)
        self.setToolTip(column, "Values the GSV can take.")

        if self.gsv.is_edited:

            self.cbb_values = QtWidgets.QComboBox()
            self.cbb_values.addItems(text)
            self.cbb_values.setCurrentText(
                str(self.gsv.get_current_value())
            )
            self.cbb_values.activated.connect(self.__emit_edited)

            self.parent.setItemWidget(self, column, self.cbb_values)

        else:

            self.setText(column, list2str(text))
            # self.setTextAlignment(column, QtCore.Qt.AlignLeft)
            self.setTextAlignment(column, QtCore.Qt.AlignVCenter)

        # column: action buttons
        column = 3

        # is_edited must be first
        if self.gsv.is_edited:

            self.btn = ResetButton("Reset")
            self.btn.clicked.connect(self.__emit_reset)

        elif self.gsv.is_editable:

            self.btn = EditButton("Edit")
            self.btn.clicked.connect(self.__emit_set_edited)

        else:
            # column is left empty
            pass

        if self.btn:
            self.parent.setItemWidget(self, column, self.btn)

        # all columns should be colored
        self._update_columns_color([0, 1, 2])
        # only first column hold the icon
        self._update_columns_icon([0])
        self._update_size_hints()

        logger.debug(
            "[{}][__cook] Finished."
            "".format(self.__class__.__name__)
        )

        return

    def __emit_set_edited(self):
        """
        For the Edit QPushButton
        """
        self.parent.edited_sgn.emit(self.gsv, "")
        logger.debug(
            "[TreeWidgetItemGSV:name={}][__emit_set_edited] Finished."
            "".format(self.gsv.name)
        )
        return

    def __emit_edited(self):

        if not self.cbb_values:
            raise RuntimeError(
                "[TreeWidgetItemGSV:name={}][__emit_edited] "
                "The value ComboBox widget doesn't exists ! This should"
                "never happens ??"
                "".format(self.gsv.name)
            )

        value = self.cbb_values.currentText()
        self.parent.emit_edited(self.gsv, value)
        logger.debug(
            "[TreeWidgetItemGSV:name={}][__emit_edited] Finished."
            "".format(self.gsv.name)
        )
        return

    def __emit_reset(self):
        """
        For the Reset QPushButton
        """
        self.parent.emit_reset(self.gsv)
        logger.debug(
            "[TreeWidgetItemGSV:name={}][__emit_reset] Finished."
            "".format(self.gsv.name)
        )
        return


class GSVTreeWidget(QtWidgets.QTreeWidget):
    """
    TreeWidget used to display GSV in Scene.
    Store TreeWidgetItemGSV that themself store SuperToolGSV.

    Attributes:
        last_selected(str or None): name of the last selected GSV
    """

    # object is a SuperTool GSV, str is the new value set
    edited_sgn = QtCore.pyqtSignal(object, str)
    reset_sgn = QtCore.pyqtSignal(object)

    def __init__(self):
        super(GSVTreeWidget, self).__init__()
        self.__cook()
        self.last_selected = None

    def __cook(self):

        color1 = resources.Colors.app_background_light().getRgb()
        color2 = "rgb(71,72,101)"
        style = """
        
        QTreeView {{
            background-color: transparent;
            border-radius: 3px;
            border: 0;
            padding: 3px;
        }}
         
        QTreeView::item {{
            background: rgb{0};
            margin: 2px 0 2px;
        }}
        
        QTreeView::item:first {{
            border-left: 3px solid transparent;
            border-top-left-radius: 3px;
            border-bottom-left-radius: 3px;
        }}
        
        QTreeView::item:last {{
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }}

        QTreeView::item:hover:first {{
            border-left: 3px solid {1};
        }}

        QTreeView::item:selected {{
            background: rgb(57,57,71);
            border-top: 1px solid {1};
            border-bottom: 1px solid {1};
        }}        
        QTreeView::item:selected:first {{
            border-left: 3px solid {1};
        }}
        QTreeView::item:selected:last {{
            border-right: 1px solid {1};
        }}

        QHeaderView::section {{
            margin:3px;
            margin-bottom:8px;
            padding-bottom:3px;
            border: 0;
            /*border-bottom: 1px solid #444444;*/
        }}
        
        /* for the values column */
        QComboBox {{
            background: transparent;
            border-radius: 3px;
            margin:3px;
            padding-left: 3px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        QPushButton {{
            margin: 3px;
        }}

        """.format(color1, color2)

        self.setStyleSheet(style)
        self.setColumnCount(TreeWidgetItemGSV.column_number())
        self.setMinimumHeight(150)
        self.setAlternatingRowColors(False)
        self.setSortingEnabled(True)
        self.setUniformRowHeights(True)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        # select only one row at a time
        self.setSelectionMode(self.SingleSelection)
        # select only rows
        self.setSelectionBehavior(self.SelectRows)
        # remove dotted border on columns
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        header = self.header()
        self.setHeaderLabels(TreeWidgetItemGSV.column_labels())

        for i in range(TreeWidgetItemGSV.column_number()):

            size = TreeWidgetItemGSV.column_size(i)[0]
            if size:
                self.setColumnWidth(i, size)

        header.setStretchLastSection(False)
        # The user can resize the section
        header.setSectionResizeMode(header.Interactive)
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(2, header.Stretch)
        header.setSortIndicator(0, QtCore.Qt.DescendingOrder)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # CONNECTIONS

        self.itemSelectionChanged.connect(self.__on_selection_changed)
        self.customContextMenuRequested[QtCore.QPoint].connect(
            self.__contextmenu
        )

        return

    def __contextmenu(self, point):
        """
        Create a context menu at the given point.

        Args:
            point(QtCore.QPoint):

        Returns:
            bool: True if created
        """

        # Infos about the node selected.
        index = self.indexAt(point)
        if not index.isValid():
            logger.debug(
                "[GSVTreeWidget][__contextmenu] index not valid, returning."
            )
            return False

        item = self.itemAt(point)  # type: TreeWidgetItemGSV
        stgsv = item.gsv

        # Building menu
        menu = MenuNodeList()
        menu.build_from(stgsv)
        menu.display(QtGui.QCursor.pos())

        logger.debug(
            "[GSVTreeWidget][__contextmenu] Finished for gsv={}.".format(stgsv.name)
        )
        return True

    def __on_selection_changed(self):

        gsv = self.get_selected_gsv_data()
        if not gsv:
            return
        self.last_selected = gsv.name

        return

    def get_selected_gsv_data(self):
        """
        Return the SuperToolGSV instance for the currently selected GSV in
        the treewidget.

        Returns:
            SuperToolGSV or None: Should in theory never return None
        """
        selection = self.selectedItems()  # type: List[TreeWidgetItemGSV]
        if not selection:
            logger.debug(
                "[{}][get_selected_gsv_data] Called but"
                "self.selectedItems() return None ?"
                "".format(self.__class__.__name__)
            )
            return

        # selection in the GUI can only be done on one item anyway
        selection = selection[0]  # type: TreeWidgetItemGSV

        gsv_data = selection.gsv  # type: SuperToolGSV
        if not gsv_data:
            logger.error(
                "[{}}][__tw_get_gsv_data] No gsv data found "
                "for the currently selected tree widget item <{}>. This is"
                "not supposed to happens ?!"
                "".format(self.__class__.__name__, selection)
            )
        return gsv_data

    def get_all_items(self):
        """
        source:
            https://stackoverflow.com/questions/8961449/pyqt-qtreewidget-iterating

        Returns:
            list of TreeWidgetItemGSV:
                list of TreeWidgetItemGSV
        """

        out = list()
        root = self.invisibleRootItem()
        child_count = root.childCount()
        # iterate through the direct child of the invisible_root_item
        for index in range(child_count):
            qitem_root = root.child(index)  # type: TreeWidgetItemGSV
            out.append(qitem_root)

        return out

    def emit_edited(self, stgsv, newvalue):
        self.edited_sgn.emit(stgsv, newvalue)
        return

    def emit_reset(self, stgsv):
        self.reset_sgn.emit(stgsv)
        return


""" ---------------------------------------------------------------------------
    UI: Custom Widgets

"""


class MenuNodeList(QtWidgets.QMenu):
    """
    Context menu for the GSVTreewidget that list all nodes for the currently
    selected GSV.

    ::

        | Associated Nodes
        | ----------------
        | node_name1    >   | Select and Edit Node
        |                   | gsv_value1
        |                   | gsv_value2
        | node_name2

    """

    icons = {
        GSVNode.action_getter: resources.Icons.status_node_getter,
        GSVNode.action_setter: resources.Icons.status_node_setter,
    }

    def build_from(self, stgsv):
        """
        Args:
            stgsv(SuperToolGSV):
        """

        for gsvnode in stgsv.get_nodes():

            menu = QtWidgets.QMenu(gsvnode.node_name, self)
            qpixmap = QtGui.QPixmap(self.icons.get(gsvnode.gsv_action))
            qicon = QtGui.QIcon(qpixmap)
            menu.setIcon(qicon)
            menu.setToolTip("Node's name")

            act = QtWidgets.QAction("Select and Edit Node", menu)
            act.triggered.connect(gsvnode.select_edit)  # TODO see if this works

            menu.addAction(act)
            menu.addSeparator()

            for node_gsv_value in gsvnode.gsv_values:
                act = QtWidgets.QAction(node_gsv_value, menu)
                act.setDisabled(True)
                menu.addAction(act)

            self.addMenu(menu)

        return

    def display(self, position):
        """

        Args:
            position(QtCore.QPoint):

        """
        self.exec_(position)
        return


"""
Low-level widget
"""


class QTitleBar(QtWidgets.QWidget):
    """
    Horizontal widget with a title and left icon (both optionals).
    You can append a bunch of widgets at it's end.
    ::

        -[icon]--Title------------------- {widgets}

    """

    def __init__(self, parent=None, title=None):

        super(QTitleBar, self).__init__(parent)
        self.__title = title
        self.__icon = None
        self.__widgets = list()

        self.icon_size = 16

        self.__uicook()
        return

    def __uicook(self):

        # ==============
        # Create Layouts
        # ==============

        self.lyt = QtWidgets.QHBoxLayout()
        self.lyt_header = QtWidgets.QHBoxLayout()
        self.lyt_aside = QtWidgets.QHBoxLayout()

        # ==============
        # Create Widgets
        # ==============

        self.header = QtWidgets.QWidget()
        self.aside = QtWidgets.QWidget()
        self.icon = QtWidgets.QPushButton()
        self.lbl = QtWidgets.QLabel()

        # ==============
        # Modify Widgets
        # ==============
        self.lbl.setHidden(True)
        self.lbl.setMinimumHeight(30)
        # self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        # Icon
        #   reset stylesheet, we only need the icon
        self.icon.setMaximumSize(self.icon_size, self.icon_size)
        self.icon.setHidden(True)
        # Bar
        self.header.setMinimumHeight(5)
        self.setMaximumHeight(50)  # random limit
        policy = QtWidgets.QSizePolicy()
        policy.setVerticalPolicy(QtWidgets.QSizePolicy.MinimumExpanding)
        policy.setHorizontalPolicy(QtWidgets.QSizePolicy.MinimumExpanding)
        self.header.setSizePolicy(policy)
        self.__set_style()

        # ==============
        # Modify Layouts
        # ==============
        self.setLayout(self.lyt)
        self.lyt.addWidget(self.header)
        self.lyt.addWidget(self.aside)
        self.header.setLayout(self.lyt_header)
        self.lyt_header.addWidget(self.icon)
        self.lyt_header.addWidget(self.lbl)
        self.lyt_header.addStretch(1)
        self.aside.setLayout(self.lyt_aside)
        # self.lyt_aside is build in __ui_bake

        self.lyt.setSpacing(0)
        self.lyt.setContentsMargins(0, 0, 0, 0)
        self.lyt_header.setContentsMargins(5, 0, 5, 0)
        self.lyt_header.setSpacing(10)
        self.lyt_aside.setSpacing(10)
        self.lyt_aside.setContentsMargins(5, 0, 5, 0)

        return

    def __uibake(self):

        if self.__title:
            self.lbl.setText(self.__title)
            self.lbl.setHidden(False)
        else:
            self.lbl.setHidden(True)

        if self.__icon:
            qpixmap = QtGui.QPixmap(str(self.__icon))
            qicon = QtGui.QIcon(qpixmap)
            self.icon.setIcon(qicon)
            self.icon.setHidden(False)
        else:
            self.icon.setHidden(True)

        # clear main layout first
        while self.lyt_aside.count():
            self.lyt_aside.takeAt(0)

        # self.lyt.addWidget(self.header, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        for wgt in self.__widgets:
            self.lyt_aside.addWidget(wgt)

        return

    def __set_style(self):

        style = """
        .QWidget {{
            background-color: rgba{0};
            border-radius: 5px;
        }}
        """.format(
            resources.Colors.app_background_dark().getRgb()
        )
        # self.header.setStyleSheet(style)

        style = """
        .QWidget {{
            background-color: rgba{0};
        }}
        """.format(
            resources.Colors.app_disabled_text().getRgb()
        )
        # self.aside.setStyleSheet(style)

        style = """
        QPushButton {{
            background-color: transparent;
            border: 0;
        }}

        QToolTip {{
            background-color: rgb{0};
            border: 1px solid rgba({1}, 0.5);
            border-radius: 3px;
            color: rgb({1});
            padding: 4px;
        }}

        """.format(
            resources.Colors.app_background().getRgb()[:-1],
            str(resources.Colors.app_disabled_text().getRgb()[:-1])[1:][:-1]
        )
        self.icon.setStyleSheet(style)

        return

    def add_widget(self, widget):
        """
        Add a new widgets at the end.
        Update the UI after.

        Args:
            widget(QtWidgets.QWidget):
        """
        if widget not in self.__widgets:
            self.__widgets.append(widget)
        self.__uibake()
        return

    def clear_widgets(self):
        """
        Remove all stored widgets.
        Update the UI after.
        """
        self.__widgets = list()
        self.__uibake()
        return

    def set_title(self, title):
        """
        Update the UI after.

        Args:
            title(str):
        """
        self.__title = title
        self.__uibake()
        return

    def set_icon(self, icon_path, size=None):
        """
        Update the UI after.

        Args:
            icon_path(str or Path): full path to the icon location
        """
        self.__icon = icon_path
        self.icon_size = size or self.icon_size
        self.__uibake()
        return

    def set_icon_tooltip(self, tooltip):
        """
        Args:
            tooltip(str):
        """
        self.icon.setToolTip(tooltip)
        return


class ResetButton(QtWidgets.QPushButton):

    bgcolor = resources.Colors.reset

    def __init__(self, *args, **kwargs):
        super(ResetButton, self).__init__(*args, **kwargs)

        style = """
        QPushButton {{
            color: rgb(250, 250, 250);
            border-radius: 3px;
            border: 1px solid rgba({0}, 0.5);
            background-color: rgba({0}, 0.2);
            padding: 5px;
            padding-left: 10px;
            padding-right: 10px;
        }}
        QPushButton:hover {{
            border: 1px solid rgba({0}, 0.2);
            background-color: rgba({0}, 0.05);
        }}
        """.format(str(self.bgcolor)[1:][:-1])

        self.setStyleSheet(style)

        return


class EditButton(ResetButton):

    bgcolor = resources.Colors.edit





