from storage_objects import RectangleObject, EllipseObject, Group

class StorageFactory:
    @staticmethod
    def create_object(type_name: str):
        if type_name == "Rectangle":
            return RectangleObject()
        elif type_name == "Ellipse":
            return EllipseObject()
        elif type_name == "Group":
            return Group()
        else:
            raise ValueError(f"Unknown object type: {type_name}")