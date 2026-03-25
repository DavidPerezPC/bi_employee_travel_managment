from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    duration_dependant = fields.Boolean(string='Duration Dependant', 
                                        help="Indicates if the product's price is dependent on the duration of the travel",
                                        default=False)
    
    expense_type = fields.Selection([
        ('viaticos', 'Viaticos'),
        ('general', 'General'),
    ], string="Tipo de Gasto", default='viaticos', help="Tipo del gasto para productos relacionados con viajes/gastos generales")