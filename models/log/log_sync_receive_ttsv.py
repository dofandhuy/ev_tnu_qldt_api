# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class LogSyncReceiveTTSV(models.Model):
    _name = 'log.sync.receive.ttsv'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ thanh toán sinh viên'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveTTSV, self).create(vals_list)
        for log in res:
            log.code = 'LSRT' + str(log.id)
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

            qldt_id = data.get('student_payment_id')
            if not qldt_id:
                _logger.error("Dữ liệu thiếu student_payment_id")
                return '145'

            ma_dv_raw = str(data.get('unit_code') or '').strip()
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)
                return '147'

            TTSVObj = self.env['hp.thanh.toan.sinh.vien'].sudo()
            ttsv = TTSVObj.search([('qldt_id', '=', qldt_id),
                                   ('business_unit_id', '=', business_unit.id)], limit=1)

            if not ttsv:
                if action in ['update', 'delete']:
                    _logger.error("Lỗi: Yêu cầu %s nhưng ID %s không tồn tại", action, qldt_id)
                    return '147'
            else:
                if action == 'create':
                    # If already exists and action is create, we will append data
                    action = 'update_append'

            if action == 'delete':
                if ttsv:
                    ttsv.trang_thai = 'nhap'
                    ttsv.unlink()
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000'

            # Logic for create/update
            student_code = data.get('student_code')
            student = self.env['res.partner'].sudo().search([
                ('ma_sinh_vien', '=', student_code),
                ('business_unit_id', '=', business_unit.id)
            ], limit=1)
            if not student:
                _logger.error("Không tìm thấy sinh viên với mã: %s", student_code)
                return '147'

            payment_method = data.get('payment_method')
            journal_code = 'CSH1' if payment_method == 'tm' else 'BNK1'
            journal = self.env['account.journal'].sudo().search([
                ('code', '=', journal_code),
            ], limit=1)
            if not journal:
                # Fallback to search without business_unit_id if not found
                journal = self.env['account.journal'].sudo().search([
                    ('code', '=', journal_code)
                ], limit=1)

            if not journal:
                _logger.error("Không tìm thấy sổ nhật ký với mã: %s", journal_code)
                return '147'

            hinh_thuc_dt_code = data.get('hinh_thuc_dao_tao_id')
            hinh_thuc_dt = self.env['hp.hinh.thuc.dt'].sudo().search([
                ('ma_hinh_thuc_dt', '=', hinh_thuc_dt_code)
            ], limit=1)

            cap_bac_code = data.get('cap_bac_dt_id')
            cap_bac = self.env['hp.cap.bac'].sudo().search([
                ('ma_cap_bac', '=', cap_bac_code)
            ], limit=1)

            chuong_trinh_code = data.get('chuong_trinh_dao_tao_id')
            chuong_trinh = self.env['hp.chuong.trinh.dao.tao'].sudo().search([
                ('ma_chuong_trinh_dao_tao', '=', chuong_trinh_code)
            ], limit=1)

            nien_khoa_code = data.get('nien_khoa_id')
            nien_khoa = self.env['hp.nien.khoa'].sudo().search([
                ('ma_nien_khoa', '=', nien_khoa_code)
            ], limit=1)

            nganh_hoc_code = data.get('nganh_hoc_id')
            nganh_hoc = self.env['hp.nganh.hoc'].sudo().search([
                ('ma_nganh_hoc', '=', nganh_hoc_code)
            ], limit=1)

            vals = {
                'qldt_id': qldt_id,
                'so_chung_tu': data.get('code'),
                'trang_thai': 'cho_xac_nhan',
                'ngay_thanh_toan': data.get('payment_date'),
                'ngay_hach_toan': data.get('accounting_date'),
                'business_unit_id': business_unit.id,
                'so_nhat_ky_id': journal.id,
                'sinh_vien_id': student.id,
                'hinh_thuc_dt_id': hinh_thuc_dt.id if hinh_thuc_dt else False,
                'cap_bac_id': cap_bac.id if cap_bac else False,
                'chuong_trinh_dao_tao_id': chuong_trinh.id if chuong_trinh else False,
                'nien_khoa_id': nien_khoa.id if nien_khoa else False,
                'nganh_hoc_id': nganh_hoc.id if nganh_hoc else False,
                'mo_ta': data.get('description'),
                'hinh_thuc_tt': payment_method,
            }

            # Handle details
            details_data = data.get('details') or []
            line_ids = []
            for line in details_data:
                product_qldt_id = line.get('product_id')
                product = self.env['product.template'].sudo().search([
                    ('default_code', '=', product_qldt_id)
                ], limit=1)
                if not product:
                    _logger.error("Không tìm thấy khoản thu với qldt_id: %s", product_qldt_id)
                    continue

                year_qldt_id = line.get('year_id')
                year = self.env['hp.nam.hoc'].sudo().search([
                    ('ma_nam_hoc', '=', year_qldt_id)
                ], limit=1)
                
                semester_qldt_id = line.get('semester_id')
                semester = self.env['hp.ky.hoc'].sudo().search([
                    ('ma_ky_hoc', '=', semester_qldt_id),
                    ('business_unit_id', '=', business_unit.id)
                ], limit=1)

                line_vals = {
                    'nam_hoc_id': year.id if year else False,
                    'ky_hoc_id': semester.id if semester else False,
                    'sinh_vien_id': student.id,
                    'khoan_thu_id': product.id,
                    'phai_thanh_toan': line.get('amount_total'),
                    'so_tien': line.get('amount_paid'),
                }

                # Link to tuition collection if provided
                dot_thu_qldt_id = line.get('tuition_collection_id')
                dot_thu = False
                if dot_thu_qldt_id:
                    dot_thu = self.env['hp.ql.dot.thu'].sudo().search([
                        ('qldt_id', '=', dot_thu_qldt_id),
                        ('business_unit_id', '=', business_unit.id)
                    ], limit=1)
                    if dot_thu:
                        line_vals['dot_thu_id'] = dot_thu.id

                # Search for tuition collection detail if dot_thu is found
                if dot_thu and student:
                    domain = [
                        ('sinh_vien_id', '=', student.id),
                        ('dt_sinh_vien_id.ql_dot_thu_id', '=', dot_thu.id),
                        ('khoan_thu_id', '=', product.id if product else False)
                    ]
                    dtsv_ct = self.env['hp.dot.thu.sinh.vien.chi.tiet'].sudo().search(domain, limit=1)
                    if dtsv_ct:
                        line_vals['dtsv_chi_tiet_id'] = dtsv_ct.id

                line_ids.append((0, 0, line_vals))

            if line_ids:
                vals['chi_tiet_ids'] = line_ids

            if not ttsv:
                TTSVObj.create(vals)
            else:
                # If action was create but record existed, we append (don't unlink)
                # If action was update, we replace (unlink)
                if action == 'update':
                    ttsv.chi_tiet_ids.unlink()
                ttsv.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'
        except Exception as e:
            _logger.error("Lỗi thực thi action_handle TTSV: %s", str(e))
            self.write({'state': 'fail', 'date_done': datetime.now()})
            return '096'


