import json
import jsonschema
import logging
from flask import Response
from flasgger import swag_from
from http import HTTPStatus
from werkzeug.exceptions import abort
from functools import partial

log = logging.getLogger(__name__)


def validation_error_handler(err, data, schema):
    """
    Custom validation error handler which produces 404 Bad Request
    response in case validation fails and returns the error
    """
    log.warning("Error validation request: data={}, error={}".format(data, err))
    abort(Response(json.dumps({"error": str(err)}), status=HTTPStatus.BAD_REQUEST))


def validation_function(data, schema):
    """
    Custom validation function which drops parameter '_id' if present
    in data
    """
    clean_data = remove_null_fields(data)
    jsonschema.validate(clean_data, schema)


def remove_null_fields(d):
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (remove_null_fields(v) for v in d) if v]
    return {k: v for k, v in ((k, remove_null_fields(v)) for k, v in d.items()) if v}


# Allow easy access to swagger docs with validation
swag_and_validate = partial(
    swag_from,
    validation=True,
    validation_function=validation_function,
    validation_error_handler=validation_error_handler,
)
