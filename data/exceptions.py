class RecordAlreadyExists(Exception):
    def __init__(self, obj):
        super().__init__(f"This record already exists {obj}")


class RecordIsMissing(Exception):
    def __init__(self, fieldValue):
        super().__init__(f"Record with field value {fieldValue} is missing")
