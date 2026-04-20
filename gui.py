import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTreeWidget, QFileDialog, QMessageBox,
                             QApplication)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QKeyEvent

from storage_objects import StorageObject, RectangleObject, EllipseObject, Group
from container import StorageContainer
from observers import TreeViewObserver, Arrow


class DrawingWidget(QWidget):
    def __init__(self, container: StorageContainer, parent=None):
        super().__init__(parent)
        self.container = container
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.dragging = False
        self.drag_start = None
        self.rubber_band_active = False
        self.rubber_band_rect = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.arrows = []

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        for obj in self.container.get_objects():
            obj.draw(painter)
        for arrow in self.arrows:
            arrow.draw(painter)
        if self.rubber_band_rect:
            painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rubber_band_rect)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            selected = [obj for obj in self.container.get_objects() if obj.selected]
            if selected:
                if hasattr(self.parent(), 'remove_arrows_for_objects'):
                    self.parent().remove_arrows_for_objects(selected)
                for obj in selected:
                    self.container.remove(obj)
                self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.pos()
            clicked_obj = None
            for obj in reversed(self.container.get_objects()):
                if obj.contains_point(event.pos()):
                    clicked_obj = obj
                    break
            if clicked_obj:
                # Нажат объект
                if event.modifiers() & Qt.ControlModifier:
                    if clicked_obj.selected:
                        clicked_obj.selected = False
                        self.container._notify_selected(None)
                    else:
                        # Добавляем к выделению
                        clicked_obj.selected = True
                        self.container._notify_selected(clicked_obj)
                else:
                    self.container.clear_selection()
                    clicked_obj.selected = True
                    self.container._notify_selected(clicked_obj)
                self.dragging = True
                self.rubber_band_active = False
                self.rubber_band_rect = None
            else:
                self.container.clear_selection()
                self.rubber_band_active = True
                self.rubber_band_rect = QRect(event.pos(), event.pos())
            self.update()

    def mouseMoveEvent(self, event):
        if self.dragging and self.drag_start:
            # Перетаскивание выделенных объектов
            dx = event.x() - self.drag_start.x()
            dy = event.y() - self.drag_start.y()
            if dx != 0 or dy != 0:
                selected = [obj for obj in self.container.get_objects() if obj.selected]
                for obj in selected:
                    self.container.move_object(obj, dx, dy, self.rect())
                self.drag_start = event.pos()
                self.update()
        elif self.rubber_band_active and self.rubber_band_rect:
            # Обновляем резиновую рамку
            self.rubber_band_rect.setBottomRight(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.rubber_band_active and self.rubber_band_rect:
            rubber = self.rubber_band_rect.normalized()
            self.container.clear_selection()
            for obj in self.container.get_objects():
                if self._rect_intersects_object(rubber, obj):
                    obj.selected = True
                    self.container._notify_selected(obj)
            self.rubber_band_active = False
            self.rubber_band_rect = None
            self.update()
        self.dragging = False
        self.drag_start = None

    def _rect_intersects_object(self, rect: QRect, obj: StorageObject) -> bool:
        obj_rect = QRect(obj.x, obj.y, obj.width, obj.height)
        return rect.intersects(obj_rect)

    def get_selected_objects(self):
        return [obj for obj in self.container.get_objects() if obj.selected]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЛР 6,7")
        self.container = StorageContainer()
        self.arrows = []

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Объекты")
        self.tree.itemSelectionChanged.connect(self.on_tree_selection)
        left_layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        self.btn_group = QPushButton("Сгруппировать")
        self.btn_ungroup = QPushButton("Разгруппировать")
        self.btn_save = QPushButton("Сохранить")
        self.btn_load = QPushButton("Загрузить")
        self.btn_add_rect = QPushButton("Добавить прямоуг.")
        self.btn_add_ellipse = QPushButton("Добавить эллипс")
        self.btn_add_arrow = QPushButton("Добавить стрелку")
        btn_layout.addWidget(self.btn_add_rect)
        btn_layout.addWidget(self.btn_add_ellipse)
        btn_layout.addWidget(self.btn_group)
        btn_layout.addWidget(self.btn_ungroup)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_add_arrow)
        left_layout.addLayout(btn_layout)

        self.drawing = DrawingWidget(self.container)
        self.drawing.arrows = self.arrows
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.drawing, 3)

        self.tree_observer = TreeViewObserver(self.tree, self.container)
        self.container.attach(self.tree_observer)
        self.tree_observer.rebuild_tree()

        self.btn_group.clicked.connect(self.group_selected)
        self.btn_ungroup.clicked.connect(self.ungroup_selected)
        self.btn_save.clicked.connect(self.save_project)
        self.btn_load.clicked.connect(self.load_project)
        self.btn_add_rect.clicked.connect(lambda: self.add_object(RectangleObject()))
        self.btn_add_ellipse.clicked.connect(lambda: self.add_object(EllipseObject()))
        self.btn_add_arrow.clicked.connect(self.create_arrow)

        self.add_object(RectangleObject(50, 50, 80, 80))
        self.add_object(EllipseObject(200, 100, 70, 70))

    def add_object(self, obj):
        self.container.add(obj)
        self.drawing.update()

    def group_selected(self):
        selected = self.drawing.get_selected_objects()
        if len(selected) < 2:
            QMessageBox.information(self, "Группировка", "Выделите хотя бы 2 объекта")
            return
        group = Group()
        for obj in selected:
            group.add(obj)
            self.container.remove(obj)
        self.container.add(group)
        self.container.select_object(group)
        self.drawing.update()

    def ungroup_selected(self):
        selected = self.drawing.get_selected_objects()
        if len(selected) != 1 or not isinstance(selected[0], Group):
            QMessageBox.information(self, "Разгруппировка", "Выделите одну группу")
            return
        group = selected[0]
        self.container.remove(group)
        for child in group.children:
            self.container.add(child)
        self.drawing.update()

    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить проект", "", "Text files (*.txt)")
        if filename:
            self.container.save_to_file(filename)
            QMessageBox.information(self, "Сохранение", "Проект сохранён")

    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузить проект", "", "Text files (*.txt)")
        if filename:
            self.container.load_from_file(filename)
            for arrow in self.arrows:
                self.container.detach(arrow)
            self.arrows.clear()
            self.drawing.update()

    def create_arrow(self):
        selected = self.drawing.get_selected_objects()
        if len(selected) != 2:
            QMessageBox.information(self, "Стрелка", "Выделите два объекта (источник и цель)")
            return
        src, tgt = selected[0], selected[1]
        arrow = Arrow(src, tgt, self.container, self.drawing)
        self.arrows.append(arrow)
        self.drawing.update()
        QMessageBox.information(self, "Стрелка", f"Стрелка от {src.get_type_name()} к {tgt.get_type_name()} создана")

    def on_tree_selection(self):
        items = self.tree.selectedItems()
        if items and not self.tree_observer.block_selection:
            obj = items[0].data(0, 256)
            if obj:
                self.container.select_object(obj)
                self.drawing.update()

    def remove_arrows_for_objects(self, objects_to_delete):
        to_remove = []
        for arrow in self.arrows:
            if arrow.source in objects_to_delete or arrow.target in objects_to_delete:
                self.container.detach(arrow)
                to_remove.append(arrow)
        for arrow in to_remove:
            self.arrows.remove(arrow)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()