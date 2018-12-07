import PySide2.QtWidgets as QtW
import PySide2.QtGui as QtG
from PySide2.QtCore import Signal, Qt, QRect, QMargins, QPointF

import sys
import MaxPlus


class QMaxRollup(QtW.QGroupBox):
    collapsed = Signal()
    expanded = Signal()

    def __init__(self, *args):
        super(QMaxRollup, self).__init__(*args)
        self._expanded = True

        self.setCheckable(True)
        self.setChecked(True)

        self.clicked.connect(self.toggle)

        self._base_margin = QMargins(9, 9, 9, 9)

    # noinspection PyPep8Naming
    def setExpanded(self, state):
        self._expanded = state
        self.setChecked(state)

        for child in self.children():
            if hasattr(child, "setVisible"):
                child.setVisible(state)

        if state:
            self.expanded.emit()
        else:
            self.collapsed.emit()

    # noinspection PyPep8Naming
    def isExpanded(self):
        return self._expanded

    def toggle(self):
        self.setExpanded(not self._expanded)

    def paintEvent(self, e):

        qp = QtG.QPainter()
        qp.begin(self)
        # qp.fillRect(e.rect(), QtG.QBrush(self.color))
        draw_info = self._draw_widget(qp)
        qp.end()

        self.setContentsMargins(draw_info.get("contentsMargin", self._base_margin))

    def _draw_widget(self, qp):
        draw_info = dict()
        size = self.size()
        w = size.width()
        h = size.height()

        margins = self._base_margin

        br_bkg = QtG.QBrush(QtG.QColor(80, 80, 80))
        pn_bkg = QtG.QPen(QtG.QColor(62, 62, 62), 2)
        br_arr = QtG.QBrush(QtG.QColor(185, 185, 185))
        pn_arr = QtG.QPen(QtG.QColor(62, 62, 62), 0)
        pn_test = QtG.QPen(Qt.red, 1)
        pn_txt = QtG.QPen(QtG.QColor(255, 255, 255))

        rnd_x, rnd_y = calculate_round_corners(w, h, 11)
        rct_bkg = QRect(0, 0, w, h)

        qp.setPen(pn_bkg)
        qp.setBrush(br_bkg)

        qp.setRenderHint(QtG.QPainter.Antialiasing)

        qp.drawRoundRect(rct_bkg, rnd_x, rnd_y, Qt.RelativeSize)

        tx_title = self.title()

        icon_w = 24

        fnt_orig = qp.font()
        fnt_title = QtG.QFont(fnt_orig)
        fnt_title.setBold(True)
        qp.setFont(fnt_title)

        bd_rct_title = qp.boundingRect(QRect(), 0, tx_title)

        rct_icon = QRect(self._base_margin.left(), self._base_margin.top(), icon_w, bd_rct_title.height())

        rct_title = QRect(rct_icon.right(), rct_icon.top(), bd_rct_title.width(), bd_rct_title.height())

        pgn_arrow = center_poly_in_rect(max_arrow(not self._expanded), rct_icon)

        qp.setPen(pn_test)
        qp.setBrush(Qt.NoBrush)

        qp.drawRect(rct_icon)
        qp.drawRect(rct_title)

        qp.drawRect(QRect(
            margins.left(),
            margins.top(),
            w - (margins.left() + margins.right()),
            h - (margins.top() + margins.bottom())
        ))

        qp.drawRect(self.childrenRect())

        qp.setPen(pn_arr)
        qp.setBrush(br_arr)

        qp.drawPolygon(pgn_arrow)

        qp.setPen(pn_txt)

        qp.drawText(rct_title, tx_title)

        draw_info["contentsMargin"] = QMargins(margins.left(),
                                               rct_icon.height() + margins.top(),
                                               margins.right(),
                                               margins.bottom())

        qp.setFont(fnt_orig)

        return draw_info


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


class Window(QtW.QDialog):
    def __init__(self, parent=MaxPlus.GetQMaxMainWindow()):
        super(Window, self).__init__(parent)

        self._main_layout = QtW.QVBoxLayout()

        self._rollup_test = QMaxRollup("Settings")

        self.radio1 = QtW.QRadioButton("Radio button 1")
        self.radio2 = QtW.QRadioButton("Radio button 2")
        self.radio3 = QtW.QRadioButton("Radio button 3")

        self.radio1.setChecked(True)

        self.v_box = QtW.QVBoxLayout()
        self.v_box.addWidget(self.radio1)
        self.v_box.addWidget(self.radio2)
        self.v_box.addWidget(self.radio3)
        self.v_box.addStretch(1)

        self._rollup_test.setLayout(self.v_box)

        self._main_layout.addWidget(self._rollup_test)
        self._main_layout.addStretch(1)

        self.setLayout(self._main_layout)

        print("Window Initialized!")


print("Started")
# app = QtW.QApplication(sys.argv)
ui = Window()
ui.show()
# app.exec_()
