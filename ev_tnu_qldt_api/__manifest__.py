# -*- coding: utf-8 -*-
{
    'name': "TNU tích hợp QLDT API",

    'summary': """
        TNU tích hợp QLDT API
        """,
    'description': """
        TNU tích hợp QLDT API
    """,

    'author': "IZISolution",
    'website': "https://www.izisolution.vn",
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['ev_config_connect_api', 'ev_api_sync_base', 'queue_job', 'izi_lib', 'base','ev_tnu_hp_master_data'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/qldt_api_config_data.xml',
        'data/api_qldt_login_data.xml',
        'view/api_nam_hoc_views.xml',
        'view/api_ky_hoc_views.xml',
        'view/api_sinh_vien_views.xml',
        'view/api_khoan_thu_views.xml'
    ],
}