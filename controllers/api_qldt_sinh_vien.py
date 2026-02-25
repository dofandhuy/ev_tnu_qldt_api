# -*- coding: utf-8 -*-
import logging
import json
from odoo.http import route, Controller, request
from odoo.addons.izi_lib.helpers.Route import Route
from odoo.addons.izi_lib.helpers.ApiException import ApiException
from odoo.addons.izi_lib.helpers.Response import Response
from odoo.addons.ev_tnu_api_utils.controllers import utils
from odoo.addons.ev_tnu_api_utils.controllers.code_response import RESPONSE_CODE_MSG
from odoo.addons.ev_config_connect_api.helpers import Configs


logger = logging.getLogger(__name__)


api_url = Route('student', version='1', app='qldt')

class QLDTStudent(Controller):

    @route(route=api_url, methods=['POST'], auth='public', type='json', csrf=False)
    def student(self, **post):
        try:
            verify = ["student_code", "full_name", "birthday", "gender", "unit_code"]
            params = request.httprequest.json

            result, code, message, remote_ip, api_name, api_id = utils.check_error(
                request, api_url, require_params=verify
            )

            if result:
                raise ApiException(message=message, code=code)

            data = params.get('data', {})
            action = params.get('action')
            ma_sinh_vien = data.get('student_code')
            code = "000"
            message = "Thành công"

            if code == '000' and action in ['update', 'delete']:
                student_id = request.env['res.partner'].sudo().search([
                    ('ma_sinh_vien', '=', ma_sinh_vien),
                ], limit=1)
                if not student_id:
                    code = '147'
                    message = f'Học sinh (Mã: {ma_sinh_vien}) không tồn tại trong hệ thống'

            Configs._set_log_api(remote_ip, api_url, api_name, params, code, message)
            if code == '000':
                # Tạo Log Sync
                log_sync = request.env['log.sync.receive.student'].sudo().create({
                    'params': json.dumps(params, ensure_ascii=False),  # Chứa cả 'action' và 'data'
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
                    return Response.success('Đồng bộ sinh viên thành công', data={'code': res_code}).to_json()
                else:
                    return Response.error(message='Xử lý dữ liệu thất bại', code=res_code).to_json()

        except ApiException as e:
            return e.to_json()
        except Exception as e:
            logger.error("Error in QLDTStudent API: %s", str(e))
            return Response.error(message="Lỗi hệ thống", code='500').to_json()