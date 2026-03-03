# -*- coding: utf-8 -*-
import logging
import json
from odoo.http import route, Controller, request
from odoo.addons.izi_lib.helpers.Route import Route
from odoo.addons.izi_lib.helpers.ApiException import ApiException
from odoo.addons.izi_lib.helpers.Response import Response
from odoo.addons.ev_tnu_api_utils.controllers import utils
from odoo.addons.ev_config_connect_api.helpers import Configs

_logger = logging.getLogger(__name__)

api_url = Route('tuition_collection', version='1', app='qldt')

class QLDTDotThu(Controller):

    @route(route=api_url, methods=['POST'], auth='public', type='json')
    def dot_thu(self):
        try:
            verify = ["tuition_collection_id", "code", "unit_code", "year_id", "semester_id"]
            params = request.httprequest.json

            result, code, message, remote_ip, api_name, api_id = utils.check_error(
                request, api_url, require_params=verify
            )
            if result:
                raise ApiException(message=message, code=code)

            data = params.get('data', {})
            action = params.get('action')
            qldt_id = data.get('tuition_collection_id')
            if not qldt_id:
                return '096'

            code = "000"
            message = "Thành công"

            if action == 'delete':
                # 3. VERIFY LOGIC NGHIỆP VỤ
                ma_dv_raw = str(data.get('unit_code') or '').strip()
                business_unit = request.env['res.business.unit'].sudo().search([
                    ('code', '=', ma_dv_raw)
                ], limit=1)

                if not business_unit:
                    code = '147'
                    message = f'Business Unit với mã: {ma_dv_raw} không tồn tại'
                else:
                    dot_thu_id = request.env['hp.ql.dot.thu'].sudo().search([
                        ('qldt_id', '=', qldt_id),
                        ('business_unit_id', '=', business_unit.id)
                    ], limit=1)

                    if not dot_thu_id:
                        code = '147'
                        message = f'Đợt thu (ID QLDT: {qldt_id}) không tồn tại trong hệ thống'

            # 4. GHI LOG API HỆ THỐNG
            Configs._set_log_api(remote_ip, api_url, api_name, params, code, message)

            # 5. XỬ LÝ ĐỒNG BỘ QUA LOG SYNC
            if code == '000':
                # Tạo Log Sync
                log_sync = request.env['log.sync.receive.dot.thu'].sudo().create({
                    'params': json.dumps(params, ensure_ascii=False),
                    'state': 'draft',
                    'job_queue': api_id.job_queue.id if api_id and api_id.job_queue else False,
                    'ip_address': remote_ip
                })

                # Thực thi xử lý
                res_code = log_sync.action_handle()
                res_msg = "Thành công" if res_code == '000' else "Thất bại"
                response_data = {'code': res_code, 'message': res_msg}

                log_sync.sudo().write({
                    'response': json.dumps(response_data, ensure_ascii=False)
                })
                if res_code == '000':
                    return Response.success('Đồng bộ đợt thu thành công', data={'code': res_code}).to_json()
                else:
                    return Response.error(message='Xử lý dữ liệu thất bại', code=res_code).to_json()

        except ApiException as e:
            return e.to_json()
        except Exception as e:
            _logger.error("API QLDT Dot Thu Critical Error: %s", str(e), exc_info=True)
            return Response.error(message="Lỗi hệ thống: " + str(e), code="500").to_json()
