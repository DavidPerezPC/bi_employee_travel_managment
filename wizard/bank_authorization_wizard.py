import base64
import io
import csv
from odoo import models, fields
from datetime import datetime

class BankAuthorizationWizard(models.TransientModel):
    _name = 'bank.authorization.wizard'
    _description = 'Bank Authorization Wizard'
    
    file_upload = fields.Binary(string='Upload Authorization Document', required=True)
    file_name = fields.Char(string='File Name')

    def action_bank_authorization_transfer(self):
        travels = self.env['travel.request'].search([('state', 'in', ['treasury_department','approved'])])
        if self.file_upload:
            # Decode the base64 data to bytes
            binary_data = base64.b64decode(self.file_upload)
            
            # Use io.StringIO to treat binary data as a file for reading
            # Decode bytes to a string (assuming utf-8 encoding)
            data_file = io.StringIO(binary_data.decode("utf-8"))
            data_file.seek(0)
            
            # Example: Reading a CSV file
            csv_reader = csv.reader(data_file, delimiter=';')
            file_content = []
            for row in csv_reader:
                cheque_number = row[1]
                departure_date = row[10]
                if len(row) < 20 or row[16] != 'Aplicado' or row[19] != 'CORRECTO':
                    continue
                departure_date = datetime.strftime(datetime.strptime(departure_date, "%d%m%Y"),"%Y%m%d")
                #travel = travels.filtered(lambda t: t.cheque_number == cheque_number )
                travel = travels.filtered(lambda t: t.cheque_number == cheque_number and not t.bank_authorization \
                                          and t.req_dispersal_date.strftime('%Y%m%d') <= departure_date <= t.req_return_date.strftime('%Y%m%d')  )
                # if travel and row[16] == 'Aplicado' and row[19] == 'CORRECTO':
                if travel:
                    if len(travel) > 1:
                        # Handle case where multiple travels match
                        travel = travel[0]  # or some other logic   
                    travel.write({'bank_authorization': row[13],
                                  'state': 'approved'  
                                  })
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