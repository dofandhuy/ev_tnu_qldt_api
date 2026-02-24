# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LogSyncReceiveKhoanThu(models.Model):
    _name = 'log.sync.receive.revenue'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ Khoản thu'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveKhoanThu, self).create(vals_list)
        for log in res:
            log.code = 'LSRP' + str(log.id)
        return res

    def execute_data(self):
        self.ensure_one()
        self.state = 'queue'
        return self.sudo().with_delay(
            channel=self.job_queue.complete_name if self.job_queue else 'root',
            max_retries=3,
            priority=2
        ).action_handle()

    def action_handle(self):
        self.ensure_one()
        try:
            raw_data = json.loads(self.params or "{}")
            params = raw_data.get('params', raw_data)
            action = params.get('action')  # Lấy hành động: 'update' hay 'delete'
            data = params.get('data') or {}

            ma_dv_raw = str(data.get('ma_don_vi') or '').strip()
            if not ma_dv_raw:
                _logger.error("Dữ liệu thiếu ma_don_vi để xác định Company")
                return '096'

            # Tra cứu Business Unit dựa trên code gửi về
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)
                return '096'

            target_company_id = business_unit.company_id.id
            if not target_company_id:
                _logger.error("Business Unit %s chưa được gán Company", ma_dv_raw)
                return '096'

            sku = data.get('default_code')

            if not sku: return '096'

            ProdObj = self.env['product.template'].sudo()
            product = ProdObj.search([('default_code', '=', sku),
                                      ('company_id','=','target_company_id')],
                                     limit=1)

            if action == 'delete':
                if product:
                    product.write({'active': False})
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000'



            vals = {
                'default_code': sku,
                'name': data.get('name'),
                'company_id': target_company_id,
                'sale_ok': True,
                'purchase_ok': False,
            }

            if not product:
                ProdObj.create(vals)
            else:
                product.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'

        except Exception as e:
            _logger.error("Lỗi LogSyncProduct %s: %s", self.code, str(e))
            self.write({'state': 'fail', 'date_done': datetime.now()})
            return '096'
