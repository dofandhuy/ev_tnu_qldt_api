from odoo import models, fields

class Years(models.Model):
    _inherit = 'hp.nam.hoc'
    qldt_id_years = fields.Char(string='ID Năm học QLDT', index=True)

    _sql_constraints = [
        ('unique_qldt_id_years', 'unique(qldt_id_years)', 'ID QLDT này đã tồn tại trên một năm học khác!')
    ]