# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'HR Employee Travel Expense in Odoo ',
    'version': '18.0.0.1',
    'category': 'human resources',
    'summary': 'Apps for Hr Travel Expense Travel Expense reimbursement Employee Travel Expenses for Employee Travel Request for Employee Expenses Travel Expense voucher employee Travel expense Advance HR Travel Expense request HR Expenses of travel HR Expenses request',
    'description': """Employee Travel and Travel Expense Manage 
	
	Employee Travel Management and Expense Management
This module will allow you to manage travel of your employees and expense advance and submit expense claim.
Travel Expense reimbursement
employee Travel Expense reimbursement
employee Travel reimbursement in Odoo
employee reimbursement
Created Menus :
Employee Travel and Travel Expense

Travel/Travel Request
Travel/Travel Request/Employee Travel Request
Travel/Travel Request/Travel Requests To Approve
Defined Reports
HR Employee Travel Expenses
Employee Travel Expenses
Travel Expenses
Expenses of travel
employee Travel
Travel Expense voucher
travel voucher
Travel Request
Employee Travel Expenses
Travel Expenses
Employee Expenses

	
	""",
	
    'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_employee_travel_managment&version=18&edition=Community',
    "price": 30,
    "currency": 'EUR',
    'depends': ['base','hr','hr_expense','project','hr_contract','calzzapato_masterdata'],
    'data': ['security/ir.model.access.csv',
            'security/groups.xml',
            'data/employee_travel_sequencer_data.xml',
            'views/travel_request_views.xml',
            'views/budget_rule_views.xml',
            'views/hr_expense_views.xml',
            'views/czp_zone.xml',
            'wizard/reject_reason_views.xml',
            'report/employee_travel_report.xml',
            'report/report_views.xml',],
    'installable': True,
    'auto_install': False,
    'application': True,
    "license":'OPL-1',
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_employee_travel_managment&version=18&edition=Community',
    "images":["static/description/Banner.gif"],
}
