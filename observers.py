from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPen
from container import StorageObserver
from storage_objects import StorageObject, Group

class TreeViewObserver(StorageObserver):
    def __init__(self, tree_widget: QTreeWidget, container):
        self.tree = tree_widget
        self.container = container
        self.block_selection = False

    def rebuild_tree(self):
        self.tree.clear()
        for obj in self.container.get_objects():
            self._add_tree_item(None, obj)

    def _add_tree_item(self, parent_item: QTreeWidgetItem, obj: StorageObject):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, f"{obj.get_type_name()} (id={id(obj)})")
        item.setData(0, 256, obj)
        if parent_item is None:
            self.tree.addTopLevelItem(item)
        if isinstance(obj, Group):
            for child in obj.children:
                self._add_tree_item(item, child)

    def on_object_added(self, obj: StorageObject):
        self.rebuild_tree()

    def on_object_removed(self, obj: StorageObject):
        self.rebuild_tree()

    def on_object_selected(self, obj: StorageObject):
        self.block_selection = True
        self._select_in_tree(obj)
        self.block_selection = False

    def _select_in_tree(self, obj):
        def find_item(root_item):
            if root_item.data(0, 256) == obj:
                return root_item
            for i in range(root_item.childCount()):
                res = find_item(root_item.child(i))
                if res:
                    return res
            return None

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            found = find_item(item)
            if found:
                self.tree.setCurrentItem(found)
                return

    def on_container_cleared(self):
        self.rebuild_tree()

    def on_object_moved(self, obj: StorageObject, dx: int, dy: int):
        self.rebuild_tree()


class Arrow(StorageObserver):
    def __init__(self, source: StorageObject, target: StorageObject, container, drawing_widget):
        self.source = source
        self.target = target
        self.container = container
        self.drawing_widget = drawing_widget
        container.attach(self)

    def on_object_moved(self, obj: StorageObject, dx: int, dy: int):
        if obj == self.source and self.target in self.container.get_objects():
            # Используем move_object, чтобы сгенерировать уведомление для транзитивности
            self.container.move_object(self.target, dx, dy, self.drawing_widget.rect())

    def draw(self, painter):
        src_center = (self.source.x + self.source.width//2, self.source.y + self.source.height//2)
        tgt_center = (self.target.x + self.target.width//2, self.target.y + self.target.height//2)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(src_center[0], src_center[1], tgt_center[0], tgt_center[1])

    def on_object_added(self, obj): pass
    def on_object_removed(self, obj): pass
    def on_object_selected(self, obj): pass
    def on_container_cleared(self): pass