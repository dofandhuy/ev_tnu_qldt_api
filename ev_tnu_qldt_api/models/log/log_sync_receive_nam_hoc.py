# -*- coding: utf-8 -*-
import json
import logging

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LogSyncReceiveNamHoc(models.Model):
    _name = 'log.sync.receive.years'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ năm học'
    _rec_name = 'code'


    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveNamHoc, self).create(vals_list)
        for log in res:
            log.code = 'LSRY' + str(log.id)  # LSRY: Log Sync Receive Nam Hoc
        return res

    def execute_data(self):
        self.state = 'queue'
        return self.sudo().with_delay(channel=self.job_queue.complete_name,
                                      max_retries=3, priority=2).action_handle()

    def action_handle(self):
        self.ensure_one()
        try:
            raw_data = json.loads(self.params or "{}")
            params = raw_data.get('params', raw_data)
            action = params.get('action')  # Lấy hành động: 'update' hay 'delete'
            data = params.get('data') or {}

            year_code = data.get('ma_nam_hoc')
            year_name = data.get('ten_nam_hoc')



            YearObj = self.env['years'].sudo()
            year = YearObj.search([('ma_nam_hoc', '=', year_code)], limit=1)

            if action == 'delete':
                if year:
                    year.unlink()

            else:
                # Ép kiểu và kiểm tra dữ liệu
                b_id = int(data.get('business_unit_id') or 0)

                # Nếu là trường bắt buộc mà API gửi về bằng 0 hoặc không gửi
                if  not b_id:
                    _logger.error("LỖI: company_id và business_unit_id là bắt buộc nhưng đang trống!")
                    return '096'
                vals = {
                    'ma_nam_hoc': year_code,
                    'ten_nam_hoc': data.get('ten_nam_hoc'),
                    'nam_bat_dau': int(data.get('nam_bat_dau') or 0),
                    'nam_ket_thuc': int(data.get('nam_ket_thuc') or 0),
                    'business_unit_id': b_id,
                }
                if not year:
                    YearObj.create(vals)
                else:
                    year.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'  # Trả về thành công


        except Exception as e:
            _logger.error("Lỗi thực thi action_handle: %s", str(e))
            self.write({
                'state': 'fail',
                'date_done': datetime.now(),
            })
            return '096'
