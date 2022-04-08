# -*- coding: utf-8 -*-
"""
Description:
    同步日志
Versions:
    Created by www.rokedata.com<HuChuanwei>
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RokeMesSyncErpLog(models.Model):
    _name = "roke.mes.erp.system.log"
    _description = "同步日志"
    _order = "id desc"

    # 入参
    requst_parameter = fields.Text(string="同步入参")
    # 出参
    response_result = fields.Text(string="返回结果")
    sync_erp_model_id = fields.Many2one("roke.mes.sync.erp.model", string="同步模型")
