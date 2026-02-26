from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    qldt_id_student = fields.Char(
        string='ID Sinh viên QLDT',
        index=True,
        copy=False,
        help="Mã định danh duy nhất từ hệ thống Quản lý đào tạo"
    )

    _sql_constraints = [
        ('unique_qldt_id_student', 'unique(qldt_id_student)', 'ID QLDT này đã tồn tại trên một sinh viên khác!')
    ]