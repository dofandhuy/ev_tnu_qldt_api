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


api_url = Route('product', version='1', app='qldt')

class QLDTProduct(Controller):

    @route(route=api_url, methods=['POST'], auth='public', type='json')
    def purchase(self, **post):
        try:
            verify = ["default_code","name","unit_code","qldt_id_product"]
            params = request.httprequest.json

            result, code, message, remote_ip, api_name, api_id = utils.check_error(
                request, api_url, require_params=verify
            )

            if result:
                raise ApiException(message=message, code=code)

            data = params.get('data', {})
            action = params.get('action')
            qldt_id = data.get('qldt_id_product')
            code = "000"
            msg = "Thành công"

            if code == '000' and action in ['update', 'delete']:
                purchase_id = request.env['product.template'].sudo().search([
                    ('qldt_id_product', '=', qldt_id)
                ], limit=1)
                if not purchase_id:
                    code = '147'
                    message = f'Khoản thu (Mã: {qldt_id}) không tồn tại trong hệ thống'

            Configs._set_log_api(remote_ip, api_url, api_name, params, code, msg)

            if code == '000':
                log_sync = request.env['log.sync.receive.product'].sudo().create({
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
                    return Response.success('Đồng bộ khoản thu thành công', data={'code': res_code}).to_json()
                else:
                    return Response.error(message='Xử lý dữ liệu thất bại', code=res_code).to_json()

        except ApiException as e:
            return e.to_json()
        except Exception as e:
            logger.error("Error in QLDTKhoanThu API: %s", str(e))
            return Response.error(message="Lỗi hệ thống", code='500').to_json()