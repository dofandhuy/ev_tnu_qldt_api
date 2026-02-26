# -*- coding: utf-8 -*-
import json
import logging


from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LogSyncReceiveYears(models.Model):
    _name = 'log.sync.receive.years'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận đồng bộ năm học'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceiveYears, self).create(vals_list)
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


            ma_dv_raw = str(data.get('unit_code') or '').strip()
            business_unit = self.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)

            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)
                return '147'


            qldt_id = data.get('qldt_id_years')
            YearObj = self.env['hp.nam.hoc'].sudo()
            year = YearObj.search([('qldt_id_years', '=', qldt_id),('business_unit_id','=', business_unit.id)],
                                  limit=1)
            if not year:
                # Nếu không tìm thấy mà lại yêu cầu Update hoặc Delete thì báo lỗi
                if action in ['update', 'delete']:
                    _logger.error("Lỗi: Yêu cầu %s nhưng ID %s không tồn tại", action, qldt_id)
                    return '147'
            else:
                # Nếu đã tìm thấy mà lại yêu cầu Create thì báo lỗi trùng
                if action == 'create':
                    _logger.error("Lỗi: Yêu cầu create nhưng ID %s đã tồn tại", qldt_id)
                    return '147'

            if action == 'delete':
                if year:
                    year.write({'active': False})
                    self.write({'state': 'done', 'date_done': datetime.now()})
                    return '000'



            vals = {
                    'qldt_id_years': qldt_id,

                    'ma_nam_hoc': str(data.get('year_code') or '').strip(),

                    'ten_nam_hoc': str(data.get('year_name') or '').strip(),

                    'nam_bat_dau': str(data.get('year_start') or 0).strip(),

                    'nam_ket_thuc': str(data.get('year_end') or 0).strip(),

                    'ma_don_vi': ma_dv_raw,

                    'business_unit_id': business_unit.id if business_unit else False,

                }

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
