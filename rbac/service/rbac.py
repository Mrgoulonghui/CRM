#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect, HttpResponse


class PermissionMiddleware(MiddlewareMixin):

    def process_request(self, request):
        current_path = request.path  # 当前的路径
        white_url = ["/login/", "/index/", "/log_out/", "/admin/*"]  # 白名单
        for white_url_reg in white_url:
            ret = re.search(white_url_reg, current_path)
            if ret:
                return

        user = request.session.get("user", "")
        if not user:
            return redirect("/login/?next={}".format(current_path))

        # 权限认证
        permission_list = request.session.get("permission_list")
        for permission_reg in permission_list:
            permission_reg = "^{}$".format(permission_reg)
            # 不加开始 和结束，会导致添加，编辑等页面都匹配到查看页面，权限就会错误
            ret = re.search(permission_reg, current_path)  # 开始匹配
            if ret:  # 匹配到正常访问
                return
        return HttpResponse("无权限访问")  # 放在for循环外面，不然第一次没匹配到，直接return了，结束循环了





