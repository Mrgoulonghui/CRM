#!/usr/bin/env python
# -*- coding:utf8 -*-

from django import forms


class LoginForm(forms.Form):
    user = forms.CharField(
        max_length=32,
        label="用户名",
        error_messages={
            "required": "用户名不能为空",
        },
        widget=forms.widgets.TextInput(
            attrs={"class": "form-control"}
        )
    )
    password = forms.CharField(
        max_length=16,
        label="密码",
        error_messages={
            "required": "密码不能为空",
        },
        widget=forms.widgets.PasswordInput(
            attrs={"class": "form-control"}
        )
    )

