from odoo import models, fields
class Semester(models.Model):
    _inherit = 'hp.ky.hoc'
    qldt_id = fields.Char(string='ID Kỳ học QLDT', index=True)

