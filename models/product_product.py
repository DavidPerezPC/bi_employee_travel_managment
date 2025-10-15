from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    duration_dependant = fields.Boolean(string='Duration Dependant', 
                                        help="Indicates if the product's price is dependent on the duration of the travel",
                                        default=False)