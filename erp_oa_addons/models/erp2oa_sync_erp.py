# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2022-04-10 14:25
    @Author: 全脂老猫
    @Describe: erp数据推送泛微OA处理逻辑
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
from odoo.addons.erp_oa_addons.controllers import Db_connection
mssql = Db_connection.Mssql()
import xmlrpc.client
try:
    from suds.client import Client as sudsClient
except ImportError:
    sudsClient = None
import json
import logging
import base64

_logger = logging.getLogger(__name__)


class Erp2OaSyncErpSystem(models.Model):
    _name = "erp2oa.erp.system"
    _description = "ERP系统"
    _order = "id desc"

    name = fields.Char(string="系统名称")
    erp_type = fields.Selection(
        [("webService", "webService"), ("odooXmlRpc", "Odoo xmlrpc"), ("sqlserver", "SqlServer")],
        default="odooXmlRpc", string="对接类型", required=True)
    erp_url = fields.Char(string="访问地址", required=True)
    db_name = fields.Char(string="数据库名", required=True)
    user_name = fields.Char(string="同步账号", required=True)
    password = fields.Char(string="同步密码", required=True)

    oa_url = fields.Char(string="OA访问地址", required=True)
    oa_appid = fields.Char(string="OA_appid", required=True)
    oa_loginid = fields.Char(string="用户", required=True)
    oa_pwd = fields.Char(string="密码", required=True)
    oa_workflowId = fields.Char(string="workflowId", required=True)

    logging_enable = fields.Boolean(string="记录同步日志", help="勾选后系统会记录每次同步结果", default=False)

    erp_sync_method_ids = fields.One2many("erp2oa.sync.method", "erp_id", string="同步方法")
    model_sync_setting_ids = fields.One2many("erp2oa.erp.model", "erp_id", string="同步模型")

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
            'model_id': self.sudo().env["ir.model"].search([("model", "=", "erp2oa.erp.system")]).id,
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
        res = super(Erp2OaSyncErpSystem, self).create(vals)
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
        return super(Erp2OaSyncErpSystem, self).write(vals)

    def unlink(self):
        """
        删除记录时同步删除定时任务
        :return:
        """
        if self.cron_id:
            self.cron_id.unlink()
        return super(Erp2OaSyncErpSystem, self).unlink()


class Erp2oaSyncMethod(models.Model):
    _name = "erp2oa.sync.method"
    _description = "ERP方同步方法"
    _rec_name = "interior_name"

    erp_id = fields.Many2one("erp2oa.erp.system", string="ERP系统")
    interior_name = fields.Char(string="ERP内部方法名")
    name = fields.Char(string="描述")


class Erp2oaErpSetting(models.Model):
    _name = "erp2oa.erp.model"
    _description = "同步模型"
    _order = "execute_sequence"
    _rec_name = "mes_model_id"

    erp_id = fields.Many2one("erp2oa.erp.system", string="ERP系统", required=True, ondelete='restrict')
    erp_type = fields.Selection(related="erp_id.erp_type", string="对接类型")
    mes_model_id = fields.Many2one('erp2oa.erp.ljbm', string="业务ID")
    erp_model_name = fields.Many2many('erp2oa.erp.models.detail', string="erp表名")
    erp_sync_method_id = fields.Many2one("erp2oa.sync.method", string="ERP内部方法")
    # data_key = fields.Char(string="返回数据标识")

    sync_field_ids = fields.One2many("erp2oa.model.fields", "sync_setting_id", string="对应字段")
    execute_sequence = fields.Integer(string="执行序号", help="根据序号从小到大依次从ERP中获取数据"
                                                          "如，同步物料类别要在同步物料之前。", default=10)
    last_execute_time = fields.Datetime(string="上次执行时间")
    is_enclosure = fields.Boolean(string="是否发送附件", help="勾选上会传递相应单据的附件")
    oa_fjmc = fields.Char(string="OA附件标识")
    oa_detail_table = fields.Char(string="OA表体名")

    def create_log(self, requst_parameter, response_result):
        """
        创建同步日志
        :param requst_parameter: 同步入参
        :param response_result: 返回结果
        :return:
        """
        self.ensure_one()
        self.sudo().env["erp2oa.erp.system.log"].create({
            "requst_parameter": requst_parameter,
            "response_result": response_result,
            "sync_erp_model_id": self.id
        })

    def sync_sqlserver_data(self):
        sp_datas = self.get_spdata()
        if len(sp_datas) <= 0:
            return
        # 获取CPK
        cpk = ''
        requst_parameter = {}
        cpk_url = 'http://{url}/api/getSecret/cpk'.format(url=self.erp_id.oa_url)
        try:
            res_cpk = requests.get(cpk_url)
            if res_cpk.ok:
                cpk = str(res_cpk.text)
        except requests.ConnectionError as e:
            _logger.info(str(e))
            cpk = str(e)
        requst_parameter['cpk'] = cpk

        # 注册泛微OA
        secret = ''
        spk = ''
        regist_url = 'http://{url}/api/ec/dev/auth/regist'.format(url=self.erp_id.oa_url)
        data = {
            # 'appid': self.erp_id.oa_appid,
            'cpk': cpk,
            'loginid': self.erp_id.oa_loginid,
            'pwd': self.erp_id.oa_pwd
        }
        try:
            headers = {
                'appid': self.erp_id.oa_appid
            }
            req = requests.post(regist_url, headers=headers, data=json.dumps(data))
            response = req.json()
            _logger.info(response)
            if response['code'] == -1:
                _logger.info('调用注册接口出错，错误信息：{error}'.format(error=response['msg']))
                # raise UserError('调用注册接口出错，错误信息：{error}'.format(error=response['msg']))
            else:
                secret = response['secrit']
                spk = response['spk']
        except requests.HTTPError as error:
            _logger.info('调用注册接口出错，错误信息{error}'.format(error=error))
            spk = str(error)
            # raise UserError('调用注册接口出错，错误信息{error}'.format(error=error))

        requst_parameter['secret'] = secret
        requst_parameter['spk'] = spk
        # 获取spk
        secrit = ''
        spk_url = 'http://{url}/api/getSecret/secret'.format(url=self.erp_id.oa_url)
        data = {
            'spk': spk,
            'secrit': secret
        }
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            req = requests.post(spk_url, headers=headers, data=data, verify=False)
            if req.ok:
                secrit = str(req.text)
            else:
                _logger.info('获取secret出错，错误信息：{error}'.format(error=req.status_code))
                secrit = str(req.status_code)
        except requests.HTTPError as error:
            _logger.info('获取secret出错，错误信息：{error}'.format(error=error))
            secrit = str(error)
            # raise UserError('获取secret出错，错误信息{error}'.format(error=error))

        requst_parameter['secrit'] = secrit
        # 获取USERID
        userid = ''
        userid_url = 'http://{url}/api/getSecret/userid'.format(url=self.erp_id.oa_url)
        data = {
            'spk': spk,
            'userid': 1
        }
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            req = requests.post(userid_url, headers=headers, data=data, verify=False)
            if req.ok:
                userid = str(req.text)
            else:
                _logger.info('获取secret出错，错误信息：{error}'.format(error=req.status_code))
                userid = str(req.status_code)
        except requests.HTTPError as error:
            _logger.info('获取secret出错，错误信息{error}'.format(error=error))
            userid = str(error)
            # raise UserError('获取secret出错，错误信息{error}'.format(error=error))

        requst_parameter['userid'] = userid
        # 获取泛微OA的token
        token = ''
        applytoken_url = 'http://{url}/api/ec/dev/auth/applytoken'.format(url=self.erp_id.oa_url)
        data = {
            'appid': self.erp_id.oa_appid,
            'secret': secrit
        }
        headers = {
            "appid": self.erp_id.oa_appid,
            'secret': secrit
        }
        try:
            req = requests.post(applytoken_url, headers=headers, data=json.dumps(data))
            response = req.json()
            _logger.info(response)
            if response['code'] == -1:
                # raise UserError('获取token出错，错误信息：{error}'.format(error=response['msg']))
                token = response['msg']
            else:
                token = response['token']
        except requests.HTTPError as error:
            token = error
            # raise UserError('获取token出错，错误信息{error}'.format(error=error))
        requst_parameter['token'] = token

        # 推送审批数据
        for sp_data in sp_datas:
            headers = {
                "appid": self.erp_id.oa_appid,
                'token': token,
                'userid': userid,
                # "Content-type": "application/x-www-form-urlencoded"
            }

            if self.oa_detail_table:
                detail_data = []
                detail_data.append(sp_data.get('detailData'))
                data = {
                    "mainData": json.dumps(sp_data.get('mainData')),
                    "detailData": json.dumps(detail_data),
                    "workflowId":  self.erp_id.oa_workflowId,
                    "requestName": 'ERP-采购订单审批流程'
                }
            else:
                data = {
                    "mainData": json.dumps(sp_data.get('mainData')),
                    "workflowId": self.erp_id.oa_workflowId,
                    "requestName": 'ERP-采购订单审批流程'
                }
            _logger.info(data)
            url = 'http://{url}/api/workflow/paService/doCreateRequest'.format(
                url=self.erp_id.oa_url)
            try:
                req = requests.post(url, data=data, headers=headers)
                _logger.info(req.json())
                res = req.json()
                if res.get('code') == 'SUCCESS':
                    # 更新回写状态
                    self.set_send_bz(sp_data.get('key'))
                else:
                    _logger.info('同步数据失败')
                    _logger.info(req.json())
                    _logger.info(data)


            except Exception as e:
                _logger.info(e)
                req = e
            # self.create_log(requst_parameter, req)

    def set_send_bz(self, key):
        erp_system = self.sudo().env["erp2oa.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
        if not erp_system:
            return {'code': -1, 'msg': '获取数据库连接信息失败!'}
        db_host = erp_system.erp_url
        db_user = erp_system.user_name
        db_pwd = erp_system.password
        db_name = erp_system.db_name

        # 处理业务单据SQL
        sql = " UPDATE CGDD1 SET CGDD1_SHBZ = '3' WHERE CGDD1_LSBH = '%s' " % (key)

        reslist = mssql.execNonQuery(args={
            "db_host": db_host,
            "db_user": db_user,
            "db_pwd": db_pwd,
            "db_name": db_name,
            "SQL": sql
        })

    def get_spdata(self):
        # 归集单据信息
        erp_system = self.sudo().env["erp2oa.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
        if not erp_system:
            return {'code': -1, 'msg': '获取数据库连接信息失败!'}
        db_host = erp_system.erp_url
        db_user = erp_system.user_name
        db_pwd = erp_system.password
        db_name = erp_system.db_name

        # 处理业务单据SQL
        table_sql = ''
        domain = ''
        fields = ''
        where_sql = ''
        field_master = []
        field_detail = []
        for table in self.erp_model_name:
            table_sql = table_sql + ',' + table.bh
            # detail_where_sql = table.bh + "_LSBH = 'S-LSBH' AND " + where_sql
            if table.gltj:
                domain = domain + ' AND ' + table.gltj
            # if table.xxjtj:
            #     domain = domain + ' AND ' + table.xxjtj

        relation_table = ""
        relation_where = ""
        for field in self.sync_field_ids:
            if field.erp_relation_table:
                if field.erp_field_type == 'master':
                    field_master.append(field.erp_relation_field)
                else:
                    field_detail.append(field.erp_relation_field)
                relation_table = relation_table + ',' + field.erp_relation_table
                relation_where = relation_where + ' AND ' + field.erp_relation_where
                fields = fields + ' , ' + field.erp_relation_field
            else:
                if field.erp_field_type == 'master':
                    field_master.append(field.erp_field_code)
                else:
                    field_detail.append(field.erp_field_code)
                fields = fields + ' , ' + field.erp_field_code
        if self.mes_model_id.code == 'CGDD':
            where_sql = " CGDD1_SHBZ = '0' AND "
            fields = fields + ' , CGDD1_LSBH '
        if len(relation_table)> 0:
            table_sql = table_sql + relation_table
            where_sql = where_sql + relation_where[4:] + ' AND '

        SQL = 'SELECT ' + fields[2:] + ' FROM ' + table_sql[1:] + ' WHERE ' + where_sql + ' ' + domain[4:]

        reslist = mssql.execQuery_fields(args={
            "db_host": db_host,
            "db_user": db_user,
            "db_pwd": db_pwd,
            "db_name": db_name,
            "SQL": SQL
        })
        if reslist.get('code') == 'success':
            reslist = reslist.get('data')
            data_temp = {}
            data = {}
            data_key = []
            for order in reslist:
                # 处理分组数据
                if order.get('CGDD1_LSBH') not in data_temp.keys():
                    temp = []
                data_temp[order.get('CGDD1_LSBH')] = order
                temp.append(data_temp[order.get('CGDD1_LSBH')])
                data[order.get('CGDD1_LSBH')] = temp
                data_key.append(order.get('CGDD1_LSBH'))
            fin_data = []
            for key in list(set(data_key)):
                mainData = []
                workflowRequestTableRecords = []
                # 归集表头数据
                for order in data[key]:
                    if len(mainData) <= 0:
                        for field_key in field_master:
                            oa_key = self.env['erp2oa.model.fields'].search([("sync_setting_id", "=", self.id),
                                                                             ("erp_field_code", "=", field_key)], limit=1)
                            if not oa_key:
                                oa_key = self.env['erp2oa.model.fields'].search([("sync_setting_id", "=", self.id),
                                                                                 ("erp_relation_field", "=",field_key)], limit=1)

                            _logger.info(oa_key)

                            mainData.append({
                                "fieldName": oa_key.oa_field_code,
                                'fieldValue': order.get(field_key)
                            })

                    workflowRequestTableFields = []
                    for field_key in field_detail:
                        oa_key = self.env['erp2oa.model.fields'].search([("sync_setting_id", "=", self.id),
                                                                             ("erp_field_code", "=", field_key)],
                                                                            limit=1).oa_field_code
                        if not oa_key:
                            oa_key = self.env['erp2oa.model.fields'].search([("sync_setting_id", "=", self.id),
                                                                             ("erp_relation_field", "=", field_key)],
                                                                            limit=1).oa_field_code
                        workflowRequestTableFields.append({
                            "fieldName": oa_key,
                            "fieldValue": order.get(field_key)
                        })
                    workflowRequestTableRecords.append({
                        "recordOrder": 0,
                        "workflowRequestTableFields": workflowRequestTableFields
                    })
                # 处理附件
                if self.is_enclosure:
                    if self.mes_model_id.code == 'CGDD':
                        gnbh = 'CG02A0'
                    else:
                        gnbh = ''
                    fj_sql = "SELECT PPWJJL_WJMC,PPWJJL_WJNR FROM PPWJGN,PPWJJL WHERE PPWJGN_GNBH = '%s' " \
                             "AND PPWJGN_LSBH = '%s' AND PPWJGN_WJBH = PPWJJL_WJBH" % (
                             gnbh, key)

                    fj_res = mssql.execQuery_fields(args={
                        "db_host": db_host,
                        "db_user": db_user,
                        "db_pwd": db_pwd,
                        "db_name": db_name,
                        "SQL": fj_sql
                    })
                    if fj_res.get('code') == 'success':
                        fj_values = []
                        fjs = fj_res.get('data')
                        if len(fjs) > 0:
                            for fj in fjs:
                                PPWJJL_WJNR = base64.b64encode(fj.get('PPWJJL_WJNR'))
                                wjnr = PPWJJL_WJNR.decode()
                                fj_values.append({
                                    "filePath": "base64:" + wjnr,
                                    "fileName": fj.get('PPWJJL_WJMC')
                                })
                            mainData.append({
                                "fieldName": self.oa_fjmc,
                                'fieldValue': fj_values
                            })
                        else:
                            continue

                fin_data.append({
                    'key': key,
                    'mainData': mainData,
                    'detailData': {
                        "tableDBName": self.oa_detail_table,
                        "workflowRequestTableRecords": workflowRequestTableRecords
                    }
                })
            _logger.info(fin_data)
            return fin_data

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


class Erp2oaSettingFields(models.Model):
    _name = "erp2oa.model.fields"
    _description = "同步字段对应设置"

    sync_setting_id = fields.Many2one("erp2oa.erp.model", string="同步设置", required=True, ondelete='cascade')
    erp_field_code = fields.Char(string="ERP字段数据库名", related='erp_field_name.field_code', store=True)
    erp_field_name = fields.Many2one('erp2oa.erp.table.field', string="ERP字段名")
    erp_field_type = fields.Selection([('master', '表头'), ('detail', '表体')], string='字段位置', required=True)
    oa_field_code = fields.Char(string="oa字段标识", required=True)
    erp_relation_table = fields.Char(string="关联表")
    erp_relation_field = fields.Char(string="关联字段")
    erp_relation_where = fields.Char(string="关联条件")

