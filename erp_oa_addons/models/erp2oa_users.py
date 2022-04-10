# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2022-04-11 14:25
    @Author: 全脂老猫
    @Describe: erp用户与oa对接
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import hashlib


class Erp2oaUsers(models.Model):
    _name = "erp2oa.users"
    _rec_name = "user_id"
    _description = "ERP登录日志"
    _order = "id desc"

    user_id = fields.Char(string="OA用户账号")
    erp_user_id = fields.Char(string="erp用户id")
    erp_user_login = fields.Char(string="erp用户账号")
    erp_user_name = fields.Char(string="erp用户名称")


