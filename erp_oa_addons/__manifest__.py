# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Erp2Oa 协同中心',
    'version': '1.0',
    'category': 'Erp2Oa',
    'depends': ['web', 'web_gantt', 'web_dashboard'],
    'author': '全脂老猫',
    'website': 'https://github.com/MrFangD',
    'description': """
用于浪潮PS与泛微OA的系统对接，实现单据移动审批功能
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/roke_mes_sync_erp_views.xml',
        'views/roke_mes_sync_erp_log_views.xml',
        'views/roke_mes_erp_users_views.xml',
        'views/roke_mes_sync_erp_login_log_views.xml',
        'views/erp_metadata.xml',
        'wizard/erp2oa_table_field_view.xml',
        'views/list_btn_js.xml',
        'views/menus.xml',
        'views/update_menus.xml',
    ],
    'qweb': [
        'static/src/xml/ps_prod_order_sync_btn.xml'
    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
