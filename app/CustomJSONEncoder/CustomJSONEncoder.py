import json
from datetime import datetime


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Преобразует datetime в строку в формате ISO 8601
        return super().default(obj)
