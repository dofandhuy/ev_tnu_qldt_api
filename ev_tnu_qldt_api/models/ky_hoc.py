from odoo import models, fields, api

# 1. KỲ HỌC
class KyHoc(models.Model):
    _name = 'semester'
    _description = 'Kỳ học'

    ma_ky_hoc = fields.Char('Mã kỳ học', required=True)
    ten_ky_hoc = fields.Char('Tên kỳ học', required=True)
    nam_hoc_id = fields.Many2one('years', string='Năm học', required=True)
    ten_nam_hoc = fields.Char('Tên năm học', related='nam_hoc_id.ten_nam_hoc', store=True)
    business_unit_id = fields.Many2one('res.business.unit', string='Đơn vị kinh doanh', required=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)
    phan_loai = fields.Selection([
        ('ky_chinh', 'kỳ chính'),
        ('ky_phu', 'kỳ phụ'),
], string='Phân loại', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(ma_ky_hoc)', 'Mã kỳ học đã tồn tại!'),
    ]