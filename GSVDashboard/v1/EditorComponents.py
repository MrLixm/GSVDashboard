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
import inspect
import logging
import os.path
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
from Katana import (
    Utils,
    UI4
)


from . import c
from . import EditorResources as resources
from .Node import SuperToolGSV
from .GSV import GSVNode


__all__ = [
    "TreeWidgetItemGSV",
    "GSVPropertiesWidget",
    "QTitleBar",
    "ResetButton",
    "EditButton",
    "GSVTreeWidget",
    "VLabeledWidget",
    "HLabeledWidget"
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
            "height": 30,
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


class TreeWidgetItemGSVNode(TreeWidgetItemBase):
    """
    Create and build a QTreeWidgetItem representing a GSVNode.

    Column 0 : Icon
    Column 1 : Node Name
    Column 2 : GSV Values the node is using.

    Args:
        gsv_node(GSVNode): A Katana node that use the GSV feature.
        parent(QtWidgets.QTreeWidget):

    Attributes:
        gsv_node(GSVNode): A Katana node that use the GSV feature.

    """

    _status_config = {
        "colors": {
        },
        "icons": {
            GSVNode.action_getter: resources.Icons.status_node_getter,
            GSVNode.action_setter: resources.Icons.status_node_setter,
        },
        "sorting": {
            GSVNode.action_getter: 0,
            GSVNode.action_setter: 1,
        }
    }

    _column_config = {
        "all": {
            "width": None,
            "height": 20,
        },
        0: {
            "label": "",
            "width": 0,
            "height": None,
        },
        1: {
            "label": "Node Name",
            "width": None,
            "height": None,
        },
        2: {
            "label": "Node GSV Values",
            "width": None,  # fill all the space left
            "height": None,
        }
    }

    def __init__(self, gsv_node, parent):

        super(TreeWidgetItemGSVNode, self).__init__(parent)
        self.gsv_node = gsv_node
        self.status = self.gsv_node.gsv_action

        self.__cook()

        return

    def __cook(self):

        # column: icon
        column = 0
        self.setTextAlignment(column, QtCore.Qt.AlignCenter)
        self.setToolTip(column, "GSV Node Action: {}".format(self.status))
        data = self._status_config["sorting"].get(self.status, 0)
        self.setData(column, QtCore.Qt.UserRole, data)

        # column: gsv node
        column = 1
        self.setText(column, self.gsv_node.node_name)
        self.setTextAlignment(column, QtCore.Qt.AlignVCenter)
        self.setToolTip(column, "Node Name")
        data = self.text(column)
        self.setData(column, QtCore.Qt.UserRole, data)

        # column: gsv node values
        column = 2
        text = self.gsv_node.gsv_values
        self.setText(column, list2str(text))
        self.setTextAlignment(column, QtCore.Qt.AlignLeft)
        self.setToolTip(column, "GSV Values the node is using.")
        self.setTextAlignment(column, QtCore.Qt.AlignVCenter)
        data = len(text)
        self.setData(column, QtCore.Qt.UserRole, data)

        # all columns should be colored
        self._update_columns_color([0, 1, 2])
        # only first column hold the icon
        self._update_columns_icon([0])
        self._update_size_hints()

        return


class NodeTreeWidget(QtWidgets.QTreeWidget):
    """
    TreeWidget used to hold GSVNodes.
    Children are TreeWidgetItemGSVNode instances.
    """

    def __init__(self):
        super(NodeTreeWidget, self).__init__()
        self.__cook()
        return

    def __cook(self):

        style = """
        QTreeWidget {
            border-radius: 3px;
            border: 0;
            padding: 3px;
        }    
        """

        # treewidget
        self.setStyleSheet(style)
        self.setHeaderHidden(True)
        self.setColumnCount(TreeWidgetItemGSVNode.column_number())
        self.setMinimumHeight(100)
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
        self.setColumnWidth(0, TreeWidgetItemGSVNode.column_size(0)[0])
        self.setHeaderLabels(TreeWidgetItemGSVNode.column_labels())
        header = self.header()  # type: QtWidgets.QHeaderView
        header.setSectionResizeMode(header.ResizeToContents)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
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
                "[NodeTreeWidget][__contextmenu] index not valid, returning."
            )
            return False

        selected_item = self.selectedItems()[0]  # type: TreeWidgetItemGSVNode

        # Building menu
        menu = QtWidgets.QMenu()

        act_select = QtWidgets.QAction("Select and Edit the Node", menu)
        act_select.triggered.connect(selected_item.gsv_node.select_edit)
        menu.addAction(act_select)

        menu.exec_(QtGui.QCursor.pos())

        return True


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

        self.itemSelectionChanged.connect(self.__on_selection_changed)

        return

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
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Maximum,
                QtWidgets.QSizePolicy.Maximum
            )
        )

        return


class EditButton(ResetButton):

    bgcolor = resources.Colors.edit


"""
Higher-level widget
"""


class VLabeledWidget(QtWidgets.QWidget):
    """
    Wrap an existing widget with a bottom info line composed of an optional
    info icon (with a tooltip) and a label.
    ::

        [                  ]
        [  content widget  ]
        [                  ]
        [info icon][text]

    Args:
        content(QtWidgets.QWidget):
        text(str):
        info_text(str): used in the info icon tooltip

    """
    direction = QtWidgets.QBoxLayout.TopToBottom
    info_icon_size = 10
    txt_font_size = 10

    def __init__(self, content=None, text=None, info_text=None):
        super(VLabeledWidget, self).__init__()
        self.__content = None
        self.__text = None
        self.__info = None
        self.__ui_build()

        self.set_content(content)
        self.set_text(text)
        self.set_info(info_text)

        return

    def __ui_build(self):

        # =============
        # Create Styles
        # =============

        main_window = UI4.App.MainWindow.GetMainWindow()
        qpalette = main_window.palette()  # type: QtGui.QPalette
        bgcolor = qpalette.color(qpalette.Background)
        color_disabled = qpalette.color(qpalette.Disabled, qpalette.Text)
        style_info = """
        QPushButton {{
            background-color: transparent;
            margin: 0;
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
            bgcolor.getRgb()[:-1],
            str(color_disabled.getRgb()[:-1])[1:][:-1]
        )

        style_lbl = """
        QLabel{{
            font-size: {}px;
            margin-top: 2px;
        }}
        """.format(self.txt_font_size)

        # ==============
        # Create Layouts
        # ==============
        self.lyt = QtWidgets.QBoxLayout(self.direction)
        self.lyt_text = QtWidgets.QHBoxLayout()

        # ==============
        # Create Widgets
        # ==============
        self.lbl = QtWidgets.QLabel()
        self.info = QtWidgets.QPushButton()

        # ==============
        # Modify Widgets
        # ==============
        self.lbl.setEnabled(False)
        # small text for label
        self.lbl.setStyleSheet(style_lbl)

        qpixmap = QtGui.QPixmap(resources.Icons.info)
        qpixmap = qpixmap.scaled(
            self.info_icon_size,
            self.info_icon_size,
            transformMode=QtCore.Qt.SmoothTransformation
        )
        qicon = QtGui.QIcon(qpixmap)
        self.info.setIcon(qicon)
        # self.info.setEnabled(False)
        # reset stylesheet, we only need the icon
        self.info.setStyleSheet(style_info)
        # self.info.setMaximumSize(self.info_icon_size, self.info_icon_size)
        self.info.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Maximum,
                QtWidgets.QSizePolicy.Maximum
            )
        )

        # ==============
        # Modify Layouts
        # ==============
        self.lyt_text.addWidget(self.info, QtCore.Qt.AlignCenter)
        self.lyt_text.addWidget(self.lbl)

        temp_widget = QtWidgets.QWidget()
        temp_widget.setHidden(True)
        self.lyt.insertWidget(0, temp_widget)
        self.lyt.addLayout(self.lyt_text)
        self.lyt.setSpacing(0)

        self.setLayout(self.lyt)
        return

    def __ui_bake(self):

        if self.__text:
            self.lbl.setText(self.__text)
        else:
            self.lbl.setText("")

        if self.__info:
            self.info.setToolTip(self.__info)
            self.info.setHidden(False)
        else:
            self.info.setHidden(True)

        if self.__content is not None:
            # __content is always the first item, remove it first then add it back.
            removed_widget = self.lyt.takeAt(0).widget()  # can return None
            if removed_widget and not removed_widget == self.__content:
                # this delete the widget
                removed_widget.deleteLater()
            # add the new content widget
            self.lyt.insertWidget(0, self.__content)

        return

    @property
    def content(self):
        return self.__content

    @content.setter
    def content(self, content):
        self.set_content(content)
        return

    def set_content(self, content):
        self.__content = content
        self.__ui_bake()
        return

    def set_text(self, text):
        """
        Args:
            text(str or None):
        """
        self.__text = text
        self.__ui_bake()
        return

    def set_info(self, info_text):
        """
        Args:
            info_text(str or None): text to use in the info icon
        """
        self.__info = info_text
        self.__ui_bake()
        return


class HLabeledWidget(VLabeledWidget):
    direction = QtWidgets.QBoxLayout.RightToLeft


class GSVPropertiesWidget(QtWidgets.QFrame):
    """
    """

    value_changed_sgn = QtCore.pyqtSignal(object, object)
    unedited_sgn = QtCore.pyqtSignal(object)
    status_changed_sgn = QtCore.pyqtSignal(str, str)

    status_editable = "editable"
    status_edited = "edited"
    status_locked = "locked"  # = read only

    def __init__(self):

        super(GSVPropertiesWidget, self).__init__()

        self.__status = self.status_locked  # default status is read only
        self.__data = None  # type: SuperToolGSV

        self.lyt = None
        self.lyt_top = None
        self.lbl_name = None
        self.cbb_value = None
        self.tw_nodes = None

        self.__ui_cook()

        return

    @property
    def status(self):
        return self._status

    @property
    def _status(self):
        return self.__status

    @_status.setter
    def _status(self, new_status):
        """
        Change current status and emit signal if there was an actual change.
        Private property cause we don't want to be able to set the status
        directly from outside.

        Args:
            new_status(str):
        """
        before_status = self.__status
        self.__status = new_status
        # check if the update actually changed something
        if before_status == new_status:
            # don't emit signal if no change
            return
        self.status_changed_sgn.emit(new_status, before_status)
        return

    def set_data(self, gsv_data):
        """
        Set the GSV data this widget represents.
        Handle the redraw of the ui with the new data.

        Args:
            gsv_data(SuperToolGSV):

        """

        self.__data = gsv_data
        self.__update_status()
        # update the ui with the new data
        self.__ui_bake()

        return

    def set_edited(self):
        """
        If the widget is editable, turn it into edited and emit the
        corresponding signals.
        """

        if not self.status == self.status_editable:
            logger.warning(
                "[{}][set_edited] Called but status is not editable but <{}>."
                "".format(self.__class__.__name__, self.status)
            )
            return

        self._status = self.status_edited
        self.__ui_bake()
        self.__value_changed()  # call __update_status
        return

    def set_unedited(self):
        """
        Reset the interface as it was never modified by the user.
        If the widget was being edited, it is no more.

        Emits:
            reseted_sgn(SuperToolGSV): emit the current GSV represented
                as SuperToolGSV instance.
        """
        # we do not want to unedit if we are already unedited.
        if not self.status == self.status_edited:
            logger.warning(
                "[{}][set_unedited] Called, but _edited is already False."
                "".format(self.__class__.__name__)
            )
            return

        # order is important
        self._status = self.status_editable
        self.__ui_bake()
        self.unedited_sgn.emit(self.__data)
        return

    def __ui_cook(self):

        # =============
        # Create Styles
        # =============

        main_window = UI4.App.MainWindow.GetMainWindow()
        qpalette = main_window.palette()  # type: QtGui.QPalette
        color_disabled = qpalette.color(qpalette.Disabled, qpalette.Text)
        darkbgcolor = qpalette.color(
            qpalette.Normal,
            qpalette.Shadow
        )

        style_lbl = """
            border: 1px solid rgba({0}, 0.25);
            border-radius: 3px;
            padding: 3px;
        """.format(str(color_disabled.getRgb()[:-1])[1:][:-1])

        style = """
        QFrame#{} {{
            border: 2px solid rgba{};
            border-top-width: 0;
            border-bottom-width: 0;
            border-right-width: 0;
        }}
        """.format(self.__class__.__name__, darkbgcolor.getRgb())

        # ==============
        # Create Layouts
        # ==============
        self.lyt = QtWidgets.QVBoxLayout()
        self.lyt_top = QtWidgets.QHBoxLayout()

        # ==============
        # Create Widgets
        # ==============
        self.lbl_name = VLabeledWidget(QtWidgets.QLabel())
        self.cbb_value = VLabeledWidget(QtWidgets.QComboBox())
        self.tw_nodes = VLabeledWidget(NodeTreeWidget())

        # ==============
        # Modify Widgets
        #
        # Have to use .content on VLabeledWidget() for now,
        # see to remove this drawback later
        # ==============

        self.setObjectName(str(self.__class__.__name__))
        self.setContentsMargins(10, 20, 10, 20)
        self.setStyleSheet(style)

        self.lbl_name.setEnabled(False)
        self.lbl_name.set_text("Name")
        self.lbl_name.content.setStyleSheet(style_lbl)
        self.cbb_value.content.setEditable(False)
        self.cbb_value.set_text("Values")
        self.cbb_value.set_info(
            "Values the GSV can take based on what values nodes are using.\n"
            "The currently active value should correspond to last value set "
            "for the gsv (if the GSV is set), but this might not be accurate."
        )
        # treewidget
        self.tw_nodes.set_text("Linked Nodes")

        # ==============
        # Modify Layouts
        # ==============
        self.lyt_top.addWidget(self.lbl_name)
        self.lyt_top.addWidget(self.cbb_value)
        self.lyt.addLayout(self.lyt_top)
        self.lyt.addWidget(self.tw_nodes)
        self.setLayout(self.lyt)

        # =================
        # Setup Connections
        # =================

        # only emit on user interaction
        self.cbb_value.content.activated.connect(self.__value_changed)

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

        # label
        self.lbl_name.content.setText(self.__data.name)
        # cbb
        self.cbb_value.content.clear()
        self.cbb_value.content.addItems(self.__data.get_all_values())
        self.cbb_value.content.setCurrentText(self.__data.get_current_value())
        # cbb is enable only when the status is "edited"
        if self.status != self.status_edited:
            self.cbb_value.content.setEnabled(False)
        else:
            self.cbb_value.content.setEnabled(True)
        # treewidget
        self.__tw_update()

        return

    def __tw_update(self):
        """
        Populate the node tree widget with GSVNode fron the current GSV.
        """

        # clear the treewidget before adding new entries
        self.tw_nodes.content.clear()

        for gsvnode in self.__data.get_nodes():
            qtwi = TreeWidgetItemGSVNode(
                gsv_node=gsvnode,
                parent=self.tw_nodes.content
            )

        logger.debug(
            "[{}][__tw_update] Finished.".format(self.__class__.__name__)
        )
        return

    def __update_status(self):
        """
        Update ``status`` attribute according to instance attributes.
        Status depends of :

        * ``__data`` : if locked

        Emits:
            status_changed_sgn:
                If status is different from previous one.
        """
        if not self.__data:
            logger.warning(
                "[GSVPropertiesWidget][update_status] Called but "
                "self.__data is None."
            )
            self.__status = self.status_locked
            # return without emitting signal
            return

        if not self.__data.is_editable:
            self._status = self.status_locked

        # The SuperTool already have a node that edit this GSV or this widget
        # is marked as edited :
        elif self.__data.is_edited:
            self._status = self.status_edited

        else:
            self._status = self.status_editable

        return

    def __value_changed(self):
        """
        To call when the user edit the ``value combobox``.

        Emits:
            value_changed_sgn(tuple(SuperToolGSV, str)):
                current GSV data + new value set.

        """
        self._status = self.status_edited
        value = self.cbb_value.content.currentText()  # type: str
        self.value_changed_sgn.emit(self.__data, value)
        return



