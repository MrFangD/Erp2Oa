# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2021-10-25 14:42
    @Author: 全脂老猫
    @Describe: 获取表字段信息
"""
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.erp_oa_addons.controllers import Db_connection
mssql = Db_connection.Mssql()


class Erp2oaTableField(models.TransientModel):
    _name = 'erp2oa.table.field.wizard'

    table_name = fields.Many2many('erp2oa.erp.models.detail', string="表名")

    def confirm(self):

        table = self.sudo().env['erp2oa.erp.table'].create({
            'table_name': self.table_name
        })

        sql = """SELECT PPITEM_DM, PPITEM_MC FROM PPITEM WHERE PPITEM_XXJDM LIKE 'CGDD%' 
        AND (PPITEM_DM LIKE 'CGDD1%' or PPITEM_DM LIKE 'CGDD2%')
        ORDER BY PPITEM_XXJDM, PPITEM.PPITEM_XH ASC"""

        erp_system = self.sudo().env["roke.mes.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
        if not erp_system:
            raise UserError('未获取到PS系统相关的配置信息，请联系系统管理员')
        db_host = erp_system.erp_url
        db_user = erp_system.user_name
        db_pwd = erp_system.password
        db_name = erp_system.db_name
        reslists = mssql.execQuery(args={
            "db_host": db_host,
            "db_user": db_user,
            "db_pwd": db_pwd,
            "db_name": db_name,
            "SQL": sql
        })
        if reslists.get('code') == 'success':
            reslist = reslists.get('data')
            for list_data in reslist:

                # ljbm = self.sudo().env['erp2oa.erp.ljbm'].search([('code', '=', list_data[0])])
                # if ljbm:
                #     continue
                self.sudo().env['erp2oa.erp.table.field'].create({
                    'table_id': table.id,
                    'field_code': list_data[0],
                    'field_name': list_data[1]
                })
        else:
            raise UserError('获取数据异常！' + reslists.get('msg'))

