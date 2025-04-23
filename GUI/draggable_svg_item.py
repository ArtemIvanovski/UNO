from PyQt5.QtGui import QTransform
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, pyqtProperty, QEasingCurve
from logger import logger


class DraggableCardItem(QGraphicsSvgItem):
    def __init__(self, svg_path, draggable=False, card=None, parent=None):
        super().__init__(svg_path, parent)

        self.draggable = draggable
        self.card = card
        self.card_is_played = False
        self.card_dropped_in_center = None
        self.compare_cards = None

        self.setAcceptHoverEvents(self.draggable)
        self.setFlags(self.ItemIsSelectable | self.ItemIsFocusable)

        self.center_rect = QRectF(700, 250, 300, 300)

        self.old_pos = None
        self.old_transform = None
        self.old_zvalue = 0

        self.anim = None

    @pyqtProperty(QPointF)
    def item_pos(self):
        return self.pos()

    @item_pos.setter
    def item_pos(self, new_pos):
        self.setPos(new_pos)

    def fly_to_position(self, x, y, duration=500, callback=None):
        self.anim = QPropertyAnimation(self, b"item_pos")
        self.anim.setDuration(duration)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPointF(x, y))
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        if callback:
            self.anim.finished.connect(callback)
        self.anim.start(QPropertyAnimation.DeleteWhenStopped)

    def hoverEnterEvent(self, event):
        if self.draggable and not self.card_is_played:
            self.setScale(self.scale() * 1.2)
            self.setZValue(10)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.draggable and not self.card_is_played:
            self.setScale(self.scale() / 1.2)
            self.setZValue(self.old_zvalue)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton and not self.card_is_played:
            self.old_pos = self.pos()
            self.old_transform = self.transform()
            self.old_zvalue = self.zValue()

            self.setZValue(10000)

            t = QTransform()
            t.reset()
            self.setTransform(t)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & Qt.LeftButton and not self.card_is_played:
            new_pos = self.mapToScene(event.pos())
            self.setPos(new_pos - QPointF(self.boundingRect().width() / 2,
                                          self.boundingRect().height() / 2))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton and not self.card_is_played:
            if self.center_rect.contains(self.scenePos()):
                if self.compare_cards and not self.compare_cards(self.card):
                    self.restore_position()
                else:
                    self.card_is_played = True
                    self.setScale(self.scale() / 1.2)
                    self.setZValue(9999)
                    logger.info("Карта сыграна!")
                    if self.card_dropped_in_center:
                        self.card_dropped_in_center()
            else:
                self.restore_position()
        super().mouseReleaseEvent(event)

    def restore_position(self):
        self.setZValue(self.old_zvalue)
        if self.old_pos:
            self.setPos(self.old_pos)
        if self.old_transform:
            self.setTransform(self.old_transform)