from jsonmodels import fields
from utils.jsonmodels_ext import BaseModel


class HouseholdGeneral(BaseModel):
    number_people = fields.FloatField()
    start_time = fields.StringField()
    end_time = fields.StringField()
    latitude = fields.FloatField()
    longitude = fields.FloatField()


class LoadprofileConfig(BaseModel):
    general = HouseholdGeneral()
