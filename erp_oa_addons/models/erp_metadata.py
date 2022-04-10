# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2022-04-04 14:25
    @Author: 全脂老猫
    @Describe:erp元数据
"""
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from odoo.addons.erp_oa_addons.controllers import Db_connection
mssql = Db_connection.Mssql()
_logger = logging.getLogger(__name__)


def exec_sql(self, sql):
    erp_system = self.sudo().env["erp2oa.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
    if not erp_system:
        return -1
        # return {
        #     'warning': {
        #         'title': '系统参数错误',
        #         'message': '未获取到PS系统相关的配置信息，请联系系统管理员'
        #     }}
    db_host = erp_system.erp_url
    db_user = erp_system.user_name
    db_pwd = erp_system.password
    db_name = erp_system.db_name
    reslist = mssql.execQuery(args={
        "db_host": db_host,
        "db_user": db_user,
        "db_pwd": db_pwd,
        "db_name": db_name,
        "SQL": sql
    })
    return reslist


class Erp2oaErpLjbm(models.Model):
    _name = "erp2oa.erp.ljbm"
    _description = "ERP业务ID"
    _order = "id desc"
    _rec_name = 'name'

    # SELECT LSLJBM_LJBM,LSLJBM_LJBMNAME FROM LSLJBM
    code = fields.Char(string="业务ID")
    name = fields.Char(string="业务名称")

    def get_erp_ywid(self):

        SQL = """SELECT LSLJBM_LJBM,LSLJBM_LJBMNAME FROM LSLJBM"""

        reslists = exec_sql(self, SQL)
        if reslists.get('code') == 'success':
            reslist = reslists.get('data')
            _logger.info('--------获取业务ID--------')
            for list_data in reslist:
                _logger.info(list_data[0])
                _logger.info(list_data[1])

                ljbm = self.sudo().env['erp2oa.erp.ljbm'].search([('code', '=', list_data[0])])
                if ljbm:
                    continue
                self.sudo().env['erp2oa.erp.ljbm'].create({
                    'code': list_data[0],
                    'name': list_data[1]
                })
        else:
            raise UserError('获取数据异常！' + reslists.get('msg'))


class Erp2oaErpModels(models.Model):
    _name = "erp2oa.erp.models"
    _description = "ERP业务模块"
    _order = "id desc"
    _rec_name = 'name'

    # SELECT PPTALB_BH,PPTALB_MC  FROM PPTALB WHERE PPTALB_MX = '1'
    code = fields.Char(string="模块编号")
    name = fields.Char(string="模块名称")
    detail = fields.One2many('erp2oa.erp.models.detail', 'model_id', string='模块明细')

    def get_erp2oa_models(self):

        SQL = """SELECT PPTALB_BH,PPTALB_MC  FROM PPTALB WHERE PPTALB_MX = '1'"""
        reslists = exec_sql(self, SQL)
        _logger.info(reslists)
        if reslists.get('code') == 'success':
            reslist = reslists.get('data')
            for list_data in reslist:

                models = self.sudo().env['erp2oa.erp.models'].search([('code', '=', list_data[0])])
                if models:
                    models.write({
                        'code': list_data[0],
                        'name': list_data[1]
                    })
                else:
                    models = self.sudo().env['erp2oa.erp.models'].create({
                        'code': list_data[0],
                        'name': list_data[1]
                    })
                # 处理明细
                SQL = """SELECT PPTABLE_BM,PPTABLE_BH,PPTABLE_MC,PPTABLE_JS,PPTABLE_GLTJ,PPTABLE_XXJTJ 
                FROM PPTABLE WHERE  PPTABLE_XXJLB =  '%s'""" % list_data[0]
                reslists = exec_sql(self, SQL)
                _logger.info(reslists)
                if reslists.get('code') == 'success':
                    reslist = reslists.get('data')
                    for list_data in reslist:

                        detail = self.sudo().env['erp2oa.erp.models.detail'].search([('bm', '=', list_data[0]),
                                                                                     ('bh', '=', list_data[1])])
                        if list_data[3] == '1':
                            name = list_data[2] + '表头'
                        elif list_data[3] == '2':
                            name = list_data[2] + '表体'
                        if detail:
                            detail.write({
                                'model_id': models.id,
                                'bm': list_data[0],
                                'bh': list_data[1],
                                'name': name,
                                'gltj': list_data[4],
                                'xxjtj': list_data[5]
                            })
                        else:
                            detail = self.sudo().env['erp2oa.erp.models.detail'].create({
                                'model_id': models.id,
                                'bm': list_data[0],
                                'bh': list_data[1],
                                'name': name,
                                'gltj': list_data[4],
                                'xxjtj': list_data[5]
                            })
                else:
                    raise UserError('获取数据异常！' + reslists.get('msg'))

        else:
            raise UserError('获取数据异常！' + reslists.get('msg'))


class Erp2oaErpModelsDetail(models.Model):
    _name = "erp2oa.erp.models.detail"
    _description = "ERP业务模块明细"
    _order = "id desc"
    _rec_name = 'name'

    model_id = fields.Many2one('erp2oa.erp.models', string='业务模块')
    bm = fields.Char(string="模块编码")
    bh = fields.Char(string="模块编号")
    name = fields.Char(string="模块名称")
    gltj = fields.Char(string="关联条件")
    xxjtj = fields.Char(string="内置条件")


class Erp2oaErpTable(models.Model):
    _name = "erp2oa.erp.table"
    _description = "ERP表"
    _order = "id desc"

    table_name = fields.Many2many('erp2oa.erp.models.detail', string="表名")
    field = fields.One2many('erp2oa.erp.table.field', 'table_id', string='字段')

    def get_erp2oa_table_field(self):

        view = self.env.ref('erp_oa_addons.erp2oa_table_field_wizard_from')  # 项目名.跳转的id
        return {
            'name': "同步表数据",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'res_model': 'erp2oa.table.field.wizard',
            'target': 'new',
        }


class Erp2oaErpTableField(models.Model):
    _name = "erp2oa.erp.table.field"
    _description = "ERP表字段"
    _order = "id desc"
    _rec_name = 'field_name'

    # SELECT PPTABLE_BH, PPITEM_DM, PPITEM_MC, PPTABLE_XXJTJ
    # FROM PPITEM, PPTABLE
    # WHERE PPITEM_XXJDM LIKE 'CGDD%' and PPTABLE_XXJLB
    # LIKE '0301%' and PPTABLE_BM = PPITEM_XXJDM
    # ORDER BY PPITEM_XXJDM, PPITEM.PPITEM_XH ASC
    table_id = fields.Many2one('erp2oa.erp.table', string='表名')
    field_code = fields.Char(string="字段数据库名")
    field_name = fields.Char(string="字段名")
