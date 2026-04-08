# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import xmltodict
import base64
import zeep

class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    travel_request_id = fields.Many2one('travel.request',string="Travel Request")


class HrExpense(models.Model):
    _inherit = "hr.expense"

    travel_id = fields.Many2one('travel.request', string='Travel Request',
                                help="Link to the travel request associated with this expense",
                                domain=[('state', 'in', ['approved','submitted','returned'])])
    travel_expence_id = fields.Many2one('travel.request')
    card_number = fields.Char(string='Card Number', 
                              index=True, 
                              help="The Card Number associated with this expense"
                              )
    vat = fields.Char(string='Tax ID', 
                      index=True, 
                      help="The Tax Identification Number for this expense"
                      ) 
    receipt_authorization = fields.Char(string='Recibo #',
                                       index=True, 
                                       help="Numero de recibo bancario para este gasto"
                                       )
    cash_withdrawal = fields.Boolean(string='Retiro de Efectivo',
                                     compute='_compute_cash_withdrawal',
                                     help="Indica si este gasto es un retiro de efectivo")
    cfdi_line_ids = fields.One2many('hr.expense.cfdi', 'expense_id', string='Detalles CFDI')
    # Campo computado para ver el UUID principal en la vista de lista si se desea
    l10n_mx_edi_uuid = fields.Char(string='UUID Principal', compute='_compute_main_uuid', store=True)


    @api.depends('description')
    def _compute_cash_withdrawal(self):
        for rec in self:
            if rec.description.lower().find('retiro') != -1:
                rec.cash_withdrawal = True
            else:
                rec.cash_withdrawal = False
    
    @api.onchange('travel_id')
    def onchange_travel_id(self):
        for record in self:
            if record.travel_id:
                record.employee_id = record.travel_id.employee_id.id

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
            travel_id = self.env['travel.request'].browse(self._context.get('default_travel_id'))
            result.update({'travel_expence_id':travel_id.id})
        return result


    @api.depends('cfdi_line_ids')
    def _compute_main_uuid(self):
        for rec in self:
            rec.l10n_mx_edi_uuid = rec.cfdi_line_ids[0].uuid if rec.cfdi_line_ids else False

    def attach_document(self, **kwargs):
        res = super(HrExpense, self).attach_document(**kwargs)
        attachment_ids = kwargs.get('attachment_ids', []) or self.env.context.get('default_attachment_ids', [])
        
        if attachment_ids:
            attachments = self.env['ir.attachment'].browse(attachment_ids)
            for attach in attachments:
                if attach.mimetype in ['application/xml', 'text/xml'] or attach.name.lower().endswith('.xml'):
                    self._process_cfdi_xml(attach)
        return res
    
    def _validate_with_sat(self, rfc_emisor, rfc_receptor, total, uuid):
        """ Consulta el webservice del SAT para verificar el estatus del CFDI """
        url = 'https://sat.gob.mx'
        try:
            client = zeep.Client(wsdl=url)
            # El formato de la consulta requiere escapar caracteres especiales
            # re=RFC Emisor, rr=RFC Receptor, tt=Total, id=UUID
            consulta = f"?re={rfc_emisor}&rr={rfc_receptor}&tt={total}&id={uuid}"
            res = client.service.Consulta(consulta)
            
            if res and res.Estado == 'Cancelado':
                raise ValidationError(_("El CFDI con UUID %s está CANCELADO en el SAT.") % uuid)
            if res and res.Estado == 'No Encontrado':
                raise ValidationError(_("El CFDI con UUID %s NO se encuentra en los registros del SAT.") % uuid)
            
            return True
        except Exception as e:
            # Si el servicio del SAT falla, permitimos continuar pero logueamos el error
            # o podrías bloquearlo según tu política de empresa.
            return True
        
    def _process_cfdi_xml(self, attach):
 
        try:
            xml_content = base64.b64decode(attach.datas)
            data = xmltodict.parse(xml_content, process_namespaces=False)
            comp = data.get('cfdi:Comprobante', data.get('Comprobante', {}))
            
            # Datos para validación
            metodopago = comp.get('@MetodoPago')
            formapago = comp.get('@FormaPago')
            serie = comp.get('@Serie', False)
            folio = comp.get('@Folio', False)
            emisor = comp.get('cfdi:Emisor', {}).get('@Rfc')
            receptor = comp.get('cfdi:Receptor', {}).get('@Rfc')
            total = comp.get('@Total')
            complemento = comp.get('cfdi:Complemento', comp.get('Complemento', {}))
            timbre = complemento.get('tfd:TimbreFiscalDigital', {})
            uuid = timbre.get('@UUID')

            # 1. VALIDACIÓN ANTE EL SAT
            if uuid and emisor and receptor and total:
                self._validate_with_sat(emisor, receptor, total, uuid)

            # 3. VALIDACIÓN DE RFC RECEPTOR - Solo para gastos de viaje, el receptor debe ser la empresa
            if self.travel_id and receptor != self.employee_id.czp_company_id.vat:
                raise ValidationError(_("El RFC Receptor del CFDI debe coincidir con el RFC de la empresa para gastos de viaje."))

            #VALIDCION QUE SI EL GASTO TIENE RFC EMISOR EL COMPROBANTE COINCIDA CON EL RFC DEL PROVEEDOR
            # Si el gasto tiene un RFC Emisor, entonces el CFDI debe coincidir con el RFC del proveedor seleccionado en el gasto            
            if self.vat and emisor and emisor != self.vat:
                raise ValidationError(_("El RFC Emisor del CFDI (%s) no coincide con el RFC del gasto (%s).") % (emisor, self.vat))
            #SI FUE UN RETIRO, LA FORMA DE PAGO DEBE SER EFECTIVO
            if self.cash_withdrawal and formapago != '01':
                raise ValidationError(_("Para gastos de retiro de efectivo, la Forma de Pago del CFDI debe ser '01' (Efectivo)."))
            
            if not self.cash_withdrawal and formapago not in ['04', '28', '29']:
                raise ValidationError(_("Para gastos que no son retiros de efectivo, la Forma de Pago del CFDI debe ser '04' (Tarjeta de Débito), '28' (Tarjeta de Crédito) o '29' (Tarjeta de Servicios)."))
            # 2. PROCESAMIENTO ESTÁNDAR (Lo que ya teníamos)

            self.env['hr.expense.cfdi'].create({
                'expense_id': self.id,
                'name': comp.get('cfdi:Emisor', {}).get('@Nombre'),
                'rfc_emisor': emisor,
                'uuid': uuid,
                'total': float(total),
                'fecha': comp.get('@Fecha', '')[:10],
                'serie': serie,
                'folio': folio,
                'metodopago': metodopago,
                'formapago': formapago,
                'xml_file': attach.datas,
                'xml_filename': attach.name,
            })

            # Recalcular totales e impuestos (Lógica previa)
            self._update_expense_totals(comp)

        except ValidationError as e:
            raise e
        except Exception as e:
            raise UserError(_("Error al procesar el CFDI XML: %s") % str(e))
            pass

    def _update_expense_totals(self, comp):
        """ Método auxiliar para actualizar montos e impuestos """
        total_acumulado = sum(self.cfdi_line_ids.mapped('total'))
        # Extraer impuestos del XML actual para agregarlos al gasto
        impuestos_node = comp.get('cfdi:Impuestos', {})
        traslados_node = impuestos_node.get('cfdi:Traslados', {}) or {}
        traslados = traslados_node.get('cfdi:Traslado', [])
        if isinstance(traslados, dict): traslados = [traslados]

        current_tax_ids = self.tax_ids.ids
        for t in traslados:
            tasa = round(float(t.get('@TasaOCuota', 0.0)) * 100, 2)
            tax = self.env['account.tax'].search([
                ('amount', '=', tasa),
                ('type_tax_use', '=', 'purchase'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if tax and tax.id not in current_tax_ids:
                current_tax_ids.append(tax.id)
        self.write(
            {'total_amount': total_acumulado, 
             'tax_ids': [(6, 0, current_tax_ids)]
            })

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


class HrExpenseCFDI(models.Model):
    _name = 'hr.expense.cfdi'
    _description = 'Detalle Técnico CFDI'

    expense_id = fields.Many2one('hr.expense', ondelete='cascade')
    name = fields.Char('Emisor')
    rfc_emisor = fields.Char('RFC Emisor')
    uuid = fields.Char('UUID', index=True)
    total = fields.Float('Total XML')
    fecha = fields.Date('Fecha Emisión')
    serie = fields.Char('Serie', help="Serie del CFDI, si está disponible")
    folio = fields.Char('Folio', index=True, help="Folio del CFDI, si está disponible")
    metodopago = fields.Char('Método de Pago', help="Método de pago del CFDI")
    formapago = fields.Char('Forma de Pago', help="Forma de pago del CFDI")


    
    # NUEVOS CAMPOS DE ESTATUS SAT
    l10n_mx_edi_sat_status = fields.Selection([
        ('none', 'No Validado'),
        ('vigente', 'Vigente'),
        ('cancelado', 'Cancelado'),
        ('not_found', 'No Encontrado'),
    ], string='Estatus SAT', default='none')
    l10n_mx_edi_sat_last_check = fields.Datetime('Última Validación')
    
    xml_file = fields.Binary('Archivo')
    xml_filename = fields.Char('Nombre')

    _sql_constraints = [
        ('unique_uuid', 'unique(uuid)', '¡Este UUID ya existe en otro gasto!')
    ]
