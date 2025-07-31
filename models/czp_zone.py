from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class CZPZone(models.Model):
    _name = 'czp.zone'
    _description = 'Zone'

    name = fields.Char(string='Name', help='Name of the zone', required=True)
    budget_ids = fields.One2many('czp.zone.budget', 'czp_zone_id', 
                                 string='Budgets',
                                 help='Budgets associated with this zone')

    def copy(self, default=None):
        default = dict(default or {'name': self.name + ' (copy)'})
        new_budget_ids = []
        for budget in self.budget_ids:
            new_budget_ids.append((0, 0, {
                'categ_id': budget.categ_id.id,
                'min_amount': budget.min_amount,
                'max_amount': budget.max_amount,
            }))
        default['budget_ids'] = new_budget_ids
        return super(CZPZone, self).copy(default)

class CZPZoneBudget(models.Model):
    _name = 'czp.zone.budget'
    _description = 'Zone Budget'

    czp_zone_id = fields.Many2one('czp.zone', string='Zone', required=True, ondelete='cascade')
    categ_id = fields.Many2one('product.category', 
                               string='Category', 
                               help='Category of the budget', 
                               required=True)
    min_amount = fields.Float(string='Minimum Amount', help='Minimum budget amount within this zone')
    max_amount = fields.Float(string='Maximum Amount', help='Maximum budget amount within this zone')

    @api.constrains('min_amount', 'max_amount')
    def _check_min_max_amount(self):
        for record in self:
            if record.min_amount > record.max_amount:
                raise ValidationError(_("Minimum Amount cannot be greater than Maximum Amount."))
            if record.max_amount < record.min_amount:
                raise ValidationError(_("Maximum Amount cannot be smaller than Minimum Amount."))


class CZPZoneDepartmentJobBudget(models.Model):
    _name = 'czp.zone.department.job.budget'
    _description = 'Zone Department Job Budget'

    name = fields.Char(string='Budget Name', help='Name of the budget', required=True)
    hr_department_id = fields.Many2one('hr.department', 
                                       string='Department', 
                                       help='Department associated with the budget', 
                                       required=True)
    hr_job_id = fields.Many2one('hr.job', 
                                string='Job', 
                                help='Job associated with the budget', 
                                required=True)
    czp_zone_id = fields.Many2one('czp.zone', 
                                  string='Zone', 
                                  help='Zone associated with the budget', 
                                  required=True, ondelete='cascade')
    budget_ids = fields.One2many('czp.zone.department.job.budget.line', 'zone_department_job_budget_id', 
                                 string='Budgets',
                                 help='Budgets associated with this zone, department, and job combination')

    # def copy(self, default=None):
    #     default = dict(default or {'name': self.name + ' (copy)', 
    #                     'hr_department_id': self.hr_department_id.id,
    #                     'hr_job_id': self.hr_job_id.id,
    #                     'czp_zone_id': False}
    #                     )
    #     # new_budget_lines = []
    #     # for line in self.budget_ids:
    #     #     new_budget_lines.append((0, 0, {
    #     #         'categ_id': line.categ_id.id,
    #     #         'min_amount': line.min_amount,
    #     #         'max_amount': line.max_amount,
    #     #     }))
    #     # default['budget_ids'] = new_budget_lines
    #     return super(CZPZoneDepartmentJobBudget, self).copy(default)

    @api.constrains('czp_zone_id', 'hr_department_id', 'hr_job_id')
    def _check_unique_zone_department_job(self):
        for record in self:
            domain = [
                ('czp_zone_id', '=', record.czp_zone_id.id),
                ('hr_department_id', '=', record.hr_department_id.id),
                ('hr_job_id', '=', record.hr_job_id.id),
                ('id', '!=', record.id)
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _("The combination of Zone, Department, and Job must be unique.")
                )

    @api.onchange('czp_zone_id')
    def _onchange_czp_zone_id(self):
        if self.czp_zone_id and not self.budget_ids:
            zone_budgets = self.czp_zone_id.budget_ids
            new_lines = []
            for zone_budget in zone_budgets:
                new_lines.append((0, 0, {
                    'categ_id': zone_budget.categ_id.id,
                    'min_amount': zone_budget.min_amount,
                    'max_amount': zone_budget.max_amount,
                }))
            if new_lines:
                self.budget_ids = new_lines

class CZPZoneDepartmentJobBudgetLine(models.Model):
    _name = 'czp.zone.department.job.budget.line'
    _description = 'Zone Department Job Budget Line'

    zone_department_job_budget_id = fields.Many2one('czp.zone.department.job.budget', 
                                                    string='Zone Department Job Budget', 
                                                    required=True, 
                                                    ondelete='cascade')
    categ_id = fields.Many2one('product.category', 
                               string='Category', 
                               help='Category of the budget line for this zone, department, and job combination',
                               required=True)
    czp_zone_id = fields.Many2one('czp.zone', string='Zone', related='zone_department_job_budget_id.czp_zone_id', store=True)
    hr_department_id = fields.Many2one('hr.department', string='Department', related='zone_department_job_budget_id.hr_department_id', store=True)
    hr_job_id = fields.Many2one('hr.job', string='Job', related='zone_department_job_budget_id.hr_job_id', store=True)
    min_amount = fields.Float(string='Minimum Amount',help='Minimum budget amount for this category within the zone, department, and job combination')
    max_amount = fields.Float(string='Maximum Amount',help='Maximum budget amount for this category within the zone, department, and job combination')

    @api.constrains('min_amount', 'max_amount')
    def _check_min_max_amount(self):
        for record in self:
            if record.min_amount > record.max_amount:
                raise ValidationError(_("Minimum Amount cannot be greater than Maximum Amount."))
            if record.max_amount < record.min_amount:
                raise ValidationError(_("Maximum Amount cannot be smaller than Minimum Amount."))