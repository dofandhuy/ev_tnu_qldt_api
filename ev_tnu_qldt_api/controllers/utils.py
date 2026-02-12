from odoo.addons.izi_lib.helpers.Response import Response
from odoo.addons.ev_config_connect_api.helpers import Configs
from . import code_response
from odoo import _, SUPERUSER_ID, api, tools, registry
from odoo.addons.izi_lib.helpers.Dispatch import Dispatch


def check_error(request, API_URL, require_params=None):
    if require_params is None:
        require_params = []
    result = False
    code = message = ''
    params = request.params
    token = ''
    api_id = Configs._get_api_config(API_URL, token)
    remote_ip = Configs.get_request_ip()
    api_name = ''
    # check api config
    if not api_id:
        result = True
        code = '011'
        message = code_response.RESPONSE_CODE_MSG.get(code,'Lỗi không xác định')
        Configs._set_log_api(remote_ip, API_URL, api_name, params, code, message)
        return result, code, message, remote_ip, api_name, api_id
    else:
        api_name = api_id.name

    # check allow ip
    is_ip_valid = Configs.check_allow_ip(remote_ip)
    if not is_ip_valid:
        result = True
        code = '146'
        message = code_response.RESPONSE_CODE_MSG.get(code,'Lỗi không xác định')
        Configs._set_log_api(remote_ip, API_URL, api_name, params, code, message)
        return result, code, message, remote_ip, api_name, api_id
    # check token
    auth_header = request.httprequest.headers.get('Authorization')
    token = ''
    if not auth_header or not auth_header.startswith('Bearer '):
        if 'login' not in API_URL:
            result = True
            code = '400'
            message = code_response.RESPONSE_CODE_MSG.get(code,'Lỗi không xác định')
            Configs._set_log_api(remote_ip, API_URL, api_name, params, code, message)
            return result, code, message, remote_ip, api_name, api_id
    else:
        token = auth_header.split(' ')[1]

    additional_params = {}
    additional_params['access_token'] = token

    #check authorize
    if 'login' not in API_URL:
        env, user = check_authorize(request, additional_params)
        if not user:
            result = True
            code = '012'
            message = code_response.RESPONSE_CODE_MSG.get(code,'Lỗi không xác định')
            Configs._set_log_api(remote_ip, API_URL, api_name, params, code, message)
            return result, code, message, remote_ip, api_name, api_id

    ## Check required params
    missing_key = ''
    data = None
    if require_params:
        # for not login api
        if 'login' not in API_URL:
            if "action" not in params.keys() or params["action"] not in ["create","update","delete"]:
                code = '145'
                missing_key += " " + "action"
                message = code_response.RESPONSE_CODE_MSG.get(code, 'Lỗi không xác định')
            if "data" not in params.keys():
                code = '145'
                missing_key += " " + "data"
                message = code_response.RESPONSE_CODE_MSG.get(code, 'Lỗi không xác định')
            data = params.get("data",{})
        else:
            data = params

        for key in require_params:
            if key not in data.keys():
                missing_key += " " + key

        if missing_key:
            result = True
            code = '145'
            message = code_response.RESPONSE_CODE_MSG.get(code, 'Lỗi không xác định')
            message = '{}: {}'.format(message, missing_key)
            Configs._set_log_api(remote_ip, API_URL, api_name, params, code, message)
            return result, code, message, remote_ip, api_name, api_id

    return result, code, message, remote_ip, api_name, api_id

def check_authorize(request,additional_params):
    params = request.httprequest.json
    context = request.context
    if params.get('lang'):
        context = dict(context)
        context['lang'] = params.get('lang')
    env = request.env(user=SUPERUSER_ID, context=context)
    user = False
    env, user = Dispatch.access_token_authenticate(env, additional_params, {})
    return env, user