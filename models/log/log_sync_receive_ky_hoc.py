import json
import logging

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LogSyncReceiveSemester(models.Model):
    _name = 'log.sync.receive.semester'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ kỳ học'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveSemester, self).create(vals_list)
        for log in res:
            log.code = 'LSRS' + str(log.id)  # LSRS: Semester
        return res

    def execute_data(self):
        self.state = 'queue'
        return self.sudo().with_delay(channel=self.job_queue.complete_name,
                                      max_retries=3, priority=2).action_handle()

    def action_handle(self):
        self.ensure_one()
        try:
            raw_data = json.loads(self.params or "{}")

            inner_params = raw_data.get('params', {})
            data = inner_params.get('data') or raw_data.get('data') or {}
            action = raw_data.get('action') or inner_params.get('action')

            ma_dv_raw = str(data.get('unit_code') or '').strip()
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)
                return '147'

            qldt_id = data.get('qldt_id_semester') or 0
            if not qldt_id:
                _logger.error("Dữ liệu thiếu qldt_id_semester")
                return '145'

            SemObj = self.env['hp.ky.hoc'].sudo()
            semester = SemObj.search([('qldt_id_semester', '=', qldt_id),
                                      ('business_unit_id', '=', business_unit.id), ],
                                     limit=1)

            if not semester:
                # Nếu không tìm thấy mà đòi Update hoặc Delete thì báo lỗi
                if action in ['update', 'delete']:
                    _logger.error("Lỗi: Yêu cầu %s nhưng Kỳ học ID %s không tồn tại", action, qldt_id)
                    return '147'
            else:
                # Nếu đã có bản ghi mà đòi Create thì báo lỗi trùng
                if action == 'create':
                    _logger.error("Lỗi: Yêu cầu create nhưng Kỳ học ID %s đã tồn tại", qldt_id)
                    return '147'

            # 1. Xử lý xóa
            if action == 'delete':
                if semester:
                    semester.write({'active': False})
                    self.write({'state': 'done', 'date_done': datetime.now()})
                    return '000'

            search_year_code = data.get('qldt_id_years')

            year_rec = self.env['hp.nam.hoc'].sudo().search([('qldt_id_years', '=', search_year_code),
                                                             ('business_unit_id', '=', business_unit.id), ],
                                                            limit=1)
            if not year_rec:
                _logger.error("Không tìm thấy Năm học với mã: %s", search_year_code)
                return '147'

            ma_ky_hoc = str(data.get('semester_code') or '').strip()
            if not ma_ky_hoc:
                _logger.error("Dữ liệu thiếu ma_ky_hoc")
                return '145'

            raw_phan_loai = data.get('type', '')
            val_phan_loai = 'ky_chinh'
            if any(x in str(raw_phan_loai).lower() for x in ['phu']):
                val_phan_loai = 'ky_phu'

            vals = {
                'qldt_id_semester': qldt_id,
                'ma_ky_hoc': ma_ky_hoc,
                'ten_ky_hoc': data.get('semester_name'),
                'nam_hoc_id': year_rec.id,
                'ma_nam_hoc': year_rec.ma_nam_hoc,
                'ma_don_vi': ma_dv_raw,
                'phan_loai': val_phan_loai,
                'business_unit_id': business_unit.id,
                'active': True,
            }

            if not semester:
                SemObj.create(vals)
            else:
                semester.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'

        except Exception as e:
            _logger.error("Lỗi chi tiết tại LogSyncSemester: %s", str(e))
            self.write({'state': 'fail', 'date_done': datetime.now()})
            return '096'
