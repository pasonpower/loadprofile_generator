import logging
import numpy as np
import pandas as pd
from flasgger import Swagger
from flask import Flask, request, jsonify, redirect
from datetime import datetime

from config.loadprofile_config import LoadprofileConfig, HouseholdGeneral
from utils.swagger import swag_and_validate
from household_appliances.household_appliances import EVCharger

DATE_TIME = "date_time"
DATE_FORMATE = "%Y-%m-%d"
DATE_TIME_FORMATE = "%Y-%m-%d %H:%M:%S"
START_TIME = "2010-01-01 00:00:00"
END_TIME = "2010-03-01 00:00:00"
DATE_RANGE = pd.date_range("2020-01-01", "2020-01-03", freq="15T", tz="UTC")
DATE_RANGE.name = DATE_TIME
EXAMPLE_LOADPROFILE_DATAFRAME = pd.DataFrame(data={"load_power_w": np.random.rand(len(DATE_RANGE))}, index=DATE_RANGE)
EXAMPLE_HOUSEHOLD_GENERAL = HouseholdGeneral(
    number_people=3, start_time=START_TIME, end_time=END_TIME, latitude=29.760427, longitude=-95.369804
)
EXAMPLE_LOADPROFILE_CONFIG = LoadprofileConfig(general=EXAMPLE_HOUSEHOLD_GENERAL).to_json()

log = logging.getLogger(__name__)
# Enable HTTP request logs to stdout
logging.getLogger("werkzeug").setLevel(logging.INFO)

app = Flask(__name__)
app.config["SWAGGER"] = {
    "swagger_version": "2.0",
    "title": "Energy Toolbase Loadprofile Generator API",
    "uiversion": 2,
    "specs": [
        {
            "version": "0.0.1",
            "title": "Loadprofile Generator API",
            "description": "An API for Interacting with Energy Toolbase Loadprofile Generator",
            "endpoint": "spec",
            "route": "/spec",
        }
    ],
}
app.config["PROPOGATE_EXCEPTIONS"] = True
app.config["JWT_AUTH_URL_RULE"] = "/login"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # max content-length is 50MB
app.logger.propagate = True

Swagger(app)


@app.route("/version")
def version():
    return "loadprofile_generator v0.1"


@app.route("/api")
def swagger():
    return redirect("/apidocs/index.html", code=302)


@app.route("/health", methods=["GET"])
def health():
    return "ok"


@app.route("/getloadprofile", methods=["POST"])
# @swag_and_validate(
#     {"definitions": {"LoadprofileConfig": LoadprofileConfig.to_def(example=EXAMPLE_LOADPROFILE_CONFIG)}},
#     validation=True,
# )
def getloadprofile():
    """
        Loadprofile Generator API / Get Loadprofile
        ---
        tags:
        - Loadprofile Generator
        summary: >-
            Return the aggregated loadprofile based on query config
        consumes:
            - "application/json"
        parameters:
          - name: loadprofile_config
            in: body
            required: true
            description: loadprofile configuration
            # schema:
            #     $ref: '#/definitions/LoadprofileConfig'
        produces:
          - "text/csv"
        responses:
            204:
                description: Empty response on success
    """

    parameters = request.get_json()
    general = parameters["general"]
    appliances = list(parameters["appliances"].keys())
    result = {}
    individual_trace_result = {}
    try:
        start_time = general["start_time"] if "start_time" in general else START_TIME
        end_time = general["end_time"] if "end_time" in general else END_TIME
        start_time = datetime.strptime(start_time, DATE_TIME_FORMATE)
        end_time = datetime.strptime(end_time, DATE_TIME_FORMATE)
        aggregated_load = None
        if "ev_charger" in appliances:
            ev_charger_config = parameters["appliances"]["ev_charger"]
            number_ev = ev_charger_config["number_ev"] if "number_ev" in ev_charger_config.keys() else 1
            level = ev_charger_config["level"] if "level" in ev_charger_config.keys() else 1
            ev_charger = EVCharger(number_ev=number_ev, level=level)
            ev_charger_load = ev_charger.get_load(start_time, end_time)
            aggregated_load = ev_charger_load
            data_dict = parse_loadprofile_dateframe(ev_charger_load)
            individual_trace_result.update({"ev_charger": data_dict})
        aggregated_load = parse_loadprofile_dateframe(aggregated_load)
        result.update({"aggreated_load": aggregated_load})
        result.update({"individual_trace": individual_trace_result})
        return jsonify({"data": result})
    except:
        return "Invalid parameters", 400


def parse_loadprofile_dateframe(loadprofile):

    groupby_date = loadprofile.groupby(loadprofile.index.date)
    data_dict = {}
    for date, data in groupby_date:
        data_dict.update({date.strftime(DATE_FORMATE): data.values.ravel().tolist()})
    return data_dict


if __name__ == "__main__":

    app.run(host="0.0.0.0", use_reloader=False, port=5002)
