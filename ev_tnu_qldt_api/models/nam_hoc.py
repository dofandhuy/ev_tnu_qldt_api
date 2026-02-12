# -*- coding: utf-8 -*-
from odoo import models, fields, api

class NamHoc(models.Model):
    _name = 'years'
    _description = 'Năm học'
    _order = 'nam_bat_dau desc'

    ten_nam_hoc = fields.Char(string='Tên năm học', required=True)
    ma_nam_hoc = fields.Char(string='Mã năm học', required=True)
    nam_bat_dau = fields.Integer(string='Năm bắt đầu', required=True)
    nam_ket_thuc = fields.Integer(string='Năm kết thúc', required=True)
    active = fields.Boolean(string='Còn hoạt động', required=True   )
    company_id = fields.Many2one('res.company', string='Công ty', required=True)
    business_unit_id = fields.Many2one('res.business.unit', string='Đơn vị kinh doanh', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(ma_nam_hoc)', 'Mã năm học đã tồn tại!'),
    ]