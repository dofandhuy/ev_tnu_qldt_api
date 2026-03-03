# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ConfigAPI(models.Model):
    _inherit = 'config.api'

    code = fields.Selection(selection_add=[
        ("/api/v1/qldt/years", "/api/v1/qldt/years"),
        ("/api/v1/qldt/semester", "/api/v1/qldt/semester"),
        ("/api/v1/qldt/login", "/api/v1/qldt/login"),
        ("/api/v1/qldt/student", "/api/v1/qldt/student"),
        ("/api/v1/qldt/product", "/api/v1/qldt/product"),
        ("/api/v1/qldt/cap_bac", "/api/v1/qldt/cap_bac"),
        ("/api/v1/qldt/hinh_thuc_dt", "/api/v1/qldt/hinh_thuc_dt"),
        ("/api/v1/qldt/chuong_trinh_dt", "/api/v1/qldt/chuong_trinh_dt"),
        ("/api/v1/qldt/nien_khoa", "/api/v1/qldt/nien_khoa"),
        ("/api/v1/qldt/nganh_hoc", "/api/v1/qldt/nganh_hoc"),
        ("/api/v1/qldt/student_payment", "/api/v1/qldt/student_payment"),
        ("/api/v1/qldt/tuition_collection", "/api/v1/qldt/tuition_collection"),
    ])