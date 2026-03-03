from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    qldt_id = fields.Char(
        string='ID Sinh viên QLDT',
        index=True,
        copy=False,
        help="Mã định danh duy nhất từ hệ thống Quản lý đào tạo"
    )

