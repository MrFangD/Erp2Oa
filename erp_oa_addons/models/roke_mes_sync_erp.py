# -*- coding: utf-8 -*-
"""
Description:
    同步ERP基础数据
Versions:
    Created by www.rokedata.com<HuChuanwei>
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xmlrpc.client
try:
    from suds.client import Client as sudsClient
except ImportError:
    sudsClient = None
import json
import logging

_logger = logging.getLogger(__name__)


class RokeMesSyncErpSystem(models.Model):
    _name = "roke.mes.erp.system"
    _description = "ERP系统"
    _order = "id desc"

    name = fields.Char(string="系统名称")
    erp_type = fields.Selection(
        [("webService", "webService"), ("odooXmlRpc", "Odoo xmlrpc"), ("sqlserver", "SqlServer")],
        default="odooXmlRpc", string="对接类型", required=True)
    erp_url = fields.Char(string="访问地址")
    db_name = fields.Char(string="数据库名")
    user_name = fields.Char(string="同步账号")
    password = fields.Char(string="同步密码")
    logging_enable = fields.Boolean(string="记录同步日志", help="勾选后系统会记录每次同步结果", default=False)

    erp_sync_method_ids = fields.One2many("roke.mes.erp.sync.method", "erp_id", string="同步方法")
    model_sync_setting_ids = fields.One2many("roke.mes.sync.erp.model", "erp_id", string="同步模型")

    interval_number = fields.Integer(default=1, string="执行频率", help="每X一次")
    interval_type = fields.Selection([('minutes', '分钟'),
                                      ('hours', '小时'),
                                      ('days', '天'),
                                      ('weeks', '周'),
                                      ('months', '月')], string='执行频率单位', default='months')
    cron_id = fields.Many2one("ir.cron", string="定时任务")

    def _create_cron(self):
        # 创建定时任务
        cron = self.env['ir.cron'].sudo().create({
            'name': '%s-数据同步' % self.name,
            'model_id': self.sudo().env["ir.model"].search([("model", "=", "roke.mes.erp.system")]).id,
            'state': 'code',
            'code': 'model.execute_sync_task_cron()',
            'user_id': self.env.ref('base.user_root').id,
            'interval_number': self.interval_number,
            'interval_type': self.interval_type,
            'doall': True,
            'active': True,
            'numbercall': -1,
        })
        self.write({"cron_id": cron.id})

    def method_direct_trigger(self):
        """
        手动触发定时任务
        :return:
        """
        if self.cron_id:
            self.cron_id.method_direct_trigger()

    def execute_sync_task_cron(self):
        """
        按顺序对当前ERP系统下要同步的模型执行同步操作
        :return:
        """
        for record in self.search([]):
            if record.erp_type == "sqlserver":
                _logger.info("*-*-*-*-*-*-*执行同步PS数据*-*-*-*-*-*-*")
                _logger.info("*-*-*-*-*-*-*开始执行同步*-*-*-*-*-*-*")
                for model_record in record.model_sync_setting_ids:
                    _logger.info("同步模型：%s" % model_record.mes_model_id.display_name)
                    try:
                        model_record.sync_sqlserver_data()
                    except Exception as e:
                        _logger.error(e)
                        continue
                _logger.info("*-*-*-*-*-*-*执行同步完成*-*-*-*-*-*-*")

    @api.model
    def create(self, vals):
        """
        创建记录时同步创建定时任务
        :param vals:
        :return:
        """
        res = super(RokeMesSyncErpSystem, self).create(vals)
        res._create_cron()
        return res

    def write(self, vals):
        """
        编辑执行频率时同步修改定时任务
        :param vals:
        :return:
        """
        cron_dict = {}
        if vals.__contains__("interval_number"):
            cron_dict["interval_number"] = vals.get("interval_number")
        if vals.__contains__("interval_type"):
            cron_dict["interval_type"] = vals.get("interval_type")
        if cron_dict:
            self.cron_id.write(cron_dict)
        return super(RokeMesSyncErpSystem, self).write(vals)

    def unlink(self):
        """
        删除记录时同步删除定时任务
        :return:
        """
        if self.cron_id:
            self.cron_id.unlink()
        return super(RokeMesSyncErpSystem, self).unlink()


class RokeMesSyncErpSyncMethod(models.Model):
    _name = "roke.mes.erp.sync.method"
    _description = "ERP方同步方法"
    _rec_name = "interior_name"

    erp_id = fields.Many2one("roke.mes.erp.system", string="ERP系统")
    interior_name = fields.Char(string="ERP内部方法名")
    name = fields.Char(string="描述")


class RokeMesSyncErpSetting(models.Model):
    _name = "roke.mes.sync.erp.model"
    _description = "同步模型"
    _order = "execute_sequence"
    _rec_name = "mes_model_id"

    erp_id = fields.Many2one("roke.mes.erp.system", string="ERP系统", required=True, ondelete='restrict')
    erp_type = fields.Selection(related="erp_id.erp_type", string="对接类型")
    mes_model_id = fields.Many2one('erp2oa.erp.ljbm', string="业务ID")
    erp_model_name = fields.Many2many('erp2oa.erp.models.detail', string="erp表名")
    erp_sync_method_id = fields.Many2one("roke.mes.erp.sync.method", string="ERP内部方法")
    # data_key = fields.Char(string="返回数据标识")

    sync_field_ids = fields.One2many("roke.mes.sync.erp.model.fields", "sync_setting_id", string="对应字段")
    execute_sequence = fields.Integer(string="执行序号", help="根据序号从小到大依次从ERP中获取数据"
                                                          "如，同步物料类别要在同步物料之前。", default=10)
    last_execute_time = fields.Datetime(string="上次执行时间")
    is_enclosure = fields.Boolean(string="是否发送附件", help="勾选上会传递相应单据的附件")

    def create_log(self, requst_parameter, response_result):
        """
        创建同步日志
        :param requst_parameter: 同步入参
        :param response_result: 返回结果
        :return:
        """
        self.ensure_one()
        self.sudo().env["roke.mes.erp.system.log"].create({
            "requst_parameter": requst_parameter,
            "response_result": response_result,
            "sync_erp_model_id": self.id
        })

    def sync_sqlserver_data(self):
        # 归集审批数据
        pass

    def test_sync(self):
        """
        测试同步
        :return:
        """
        for record in self:
            if record.erp_type == "webService":
                record.sync_webService_data()
            elif record.erp_type == "odooXmlRpc":
                record.sync_xmlrpc_data()
            elif record.erp_type == "sqlserver":
                record.sync_sqlserver_data()
            else:
                raise UserError("未配置ERP执行类型，请联系系统管理员。")


class RokeMesSyncErpSettingFields(models.Model):
    _name = "roke.mes.sync.erp.model.fields"
    _description = "同步字段对应设置"

    sync_setting_id = fields.Many2one("roke.mes.sync.erp.model", string="同步设置", required=True, ondelete='cascade')
    erp_field_code = fields.Char(string="ERP字段数据库名", related='erp_field_name.field_code')
    erp_field_name = fields.Many2one('erp2oa.erp.table.field', string="ERP字段名")
