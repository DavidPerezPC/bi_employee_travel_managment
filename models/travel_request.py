# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta,date
import base64
import csv
from io import StringIO

class travel_expence(models.Model):
    _name = "travel.expence"
    _description = "Travel Expence"

    product_id = fields.Many2one('product.product', string="Product", domain=[('can_be_expensed', '=', True)],
                                 required=True)
    unit_price = fields.Float(string="Unit Price", required=True)
    product_qty = fields.Float(string="Quantity", required=True)
    name = fields.Char(string="Expense Note")
    currency_id = fields.Many2one('res.currency', string="Currency")


class My_travel_request(models.Model):
    _name = "travel.request"
    _description = "My Travel Request"

    name = fields.Char(string="Name", readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee", 
        required=True,
        domain="[('active', '=', True), ('employee_status', '=', 'active')]",
        help="Employee requesting the travel",
        #default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    )

    card_employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee Card", 
        store=True, 
        help="Employee card number to cover travel's expenses",
        domain="[('active', '=', True), ('employee_status', '=', 'active')]",
        #default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    )

    czp_company_id = fields.Many2one('czp.companies',
                                     related='employee_id.czp_company_id', 
                                     string="Company", store=True)
    department_manager_id = fields.Many2one('hr.employee', string="Manager")
    czp_zone_id = fields.Many2one('czp.zone', string="Zone", required=True)
    #plaza_id = fields.Many2one('czp.plazas', string="Plaza", required=True)
    plaza_ids = fields.Many2many('czp.plazas', string="Plazas", required=True)
    plaza_domain = fields.Char(string="Plaza Domain", compute="_compute_plaza_domain")
    department_id = fields.Many2one('hr.department', string="Department")
    job_id = fields.Many2one('hr.job', string="Job Position")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id, readonly=True)
    request_by = fields.Many2one('hr.employee', string="Requested By")
    confirm_by = fields.Many2one('res.users', string="Confirmed By")
    default_approver = fields.Many2one('res.users', string="Expense Approver")
    default_approver_domain = fields.Char(string="Default Approver Domain", compute="_compute_approver_domain")
    approve_by = fields.Many2one('res.users', string="Approved By")
    reject_by = fields.Many2one('res.users',string="Rejected By")
    req_date = fields.Date(string="Request Date",readonly=True)
    confirm_date = fields.Date(string="Confirm Date",readonly=True)
    approve_date = fields.Date(string="Approved Date",readonly=True)
    expence_sheet_id = fields.Many2one('hr.expense.sheet', string="Created Expense Sheet", readonly=True)
    #travel_purpose = fields.Char(string="Travel Purpose", required=True)
    trip_purpose_id = fields.Many2one('czp.trip.purpose', string="Trip Purpose", required=True)
    project_id = fields.Many2one('project.task', string="Project" )
    account_analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    from_city = fields.Char('City', required=True)
    from_state_id = fields.Many2one('res.country.state', string="State",required=True)
    from_country_id = fields.Many2one('res.country', string="Country", required=True)
    to_street = fields.Char('Street')
    to_street_2 = fields.Char('Street2')
    to_city = fields.Char('city')
    to_state_id = fields.Many2one('res.country.state', string="state")
    to_country_id = fields.Many2one('res.country', string="country")
    to_zip_code = fields.Char('Zip')
    req_departure_date = fields.Datetime(string="Request Departure Date", required=True)
    req_return_date = fields.Datetime(string="Request Return Date", required=True)
    req_dispersal_date  = fields.Datetime(string="Request Dispersal Date", required=True)
    days = fields.Char('Days', compute="_compute_days")
    req_travel_mode_id = fields.Many2one('travel.mode', string="Request Mode Of Travel")
    return_mode_id = fields.Many2one('travel.mode', string="Return Mode of Travel")
    phone_no = fields.Char('Contact Number', required=True)
    email = fields.Char('Email', required=True)
    available_departure_date = fields.Datetime(string="Available Departure Date")
    available_return_date = fields.Datetime(string="Available Return Date")
    departure_mode_travel_id = fields.Many2one('travel.mode', string="Departure Mode Of Travel")
    return_mode_travel_id = fields.Many2one('travel.mode', string="Return Mode Of Travel")
    visa_agent_id = fields.Many2one('res.partner', string="Visa Agent")
    ticket_booking_agent_id = fields.Many2one('res.partner', string="Ticket Booking Agent")
    bank_id = fields.Many2one('res.bank', 
                              string="Bank Name",
                              help="Bank associated with the cheque number", 
                              required=True
                              )
    cheque_number = fields.Char(string="Cheque Number", 
                                help="Cheque number associated with the bank",
                                required=True
                                )
    advance_payment_ids = fields.One2many('hr.expense', 'travel_id', string="Advance Expenses")
    expense_ids = fields.One2many('hr.expense', 'travel_expence_id', string="Expenses")
    travel_expense_ids = fields.One2many('travel.expense.line', 'travel_exp_id', string="Employee Travel Expense")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'),('manager_approval','Manager Approval'), ('treasury_department','Treasury Department'), ('approved', 'Approved'), ('rejected', 'Rejected'),
         ('returned', 'Returned'), ('submitted', 'Expenses Submitted')], default="draft", string="States")
    original_budget = fields.Monetary(string="Original Budget",compute="_check_original_budget")
    modify_budget = fields.Monetary(string="Modify Budget")
    within_budget = fields.Boolean(string="Within Budget",compute="_check_original_budget")
    over_budget = fields.Boolean(string="Over Budget",compute="_check_original_budget")
    company_id = fields.Many2one(comodel_name='res.company',string="Company",required=True,readonly=True,default=lambda self: self.env.company)
    count_journal = fields.Integer('Count Invoice',compute="_count_pentaly")
    journal_id = fields.Many2one(comodel_name='account.journal',string="Expense Journal",domain=[('type', '=', 'purchase')], store=True,
        check_company=True)
    exp_account_ids = fields.Many2many('account.move',string="Journals")


    # @api.model
    # def _get_employee_bank(self):
    #     return self._get_bank_cheque_number('bank_id.id')
    #     # if not self.employee_id:
    #     #     self.employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    #     # if not self.card_employee_id and self.employee_id:
    #     #     self.card_employee_id = self.employee_id
    #     # return self.card_employee_id.bank_account_id.bank_id.id

    # @api.model
    # def _get_employee_cheque_number(self):
    #     return self._get_bank_cheque_number('acc_number')

    # def _get_bank_cheque_number(self, field_name):

    #     if not self.employee_id:
    #         emp_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #         if emp_id:
    #             self.employee_id = emp_id[0]

    #     if not self.card_employee_id and self.employee_id:
    #         self.card_employee_id = self.employee_id

    #     value_to_return = False
    #     cexpr = "self.card_employee_id.bank_account_id." + field_name 
    #     if self.card_employee_id:
    #         value_to_return = eval(cexpr)

    #     return value_to_return
     
    @api.depends('state','travel_expense_ids')
    def _count_pentaly(self):
        for rec in self:
            invoices  = self.env['account.move'].search([('travel_request_id','=',rec.id)])
            rec.count_journal = len(invoices)

    @api.depends('travel_expense_ids')
    def _check_original_budget(self):
        for rec in self:
            if rec.travel_expense_ids:
                total_amount = sum(rec.travel_expense_ids.mapped('travel_amount'))
                total_modify_amount = sum(rec.travel_expense_ids.mapped('final_amount'))
                total_min_amount = sum(rec.travel_expense_ids.mapped('travel_min_amount'))
                total_max_amount = sum(rec.travel_expense_ids.mapped('travel_max_amount'))
                rec.update({'original_budget': total_amount,
                            'modify_budget': total_modify_amount,
                            'within_budget': total_modify_amount  <= total_max_amount,
                            'over_budget':  total_modify_amount > total_max_amount
                            })
            else:
                rec.update({'original_budget': 0.0,'modify_budget': 0.0, 'within_budget': False, 'over_budget': False  })

    # @api.depends('original_budget','modify_budget')
    # def _check_budget_amount(self):
    #     for rec in self:
    #         contract_id = self.env['hr.contract'].search([('employee_id','=',rec.employee_id.id),('state','=','open')],limit=1)
    #         if contract_id:
    #             if contract_id.budget_amount <= rec.modify_budget:
    #                 rec.update({'within_budget': False,'over_budegt':True})
    #             else:
    #                 rec.update({'within_budget': True,'over_budegt':False})
    #         else:
    #             rec.update({'within_budget': False,'over_budegt':False})



    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_manager_id = self.employee_id.parent_id.id
        self.job_id = self.employee_id.job_id.id
        self.department_id = self.employee_id.department_id.id
        self.request_by = self.employee_id.id
        self.default_approver = self.employee_id.expense_manager_id.id
        if not self.card_employee_id:
            self.card_employee_id = self.employee_id.id
            if self.employee_id.bank_account_id:
                self.bank_id = self.employee_id.bank_account_id.bank_id.id
                self.cheque_number = self.employee_id.bank_account_id.acc_number
        return
    
    @api.onchange('card_employee_id')
    def onchange_card_employee(self):
        if self.card_employee_id:
            self.bank_id = self.card_employee_id.bank_account_id.bank_id.id
            self.cheque_number = self.card_employee_id.bank_account_id.acc_number
        return
    
    @api.onchange('req_departure_date')
    def _onchange_req_departure_date(self):
        if not self.req_dispersal_date:
            self.req_dispersal_date = self.req_departure_date
        return

    @api.depends('czp_zone_id')
    def _compute_plaza_domain(self):
        for rec in self:
            if rec.czp_zone_id:
                rec.plaza_domain = [('id', 'in', rec.czp_zone_id.plaza_ids.ids)]
            else:
                rec.plaza_domain = []

    @api.depends('department_id')
    def _compute_approver_domain(self):
        for rec in self:
            if rec.department_id:
                rec.default_approver_domain = [('id', 'in', rec.department_id.manager_ids.ids)]
            else:
                rec.default_approver_domain = []

    @api.constrains('req_departure_date', 'req_return_date', 'available_departure_date', 'available_return_date')
    def check_dates(self):
        if self.req_departure_date > self.req_return_date:
            raise UserError(_('Request Return Date should be after the Request Departure Date!!'))

        if self.available_departure_date > self.available_return_date:
            raise UserError(_('Available Departure Date should be before the Available Return Date!!'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            seq = self.env['ir.sequence'].next_by_code('travel.request') or '/'
            vals['name'] = seq
            vals['request_by'] = vals['employee_id']
            vals['req_date'] = fields.datetime.now()
            project_obj = self.env['project.task'].browse(vals['project_id'])
        return super(My_travel_request, self).create(vals_list)

    def write(self, vals):
        if 'project_id' in vals:
            project_obj = self.env['project.task'].sudo().browse(vals['project_id'])
            reg = self.env['account.analytic.account'].sudo().search([('name', '=', project_obj.name)], limit=1)
            if reg:
                vals['account_analytic_id'] = reg.id
            else:
                if project_obj.name:
                    value = project_obj.name
                    analytic = self.env['account.analytic.account'].create({
                        'name': project_obj.name,
                    })
                    vals['account_analytic_id'] = analytic.id
        return super(My_travel_request, self).write(vals)

    def action_expence_sheet(self):
        return {
            'name': 'Expense',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_travel_id':self.id,
                'default_test':True,
                
            },
            'res_model': 'hr.expense',
            'domain': [('id', 'in', self.expense_ids.ids)],
        }

    def action_confirm(self):
        self.write({'state': 'confirmed', 'confirm_date': fields.datetime.now(),
                    'confirm_by': self.env.user.id})
        return

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'treasury_department'})
            template_id = self.env['ir.model.data']._xmlid_lookup('bi_employee_travel_managment.approved_travel_expense_request_email_template')[1]
            email_template_obj = self.env['mail.template'].browse(template_id)
            if template_id:
                values = email_template_obj._generate_template([rec.id], ('subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'))[rec.id]
                values['email_from'] = self.env.user.email 
                values['email_to'] = rec.employee_id.work_email
                values['author_id'] = self.env.user.partner_id.id
                values['res_id'] = False
                values['body_html'] = '''
                    <div style="font-family: 'Lucica Grande', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: rgb(255, 255, 255); ">
                        <p>Dear ''' + rec.employee_id.name + ''',</p>
                        <br/>
                        <p>Your Travel Request Approved.</p>
                        <p>Approved By : ''' + self.env.user.name + ''' </p>
                        <br/>
                        <p>Thank you</p>
                    </div>
                '''
                # pdf = self.env.ref('bi_product_low_stock_notification.action_low_stock_report')._render([res.id])[0]
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.create(values)
                if msg_id:
                    msg_id.send()
        return

    def action_treasury_department(self):

        account_invoice_obj  = self.env['account.move']
        account_invoice_line_obj = self.env['account.move.line']
        for rec in self:
            if rec.within_budget:
                rec.write({'state': 'approved', 'approve_date': fields.datetime.now(),'approve_by': rec.env.user.id})
                account_move = account_invoice_obj.create({ 'move_type': 'in_invoice',
                                                            'partner_id': rec.employee_id.sudo().work_contact_id.id,
                                                            'invoice_date': date.today(),
                                                            'ref': "Employee Travel Request Of" + " " + rec.display_name,
                                                            'company_id': rec.company_id.id,
                                                            'journal_id': rec.journal_id.id,
                                                            'currency_id': rec.currency_id.id,
                                                            'travel_request_id': rec.id,
                                                            'state':'draft',
                                                         })
                for line in rec.travel_expense_ids:
                    account = line.product_id.product_tmpl_id._get_product_accounts()['expense']
                    if account:
                        account_id = account
                    if rec.within_budget:
                        move_line = account_invoice_line_obj.create({
                                                        'product_id':line.product_id.id,
                                                        'account_id': account_id.id or False,
                                                        'quantity':line.travel_qty,
                                                        'price_unit':line.travel_amount,
                                                        'tax_ids':False,
                                                        'move_id': account_move.id})
                    else:
                        move_line = account_invoice_line_obj.create({
                                                        'product_id':line.product_id.id,
                                                        'account_id': account_id.id or False,
                                                        'quantity':line.travel_qty,
                                                        'price_unit':line.final_amount,
                                                        'tax_ids':False,
                                                        'move_id': account_move.id})
                rec.update({'exp_account_ids': [(4, move_id) for move_id in account_move.ids]})
            else:
               rec.write({'state': 'manager_approval',}) 
        return


    def action_budget_approve(self):
        account_invoice_obj  = self.env['account.move']
        account_invoice_line_obj = self.env['account.move.line']
        for rec in self:
            if rec.over_budget:
                rec.write({'state': 'approved', 'approve_date': fields.datetime.now(),'approve_by': rec.env.user.id})
                account_move = account_invoice_obj.create({ 'move_type': 'in_invoice',
                                                            'partner_id': rec.employee_id.sudo().work_contact_id.id,
                                                            'invoice_date': date.today(),
                                                            'ref': "Employee Travel Request Of" + " " + rec.display_name,
                                                            'company_id': rec.company_id.id,
                                                            'journal_id': rec.journal_id.id,
                                                            'currency_id': rec.currency_id.id,
                                                            'travel_request_id': rec.id,
                                                            'state':'draft',
                                                         })
                for line in rec.travel_expense_ids:
                    account = line.product_id.product_tmpl_id._get_product_accounts()['expense']
                    if account:
                        account_id = account
                        move_line = account_invoice_line_obj.create({
                                                        'product_id':line.product_id.id,
                                                        'account_id': account_id.id or False,
                                                        'quantity':line.travel_qty,
                                                        'price_unit':line.final_amount,
                                                        'tax_ids':False,
                                                        'move_id': account_move.id})
                rec.update({'exp_account_ids': [(4, move_id) for move_id in account_move.ids]})
        return

    def action_open_invoice_journal(self):
        self.ensure_one()
        res_model = 'account.move'
        record_ids = self.exp_account_ids
        action = {'type': 'ir.actions.act_window', 'res_model': res_model}
        if len(record_ids) > 1:
            action.update({
                'name': ("Vendor Bills"),
                'view_mode': 'list,form',
                'domain': [('id', 'in', record_ids.ids)],
                'views': [(False, 'list'),(False, 'form')],
            })
        else:
            action.update({
                'name': record_ids.name,
                'view_mode': 'form',
                'res_id': record_ids.id,
                'views': [(False, 'form')],
            })
        return action


    def return_from_trip(self):
        for req in self:
            if any(req.exp_account_ids.filtered(lambda rec: rec.status_in_payment in ['in_payment','paid'])):
                raise UserError(_("Payment is already done for employee travel request"))
            else:
                req.write({'state': 'returned'})
                id_lst = []
                for line in self.advance_payment_ids:
                    id_lst.append(line.id)
                self.expense_ids = [(6, 0, id_lst)]
                vendor_bill_ids = req.exp_account_ids.filtered(lambda rec: rec.status_in_payment not in ['in_payment','paid'] and rec.state != 'cancel')
                for bill in vendor_bill_ids:
                    if bill.state == 'cancel':
                        bill.button_draft()
                        bill.button_cancel()
                    else:
                        bill.button_cancel()
        return

    def action_create_expence(self):
        id_lst = []
        for line in self.expense_ids:
            id_lst.append(line.id)
        res = self.env['hr.expense.sheet'].create(
            {'name': self.travel_purpose, 'employee_id': self._context.get('default_employee_id') or False, 'travel_expense': True,
             'expense_line_ids': [(6, 0, id_lst)]})
        self.expence_sheet_id = res.id
        self.write({'state': 'submitted'})
        return

    def action_draft(self):
        self.write({'state': 'draft'})
        return

    def action_reject(self):
        context = dict(self._context or {})
        data_obj = self.env['ir.model.data']
        view_id = data_obj._xmlid_to_res_id('bi_employee_travel_managment.travel_request_reject_form')

        return {
            'name': "Reason for Travel Request Rejection",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'travel.request.reject',
            'view_id': False,
            'context': context,
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        return

    @api.depends('req_departure_date', 'req_return_date')
    def _compute_days(self):
        for line in self:
            line.days = False
            if line.req_departure_date and line.req_return_date:
                diff = line.req_return_date - line.req_departure_date
                mini = diff.seconds // 60
                hour = mini // 60
                sec = (diff.seconds) - (mini * 60)
                miniute = mini - (hour * 60)
                time = str(diff.days) + ' Days, ' + ("%d:%02d.%02d" % (hour, miniute, sec))
                line.days = time
        return


    def action_get_date_from_wizard(self):
        selected_date=self.browse(self.env.context.get('active_ids',[])[0])[0].req_dispersal_date
        action = self.env['ir.actions.act_window']._for_xml_id('bi_employee_travel_managment.action_get_date_form_wizard')
        action['context'] = dict(self.env.context or {}, default_date=selected_date)
        return action
    
    def action_generate_transfer(self):

        #date_form = self._get_date_wizard()

        records = self.browse(self.env.context.get("active_ids", []))
        date_to_export = self.env.context.get('selected_date', fields.Date.today())
        date_to_export = datetime.strftime(date_to_export, '%Y%m%d')
        acc_number = ''
        row_count = 0
        total_amount = 0.0
        buffer = StringIO()
        writer = csv.writer(buffer, delimiter=";")

        writer.writerow([
            "Numero de Tarjeta",
            "Descripción",
            "signo",
            "Limite",
            "fecha inicio",
            "Fecha fin",
            "celular",
            "cambio de estatus"
        ])

        for r in records:
            if not acc_number:
                acc_number = r.czp_company_id.bank_account_number or ''
            row_count += 1
            total_amount += r.modify_budget or 0
            writer.writerow([
                r.cheque_number or "",
                r.trip_purpose_id.name if r.trip_purpose_id else "",
                "+",
                r.modify_budget or 0,
                str(r.req_dispersal_date)[:10].replace("-", "") if r.req_dispersal_date else "",
                str(r.req_return_date)[:10].replace("-", "") if r.req_return_date else "",
                r.phone_no or "",
                "",
            ])

        writer.writerow([
            acc_number,
            acc_number,
            date_to_export,
            row_count,
            int(total_amount),
        ])

        csv_content = buffer.getvalue().encode()
        buffer.close()

        b64 = base64.b64encode(csv_content).decode()

        attachment = self.env["ir.attachment"].create({
            "name": "travel_requests.csv",
            "datas": b64,
            "mimetype": "text/csv",
            "type": "binary",
        })

        # return {
        #     "type": "ir.actions.client",
        #     "tag": "download_and_close_wizard",
        #     "target": "new",
        #     "params": {
        #         "attachment_id": attachment.id,
        #         "filename": "travel_requests.csv",
        #     },
        # }

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            #"url": f"/bi_employee_travel_managment/download/{attachment.id}?filename={attachment.name}",
            "target": "self",
        }
    
# models/download_wizard.py
from odoo import models, fields, api

class DownloadAttachmentWizard(models.TransientModel):
    _name = "download.attachment.wizard"
    _description = "Download Attachment Wizard"

    name = fields.Char("Filename", required=True)
    attachment_id = fields.Many2one("ir.attachment", required=True)

    def action_download(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",   # IMPORTANT
            "url": f"/bi_employee_travel_managment/download/{attachment_id.id}?filename={self.name}",
        }

    
class my_travel_request(models.Model):
    _name = "travel.mode"
    _description = "My Travel Request"

    name = fields.Char('Travel Mode')


class TravelExpenseLine(models.Model):
    _name = "travel.expense.line"
    _description = "Travel Expense Line"

    travel_exp_id = fields.Many2one('travel.request',string="Travel Expence",readonly=True)
    product_id = fields.Many2one(comodel_name='product.product',string="Expense Product",domain=[('can_be_expensed', '=', True)],
        ondelete='restrict',required=True)
    travel_qty = fields.Float(string="Quantity",default=1)
    travel_amount = fields.Float(string="Amount Calculated", readonly=True, store=True)
    travel_min_amount = fields.Float(string="Minimum Amount", readonly=True, store=True)
    travel_max_amount = fields.Float(string="Maximum Amount", readonly=True, store=True)
    final_amount = fields.Float(string="Amount",required=True)
    duration_dependant = fields.Boolean(string="Duration Dependant", 
                                        related='product_id.duration_dependant', 
                                        store=True)

    @api.onchange('product_id', 'travel_qty')
    def onchange_product_id(self):
        for line in self:
            if not line.product_id:
                continue

            days = 0
            if line.travel_exp_id.days and line.travel_exp_id.days.split(' ')[0].isdigit():
                days = int(line.travel_exp_id.days.split(' ')[0])

            if line.travel_qty <= 1 and line.duration_dependant and days:
                line.travel_qty = days
                
            min_budget, max_budget = line.travel_exp_id.czp_zone_id.get_budget_amount(line.product_id.categ_id)
            if min_budget or max_budget:
                line.update({'travel_amount': min_budget * line.travel_qty,
                             'final_amount': min_budget * line.travel_qty,
                             'travel_min_amount': min_budget * line.travel_qty,
                             'travel_max_amount': max_budget * line.travel_qty})
            else:
                line.update({'travel_amount': line.product_id.list_price * line.travel_qty,
                             'final_amount': line.product_id.list_price * line.travel_qty,
                             'travel_min_amount': line.product_id.list_price * line.travel_qty,
                             'travel_max_amount': line.product_id.list_price * line.travel_qty})



