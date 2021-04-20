from elasticsearch import serializer, compat, exceptions
import json
from common.utils.text_utils import fix_utf8_string


class FlexibleUTF8Serializer(serializer.JSONSerializer):
    """UTF8 JSON Serializer that doesn't break on invalid utf-8 characters"""
    def dumps(self, data):
        if isinstance(data, compat.string_types):
            return fix_utf8_string(data)
        try:
            return json.dumps(data, default=self.default)
        except (ValueError, TypeError) as e:
            raise exceptions.SerializationError(data, e)
