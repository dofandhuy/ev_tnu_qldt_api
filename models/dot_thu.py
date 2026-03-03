# -*- coding: utf-8 -*-
from odoo import models, fields

class HpQlDotThu(models.Model):
    _inherit = 'hp.ql.dot.thu'
    qldt_id = fields.Char(string='ID Đợt thu QLDT', index=True)

class HpDotThuSinhVienChiTiet(models.Model):
    _inherit = 'hp.dot.thu.sinh.vien.chi.tiet'
    qldt_id = fields.Char(string='ID Chi tiết đợt thu QLDT', index=True)
