# -*- coding: utf-8 -*-
"""
Description:
    
Versions:
    Created by www.rokedata.com<HuChuanwei>
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RokeMesSyncErpLoginLog(models.Model):
    _name = "roke.mes.erp.login.log"
    _description = "ERP登录日志"
    _order = "id desc"

    user_id = fields.Many2one("res.users", string="登录用户")
    state = fields.Selection([("success", "成功"), ("failed", "失败")], string="登录结果")
    nonce = fields.Char(string="随机校验码")

