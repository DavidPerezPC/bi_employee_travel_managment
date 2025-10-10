from odoo import models, fields, api

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    manager_ids = fields.Many2many(
        'res.users',
        string='Travel Managers',
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref('bi_employee_travel_managment.hr_travel_manager_id').id)
        ],
        help='Users with the Travel Manager role'
    )