from odoo import models, fields, api

class GetDateFormWizard(models.TransientModel):
    _name = 'get.date.form.wizard'
    _description = 'Get Date Form Wizard'
    
    date = fields.Date(string='Date', required=True, default=lambda self: self.env.context.get('selected_date', fields.Date.today()))

    def action_confirm_bank_transfer(self):
        """Return the selected date"""
        self.ensure_one()
        self.env.context = dict(self.env.context or {}, selected_date=self.date)
        return self.env['travel.request'].action_generate_transfer()
        # return {
        #     'type': 'ir.actions.act_window_close',
        # }