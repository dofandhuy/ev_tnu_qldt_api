# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json
import logging

from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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

            ma_dv_raw = str(data.get('unit_code') or '').strip()
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)
                return '147'

            qldt_id = data.get('qldt_id_student')
            if not qldt_id:
                _logger.error("Dữ liệu thiếu qldt_id_student")
                return '145'


            PartnerObj = self.env['res.partner'].sudo()
            student = PartnerObj.search([('qldt_id_student', '=', qldt_id),
                                         ('business_unit_id','=',business_unit.id)], limit=1)

            if not student:
                if action in ['update', 'delete']:
                    _logger.error("Lỗi: Yêu cầu %s nhưng ID %s không tồn tại", action, qldt_id)
                    return '147'
            else:
                if action == 'create':
                    _logger.error("Lỗi: Yêu cầu create nhưng ID %s đã tồn tại", qldt_id)
                    return '147'


            if action == 'delete':
                if student:
                    student.write({'active': False})
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000'

            vals = {
                'qldt_id_student': qldt_id,
                'ma_sinh_vien': data.get('student_code'),
                'name': data.get('full_name'),
                'ngay_sinh': data.get('birthday'),
                'gioi_tinh': data.get('gender'),
                'ma_don_vi': str(data.get('unit_code') or '').strip(),
                'la_sinh_vien': True,
                'business_unit_id': business_unit.id ,
            }

            if not student:
                PartnerObj.create(vals)
            else:
                student.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'
        except Exception as e:
            _logger.error("Lỗi thực thi action_handle: %s", str(e))
            self.write({'state': 'fail',
                        'date_done': datetime.now(),
                       })
            return '096'
