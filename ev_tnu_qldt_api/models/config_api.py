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
        ("/api/v1/qldt/purchase", "/api/v1/qldt/purchase"),
    ])