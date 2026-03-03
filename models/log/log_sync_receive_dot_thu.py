# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class LogSyncReceiveDotThu(models.Model):
    _name = 'log.sync.receive.dot.thu'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ đợt thu'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveDotThu, self).create(vals_list)
        for log in res:
            log.code = 'LSRD' + str(log.id)
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
            action = params.get('action')
            data = params.get('data') or {}

            qldt_id = data.get('tuition_collection_id')
            if not qldt_id:
                _logger.error("Dữ liệu thiếu tuition_collection_id")
                return '145'

            ma_dv_raw = str(data.get('unit_code') or '').strip()
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)
                return '147'

            DotThuObj = self.env['hp.ql.dot.thu'].sudo()
            dot_thu = DotThuObj.search([('qldt_id', '=', qldt_id),
                                        ('business_unit_id', '=', business_unit.id)], limit=1)

            if not dot_thu:
                if action in ['update', 'delete']:
                    _logger.error("Lỗi: Yêu cầu %s nhưng ID %s không tồn tại", action, qldt_id)
                    return '147'
            else:
                if action == 'create':
                    # If already exists and action is create, we will append data
                    action = 'update_append'

            if action == 'delete':
                if dot_thu:
                    dot_thu.trang_thai = 'nhap'
                    dot_thu.unlink()
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000'

            year_qldt_id = data.get('year_id')
            year = self.env['hp.nam.hoc'].sudo().search([
                ('ma_nam_hoc', '=', year_qldt_id),
                # ('business_unit_id', '=', business_unit.id)
            ], limit=1)
            if not year:
                _logger.error("Không tìm thấy năm học với ID QLDT: %s", year_qldt_id)
                return '147'

            semester_qldt_id = data.get('semester_id')
            semester = self.env['hp.ky.hoc'].sudo().search([
                ('ma_ky_hoc', '=', semester_qldt_id),
                ('business_unit_id', '=', business_unit.id)
            ], limit=1)
            if not semester:
                _logger.error("Không tìm thấy kỳ học với ID QLDT: %s", semester_qldt_id)
                return '147'

            vals = {
                'ma_dot_thu': data.get('code'),
                'trang_thai': 'da_xac_nhan',
                'qldt_id': qldt_id,
                'business_unit_id': business_unit.id,
                'nam_hoc_id': year.id,
                'ky_hoc_id': semester.id,
                'mo_ta': data.get('description'),
                'loai_tong_hop': data.get('type', 'ca_2'),
            }

            # Handle children: dot_thu_sinh_vien_ids
            students_data = data.get('students') or []
            student_line_ids = []
            for student_item in students_data:
                student_code = student_item.get('student_code')
                student = self.env['res.partner'].sudo().search([
                    ('ma_sinh_vien', '=', student_code),
                    ('business_unit_id', '=', business_unit.id)
                ], limit=1)
                if not student:
                    _logger.error("Không tìm thấy sinh viên với mã: %s", student_code)
                    continue

                student_vals = {
                    'business_unit_id': business_unit.id,
                    'nam_hoc_id': year.id,
                    'ky_hoc_id': semester.id,
                    'sinh_vien_id': student.id,
                    'ghi_chu': student_item.get('note'),
                }

                # Handle nested children: dot_thu_sv_chi_tiet_ids
                details_data = student_item.get('details') or []
                detail_line_ids = []
                for detail_item in details_data:
                    product_qldt_id = detail_item.get('product_id')
                    product = self.env['product.template'].sudo().search([
                        ('default_code', '=', product_qldt_id)
                    ], limit=1)
                    if not product:
                        _logger.error("Không tìm thấy khoản thu với qldt_id: %s", product_qldt_id)
                        continue

                    detail_vals = {
                        'business_unit_id': business_unit.id,
                        'nam_hoc_id': year.id,
                        'ky_hoc_id': semester.id,
                        'sinh_vien_id': student.id,
                        'khoan_thu_id': product.id,
                        'so_tien_thu': detail_item.get('amount', 0.0),
                        'giam_tru': detail_item.get('discount', 0.0),
                        'mo_ta': detail_item.get('description'),
                        'qldt_id': detail_item.get('dtsv_chi_tiet_id'),
                    }
                    detail_line_ids.append((0, 0, detail_vals))

                if detail_line_ids:
                    student_vals['dot_thu_sv_chi_tiet_ids'] = detail_line_ids

                student_line_ids.append((0, 0, student_vals))

            if student_line_ids:
                vals['dot_thu_sinh_vien_ids'] = student_line_ids

            if not dot_thu:
                DotThuObj.create(vals)
            else:
                # If action was create but record existed, we append (don't unlink)
                # If action was update, we replace (unlink)
                if action == 'update':
                    dot_thu.dot_thu_sinh_vien_ids.unlink()
                dot_thu.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'
        except Exception as e:
            _logger.error("Lỗi thực thi action_handle Dot Thu: %s", str(e))
            self.write({'state': 'fail', 'date_done': datetime.now()})
            return '096'