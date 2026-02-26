from odoo import models, fields

class Product(models.Model):
    _inherit = 'product.template' # Giả sử khoản thu là product.template
    qldt_id_product = fields.Char(string='ID Khoản thu QLDT', index=True)

    _sql_constraints = [
        ('unique_qldt_id_product', 'unique(qldt_id_product)', 'ID QLDT này đã tồn tại trên một khoản thu khác!')
    ]