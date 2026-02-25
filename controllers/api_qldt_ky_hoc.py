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


api_url = Route('semester', version='1', app='qldt')

class QLDTKyhoc(Controller):

    @route(route=api_url, methods=['POST'], auth='public', type='json')
    def semester(self,**post):
        try:
            verify = [
                      "ma_ky_hoc", "ten_ky_hoc",
                      "ma_nam_hoc", "ten_nam_hoc", "ma_don_vi",
                      "phan_loai"
            ]
            params = request.httprequest.json

            result, code, message, remote_ip, api_name, api_id = utils.check_error(
                request, api_url, require_params=verify
            )

            if result:
                raise ApiException(message=message, code=code)

            data = params.get('data', {})
            action = params.get('action')
            ma_ky_hoc = data.get('ma_ky_hoc')
            success_code = "000"
            success_msg = "Thành công"

            ma_dv_raw = str(data.get('ma_don_vi') or '').strip()
            business_unit = request.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)
            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)

                return '096'

            if action in ['update', 'delete'] and code=='000':
                sem_exists = request.env['hp.ky.hoc'].sudo().search([('ma_ky_hoc', '=', ma_ky_hoc),
                                                                     ('business_unit_id','=',business_unit.id)])

                if not sem_exists:
                    success_code, success_msg = "147", "Kỳ học không tồn tại"

            Configs._set_log_api(remote_ip, api_url, api_name, params, success_code, success_msg)
            if success_code == '000':
                log_sync = request.env['log.sync.receive.semester'].sudo().create({
                    'params': json.dumps(params, ensure_ascii=False),
                    'state': 'draft',
                    'job_queue': api_id.job_queue.id if api_id and api_id.job_queue else False,
                    'ip_address': remote_ip
                })

                # Gọi handle bên trong khối IF này để không bị lỗi "referenced before assignment"
                res_code = log_sync.action_handle()

                res_msg = "Thành công" if res_code == '000' else "Thất bại"
                response_data = {'code': res_code, 'message': res_msg}

                log_sync.sudo().write({
                    'response': json.dumps(response_data, ensure_ascii=False)
                })

                if res_code == '000':
                    return Response.success('Đồng bộ kỳ học thành công', data={'code': res_code}).to_json()
                else:
                    return Response.error(message='Xử lý dữ liệu thất bại', code=res_code).to_json()
            else:
                # Trả về lỗi nghiệp vụ (ví dụ: 147)
                return Response.error(message=success_msg, code=success_code).to_json()

        except ApiException as e:
            return e.to_json()
        except Exception as e:
            logger.error("Error in QLDTKyhoc API: %s", str(e))
            return Response.error(message="Lỗi hệ thống", code='500').to_json()