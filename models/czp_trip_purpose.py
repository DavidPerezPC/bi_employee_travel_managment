from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CzPTripPurpose(models.Model):
    _name = 'czp.trip.purpose'
    _description = "Trip's Purpose"
    _rec_name = 'name'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique.'),
        ('name_unique', 'unique(name)', 'The name must be unique.'),
    ]

    code = fields.Char(string='Code', help='Enter the trip purpose code', required=True)
    name = fields.Char(string='Name', help='Enter the trip purpose name', required=True)
