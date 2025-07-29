# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    travel_request_id = fields.Many2one('travel.request',string="Travel Request")


class HrExpense(models.Model):
    _inherit = "hr.expense"

    travel_id = fields.Many2one('travel.request')
    travel_expence_id = fields.Many2one('travel.request')

    @api.model
    def default_get(self, fields):
        result = super(HrExpense, self).default_get(fields)
        if self._context.get('adv_payment'):
            result.update({'payment_mode':'company_account'})
        if self._context.get('employee_id'):
            employee_id = self.env['hr.employee'].browse(self._context.get('employee_id'))
            result.update({'employee_id':employee_id.id})
        if self._context.get('default_employee_id'):
            employee_id = self.env['hr.employee'].browse(self._context.get('default_employee_id'))
            result.update({'employee_id':employee_id.id})
        if self._context.get('default_travel_id'):
            travel_id = self.env['hr.employee'].browse(self._context.get('default_travel_id'))
            result.update({'travel_expence_id':travel_id.id})
        return result


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    travel_expense = fields.Boolean('is a travel expense', default=False)

    @api.constrains('expense_line_ids', 'employee_id')
    def _check_employee(self):
        for sheet in self:
            if sheet.travel_expense == True:
                pass
            else:
                return super(HrExpenseSheet, self)._check_employee()
