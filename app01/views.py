from django.shortcuts import render, redirect

from app01.myforms import LoginForm
from rbac import models
# Create your views here.


def login(request):
    err_msg = ""
    form_obj = LoginForm()
    if request.method == "POST":
        form_obj = LoginForm(request.POST)
        if form_obj.is_valid():
            username = form_obj.cleaned_data.get("user")
            pwd = form_obj.cleaned_data.get("password")
            user = models.User.objects.filter(username=username, password=pwd).first()
            if user:
                request.session["user"] = username  # 登陆成功，设置session
                # 获取这个人的所有权限，去重
                permissions = user.roles.all().values("permissions__url", "permissions__title",
                                                      "permissions__code").distinct()
                permission_list = []  # 拿到上面的queryset，遍历一个便于我们操作的数据类型
                permission_menu_list = []
                for permission in permissions:
                    permission_list.append(permission["permissions__url"])
                    #
                    if permission["permissions__code"] == "list":  # 如果是查看权限，就添加到权限菜单列表中
                        permission_menu_list.append({
                            "title": permission["permissions__title"],
                            "url": permission["permissions__url"]
                        })

                request.session["permission_list"] = permission_list  # 把所有权限存储在session中
                request.session["permission_menu_list"] = permission_menu_list  # 把所有的查看权限存储在session中

                next_url = request.GET.get("next")
                if next_url:
                    res = redirect(next_url)
                else:
                    res = redirect("/index/")
                return res
            else:
                err_msg = "用户名或者密码错误！"

    return render(request, "login.html", locals())


def index(request):
    return render(request, "index.html")


def log_out(request):
    request.session.flush()
    return redirect("/login/")