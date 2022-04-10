# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2022-04-10 14:25
    @Author: 全脂老猫
    @Describe: 同步日志
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class erp2oaLog(models.Model):
    _name = "erp2oa.erp.system.log"
    _description = "同步日志"
    _order = "id desc"

    # 入参
    requst_parameter = fields.Text(string="同步入参")
    # 出参
    response_result = fields.Text(string="返回结果")
    sync_erp_model_id = fields.Many2one("erp2oa.erp.model", string="同步模型")
