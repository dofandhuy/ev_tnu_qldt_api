import json
import logging

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class LogSyncReceiveKyHoc(models.Model):
    _name = 'log.sync.receive.semester'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ kỳ học'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveKyHoc, self).create(vals_list)
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
            # Cấu trúc IZI thường bọc trong params, ta lấy data từ đúng chỗ
            # Nếu gửi từ Postman { "params": { "data": { ... } } }
            inner_params = raw_data.get('params', {})
            data = inner_params.get('data') or raw_data.get('data') or {}
            action = raw_data.get('action') or inner_params.get('action')

            ma_ky_hoc = data.get('ma_ky_hoc')
            if not ma_ky_hoc:
                _logger.error("Dữ liệu thiếu ma_ky_hoc")
                return '096'

            SemObj = self.env['semester'].sudo()
            semester = SemObj.search([('ma_ky_hoc', '=', ma_ky_hoc)], limit=1)

            # 1. Xử lý xóa
            if action == 'delete':
                if semester:
                    semester.unlink()
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000'

            # 2. Tìm ID Năm học (Tránh lỗi .id trên recordset rỗng)
            year_rec = self.env['years'].sudo().search([('ma_nam_hoc', '=', data.get('ma_nam_hoc'))], limit=1)
            if not year_rec:
                _logger.error("Không tìm thấy Năm học với mã: %s", data.get('ma_nam_hoc'))
                # Nếu model semester yêu cầu bắt buộc nam_hoc_id, ta phải dừng tại đây
                return '096'

            year_id = year_rec.id

            # 3. Chuẩn hóa Phân loại
            raw_phan_loai = data.get('phan_loai', '')
            val_phan_loai = 'ky_chinh'
            if any(x in str(raw_phan_loai).lower() for x in ['phụ', 'phu', '2']):
                val_phan_loai = 'ky_phu'

            # 4. Chuẩn bị dữ liệu Update/Create
            vals = {
                'ma_ky_hoc': ma_ky_hoc,
                'ten_ky_hoc': data.get('ten_ky_hoc') or ma_ky_hoc,
                'nam_hoc_id': year_id,
                'business_unit_id': int(data.get('business_unit_id') or 1),
                'company_id': int(data.get('company_id') or self.env.company.id),
                'phan_loai': val_phan_loai,
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