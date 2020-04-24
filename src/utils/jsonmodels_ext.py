from jsonmodels import fields, models
from jsonmodels.errors import ValidationError


class DefaultField(fields.BaseField):
    """
    Extension of the jsonmodels BaseField that allows for a default value
    to be specified.
    """

    DEFAULT = None

    def __init__(self, default=None, *args, **kwargs):
        self.default = default
        super().__init__(*args, **kwargs)

    def get_default_value(self):
        return self.default if self.default else self.DEFAULT


class DefaultIntField(DefaultField, fields.IntField):

    DEFAULT = 0


class StrictFloatField(fields.FloatField):
    """
    By default jsonmodels supports float or int values in a FloatField
    This field type coerces the type into a float regardless.
    """

    def parse_value(self, value):
        parsed = super().parse_value(value)
        return float(parsed) if parsed is not None else parsed


class DefaultFloatField(DefaultField, StrictFloatField):

    DEFAULT = 0.0


class DefaultBoolField(DefaultField, fields.BoolField):

    DEFAULT = False


class DefaultStringField(DefaultField, fields.StringField):

    DEFAULT = ""


class ListOrNone(fields.ListField):
    def to_struct(self, values):
        return [self._elem_to_struct(v) for v in values] if values else None

    def get_default_value(self):
        return None

    def validate(self, value):
        if not value:
            return

        return super().validate(value)


class BaseModel(models.Base):
    """
    Extension of the jsonmodels BaseModel that provides wrapper methods for
    generating JSON and for converting to Swagger definition.
    """

    def __str__(self):
        return str(self.to_json())

    def to_json(self):
        return self.to_struct()

    @classmethod
    def to_def(cls, example=None):
        json_schema = cls.to_json_schema()

        cls._convert_float_to_number(json_schema["properties"])

        if example:
            json_schema["example"] = example
        return json_schema

    @classmethod
    def _convert_float_to_number(cls, properties):
        """
        Converts all 'float' types to the proper Swagger type of 'number' with a format of 'float'.
        Works for hierarchies of objects as well.
        Args:
            properties: the json schema properties object
        """
        for prop in properties:
            if properties[prop]["type"] == "object":
                cls._convert_float_to_number(properties[prop]["properties"])
            if properties[prop]["type"] == "float":
                properties[prop]["type"] = "number"
                properties[prop]["format"] = "float"


# TODO: remove me once updated version of jsonmodels published
class EnumValidator(object):
    """
    Validator for enums.
    """

    def __init__(self, *choices):
        """
        Init.
        :param [] choices: Valid choices for the field.
        """
        self.choices = list(choices)

    def validate(self, value):
        if value not in self.choices:
            raise ValidationError("Value '{val}' is not a valid choice.".format(val=value))

    def modify_schema(self, field_schema):
        field_schema["enum"] = self.choices
