from odoo import models, fields

class Product(models.Model):
    _inherit = 'product.template'
    qldt_id = fields.Char(string='ID Khoản thu QLDT', index=True)

