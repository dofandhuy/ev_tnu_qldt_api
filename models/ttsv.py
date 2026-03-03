# -*- coding: utf-8 -*-
from odoo import models, fields

class HpThanhToanSinhVien(models.Model):
    _inherit = 'hp.thanh.toan.sinh.vien'
    qldt_id = fields.Char(string='ID Thanh toán QLDT', index=True)
