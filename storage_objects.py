from abc import ABC, abstractmethod
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush

class StorageObject(ABC):
    def __init__(self, x=0, y=0, width=60, height=60):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.selected = False
        self.color = QColor(100, 150, 200)

    @abstractmethod
    def draw(self, painter: QPainter):
        pass

    def contains_point(self, point: QPoint) -> bool:
        return (self.x <= point.x() <= self.x + self.width and
                self.y <= point.y() <= self.y + self.height)

    def move(self, dx, dy, bounds: QRect):
        new_x = self.x + dx
        new_y = self.y + dy
        if new_x < 0:
            new_x = 0
        if new_y < 0:
            new_y = 0
        if new_x + self.width > bounds.width():
            new_x = bounds.width() - self.width
        if new_y + self.height > bounds.height():
            new_y = bounds.height() - self.height
        self.x = new_x
        self.y = new_y

    @abstractmethod
    def save(self, writer):
        pass

    @abstractmethod
    def load(self, reader):
        pass

    @abstractmethod
    def get_type_name(self) -> str:
        pass


class RectangleObject(StorageObject):
    def draw(self, painter: QPainter):
        painter.setBrush(QBrush(self.color if not self.selected else QColor(255, 255, 0)))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(self.x, self.y, self.width, self.height)

    def save(self, writer):
        writer.write("Rectangle\n")
        writer.write(f"{self.x} {self.y} {self.width} {self.height} {self.color.red()} {self.color.green()} {self.color.blue()}\n")

    def load(self, reader):
        line = reader.readline().strip()
        parts = line.split()
        if len(parts) >= 7:
            self.x = int(parts[0])
            self.y = int(parts[1])
            self.width = int(parts[2])
            self.height = int(parts[3])
            r, g, b = int(parts[4]), int(parts[5]), int(parts[6])
            self.color = QColor(r, g, b)

    def get_type_name(self):
        return "Rectangle"


class EllipseObject(StorageObject):
    def draw(self, painter: QPainter):
        painter.setBrush(QBrush(self.color if not self.selected else QColor(255, 255, 0)))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(self.x, self.y, self.width, self.height)

    def save(self, writer):
        writer.write("Ellipse\n")
        writer.write(f"{self.x} {self.y} {self.width} {self.height} {self.color.red()} {self.color.green()} {self.color.blue()}\n")

    def load(self, reader):
        line = reader.readline().strip()
        parts = line.split()
        if len(parts) >= 7:
            self.x = int(parts[0])
            self.y = int(parts[1])
            self.width = int(parts[2])
            self.height = int(parts[3])
            r, g, b = int(parts[4]), int(parts[5]), int(parts[6])
            self.color = QColor(r, g, b)

    def get_type_name(self):
        return "Ellipse"


class Group(StorageObject):
    def __init__(self):
        super().__init__()
        self.children = []

    def add(self, obj: StorageObject):
        self.children.append(obj)
        self._recalc_bounds()

    def remove(self, obj: StorageObject):
        self.children.remove(obj)
        self._recalc_bounds()

    def _recalc_bounds(self):
        if not self.children:
            return
        min_x = min(c.x for c in self.children)
        min_y = min(c.y for c in self.children)
        max_x = max(c.x + c.width for c in self.children)
        max_y = max(c.y + c.height for c in self.children)
        self.x = min_x
        self.y = min_y
        self.width = max_x - min_x
        self.height = max_y - min_y

    def draw(self, painter: QPainter):
        for child in self.children:
            child.draw(painter)
        if self.selected:
            painter.setPen(QPen(QColor(0, 0, 255), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.x, self.y, self.width, self.height)

    def contains_point(self, point: QPoint) -> bool:
        return any(child.contains_point(point) for child in self.children)

    def move(self, dx, dy, bounds: QRect):
        new_x = self.x + dx
        new_y = self.y + dy
        if new_x < 0:
            dx = -self.x
        if new_y < 0:
            dy = -self.y
        if new_x + self.width > bounds.width():
            dx = bounds.width() - (self.x + self.width)
        if new_y + self.height > bounds.height():
            dy = bounds.height() - (self.y + self.height)

        for child in self.children:
            child.move(dx, dy, bounds)
        self.x += dx
        self.y += dy
        self._recalc_bounds()

    def save(self, writer):
        writer.write("Group\n")
        writer.write(f"{len(self.children)}\n")
        for child in self.children:
            child.save(writer)

    def load(self, reader):
        line = reader.readline().strip()
        count = int(line)
        self.children.clear()
        from factory import StorageFactory
        for _ in range(count):
            type_line = reader.readline().strip()
            obj = StorageFactory.create_object(type_line)
            obj.load(reader)
            self.children.append(obj)
        self._recalc_bounds()

    def get_type_name(self):
        return "Group"