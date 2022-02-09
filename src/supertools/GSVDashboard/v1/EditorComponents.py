"""

"""
import inspect
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
from Katana import (
    Utils,
    UI4
)


from . import c
from . import EditorResources as resources
from .Node import SuperToolGSV
from .GSV import GSVNode


__all__ = [
    'QModMenu',
    "TreeWidgetItemGSV",
    "GSVPropertiesWidget",
    "QTitleBar",
    "ResetButton",
    "EditButton",
    "GSVTreeWidget",
    "UpdateButton"
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

    Args:
        st_gsv(SuperToolGSV):
        parent(QtWidgets.QTreeWidget):

    Attributes:
        gsv(SuperToolGSV): the GSV as a python object relative to the supertool
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
            SuperToolGSV.statuses.global_set: 0,
            SuperToolGSV.statuses.local_set: 1,
            SuperToolGSV.statuses.local_set_this: 2,
            SuperToolGSV.statuses.global_set_this: 3,
            SuperToolGSV.statuses.local_not_set: 4,
            SuperToolGSV.statuses.global_not_set: 5,
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

        super(TreeWidgetItemGSV, self).__init__(parent)
        self.gsv = st_gsv
        self.status = self.gsv.status

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
        self.setText(column, list2str(text))
        self.setTextAlignment(column, QtCore.Qt.AlignLeft)
        self.setToolTip(column, "Values the GSV can take.")
        self.setTextAlignment(column, QtCore.Qt.AlignVCenter)
        data = len(text)
        self.setData(column, QtCore.Qt.UserRole, data)

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

        act_select = QtWidgets.QAction("Select and Edit the Node")
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

    def __init__(self):
        super(GSVTreeWidget, self).__init__()
        self.__cook()
        self.last_selected = None

    def __cook(self):

        style = """
        QTreeView {
            border-radius: 3px;
            border: 0;
            padding: 3px;
        }   
        QHeaderView::section {
            border: 0;
        }
        """

        self.setStyleSheet(style)
        self.setColumnCount(TreeWidgetItemGSV.column_number())
        self.setMinimumHeight(150)
        self.setAlternatingRowColors(True)
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
        self.setColumnWidth(0, TreeWidgetItemGSV.column_size(0)[0])
        self.setColumnWidth(1, TreeWidgetItemGSV.column_size(1)[0])
        self.setHeaderLabels(TreeWidgetItemGSV.column_labels())
        header = self.header()
        # The user can resize the section
        header.setSectionResizeMode(header.Interactive)

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
                "[{}][__tw_selected_get_gsv_data] Called but"
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

    border_radius = 5
    icon_size = 16

    def __init__(self, parent=None, title=None):

        super(QTitleBar, self).__init__(parent)
        self.__title = title
        self.__icon = None
        self.__widgets = list()
        self.__uicook()
        return

    def __uicook(self):

        # =============
        # Create Styles
        # =============

        # must be in the instance else the mainWindow is not created yet
        mainwindow = UI4.App.MainWindow.GetMainWindow()
        qpalette = mainwindow.palette()

        bgcolor = qpalette.color(qpalette.Background)
        color_disabled = qpalette.color(
            qpalette.Disabled,
            qpalette.Text
        )
        darkbgcolor = qpalette.color(
            qpalette.Normal,
            qpalette.Shadow
        )

        style_bar = """
        .QWidget {{
            background-color: rgba{};
            border-radius: {}px;
        }}
        """.format(darkbgcolor.getRgb(), self.border_radius)

        style_icon = """
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
            bgcolor.getRgb()[:-1],
            str(color_disabled.getRgb()[:-1])[1:][:-1]
        )

        # ==============
        # Create Layouts
        # ==============

        self.lyt = QtWidgets.QHBoxLayout()
        self.lytbar = QtWidgets.QHBoxLayout()

        # ==============
        # Create Widgets
        # ==============

        self.bar = QtWidgets.QWidget()
        self.icon = QtWidgets.QPushButton()
        self.lbl = QtWidgets.QLabel()

        # ==============
        # Modify Widgets
        # ==============
        self.lbl.setHidden(True)
        self.lbl.setMinimumHeight(30)
        # Icon
        #   reset stylesheet, we only need the icon
        self.icon.setStyleSheet(style_icon)
        self.icon.setMaximumSize(self.icon_size, self.icon_size)
        self.icon.setHidden(True)
        # Bar
        # self.bar.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.bar.setStyleSheet(style_bar)
        # Self
        self.bar.setMinimumHeight(5)
        self.setMaximumHeight(50)  # random limit
        self.bar.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.MinimumExpanding,
                QtWidgets.QSizePolicy.MinimumExpanding
            )
        )
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.MinimumExpanding,
                QtWidgets.QSizePolicy.MinimumExpanding
            )
        )

        # ==============
        # Modifiy Layouts
        # ==============
        self.lytbar.setContentsMargins(5, 0, 0, 0)
        self.bar.setLayout(self.lytbar)
        self.lytbar.addWidget(self.icon)
        self.lytbar.addWidget(self.lbl)
        self.lyt.setContentsMargins(0, 0, 5, 0)
        self.lyt.addWidget(self.bar)
        self.lyt.setSpacing(10)
        self.setLayout(self.lyt)

        return

    def __uibake(self):

        if self.__title:
            self.lbl.setText(self.__title)
            self.lbl.setHidden(False)
        else:
            self.lbl.setHidden(True)

        if self.__icon:
            qpixmap = QtGui.QPixmap(str(self.__icon))
            qpixmap = qpixmap.scaled(
                self.icon_size,
                self.icon_size,
                transformMode=QtCore.Qt.SmoothTransformation
            )
            qicon = QtGui.QIcon(qpixmap)
            self.icon.setIcon(qicon)
            self.icon.setHidden(False)
        else:
            self.icon.setHidden(True)

        # clear main layout first
        while self.lyt.count():
            self.lyt.takeAt(0)
        # rebuild it
        self.lyt.addWidget(self.bar)
        for wgt in self.__widgets:
            self.lyt.addWidget(wgt)

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

    def set_icon(self, icon_path):
        """
        Update the UI after.

        Args:
            icon_path(str or Path): full path to the icon location
        """
        self.__icon = icon_path
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
        color: rgb(250, 250, 250);
        border-radius: 3px;
        border: 1px solid rgba({0}, 0.5);
        background-color: rgba({0}, 0.2);
        padding: 5px;
        padding-left: 10px;
        padding-right: 10px;
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


class UpdateButton(QtWidgets.QPushButton):

    def __init__(self, *args, **kwargs):
        super(UpdateButton, self).__init__(*args, **kwargs)

        style = """
            QPushButton {
            border: unset;
            background-color: transparent;
            padding: 2px;
        }
        """
        self.setStyleSheet(style)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Maximum,
                QtWidgets.QSizePolicy.Maximum
            )
        )
        self.setIcon(
            QtGui.QIcon(
                UI4.Util.IconManager.GetPixmap(
                    r"Icons\update_active20_hilite.png"
                )
            )
        )
        return


"""
Higher-level widget
"""


class LabeledWidget(QtWidgets.QWidget):
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

    info_icon_size = 10
    txt_font_size = 10

    def __init__(self, content=None, text=None, info_text=None):
        super(LabeledWidget, self).__init__()
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
        self.lyt = QtWidgets.QVBoxLayout()
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
                removed_widget.setParent(None)
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


# noinspection PyArgumentList
class QModMenu(QtWidgets.QWidget):
    """
    Container widget with a header and a footer widget. In between you have a
    content widget.
    The QModMenu can have multiple status that can be added on the fly.
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
        self.__statuses = dict()
        self.status = None

        self.__uicook()
        self.add_status("default")

        return

    def dict(self):
        return {
            "status": self.status,
            "content": self.__content,
            "statuses": self.__statuses
        }

    """---
        UI
    """

    def __uicook(self):
        """
        Build the ui for the first time
        """

        self.lyt = QtWidgets.QVBoxLayout()
        self.lyt_header = QtWidgets.QStackedLayout()
        self.lyt_content = QtWidgets.QStackedLayout()
        self.wgt_content_nul = QtWidgets.QWidget()
        self.lyt_footer = QtWidgets.QStackedLayout()

        self.lyt.setSpacing(0)
        self.wgt_content_nul.setHidden(True)

        self.lyt_content.addWidget(self.wgt_content_nul)
        self.lyt.addLayout(self.lyt_header)
        self.lyt.addLayout(self.lyt_content)
        self.lyt.addLayout(self.lyt_footer)

        self.setLayout(self.lyt)

        logger.debug(
            "[QModMenu][__uicook] Finished for status=<{}>.".format(self.status)
        )
        return

    def __ui_bake(self):
        """
        Update the UI widgets content for the current active status.
        """

        # header
        wgt = self.get_header_widget()
        if wgt:
            self.lyt_header.setCurrentWidget(wgt)

        # content
        wgt = self.get_content()
        if wgt:
            self.lyt_content.setCurrentWidget(wgt)
        else:
            self.lyt_content.setCurrentWidget(self.wgt_content_nul)

        # footer
        wgt = self.get_footer_widget()
        if wgt:
            self.lyt_footer.setCurrentWidget(wgt)

        logger.debug(
            "[{}][__ui_bake] Finished for current status <{}>."
            "".format(self.__class__.__name__, self.status)
        )
        return

    def update(self):
        logger.debug(
            "[{}][update] Called from {}."
            "".format(self.__class__.__name__, inspect.stack()[1][3])
        )  # TODO removve this (not py3)
        self.__ui_bake()

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
        self.__del_widgets_status(status_id)
        self.__statuses[status_id] = self.__default_status
        logger.debug(
            "[{}][__reset_status] Finished for status <{}>."
            "".format(self.__class__.__name__, status_id)
        )
        return

    @__check_status_exists_deco
    def __del_widgets_status(self, status_id):
        """
        Delete definitively the widgets holded in the given status.

        Args:
            status_id(object):
        """

        content = self.__statuses[status_id]  # type: dict
        _count = 0

        for _, wgt in content.items():

            if wgt is None:
                continue

            # removeWidget doesnt raise error if wgt not added
            self.lyt_header.removeWidget(wgt)
            self.lyt_footer.removeWidget(wgt)
            wgt.setParent(None)  # delete the widget
            _count += 1
            continue

        logger.debug(
            "[{}][__del_widgets_status] Deleted {} widgets for status <{}>"
            "".format(self.__class__.__name__, _count, status_id)
        )
        return

    @__check_status_exists_deco
    def __del_status(self, status_id):
        """
        Remove the given status from the list.
        !! Also delete the widgets it was holding

        Args:
            status_id(object):
        """
        self.__del_widgets_status(status_id)
        del self.__statuses[status_id]
        logger.debug(
            "[{}][__del_status] Finished for status <{}>."
            "".format(self.__class__.__name__, status_id)
        )

        return

    @__check_status_exists_deco
    def set_status_current(self, status_id):
        """
        Set the new currently used status.
        Update the UI too.

        Args:
            status_id(any): o
                object used to indentify the status

        Devnote: Can only take on argument !!
        """
        self.status = status_id
        self.update()
        logger.debug(
            "[{}][set_status_current] Finished new status is <{}>."
            "".format(self.__class__.__name__, status_id)
        )
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
        if replace_default and "default" in self.get_status_list():
            self.__del_status("default")

        self.__statuses[status_id] = self.__default_status.copy()

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
        Remove the given status. If it was the current status the new one
        is the last status in the status list.
        !! Also delete the widgets it was containing

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
        else:
            self.set_status_current(self.get_status_list()[-1])

        return

    def reset_status(self, status_id=None, all_status=False):
        """
        Remove the widgets sets for the given status. Make it empty.

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
        # remove and delete the previous content widget
        previous = self.get_content()
        if previous is not None:
            self.lyt_content.removeWidget(previous)
            previous.setParent(None)  # delete it
            logger.debug(
                "[{}][set_content] Removed previous widget {}."
                "".format(self.__class__.__name__, previous)
            )

        self.__content = content_widget
        self.lyt_content.addWidget(content_widget)
        self.update()
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
        self.lyt_header.addWidget(widget)
        self.update()

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

        self.is_status_existing(status_id, raise_error=True)

        self.__statuses[status_id]["footer"] = widget
        self.lyt_footer.addWidget(widget)
        self.update()

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


class GSVPropertiesWidget(QtWidgets.QFrame):
    """
    Widget used to display the properties of a single GSV.
    It's name, the value sit can take, and it's associated Nodes.

    ::

        [gsv name ] [gsv value +]

        [ node1                 ]
        [ node2                 ]
        [ node3                 ]

    Different statuses are:

    - locked : the GSV can't be modify in any way. Read only.

    - editable : the UI is visually locked but can be switched to edited.

    - edited : the user can change the GSV Values


    Attributes:
        value_changed_sgn(SuperToolGSV, Optional[str]):
            qt signal emitted when the USER change the value of the ComboBox
        status_changed_sgn:
            qt signal emitted when the widget change status, value emitted is
            one of the 3 <status_XXX> attributes. First value is the new status
            , second is the previous status ebfore it was changed.
        unedited_sgn:
            qt signal emitted when the widget stop being edited (was reset).
            i.e you go from edited to editable

    Notes:
        widget being instance of LabeledWidget need to be accessed through
        LabeledWidget().content.setStyleSheet(...)

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
        self.lbl_name = LabeledWidget(QtWidgets.QLabel())
        self.cbb_value = LabeledWidget(QtWidgets.QComboBox())
        self.tw_nodes = LabeledWidget(NodeTreeWidget())

        # ==============
        # Modify Widgets
        #
        # Have to use .content on LabeledWidget() for now,
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



