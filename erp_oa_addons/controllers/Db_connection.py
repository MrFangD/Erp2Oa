# -*- coding: utf-8 -*-
"""
    @Version: V1.0
    @Time: 2021-07-26 13:43
    @Author: 全脂老猫
    @Describe:1、python连接SqlServer数据库的工具类
              2、需要注意的是：读取数据的时候需要decode('utf-8')，写数据的时候需要encode('utf-8')，这样就可以避免烦人的中文乱码或报错问题。
              3、Python操作SQLServer需要使用pymssql模块，使用pip install pymssql安装
"""
import pymssql
from odoo import http, SUPERUSER_ID, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class Mssql:
    # def __init__(self):
    #     # 数据库连接参数
    #     print('123')
    #     erp_system = http.request.env(user=SUPERUSER_ID)["roke.mes.erp.system"].search([("erp_type", "=", "sqlserver")], limit=1)
    #     self.host = erp_system.erp_url
    #     self.user = erp_system.user_name
    #     self.pwd = erp_system.password
    #     self.db = erp_system.db_name

    def getConnect(self, db_host, db_user, db_pwd, db_name):
        if not db_name or not db_host or not db_user or not db_pwd:
            return {'code': "error", "msg": "没有设置数据库信息"}
        try:
            self.conn = pymssql.connect(host=db_host, user=db_user, password=db_pwd, database=db_name, charset="utf8")
            cursor = self.conn.cursor()
            if not cursor:
                return {'code': "error", "msg": "连接数据库失败"}
            else:
                return {'code': "success", "msg": "连接成功", "data": cursor}
        except Exception as e:
            _logger.info('---数据库连接报错----')
            _logger.info(e)
            return {'code': "error", "msg": e}

    # sql查询
    def execQuery(self, **kwargs):
        kwargs = kwargs.get('args', '')
        db_host = kwargs.get('db_host', '')
        db_user = kwargs.get('db_user', '')
        db_pwd = kwargs.get('db_pwd', '')
        db_name = kwargs.get('db_name', '')
        sql = kwargs.get('SQL', '')
        cursor = self.getConnect(db_host, db_user, db_pwd, db_name)
        if cursor.get('code') =="error":
            return {'code': "error", "msg": cursor.get('msg')}
        else:
            cursor = cursor.get("data")
            cursor.execute(sql)
            resList = cursor.fetchall()  # 获取查询的所有数据
            self.conn.close()            # 查询完毕后必须关闭连接
            return {'code': "success", "msg": "获取成功", "data": resList}

    # sql查询,带字段名称
    def execQuery_fields(self, **kwargs):
        kwargs = kwargs.get('args', '')
        db_host = kwargs.get('db_host', '')
        db_user = kwargs.get('db_user', '')
        db_pwd = kwargs.get('db_pwd', '')
        db_name = kwargs.get('db_name', '')
        sql = kwargs.get('SQL', '')
        cursor = self.getConnect(db_host, db_user, db_pwd, db_name)
        if cursor.get('code') == "error":
            return {'code': "error", "msg": cursor.get('msg')}
        else:
            cursor = cursor.get("data")
            cursor.execute(sql)
            resList = cursor.fetchall()  # 获取查询的所有数据
            fields = [field[0] for field in cursor.description]
            # 序列化 成字典 zip  把两个可迭代对象合并成2维元组。然后用dict 转化为字典。
            res = [dict(zip(fields, result)) for result in resList]
            self.conn.close()  # 查询完毕后必须关闭连接
            return {'code': "success", "msg": "获取成功", "data": res}

    # 增删改
    def execNonQuery(self, **kwargs):
        kwargs = kwargs.get('args', '')
        db_host = kwargs.get('db_host', '')
        db_user = kwargs.get('db_user', '')
        db_pwd = kwargs.get('db_pwd', '')
        db_name = kwargs.get('db_name', '')
        sql = kwargs.get('SQL', '')
        cursor = self.getConnect(db_host, db_user, db_pwd, db_name)
        try:
            if cursor.get('code') == "error":
                return {'code': "error", "msg": cursor.get('msg')}
            else:
                cursor = cursor.get("data")
                cursor.execute(sql)
        except Exception as e:
            _logger.info('执行SQL失败,失败原因%s' %e)
            self.conn.rollback()
            self.conn.close()
            return {'code': "error", "msg": e}
        else:
            self.conn.commit()
            self.conn.close()
            return {'code': "success", "msg": 'SQL执行成功'}

    # 批量执行增删改
    def batchexecNonQuery(self, **kwargs):
        kwargs = kwargs.get('args', '')
        db_host = kwargs.get('db_host', '')
        db_user = kwargs.get('db_user', '')
        db_pwd = kwargs.get('db_pwd', '')
        db_name = kwargs.get('db_name', '')
        sqls = kwargs.get('SQL', '')
        cursor = self.getConnect(db_host, db_user, db_pwd, db_name)
        if cursor.get('code') == "error":
            return {'code': "error", "msg": cursor.get('msg')}
        else:
            cursor = cursor.get("data")
            for sql in sqls:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    _logger.info('执行SQL失败,失败原因%s' % e)
                    self.conn.rollback()
                    self.conn.close()
                    return {'code': "error", "msg": e}
                else:
                    _logger.info('执行SQL成功')
            self.conn.commit()
            self.conn.close()
            return {'code': "success", "msg": 'SQL执行成功'}

    # 流水号处理
    def execQueryLsh(self, **kwargs):
        kwargs = kwargs.get('args', '')
        db_host = kwargs.get('db_host', '')
        db_user = kwargs.get('db_user', '')
        db_pwd = kwargs.get('db_pwd', '')
        db_name = kwargs.get('db_name', '')
        sql = kwargs.get('SQL', '')
        cursor = self.getConnect(db_host, db_user, db_pwd, db_name)
        try:
            if cursor.get('code') == "error":
                return {'code': "error", "msg": cursor.get('msg')}
            else:
                cursor = cursor.get("data")
                cursor.execute(sql)
                resList = cursor.fetchall()
        except Exception as e:
            _logger.info('执行SQL失败,失败原因%s' %e)
            self.conn.rollback()
            self.conn.close()
            return {'code': "error", "msg": e}
        else:
            self.conn.commit()
            self.conn.close()
            return {'code': "success", "msg": "获取成功", "data": resList}