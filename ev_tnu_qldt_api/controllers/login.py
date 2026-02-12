# -*- coding: utf-8 -*-
import logging
from odoo.http import route, Controller, request
from odoo.addons.izi_lib.helpers.Route import Route
from odoo.addons.izi_lib.helpers.Dispatch import Dispatch
from odoo.addons.izi_lib.helpers.ApiException import ApiException
from odoo.addons.izi_lib.helpers.Response import Response
from odoo.addons.izi_api_repository.controllers.base.sign_in import SignIn as SignInRepository
from odoo.addons.ev_config_connect_api.helpers import Configs
from . import utils

logger = logging.getLogger(__name__)

api_url = Route('login', version='1', app='qldt')


class Login(Controller):

    @route(route=api_url, methods=['POST'], auth='public', type='json', csrf=False)
    def login(self, **post):
        try:
            params = request.params
            if 'device_id' not in params:
                params['device_id'] = 'qldt_default'

            # 1. Xác thực mật khẩu chuẩn Odoo
            uid = request.session.authenticate(request.db or 'Bai1', params.get('login'), params.get('password'))
            if not uid:
                return Response.error(message="Tài khoản hoặc mật khẩu không chính xác", code="411").to_json()

            # 2. Gọi Repo lấy Token với bộ tham số đặc biệt
            repo = SignInRepository()
            res = repo.sign_in(request.cr, request.env, params)

            if not res or not isinstance(res, dict):
                return Response.error(message="Không lấy được Token", code="500").to_json()

            data = {
                'user_type': res.get('user_type'),
                'access_token': res.get('access_token'),
            }

            Configs._set_log_api(request.httprequest.remote_addr, api_url, "Login", params, "000", "Thành công")
            return Response.success('Đăng nhập thành công', data=data).to_json()

        except Exception as e:
            logger.error("LOI DANG NHAP: %s", str(e), exc_info=True)
            return Response.error(message=str(e), code="500").to_json()