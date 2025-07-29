# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BudgetRule(models.Model):
    _name = "budget.rule"
    _description = "Budget Rule"
    _rec_name ="state_id"

    @api.model
    def _get_mexico_states(self):
        return [('country_id', '=', self.env.ref('base.mx').id)]
     
    state_id = fields.Many2one('res.country.state', string='State',help='State to which the plaza belongs',domain=_get_mexico_states,required=True)
    plaza_id = fields.Many2one(comodel_name='czp.plazas',string="Plaza",required=True)
    job_position_id = fields.Many2one('hr.job',string="Job Position")
    product_id = fields.Many2one(comodel_name='product.product',string="Expense Product",check_company=True,
        domain=[('can_be_expensed', '=', True)],
        ondelete='restrict',required=True)
    company_id = fields.Many2one(comodel_name='res.company',string="Company",required=True,readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id, readonly=True)
    amount = fields.Monetary(string="Amount",currency_field='currency_id',required=True)


    @api.onchange('plaza_id')
    def onchange_plazza_value(self):
        for rec in self:
            rec.update({'state_id': rec.plaza_id.state_id.id or False})


class InheritHrContract(models.Model):
    _inherit = "hr.contract"

    budget_amount = fields.Monetary("Employee Budget",currency_field='currency_id')

