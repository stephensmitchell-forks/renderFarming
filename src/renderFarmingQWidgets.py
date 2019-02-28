import PySide2.QtWidgets as QtW
import PySide2.QtGui as QtG
from PySide2.QtCore import Signal, Qt, QRect, QMargins, QPointF

import math


class QMaxRollout(QtW.QWidget):
    collapsed = Signal()
    expanded = Signal()
    toggled = Signal(bool)

    def __init__(self, *args):
        super(QMaxRollout, self).__init__(*args)
        self._expanded = True
        self._delayed = False, False

        self.setSizePolicy(QtW.QSizePolicy(QtW.QSizePolicy.MinimumExpanding, QtW.QSizePolicy.Minimum))

        self._full_title = str()
        self._title = self._full_title

        self._header_rect = QRect()
        self._title_bound_rect = QRect()
        self._base_margin = QMargins(9, 9, 9, 9)
        self._icon_width = 24

        self._storage = QtW.QWidget()
        self._storage.setVisible(False)

        self._system_font = QtG.QFont()

    # noinspection PyPep8Naming
    def setExpanded(self, state):
        self._expand_collapse(state)

    # noinspection PyPep8Naming
    def setExpandedDelay(self, state):
        self._delayed = True, state

    def _expand_collapse(self, state):
        self._expanded = state

        children = self.children()

        for child in children:
            if hasattr(child, "setVisible"):
                child.setVisible(state)
            else:
                layout_collapse_and_restore(child, state)

        if state:
            self.expanded.emit()
        else:
            self.collapsed.emit()

        self.update()

    # noinspection PyPep8Naming
    def isExpanded(self):
        return self._expanded

    def title(self):
        return self._full_title

    # noinspection PyPep8Naming
    def setTitle(self, title):
        self._full_title = title

    def toggle(self):
        self._expand_collapse(not self._expanded)
        self.toggled.emit(self._expanded)

    # ---------------------------------------------------
    #                    Events
    # ---------------------------------------------------

    def mouseReleaseEvent(self, e):
        point = (e.localPos()).toPoint()
        if self._header_rect.contains(point):
            self.toggle()
            e.accept()
        else:
            e.ignore()

    def paintEvent(self, e):
        # If delayed expand/collapse is activated, it won't process until the next paint event
        if self._delayed[0]:
            self._expand_collapse(self._delayed[1])
            self._delayed = False, False

        # Object Repaint
        qp = QtG.QPainter()
        qp.begin(self)
        self._system_font = qp.font()
        self._recalculate_header()
        super(QMaxRollout, self).paintEvent(e)
        self._draw_widget(qp)
        qp.end()
        e.accept()

    # ---------------------------------------------------
    #               Paint Event Helpers
    # ---------------------------------------------------

    def _recalculate_header(self):
        fnt_title = bold_font(self._system_font)
        font_metric = QtG.QFontMetricsF(fnt_title)

        if self._full_title == str():
            prop = self.property('title')
            if prop is not None:
                self._title_bound_rect = font_metric.boundingRect(prop)
                self._full_title = prop
            else:
                self._title_bound_rect = font_metric.boundingRect("UNTITLED")
        else:
            self._title_bound_rect = font_metric.boundingRect(self._full_title)

        title_space = self.width() - (self._icon_width + self._base_margin.right() + self._base_margin.left())

        # If the title is too big to fit in the box
        if self._title_bound_rect.width() > title_space:
            self._title = chop_title(self._full_title, title_space, self._title_bound_rect.width())
            self._title_bound_rect = font_metric.boundingRect(self._title)
        else:
            self._title = self._full_title

        self._header_rect = QRect(
            self._base_margin.left(),
            self._base_margin.top(),
            self.width() - (self._base_margin.left() - self._base_margin.right()),
            self._title_bound_rect.height() + self._base_margin.top()
        )

    def _draw_widget(self, qp):
        size = self.size()
        w = size.width()
        h = size.height()

        mrgn = self._base_margin

        br_bkg = QtG.QBrush(QtG.QColor(80, 80, 80))
        # pal = self.palette()
        # br_bkg = pal.alternateBase()
        pn_bkg = QtG.QPen(QtG.QColor(62, 62, 62), 2)
        br_arr = QtG.QBrush(QtG.QColor(185, 185, 185))
        pn_arr = QtG.QPen(QtG.QColor(62, 62, 62), 0)
        # For debugging
        # pn_test = QtG.QPen(Qt.red, 1)
        pn_txt = QtG.QPen(QtG.QColor(255, 255, 255))

        rnd_x, rnd_y = calculate_round_corners(w, h, 11)
        rct_bkg = QRect(0, 0, w, h)

        qp.setPen(pn_bkg)
        qp.setBrush(br_bkg)

        qp.setRenderHint(QtG.QPainter.Antialiasing)

        qp.drawRoundRect(rct_bkg, rnd_x, rnd_y, Qt.RelativeSize)

        tx_title = self._title

        qp.setFont(bold_font(self._system_font))

        rct_icon = QRect(
            mrgn.left(), mrgn.top(), self._icon_width, self._title_bound_rect.height()
        )

        rct_title = QRect(
            rct_icon.right(), mrgn.top(), self._title_bound_rect.width(), self. _title_bound_rect.height()
        )

        pgn_arrow = center_poly_in_rect(max_arrow(not self._expanded), rct_icon)

        qp.setPen(pn_arr)
        qp.setBrush(br_arr)

        qp.drawPolygon(pgn_arrow)

        qp.setPen(pn_txt)

        qp.drawText(rct_title, tx_title)

        open_margins = QMargins(
            mrgn.left(), self._title_bound_rect.height() + (mrgn.top() * 2), mrgn.right(), mrgn.bottom()
        )
        closed_margins = QMargins(
            mrgn.left(), self._title_bound_rect.height() + mrgn.top(), mrgn.right(), mrgn.bottom()
        )
        mrgn = open_margins if self._expanded else closed_margins
        self.setContentsMargins(mrgn)

        # For debugging
        # qp.setPen(pn_test)
        qp.setBrush(Qt.NoBrush)

        qp.setFont(self._system_font)


def calculate_round_corners(width, height, bevel):
    """
    Calculates percentages for a given width and height to produce even bevels on non-square rectangles
    :param width:
    :param height:
    :param bevel:
    :return:
    """
    x = float(bevel) / width * 100.0
    y = float(bevel) / height * 100.0
    return x, y


def max_arrow(right_facing):
    """
    Creates a polygon that matches Max's ui Arrow
    :param right_facing: Bool: True for right facing arrow, false for down facing arrow
    :return: a QPolygonF
    """
    polygon = QtG.QPolygonF()
    if right_facing:
        polygon.append(QPointF(0.0, 0.0))
        polygon.append(QPointF(0.0, 12.0))
        polygon.append(QPointF(8.0, 6.0))
    else:
        polygon.append(QPointF(0.0, 0.0))
        polygon.append(QPointF(12.0, 0.0))
        polygon.append(QPointF(6.0, 8.0))
    return polygon


def center_poly_in_rect(poly, rect):
    """
    Centers a QPolygon inside a QRect
    :param poly: A QPolygon
    :param rect: A QRect
    :return: The QPolygon translated to the center of the QRect
    """
    poly_bounds = poly.boundingRect()

    p_w = poly_bounds.width()
    p_h = poly_bounds.height()
    r_w = abs(rect.left() - rect.right())
    r_h = abs(rect.top() - rect.bottom())

    m_w = (r_w - p_w) / 2
    m_h = (r_h - p_h) / 2

    poly.translate(poly_bounds.left() * -1, poly_bounds.top() * -1)

    m_w = 0 if m_w < 1 else m_w
    m_h = 0 if m_h < 1 else m_h

    x = rect.left() + m_w
    y = rect.top() + m_h

    poly.translate(x, y)

    return poly


def bold_font(font):
    """
    Returns a copy of the font but bold'd
    :param font: a QFont
    :return: a QFont, bold set to True
    """
    fnt_orig = font
    fnt_bold = QtG.QFont(fnt_orig)
    fnt_bold.setBold(True)
    return fnt_bold


def chop_title(title, title_space, title_width):
    """
    Chops a title based on the proportional space it has to fit into
    :param title: String: Containing the title
    :param title_space: Float: The space for the title to fit into
    :param title_width: Float: The length of the full title
    :return: The title with the extras chopped out
    """
    # The percentage leftover from the title width once the size of the title space is subtracted
    percent = 1 - (title_space / title_width)
    # The number of characters
    ch_count = len(title)
    # The number of characters with the proportion of percent subtracted from it
    i = int(ch_count - math.floor(ch_count * percent))
    return title[:i]


def layout_collapse_and_restore(layout, state):
    for child in layout.children():
        layout_collapse_and_restore(child, state)

    if type(layout) is QtW.QFormLayout():
        attribute_store_and_set(layout, state, 0, "verticalSpacing", "setVerticalSpacing")
        attribute_store_and_set(layout, state, 0, "horizontalSpacing", "setHorizontalSpacing")
    else:
        attribute_store_and_set(layout, state, 0, "spacing", "setSpacing")

    attribute_store_and_set(layout, state, QMargins(0, 0, 0, 0), "contentsMargins", "setContentsMargins")

    if hasattr(layout, "invalidate"):
        layout.invalidate()


def attribute_store_and_set(widget, state, new_value, get_func, set_func):
    if hasattr(widget, set_func):
        attr_name = "Old{}".format(set_func)
        if state:
            prop = widget.property(attr_name)
            if prop is not None:
                getattr(widget, set_func)(prop)
        else:
            old = getattr(widget, get_func)()
            widget.setProperty(attr_name, old)
            getattr(widget, set_func)(new_value)


# # noinspection PyUnresolvedReferences
# class Window(QtW.QDialog):
#     def __init__(self, parent=MaxPlus.GetQMaxMainWindow()):
#         super(Window, self).__init__(parent)
#
#         self._main_layout = QtW.QVBoxLayout()
#
#         self._rollup_test1 = QMaxRollout()
#         self._rollup_test1.setProperty("title", "DYNAMISM!")
#         self._rollup_test2 = QMaxRollout()
#         self._rollup_test2.setTitle("Big Ass MuthaFunkin Buttons Baby")
#         self._rollup_test3 = QMaxRollout()
#         self._rollup_test3.setTitle("Non-Empty Boy")
#
#         self.radio1 = QtW.QRadioButton("Radio button 1")
#         self.radio2 = QtW.QRadioButton("Radio button 2")
#         self.radio3 = QtW.QRadioButton("Radio button 3")
#
#         self.radio1.setChecked(True)
#
#         self.v_box1 = QtW.QVBoxLayout()
#         self.v_box1.addWidget(self.radio1)
#         self.v_box1.addWidget(self.radio2)
#         self.v_box1.addWidget(self.radio3)
#         self.v_box1.addStretch(1)
#
#         self.push1 = QtW.QPushButton("Push button 1")
#         self.push2 = QtW.QPushButton("Push button 2")
#         self.push3 = QtW.QPushButton("Push button 3")
#
#         self.push1.clicked.connect(self.expand_layout_handler)
#         self.push2.clicked.connect(self.print_layout_handler)
#
#         self.radio4 = QtW.QRadioButton("Radio button 4")
#         self.radio5 = QtW.QRadioButton("Radio button 5")
#         self.radio6 = QtW.QRadioButton("Radio button 6")
#
#         self.check1 = QtW.QCheckBox("Check Box 1")
#         self.check2 = QtW.QCheckBox("Check Box 2")
#         self.check3 = QtW.QCheckBox("Check Box 3")
#
#         self.label1 = QtW.QLabel("Combo Box 1")
#         self.label2 = QtW.QLabel("Combo Box 2")
#         self.label3 = QtW.QLabel("Combo Box 3")
#
#         self.cmbx1 = QtW.QComboBox()
#         self.cmbx2 = QtW.QComboBox()
#         self.cmbx3 = QtW.QComboBox()
#
#         self.cmbx1.addItems(("Box 1", "Tube 1", "Sphere 1"))
#         self.cmbx2.addItems(("Box 2", "Tube 2", "Sphere 2"))
#         self.cmbx3.addItems(("Box 3", "Tube 3", "Sphere 3"))
#
#         self.v_box2 = QtW.QVBoxLayout()
#         self.v_box2.addWidget(self.push1)
#         self.v_box2.addWidget(self.push2)
#         self.v_box2.addWidget(self.push3)
#
#         self.v_box2a = QtW.QVBoxLayout()
#         self.v_box2a.setSpacing(10)
#         self.v_box2a.addWidget(self.radio4)
#         self.v_box2a.addWidget(self.radio5)
#         self.v_box2a.addWidget(self.radio6)
#         self.v_box2a.addStretch(1)
#
#         self.form1 = QtW.QFormLayout()
#         self.form1.setVerticalSpacing(10)
#         self.form1.addWidget(self.check1)
#         self.form1.addWidget(self.check2)
#         self.form1.addWidget(self.check3)
#
#         self.form2 = QtW.QFormLayout()
#         self.form2.setVerticalSpacing(10)
#         self.form2.setHorizontalSpacing(10)
#         self.form2.insertRow(1, self.label1, self.cmbx1)
#         self.form2.insertRow(2, self.label2, self.cmbx2)
#         self.form2.insertRow(3, self.label3, self.cmbx3)
#
#         self.v_box2.addLayout(self.form1)
#         self.v_box2.addLayout(self.v_box2a)
#         self.v_box2.addStretch(1)
#
#         self.v_box3 = QtW.QVBoxLayout()
#         self.v_box3.addLayout(self.form2)
#
#         self._rollup_test1.setLayout(self.v_box1)
#
#         self._rollup_test2.setLayout(self.v_box2)
#
#         self._rollup_test3.setLayout(self.v_box3)
#
#         self._main_layout.addWidget(self._rollup_test1)
#         self._main_layout.addWidget(self._rollup_test2)
#         self._main_layout.addWidget(self._rollup_test3)
#         self._main_layout.addStretch(1)
#
#         self.setLayout(self._main_layout)
#
#         print("Window Initialized!")
#
#     def expand_layout_handler(self):
#         self.form2.setHorizontalSpacing(10)
#
#     def print_layout_handler(self):
#         print(self.form2.horizontalSpacing())
#
#
# import MaxPlus
# print("Started")
# # app = QtW.QApplication(sys.argv)
# ui = Window()
# ui.show()
# # app.exec_()
