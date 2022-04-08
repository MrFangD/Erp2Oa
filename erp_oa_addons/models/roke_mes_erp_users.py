# -*- coding: utf-8 -*-
"""
Description:
    erp同步用户关联
Versions:
    Created by www.rokedata.com<HuChuanwei>
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import hashlib


class RokeMesErpUsers(models.Model):
    _name = "roke.mes.erp.users"
    _rec_name = "user_id"
    _description = "ERP登录日志"
    _order = "id desc"

    user_id = fields.Many2one("res.users", string="MES系统用户")
    erp_user_id = fields.Char(string="erp用户id")
    erp_user_login = fields.Char(string="erp用户账号")
    erp_user_name = fields.Char(string="erp用户名称")

    def _compute_erp_access_token(self):
        m = hashlib.md5()
        for record in self:
            m.update(("%s-%s-%s" % (record.erp_user_id, record.erp_user_login, record.erp_user_name)).encode("utf-8"))
            record.access_token = m.hexdigest()


