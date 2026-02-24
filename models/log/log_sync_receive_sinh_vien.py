# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json
import logging

from datetime import datetime
from odoo.exceptions import ValidationError

class LogSyncReceiveStudent(models.Model):
    _name = 'log.sync.receive.student'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ sinh viên'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveStudent, self).create(vals_list)
        for log in res:
            log.code = 'LSRS' + str(log.id)
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
            ma_sv = data.get('ma_sinh_vien')

            if not ma_sv: return '096'

            PartnerObj = self.env['res.partner'].sudo()
            student = PartnerObj.search([('ma_sinh_vien', '=', ma_sv)], limit=1)

            if action == 'delete':
                if student:
                    student.write({'active': False})
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000'

            # Helper tìm ID từ mã
            def get_id(model, code):
                return self.env[model].sudo().search([('code', '=', code)], limit=1).id if code else False

            ma_dv_raw = str(data.get('ma_don_vi') or '').strip()

            # Tìm bản ghi đơn vị kinh doanh trong hệ thống
            # Giả sử model đơn vị là 'res.business.unit' và trường mã là 'code'
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)

                return '096'

            vals = {
                'ma_sinh_vien': ma_sv,
                'name': data.get('name'),
                'ngay_sinh': data.get('ngay_sinh'),
                'gioi_tinh': data.get('gioi_tinh'),
                'la_sinh_vien': True,
                'ma_don_vi': str(data.get('ma_don_vi') or '').strip(),
                'business_unit_id': business_unit.id,
            }

            if not student:
                PartnerObj.create(vals)
            else:
                student.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'
        except Exception:
            self.write({'state': 'fail'})
            return '096'
