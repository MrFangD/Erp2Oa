# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2022-04-04 14:11
    @Author: 全脂老猫
    @Describe:接收泛微的审批结果并回写相应的ERP单据
"""
import logging
from odoo import api, http, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


class ApproveController(http.Controller):

    @http.route(['/oa2erp/approve_result'], methods=['POST', 'OPTIONS'], type='json', auth='none', csrf=False, cors='*')
    def approve_result(self):
        """
        接收OA的审批结果
        :return:
        """
        _logger.info('审批结果')
        _logger.info(http.request.jsonrequest)
        users = http.request.jsonrequest.get("users")
        UserObj = http.request.env(user=SUPERUSER_ID)['res.users']

        return {"state": "success", "msg": "审批回写成功"}