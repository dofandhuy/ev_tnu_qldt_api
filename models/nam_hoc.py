from odoo import models, fields

class Years(models.Model):
    _inherit = 'hp.nam.hoc'
    qldt_id = fields.Char(string='ID Năm học QLDT', index=True)

