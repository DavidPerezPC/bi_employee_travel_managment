# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta,date


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
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_manager_id = fields.Many2one('hr.employee', string="Manager")
    department_id = fields.Many2one('hr.department', string="Department")
    job_id = fields.Many2one('hr.job', string="Job Position")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id, readonly=True)
    request_by = fields.Many2one('hr.employee', string="Requested By")
    confirm_by = fields.Many2one('res.users', string="Confirmed By")
    approve_by = fields.Many2one('res.users', string="Approved By")
    reject_by = fields.Many2one('res.users',string="Rejected By")
    req_date = fields.Date(string="Request Date",readonly=True)
    confirm_date = fields.Date(string="Confirm Date",readonly=True)
    approve_date = fields.Date(string="Approved Date",readonly=True)
    expence_sheet_id = fields.Many2one('hr.expense.sheet', string="Created Expense Sheet", readonly=True)
    travel_purpose = fields.Char(string="Travel Purpose", required=True)
    project_id = fields.Many2one('project.task', string="Project", required=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    from_city = fields.Char('City')
    from_state_id = fields.Many2one('res.country.state', string="State")
    from_country_id = fields.Many2one('res.country', string="Country")
    to_street = fields.Char('Street')
    to_street_2 = fields.Char('Street2')
    to_city = fields.Char('city')
    to_state_id = fields.Many2one('res.country.state', string="state")
    to_country_id = fields.Many2one('res.country', string="country")
    to_zip_code = fields.Char('Zip')
    req_departure_date = fields.Datetime(string="Request Departure Date", required=True)
    req_return_date = fields.Datetime(string="Request Return Date", required=True)
    days = fields.Char('Days', compute="_compute_days")
    req_travel_mode_id = fields.Many2one('travel.mode', string="Request Mode Of Travel")
    return_mode_id = fields.Many2one('travel.mode', string="Return Mode of Travel")
    phone_no = fields.Char('Contact Number')
    email = fields.Char('Email')
    available_departure_date = fields.Datetime(string="Available Departure Date")
    available_return_date = fields.Datetime(string="Available Return Date")
    departure_mode_travel_id = fields.Many2one('travel.mode', string="Departure Mode Of Travel")
    return_mode_travel_id = fields.Many2one('travel.mode', string="Return Mode Of Travel")
    visa_agent_id = fields.Many2one('res.partner', string="Visa Agent")
    ticket_booking_agent_id = fields.Many2one('res.partner', string="Ticket Booking Agent")
    bank_id = fields.Many2one('res.bank', string="Bank Name")
    cheque_number = fields.Char(string="Cheque Number")
    advance_payment_ids = fields.One2many('hr.expense', 'travel_id', string="Advance Expenses")
    expense_ids = fields.One2many('hr.expense', 'travel_expence_id', string="Expenses")
    travel_expense_ids = fields.One2many('travel.expense.line', 'travel_exp_id', string="Employee Travel Expense")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'),('treasury_department','Treasury Department'),('manager_approval','Manager Approval'),('approved', 'Approved'), ('rejected', 'Rejected'),
         ('returned', 'Returned'), ('submitted', 'Expenses Submitted')], default="draft", string="States")
    original_budget = fields.Monetary(string="Original Budget",compute="_check_original_budget")
    modify_budget = fields.Monetary(string="Modify Budget")
    within_budget = fields.Boolean(string="Within Budget",compute="_check_budget_amount")
    over_budegt = fields.Boolean(string="Over Budget",compute="_check_budget_amount")
    company_id = fields.Many2one(comodel_name='res.company',string="Company",required=True,readonly=True,default=lambda self: self.env.company)
    count_journal = fields.Integer('Count Invoice',compute="_count_pentaly")
    journal_id = fields.Many2one(comodel_name='account.journal',string="Expense Journal",domain=[('type', '=', 'purchase')], store=True,
        check_company=True)
    exp_account_ids = fields.Many2many('account.move',string="Journals")

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
                rec.update({'original_budget': total_amount,'modify_budget':total_modify_amount})
            else:
                rec.update({'original_budget': 0.0,'modify_budget': 0.0})

    @api.depends('original_budget','modify_budget')
    def _check_budget_amount(self):
        for rec in self:
            contract_id = self.env['hr.contract'].search([('employee_id','=',rec.employee_id.id),('state','=','open')],limit=1)
            if contract_id:
                if contract_id.budget_amount <= rec.modify_budget:
                    rec.update({'within_budget': False,'over_budegt':True})
                else:
                    rec.update({'within_budget': True,'over_budegt':False})
            else:
                rec.update({'within_budget': False,'over_budegt':False})



    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_manager_id = self.employee_id.parent_id.id
        self.job_id = self.employee_id.job_id.id
        self.department_id = self.employee_id.department_id.id
        return

    @api.constrains('req_departure_date', 'req_return_date', 'available_departure_date', 'available_return_date')
    def check_dates(self):
        if self.req_departure_date > self.req_return_date:
            raise UserError(_('Request Return Date should be after the Request Departure Date!!'))

        if self.available_departure_date > self.available_return_date:
            raise UserError(_('Available Departure Date should be after the Available Return Date!!'))

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
            if rec.over_budegt:
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
    travel_amount = fields.Float(string="Amount Calculated",readonly=True,store=True)
    final_amount = fields.Float(string="Amount",required=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            budget_id = self.env['budget.rule'].search([('plaza_id','=',line.travel_exp_id.employee_id.plaza_id.id),('state_id','=',line.travel_exp_id.employee_id.plaza_id.state_id.id),('job_position_id','=',line.travel_exp_id.job_id.id),('product_id','=',line.product_id.id)],limit=1)
            if budget_id:
                line.update({'travel_amount': budget_id.amount})
            else:
                line.update({'travel_amount': line.product_id.list_price})



