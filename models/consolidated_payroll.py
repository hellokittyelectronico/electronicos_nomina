from datetime import datetime
import json
import os
import re

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError


class NominaElectronicaConsolidatedSlip(models.Model):
    _inherit = 'consolidated.payroll.slip'

    nota_credito = fields.Selection(
        [('Eliminar', 'Eliminar'), ('Modificar', 'Modificar')],
        string='Tipo de nota',
        default='Eliminar',
    )
    CUNEPred = fields.Char("CUNE")
    NumeroPred = fields.Char("Numero Anterior")
    FechaGenPred = fields.Date("Fecha de Predecesor")
    causa = fields.Char("Causa")
    fecha_pago = fields.Date("Fecha de Pago")
    xml = fields.Text("XML")
    transaccionID = fields.Char("transaccionID")
    estado = fields.Selection(
        [
            ('no_generada', 'No_generada'),
            ('Generada_correctamente', 'Generada_correctamente'),
            ('Generada_con_errores', 'Con_errores'),
        ],
        string='Estado',
        default="no_generada",
    )
    prefijo = fields.Char("Prefijo")
    consecutivo = fields.Char("consecutivo")
    paisgeneracion = fields.Char("Pais de generacion")
    departamentoestado = fields.Char("Departamento")
    municipiociudad = fields.Char("Ciudad")
    Idioma = fields.Char("Idioma", default="es")
    impreso = fields.Boolean("Impreso")
    version = fields.Char("Version", default="")
    ambiente = fields.Selection(
        [('1', 'Produccion'), ('2', 'Pruebas')],
        string='Ambiente',
        default="1",
    )
    tipoXML = fields.Char("Tipo XML", default="102")
    Algoritmo = fields.Char("Algoritmo", default="CUNE-384")
    PeriodoNomina = fields.Selection(
        [
            ('1', 'Semanal'),
            ('2', 'Decenal'),
            ('3', 'Catorcenal'),
            ('4', 'Quincenal'),
            ('5', 'Mensual'),
        ],
        string='Periodo Nomina',
    )
    TipoMoneda = fields.Char('TipoMoneda', default="COP")
    Notas = fields.Char('Notas')
    RazonSocial = fields.Char('RazonSocial')
    PrimerApellido = fields.Char('PrimerApellido')
    SegundoApellido = fields.Char('SegundoApellido')
    PrimerNombre = fields.Char('PrimerNombre')
    OtrosNombres = fields.Char('OtrosNombres')
    NIT = fields.Char('NIT')
    DV = fields.Char('DV')
    PaisEmpleador = fields.Char('Pais')
    MunicipioCiudadEmpleador = fields.Char('MunicipioCiudad')
    DepartamentoEstadoEmpleador = fields.Char('DepartamentoEstado')
    DireccionEmpleador = fields.Char('Direccion')
    tipocontrato = fields.Selection(
        [
            ('1', 'Termino Fijo'),
            ('2', 'Termino Indefinido'),
            ('3', 'Obra o Labor'),
            ('4', 'Aprendizaje'),
            ('5', 'Practicas'),
        ],
        string='Tipo de contrato',
    )
    FechaGen = fields.Char('Fecha Generacion')
    HoraGen = fields.Char('Hora Generacion')
    id_plataforma = fields.Char('id_plataforma')
    password = fields.Char('password')
    cune = fields.Char('CUNE')
    error = fields.Char('Error')
    solucion = fields.Char('Solucion')
    credit_note = fields.Boolean(
        string='Credit Note',
        readonly=True,
        help="Indicates this payslip has a refund of another",
    )

    def on_change_employee(self):
        generales = self.env['base_electronicos.tabla'].search([('name', '=', 'Nómina electrónica')], limit=1)
        if not generales:
            raise UserError(_("No existe la configuración base de Nómina electrónica."))

        for record in self:
            valores = generales.generales_id.search([('company_id', '=', record.employee_id.company_id.id)], limit=1)
            if not valores:
                continue
            record.prefijo = valores.prefijo
            record.consecutivo = valores.consecutivo
            record.paisgeneracion = valores.paisgeneracion
            record.departamentoestado = valores.departamentoestado
            record.municipiociudad = valores.municipiociudad
            record.Idioma = valores.Idioma
            record.ambiente = valores.ambiente
            record.tipoXML = valores.tipoXML
            record.PeriodoNomina = valores.PeriodoNomina
            record.RazonSocial = valores.RazonSocial
            record.PrimerApellido = valores.PrimerApellido
            record.SegundoApellido = valores.SegundoApellido
            record.PrimerNombre = valores.PrimerNombre
            record.OtrosNombres = valores.OtrosNombres
            record.NIT = valores.NIT
            record.DV = valores.DV
            record.PaisEmpleador = valores.PaisEmpleador
            record.MunicipioCiudadEmpleador = valores.MunicipioCiudadEmpleador
            record.DepartamentoEstadoEmpleador = valores.DepartamentoEstadoEmpleador
            record.DireccionEmpleador = valores.DireccionEmpleador
            record.id_plataforma = valores.id_plataforma
            record.password = valores.password

    def _set_transmission_reference(self):
        self.ensure_one()
        number_value = (self.number or '').strip()
        if not number_value:
            self.prefijo = ''
            self.consecutivo = ''
            return

        match = re.match(r'^(.*?)(\d+)\D*$', number_value)
        if match:
            self.prefijo = match.group(1)
            self.consecutivo = match.group(2)
            return

        any_digits = re.search(r'(\d+)', number_value)
        if any_digits:
            start = any_digits.start(1)
            self.prefijo = number_value[:start]
            self.consecutivo = any_digits.group(1)
            return

        self.prefijo = number_value
        self.consecutivo = ''

    def action_cfdi_generate(self):
        urlini = "https://odoo15.navegasoft.com/admonclientes/status/"
        headers = {'content-type': 'application/json'}
        send = {
            "id_plataforma": self.id_plataforma,
            "transaccionID": self.transaccionID,
            "prefix": self.prefijo,
            "number": self.consecutivo,
            "ambiente": self.ambiente,
        }
        result = requests.post(urlini, headers=headers, data=json.dumps(send))
        if result.status_code != 200:
            raise UserError(str(result))

        resultado = json.loads(result.text)
        if "documentBase64" in resultado:
            return self.env['wk.wizard.message'].genrated_message('Documento impreso', 'listos')
        if "error" in resultado:
            final_error = resultado["error"]
            data_final = final_error.get("data", {}).get('message', str(final_error))
            return self.env['wk.wizard.message'].genrated_message(data_final, "Los datos no estan correctos", "https://navegasoft.com")

        final = resultado.get('result', {})
        if isinstance(final, str):
            final = json.loads(final)
        if final.get('code') == '200':
            import base64

            extension = ".pdf"
            image_64_encode = base64.b64decode(final['documentBase64'])
            i64 = base64.b64encode(image_64_encode)
            att_id = self.env['ir.attachment'].create({
                'name': f"{self.number}{extension}",
                'type': 'binary',
                'datas': i64,
                'res_model': 'consolidated.payroll.slip',
                'res_id': self.id,
            })
            if att_id:
                return self.env['wk.wizard.message'].genrated_message("Ve a attachment", "Factura impresa", "https://navegasoft.com")
        return self.env['wk.wizard.message'].genrated_message(
            final.get('mensaje', 'No fue posible imprimir el documento'),
            final.get('titulo', 'Error'),
            final.get('link', 'https://navegasoft.com'),
        )

    def genera_cufe(self):
        urlini = "https://odoo15.navegasoft.com/admonclientes/cune/"
        headers = {'content-type': 'application/json'}
        send = {
            "id_plataforma": self.id_plataforma,
            "transaccionID": self.transaccionID,
            "prefix": self.prefijo,
            "number": self.consecutivo,
            "ambiente": self.ambiente,
        }
        result = requests.post(urlini, headers=headers, data=json.dumps(send))
        if result.status_code != 200:
            raise UserError(str(result))

        resultado = json.loads(result.text)
        if "cune" in resultado:
            return self.env['wk.wizard.message'].genrated_message('CUNE: ' + resultado["cune"], 'listos')
        if "error" in resultado:
            final_error = resultado["error"]
            data_final = final_error.get("data", {}).get('message', str(final_error))
            return self.env['wk.wizard.message'].genrated_message(data_final, "Los datos no estan correctos", "https://navegasoft.com")

        final = resultado.get('result', {})
        if isinstance(final, str):
            final = json.loads(final)
        if 'CUNE' in final:
            self.write({"cune": final['CUNE']})
            return self.env['wk.wizard.message'].genrated_message(
                "Este es el CUNE " + final['CUNE'],
                "Se guardo dentro de los datos de la nomina",
                "https://navegasoft.com",
            )
        return self.env['wk.wizard.message'].genrated_message(
            'Estamos recibiendo un codigo de error Es necesario esperar para volver generar el cune',
            'Es necesario esperar para volver a imprimir el documento',
        )

    def envio_directo(self):
        now2 = datetime.now()
        current_time = now2.strftime("%H:%M:%S")
        self.on_change_employee()
        self._set_transmission_reference()
        self.FechaGen = str(now2.date())
        self.HoraGen = str(current_time)

        if not (self.consecutivo or '').isdigit():
            self.write({
                "estado": "Generada_con_errores",
                "error": f"Consecutivo invalido para nomina electronica: {self.consecutivo}",
                "solucion": "Revise el numero del consolidado y su secuencia.",
            })
            return self.env['wk.wizard.message'].genrated_message(
                f"El consecutivo enviado debe ser numerico y actualmente es: {self.consecutivo}",
                "Consecutivo invalido",
                "https://navegasoft.com",
            )

        urlini = "https://odoo15.navegasoft.com/admonclientes/objects/"
        valores = self.env['base_electronicos.tabla'].search([('name', '=', 'Nómina electrónica')], limit=1)
        valores_lineas = valores.mp_id
        send = {}
        for linea in valores_lineas:
            if linea.codigo:
                if linea.dias:
                    for lineacomprobante in self.worked_days_line_ids:
                        if linea.codigo == lineacomprobante.code and lineacomprobante.number_of_days > 0.0:
                            send[linea.name] = lineacomprobante.number_of_days
                elif linea.horas:
                    for lineacomprobante in self.worked_days_line_ids:
                        if linea.codigo == lineacomprobante.code and lineacomprobante.number_of_hours > 0.0:
                            send[linea.name] = lineacomprobante.number_of_hours
                elif linea.porcentaje:
                    reglas = self.env['hr.salary.rule'].search([('code', '=', linea.codigo)])
                    for regla in reglas:
                        if regla.porcentaje:
                            send[linea.name] = regla.porcentaje
                else:
                    for lineacomprobante in self.line_ids:
                        if linea.codigo == lineacomprobante.code and lineacomprobante.amount != 0.00:
                            send[linea.name] = lineacomprobante.amount
            elif linea.campo_tecnico:
                try:
                    if linea.campo_tecnico == "self.employee_id.address_home_id.state_id.code[0:2]":
                        if self.employee_id.address_home_id.state_id.code:
                            send[linea.name] = eval(linea.campo_tecnico)
                        else:
                            self.write({"estado": "Generada_con_errores", "error": "El campo esta vacio " + linea.campo_tecnico})
                            return self.env['wk.wizard.message'].genrated_message(
                                "El campo esta vacio " + linea.campo_tecnico,
                                "Error en el campo" + linea.name,
                                "https://navegasoft.com",
                            )
                    else:
                        value = eval(linea.campo_tecnico)
                        if value:
                            send[linea.name] = value
                except Exception:
                    self.write({"estado": "Generada_con_errores", "error": "El campo esta vacio " + linea.campo_tecnico})
                    return self.env['wk.wizard.message'].genrated_message(
                        "El campo esta vacio " + linea.campo_tecnico,
                        "Error en el campo" + linea.name,
                        "https://navegasoft.com",
                    )

        headers = {'content-type': 'application/json'}
        result = requests.post(urlini, headers=headers, data=json.dumps(send))
        if result.status_code != 200:
            self.write({"estado": "Generada_con_errores", "error": str(result), "solucion": "Volver a enviar el comprobante"})
            raise UserError(str(result))

        resultado = json.loads(result.text)
        if "result" in resultado:
            final = resultado["result"]
            if "error_d" in final:
                if "transactionID" in final:
                    self.write({"impreso": False, "transaccionID": final['transactionID'], "estado": "Generada_correctamente", "error": ""})
                    return
                self.write({"estado": "Generada_con_errores", "error": final['mensaje'], "solucion": final['link']})
                return self.env['wk.wizard.message'].genrated_message(final['mensaje'], final['titulo'], final['link'])

            final_error = json.loads(final)
            final_text = final_error['error']
            self.write({"estado": "Generada_con_errores", "error": final_text['mensaje'], "solucion": final_text['link']})
            return self.env['wk.wizard.message'].genrated_message(final_text['mensaje'], final_text['titulo'], final_text['link'])

        if "error" in resultado:
            final_error = resultado["error"]
            data_final = final_error.get("data", {}).get('message', str(final_error))
            self.write({"estado": "Generada_con_errores", "error": data_final, "solucion": "Proximamente video de solucion"})
            return self.env['wk.wizard.message'].genrated_message(data_final, "Los datos no estan correctos", "https://navegasoft.com")

    def generate_multiple_consolidated(self):
        for record in self._context.get('active_ids', []):
            payslip = self.env[self._context.get('active_model')].browse(record)
            payslip.envio_directo()


class MultipleConsolidatedGenerate(models.TransientModel):
    _name = "multiple.consolidated.payroll"
    _description = "generate Multiple Consolidated Payroll"

    def generate_multiple_consolidated(self):
        for record in self._context.get('active_ids', []):
            payslip = self.env[self._context.get('active_model')].browse(record)
            payslip.envio_directo()
