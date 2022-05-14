# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2022-04-04 14:11
    @Author: 全脂老猫
    @Describe:接收泛微的审批结果并回写相应的ERP单据
"""
import logging
from odoo import api, http, SUPERUSER_ID, _
from odoo.addons.erp_oa_addons.controllers import Db_connection
mssql = Db_connection.Mssql()

_logger = logging.getLogger(__name__)

db_link = []


class ApproveController(http.Controller):

    def check_approval_authority(self, business_id, serial_number, ppproval_node, approver):
        """
        检查当前用户，当前节点是否有审批权限
        business_id--业务ID（例：CGDD）； serial_number：单据流水
        ppproval_node：审批节点；approver：审批人
        :return: 1--有权  -1--无权
        """
        SQL = """SELECT count(1) FROM PPSPMXSJ,PPSPZSJ WHERE PPSPMXSJ_YWID = '%s' AND PPSPMXSJ_DJLS= '%s' 
                AND PPSPMXSJ_SPJD= '%s' AND PPSPMXSJ_SPR= '%s' AND PPSPZSJ_DJLS = PPSPMXSJ_DJLS 
                AND PPSPMXSJ_YWID = PPSPZSJ_YWID """ % (business_id, serial_number, ppproval_node, approver)

        reslist = mssql.execQuery(args={
            "db_host": db_link[0],
            "db_user": db_link[1],
            "db_pwd": db_link[2],
            "db_name": db_link[3],
            "SQL": SQL
        })
        _logger.info(reslist)
        if reslist.get('code') == 'success':
            reslist = reslist.get('data')
            if int(reslist[0][0]) > 0:
                return 1
            else:
                return -1
        else:
            raise -1

    @http.route(['/oa2erp/approve_result'], methods=['POST', 'OPTIONS'], type='json', auth='none', csrf=False, cors='*')
    def approve_result(self):
        """
        接收OA的审批结果
        business_id--业务ID（例：CGDD）； serial_number：单据流水
        ppproval_node：审批节点；approver：审批人
        approval_result审批结果
        :return:
        """
        _logger.info('审批结果')
        _logger.info(http.request.jsonrequest)
        business_id = http.request.jsonrequest.get("business_id")
        serial_number = http.request.jsonrequest.get("serial_number")
        ppproval_node = http.request.jsonrequest.get("ppproval_node")
        approver = http.request.jsonrequest.get("approver")
        approval_result = http.request.jsonrequest.get("approval_result")

        # 获取数据库连接信息
        erp_system = http.request.env(user=SUPERUSER_ID)["erp2oa.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
        if not erp_system:
            return {
                'code': -1,
                'message': '未获取到PS系统相关的配置信息，请联系系统管理员'
            }

        erp_system = http.request.env(user=SUPERUSER_ID)["erp2oa.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
        if not erp_system:
            return {'code': -1, 'msg': '获取数据库连接信息失败!'}
        db_host = erp_system.erp_url
        db_user = erp_system.user_name
        db_pwd = erp_system.password
        db_name = erp_system.db_name

        # 处理业务单据SQL
        if int(approval_result) == 1:
            sql = """ UPDATE CGDD1 SET CGDD1_SHBZ = '1' WHERE CGDD1_LSBH = '%s' """ % (serial_number)
        elif int(approval_result) == 2:
            sql = """ UPDATE CGDD1 SET CGDD1_SHBZ = '0', CGDD1_DDMC = '审批未通过,请修改' WHERE CGDD1_LSBH = '%s' """ % (serial_number)

        reslist = mssql.execNonQuery(args={
            "db_host": db_host,
            "db_user": db_user,
            "db_pwd": db_pwd,
            "db_name": db_name,
            "SQL": sql
        })

        if reslist.get('code') == 'success':
            return {"code": 1, "message": "审批回写成功"}
        else:
            return {"code": -1, "message": "审批回写失败"}

