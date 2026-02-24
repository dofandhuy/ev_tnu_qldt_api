# -*- coding: utf-8 -*-
import json
import logging

from Tools.scripts.fixcid import Char
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

            year_code = str(data.get('ma_nam_hoc') or '').strip()

            YearObj = self.env['hp.nam.hoc'].sudo()
            year = YearObj.search([('ma_nam_hoc', '=', year_code)], limit=1)

            if action == 'delete':
                if year:
                    year.unlink()


            else:

                # 1. Ép kiểu an toàn cho ma_don_vi

                ma_dv_raw = str(data.get('ma_don_vi') or '').strip()

                # Tìm bản ghi đơn vị kinh doanh trong hệ thống
                # Giả sử model đơn vị là 'res.business.unit' và trường mã là 'code'
                business_unit = self.env['res.business.unit'].sudo().search([
                    ('code', '=', ma_dv_raw)
                ], limit=1)

                if not business_unit:
                    _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)

                    return '096'

                # 2. Ép kiểu CHUỖI cho toàn bộ các trường Char của Odoo

                # Điều này ngăn lỗi .strip() ở các hàm hệ thống/model gốc

                vals = {

                    'ma_nam_hoc': year_code,

                    'ten_nam_hoc': str(data.get('ten_nam_hoc') or '').strip(),

                    'nam_bat_dau': str(data.get('nam_bat_dau') or 0).strip(),

                    'nam_ket_thuc': str(data.get('nam_ket_thuc') or 0).strip(),

                    'ma_don_vi': ma_dv_raw,

                }
                if business_unit:
                    vals['business_unit_id'] = business_unit.id

                if not year:

                    YearObj.create(vals)

                else:

                    year.write(vals)

            self.write({'state': 'done', 'date_done': datetime.now()})
            return '000'


        except Exception as e:
            _logger.error("Lỗi thực thi action_handle: %s", str(e))
            self.write({
                'state': 'fail',
                'date_done': datetime.now(),
            })
            return '096'
