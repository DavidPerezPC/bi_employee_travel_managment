import base64
import io
import csv
import locale
from odoo import models, fields
from datetime import datetime

MONTH_DATE = {
    'Ene': '01',
    'Feb': '02',
    'Mar': '03',
    'Abr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Ago': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dic': '12'
}

class BankAuthorizationWizard(models.TransientModel):
    _name = 'bank.expenses.statement.wizard'
    _description = 'Bank Expenses Statement Wizard'
    
    file_upload = fields.Binary(string='Upload Expenses Statement Document', required=True)
    file_name = fields.Char(string='File Name')

    def action_bank_expenses_statement(self):
        travels = self.env['travel.request'].search([('state', 'in', ['approved','submitted','returned'])])
        if self.file_upload:
            # Decode the base64 data to bytes
            binary_data = base64.b64decode(self.file_upload)
            
            # Use io.StringIO to treat binary data as a file for reading
            # Decode bytes to a string (assuming utf-8 encoding)
            data_file = io.StringIO(binary_data.decode("utf-8"))
            data_file.seek(0)
            
            HrExpense = self.env['hr.expense']
            # Example: Reading a CSV file
            csv_reader = csv.reader(data_file, delimiter=';')
            file_content = []
            for row in csv_reader:
                row_ = row[0].split(',')
                if not row_[0].isdigit():
                    continue
                
                if row_[5] == '':
                    amount = -float(row_[6])
                else:
                    amount = float(row_[5])
                date_str = row_[1][0:3] + MONTH_DATE.get(row_[1][3:6], '01') + row_[1][6:11]
                # try:
                #     locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
                # except locale.Error:
                #     locale.setlocale(locale.LC_ALL, 'es_ES')  
                date = datetime.strptime(date_str, '%d-%m-%Y').date()
                notes = row_[4].split(' | ')
                card = None
                rfc = None
                receipt_number = row_[3]
                for note in notes:
                    if not card:    
                        card = self._get_card_number_rfc(note)
                        if not card:
                            card = self._get_card_number_rfc(note, keyword='mxn en ')
                    if not rfc:
                        rfc = self._get_card_number_rfc(note, keyword='RFC ', length=13)

                    if not receipt_number:
                        receipt_number = self._get_card_number_rfc(note, keyword='Recibo # ', length=13)
                        if not receipt_number:
                            receipt_number = self._get_card_number_rfc(note, keyword='Autorización: ', length=13)

                if HrExpense.search([('card_number', '=', card), 
                                  ('receipt_authorization', '=', receipt_number),
                                  ('total_amount', '=', amount)
                                ]):
                    continue

                travel = travels.filtered(lambda t: t.cheque_number == card \
                                          and date >= t.req_dispersal_date.date()  \
                                          and date <= t.req_return_date.date()
                                          )
                if len(travel) > 1:
                    # Handle case where multiple travels match
                    travel = travel[0]  # or some other logic

                self.env['hr.expense'].create({
                    'name': notes[0],
                    'total_amount_currency': amount,
                    'payment_mode': 'company_account',
                    'date': date,
                    'product_id': 19,  # Assuming product with ID 19 exists
                    'travel_id': travel.id if travel else False,
                    'employee_id': travel.employee_id.id if travel else 1,
                    'card_number': card if card else False,
                    'vat': rfc.replace(' ', '') if rfc else False,
                    'description': ','.join(notes),
                    'state': 'reported',
                    'receipt_authorization': receipt_number if receipt_number else False,
                })
                # daparture_date = row[10]
                # travel = travels.filtered(lambda t: t.cheque_number == cheque_number \
                #                           and t.req_dispersal_date.strftime('%d%m%Y') == daparture_date)
                # if travel and row[16] == 'Aplicado' and row[19] == 'CORRECTO':
                #     if len(travel) > 1:
                #         # Handle case where multiple travels match
                #         travel = travel[0]  # or some other logic   
                #     travel.write({'bank_authorization': row[13],
                #                   'state': 'approved'  
                #                   })
                #file_content.append(row)
                #print(row)
            
            # Now 'file_content' holds your data (e.g., a list of lists)
            # You can process this data as needed
            #print(file_content)
        #for travel in travels:
        #    acc_number = 
        #    travel.action_generate_transfer()

        return {
            'type': 'ir.actions.act_window_close',
        }
    
    def _get_card_number_rfc(self, note, keyword='Tarjeta ', length=16):
        card_position = note.find(keyword)
        if card_position != -1:
            card = note[card_position + len(keyword):card_position + len(keyword) + length].strip()
            if (length == 16 and card.isdigit()) or (length == 13 and card):
                return card
        return None