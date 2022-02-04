"""

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
from Katana import (
    Utils,
    UI4
)


from . import c
from . import EditorResources as resources
# import for type hints only
try:
    from .Node import SuperToolGSV
    from .GSV import GSVNode
except:
    pass


__all__ = [
    'QModMenu',
    "TreeWidgetItemGSV",
    "GSVPropertiesWidget",
    "QTitleBar"
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
    def __build(self):
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
        width = cls._column_config["all"]["width"] or column_data["width"]
        height = cls._column_config["all"]["height"] or column_data["height"]
        if width is None or height is None:
            logger.debug(
                "[{}][column_size] Warning, returned size for column <{}> "
                "will have a None value: {}"
                "".format(cls.__name__, column, (width, height))
            )
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

        self.__build()

        return

    def __build(self):

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

        self.__build()

        return

    def __build(self):

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


""" ---------------------------------------------------------------------------
    UI: Custom Widgets

"""

"""
Low-level widget
"""


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

    info_icon_size = 8
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
            border: unset;
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
        self.lbl.setStyleSheet(
            "QLabel{{font-size: {}px;}}".format(self.txt_font_size)
        )

        qpixmap = QtGui.QPixmap(resources.Icons.info)
        qicon = QtGui.QIcon(qpixmap)
        self.info.setIcon(qicon)
        # self.info.setEnabled(False)
        # reset stylesheet, we only need the icon
        self.info.setStyleSheet(style_info)
        self.info.setMaximumSize(self.info_icon_size, self.info_icon_size)

        # ==============
        # Modify Layouts
        # ==============
        self.lyt_text.addWidget(self.info)
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


class ComboBoxGSVValue(QtWidgets.QComboBox):

    def __init__(self, parent=None):
        super(ComboBoxGSVValue, self).__init__(parent)
        self.locked = False
        self.currentIndexChanged.connect(self.setCurrentIndex)
        self.currentTextChanged.connect(self.setCurrentText)
        return

    def setCurrentIndex(self, index):
        print(
            "[ComboBoxGSVValue][setCurrentText] {}, locked={}"
            "".format(index, self.locked)
        )
        if self.locked:
            return
        super(ComboBoxGSVValue, self).setCurrentIndex(index)
        return

    def setCurrentText(self, text):
        print(
            "[ComboBoxGSVValue][setCurrentText] {}, locked={}"
            "".format(text, self.locked)
        )
        if self.locked:
            return
        super(ComboBoxGSVValue, self).setCurrentText(text)
        return


"""
Higher-level widget
"""


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
        self.__statuses = dict()
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

        # =============
        # Create Styles
        # =============

        main_window = UI4.App.MainWindow.GetMainWindow()
        qpalette = main_window.palette()  # type: QtGui.QPalette
        color_disabled = qpalette.color(qpalette.Disabled, qpalette.Text)
        style_lbl = """
            border: 1px solid rgba({0}, 0.25);
            border-radius: 3px;
            padding: 3px;
        """.format(str(color_disabled.getRgb()[:-1])[1:][:-1])

        style_tw = """
        QTreeWidget {
            border: none;
            border-radius: 3px;
        }    
        """

        # ==============
        # Create Layouts
        # ==============
        self.lyt = QtWidgets.QVBoxLayout()
        self.lyt_top = QtWidgets.QHBoxLayout()

        # ==============
        # Create Widgets
        # ==============
        self.lbl_name = LabeledWidget(QtWidgets.QLabel())
        self.cbb_value = LabeledWidget(ComboBoxGSVValue())
        self.tw_nodes = LabeledWidget(QtWidgets.QTreeWidget())

        # ==============
        # Modify Widgets
        #
        # Have to use .content on LabeledWidget() for now,
        # see to remove this drawback later
        # ==============
        self.lbl_name.setEnabled(False)
        self.lbl_name.set_text("Name")
        self.lbl_name.content.setStyleSheet(style_lbl)
        self.cbb_value.content.setEditable(False)
        self.cbb_value.set_text("Values")
        self.cbb_value.set_info(
            "Values the GSV can take based on what nodes are using."
        )
        # treewidget
        self.tw_nodes.set_text("Linked Nodes")
        self.tw_nodes.content.setStyleSheet(style_tw)
        self.tw_nodes.content.setHeaderHidden(True)
        self.tw_nodes.content.setColumnCount(
            TreeWidgetItemGSVNode.column_number()
        )
        self.tw_nodes.content.setMinimumHeight(100)
        self.tw_nodes.content.setAlternatingRowColors(False)
        self.tw_nodes.content.setSortingEnabled(True)
        self.tw_nodes.content.setUniformRowHeights(True)
        self.tw_nodes.content.setRootIsDecorated(False)
        self.tw_nodes.content.setItemsExpandable(False)
        # select only one row at a time
        self.tw_nodes.content.setSelectionMode(
            self.tw_nodes.content.SingleSelection
        )
        # select only rows
        self.tw_nodes.content.setSelectionBehavior(
            self.tw_nodes.content.SelectRows
        )
        # remove dotted border on columns
        self.tw_nodes.content.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tw_nodes.content.setColumnWidth(0, TreeWidgetItemGSVNode.column_size(0)[0])
        self.tw_nodes.content.setHeaderLabels(TreeWidgetItemGSVNode.column_labels())
        tw_nodes_header = self.tw_nodes.content.header()  # type: QtWidgets.QHeaderView
        tw_nodes_header.setSectionResizeMode(tw_nodes_header.ResizeToContents)

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

        self.cbb_value.content.currentIndexChanged.connect(self.__value_changed)

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
        print("[GSVPropertiesWidget][__ui_bake] status={}".format(self.__status))
        if self.__status == self.status_locked:
            self.cbb_value.content.locked = True
        else:
            self.cbb_value.content.locked = False
        # treewidget
        self.__tw_update()

        return

    def __tw_update(self):
        """
        """

        # clear teh treewidget before adding new entries
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
        value = self.cbb_value.content.currentText()
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
        Handle the redraw of the ui with the new data.

        Args:
            gsv_data(SuperToolGSV):

        """

        self.__data = gsv_data
        self.__update_status()
        # update the ui with the new data
        self.reset()

        return

