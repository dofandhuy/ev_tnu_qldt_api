from odoo import models, fields
class Semester(models.Model):
    _inherit = 'hp.ky.hoc'
    qldt_id_semester = fields.Char(string='ID Kỳ học QLDT', index=True)

    _sql_constraints = [
        ('unique_qldt_id_semester', 'unique(qldt_id_semester)', 'ID QLDT này đã tồn tại trên một kỳ học khác!')
    ]