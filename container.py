from typing import List, Protocol
from storage_objects import StorageObject

class StorageObserver(Protocol):
    def on_object_added(self, obj: StorageObject): ...
    def on_object_removed(self, obj: StorageObject): ...
    def on_object_selected(self, obj: StorageObject): ...
    def on_container_cleared(self): ...
    def on_object_moved(self, obj: StorageObject, dx: int, dy: int): ...

class StorageContainer:
    def __init__(self):
        self._objects: List[StorageObject] = []
        self._observers: List[StorageObserver] = []

    def attach(self, observer: StorageObserver):
        self._observers.append(observer)

    def detach(self, observer: StorageObserver):
        self._observers.remove(observer)

    def _notify_added(self, obj: StorageObject):
        for obs in self._observers:
            obs.on_object_added(obj)

    def _notify_removed(self, obj: StorageObject):
        for obs in self._observers:
            obs.on_object_removed(obj)

    def _notify_selected(self, obj: StorageObject):
        for obs in self._observers:
            obs.on_object_selected(obj)

    def _notify_cleared(self):
        for obs in self._observers:
            obs.on_container_cleared()

    def _notify_moved(self, obj: StorageObject, dx: int, dy: int):
        for obs in self._observers:
            obs.on_object_moved(obj, dx, dy)

    def add(self, obj: StorageObject):
        self._objects.append(obj)
        self._notify_added(obj)

    def remove(self, obj: StorageObject):
        self._objects.remove(obj)
        self._notify_removed(obj)

    def clear(self):
        self._objects.clear()
        self._notify_cleared()

    def get_objects(self) -> List[StorageObject]:
        return self._objects.copy()

    def select_object(self, obj: StorageObject):
        for o in self._objects:
            o.selected = (o == obj)
        self._notify_selected(obj)

    def clear_selection(self):
        for o in self._objects:
            o.selected = False
        self._notify_selected(None)

    def move_object(self, obj: StorageObject, dx: int, dy: int, bounds):
        if obj in self._objects:
            old_x, old_y = obj.x, obj.y
            obj.move(dx, dy, bounds)
            self._notify_moved(obj, obj.x - old_x, obj.y - old_y)

    def save_to_file(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{len(self._objects)}\n")
            for obj in self._objects:
                obj.save(f)

    def load_from_file(self, filename: str):
        from factory import StorageFactory
        with open(filename, 'r', encoding='utf-8') as f:
            count_line = f.readline().strip()
            count = int(count_line)
            new_objects = []
            for _ in range(count):
                type_line = f.readline().strip()
                obj = StorageFactory.create_object(type_line)
                obj.load(f)
                new_objects.append(obj)
            self.clear()
            for obj in new_objects:
                self.add(obj)