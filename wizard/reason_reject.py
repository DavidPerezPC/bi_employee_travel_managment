# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from markupsafe import Markup


class TravelRequestReject(models.TransientModel):
    _name = 'travel.request.reject'
    _description = 'Travel Request Reject'

    reason = fields.Char(string="Reason")

    def action_tarvel_req_rejected(self):
        context = dict(self._context) or {}
        if context.get('active_id', False):
            travel_request  = self.env['travel.request'].browse(context.get('active_id'))
            travel_request.write({'state': 'rejected','reject_by': self.env.user.id})
            template_id = self.env['ir.model.data']._xmlid_lookup('bi_employee_travel_managment.return_travel_expense_request_email_template')[1]
            email_template_obj = self.env['mail.template'].browse(template_id)
            if template_id:
                values = email_template_obj._generate_template([travel_request.id], ('subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'))[travel_request.id]
                values['email_from'] = self.env.user.email 
                values['email_to'] = travel_request.employee_id.work_email
                values['author_id'] = self.env.user.partner_id.id
                values['res_id'] = False
                values['body_html'] = '''
                    <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: rgb(255, 255, 255); ">
                        <p>Dear ''' + travel_request.employee_id.name + ''',</p>
                        <br/>
                        <p>Your Travel Request Rejected Due To ''' + str(self.reason) + ''', </p>
                        <p>Rejected By : ''' + self.env.user.name + ''' </p>
                        <br/>
                        <p>Thank you</p>
                    </div>
                '''
                # pdf = self.env.ref('bi_product_low_stock_notification.action_low_stock_report')._render([res.id])[0]
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.create(values)
                if msg_id:
                    msg_id.send()
        return True