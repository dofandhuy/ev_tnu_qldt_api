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

api_url = Route('years', version='1', app='qldt')


class QLDTNamHoc(Controller):

    @route(route=api_url, methods=['POST'], auth='public', type='json')
    def years(self):
        try:


            # 1. Định nghĩa các trường bắt buộc
            verify = [
                "ma_nam_hoc", "ten_nam_hoc", "nam_bat_dau",
                "nam_ket_thuc", "ma_don_vi"
            ]
            params = request.httprequest.json

            result, code, message, remote_ip, api_name, api_id = utils.check_error(
                request, api_url, require_params=verify

            )

            if result:
                raise ApiException(message=message, code=code)

            data = params.get('data', {})
            action = params.get('action')
            ma_nam_hoc = data.get('ma_nam_hoc')

            ma_dv_raw = str(data.get('ma_don_vi') or '').strip()
            business_unit = request.env['res.business.unit'].sudo().search([
                ('code', '=', ma_dv_raw)
            ], limit=1)
            if not business_unit:
                _logger.error("Không tìm thấy Business Unit với mã: %s", ma_dv_raw)

                return '096'


            code = "000"
            message = "Thành công"

            # 3. VERIFY LOGIC NGHIỆP VỤ
            nam_bat_dau = int(data.get('nam_bat_dau') or 0)
            nam_ket_thuc = int(data.get('nam_ket_thuc') or 0)

            # Kiểm tra logic năm
            if nam_bat_dau and nam_ket_thuc:
                if int(nam_ket_thuc) <= int(nam_bat_dau):
                    code = '147'
                    message = 'Năm kết thúc không được nhỏ hơn hoặc bằng năm bắt đầu'

            # Kiểm tra tồn tại đối với hành động sửa/xóa (sử dụng model hp.nam.hoc)
            if code == '000' and action in ['update', 'delete']:
                year_id = request.env['hp.nam.hoc'].sudo().search([
                    ('ma_nam_hoc', '=', ma_nam_hoc),
                    ('business_unit_id', '=', business_unit.id),
                ], limit=1)
                if not year_id:
                    code = '147'
                    message = f'Năm học (Mã: {ma_nam_hoc}) không tồn tại trong hệ thống'

            # 4. GHI LOG API HỆ THỐNG
            Configs._set_log_api(remote_ip, api_url, api_name, params, code, message)

            # 5. XỬ LÝ ĐỒNG BỘ QUA LOG SYNC
            if code == '000':
                # Tạo Log Sync
                log_sync = request.env['log.sync.receive.years'].sudo().create({
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
                    return Response.success('Đồng bộ năm học thành công', data={'code': res_code}).to_json()
                else:
                    return Response.error(message='Xử lý dữ liệu thất bại', code=res_code).to_json()

        except ApiException as e:
            return e.to_json()
        except Exception as e:
            logger.error("API QLDT Years Critical Error: %s", str(e), exc_info=True)
            return Response.error(message="Lỗi hệ thống: " + str(e), code="500").to_json()

