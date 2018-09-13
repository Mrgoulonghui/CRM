#!/usr/bin/env python
# -*- coding:utf8 -*-
from rbac import models
from stark.service.sites import site, ModelStark

site.register(models.User)
site.register(models.Role)


class PermissionConfig(ModelStark):
    list_display = ["title", "url", "code"]


site.register(models.Permission, PermissionConfig)

