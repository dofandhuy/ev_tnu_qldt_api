# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ma_sinh_vien = fields.Char('Mã sinh viên', required=True, copy=False)
    name=fields.Char('Tên sinh viên', required=True)
    ngay_sinh = fields.Date('Ngày sinh', required=True)
    gioi_tinh = fields.Selection([
        ('nam', 'Nam'),
        ('nu', 'Nữ'),
        ('khac', 'Khác')
    ], string='Giới tính', required=True)
    la_sinh_vien = fields.Boolean('Là sinh viên', default=True, index=True, required=True)
    business_unit_id = fields.Many2one('res.business.unit', string='Đơn vị kinh doanh', required=True)