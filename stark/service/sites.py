#!/usr/bin/env python
# -*- coding:utf8 -*-
from django.conf.urls import url
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.urls import reverse
# 分页
from stark.utils.mypage import MyPage
from django import forms
# 删除视图中，返回的值
from django.http import JsonResponse
# search功能需要Q
from django.db.models import Q
# filter
from copy import deepcopy


class ShowList(object):
    """
    查看的视图函数中的功能 提出来的类
    """

    def __init__(self, config_obj, request, all_data):
        self.config_obj = config_obj  # 在ModelStark类中实例化的时候，传入的第一个参数self
        self.request = request  # 传入的第二个参数request
        self.all_data = all_data  # 传入的第三个参数 所有的数据

        # 分页相关
        self.page_obj = MyPage(request.GET.get("page", 1), all_data.count(), request, per_page_data=10)
        self.page_data = all_data[self.page_obj.start:self.page_obj.end]  # 每页的数据
        self.page_html = self.page_obj.ret_html()  # 分页的html部分

    def get_header(self):
        """
        表头展示 ["书名","价格"]
        :return:
        """
        head_list = []
        for field in self.config_obj.new_list_display():
            if callable(field):  # 如果是函数，就执行，而且是表头，传参is_header=True
                val = field(self.config_obj, is_header=True)
            else:
                if field == "__str__":
                    val = self.config_obj.model_name.upper()
                else:
                    # 这个方法可以通过字段（字符串形式）获取到模型表中对应格那个字段对象
                    # title = models.CharField(max_length=32, verbose_name="书名")即拿到title这个CharField类的对象
                    # title对象可以.的方式拿到verbose_name
                    if hasattr(self.config_obj.model, field):
                        field_obj = self.config_obj.model._meta.get_field(field)
                        val = field_obj.verbose_name
                    else:
                        val = field
                        # 这里表示如果注册的list_display中的字段在表中没有对应的字段，就去他传过来的字段名为表名
            head_list.append(val)
        return head_list

    def get_body(self):
        """
        表内容展示，构建成这样的列表，然后去渲染 [["title", "price"], ["title", "price"]]
        :return:
        """
        all_data_list = []
        for obj in self.page_data:  # 循环分页后的每页的数据
            temp = []
            for field in self.config_obj.new_list_display():  # ["title", "price", edit]
                if callable(field):
                    val = field(self.config_obj, obj)
                else:
                    if hasattr(obj, field):
                        if field == "__str__":  # 如果使用的是默认配置，
                            val = getattr(obj, field)
                        else:
                            # django.db.models.fields.related.ManyToManyField 多对多字段
                            field_obj = self.config_obj.model._meta.get_field(field)
                            from django.db.models.fields.related import ManyToManyField
                            if isinstance(field_obj, ManyToManyField):
                                obj_list = getattr(obj, field).all()
                                val = ",".join([str(obj) for obj in obj_list])
                            else:
                                val = getattr(obj, field)  # getattr(book, "title") getattr(book, "price")
                                # 如果该字段在用户list_display_links自定义中，那么把该字段变为a标签
                                if field in self.config_obj.list_display_links:
                                    change_url = self.config_obj.get_change_url(obj)
                                    val = mark_safe("<a href='{}'>{}</a>".format(change_url, val))
                    else:
                        # 这里表示如果注册的list_display中的字段在表中没有对应的字段，表内内容，显示为None
                        val = None
                temp.append(val)  # ["西游记"]  ["西游记", 123]
            all_data_list.append(temp)
        return all_data_list

    def get_new_action(self):
        """
        把actions中的函数列表，格式换成我们更容易使用的类型
        :return:
        """
        new_action = [{"text": self.config_obj.patch_delete.desc, "name": self.config_obj.patch_delete.__name__}]
        for action in self.config_obj.actions:
            new_action.append({"text": action.desc, "name": action.__name__})
        return new_action

    def get_list_filter_links(self):
        list_filter_links = {}
        # params = deepcopy(self.request.GET)  # 注意，第一次取参数，不能放在这里，不然每一次的参数都会保留，
        # 比如，生成publish的时候，会添加publish=1,后面到生成authors的时候，也会保留那个publish=1,所以第一次的authors
        # 的参数会变成publish=1&authors=1,我们要的是只有authors=1，所以要放在每个字段循环的时候去拿参数
        for field in self.config_obj.list_filter:
            params = deepcopy(self.request.GET)  # 参数要放在这里拿
            current_field_pk = self.request.GET.get(field, 0)  # 后面做显示选中时使用，126行; 取不到默认为0
            # 首先通过用户定义的那个字段字符串，获取对应的字段对象
            field_obj = self.config_obj.model._meta.get_field(field)
            from django.db.models.fields.related import ForeignKey
            from django.db.models.fields.related import ManyToManyField

            # 判断一下该字段是不是多对多，或者外键的关系，不是的话field_obj.rel.to会报错
            if isinstance(field_obj, ForeignKey) or isinstance(field_obj, ManyToManyField):
                # 根据该方法获取该字段对应在那个模型表那个类
                rel_model = field_obj.rel.to  # 只有外键和多对多关系，才有该方法
                rel_model_queryset = rel_model.objects.all()

                temp = []
                for obj in rel_model_queryset:  # 循环这个字段下的所有的对象
                    params[field] = obj.pk  # 第一次页面的url，参数是字段名=对应的id 如：publish=1或者authors=1
                    if obj.pk == int(current_field_pk):
                        link = "<a href='?{}' class='filter_select'>{}</a>".format(params.urlencode(), str(obj))
                    else:
                        link = "<a href='?{}'>{}</a>".format(params.urlencode(), str(obj))  # 创建a标签,url使用反向保留参数
                    temp.append(link)  # 把该对象下的所有的a标签添加到这个小列表中
                list_filter_links[field] = temp  # 构建这样的字典 {"publish": [link, link]},交给模板去渲染
        return list_filter_links


# 仿照django_admin自定义一个类似的组件
class ModelStark(object):
    """
    默认的配置类
    """
    list_display = ["__str__"]
    model_form_class = []
    list_display_links = []
    search_fields = []
    actions = []
    list_filter = []

    def __init__(self, model):
        self.model = model  # 这一步完成了把模型表赋值在self中，即self.model

        # 获取当前的模型表名和app名
        self.model_name = self.model._meta.model_name
        self.app_name = self.model._meta.app_label
        self.res = {}  # 删除页面的响应

    # 获取 增 删 改 查 url:
    def get_list_url(self):
        _url = reverse("{}_{}_list".format(self.app_name, self.model_name))
        return _url

    def get_add_url(self):
        _url = reverse("{}_{}_add".format(self.app_name, self.model_name))
        return _url

    def get_change_url(self, obj):
        _url = reverse("{}_{}_change".format(self.app_name, self.model_name), args=(obj.pk, ))
        return _url

    def get_delete_url(self, obj):
        _url = reverse("{}_{}_delete".format(self.app_name, self.model_name), args=(obj.pk,))
        return _url

    # 自定义函数列
    def edit(self, obj=None, is_header=False):
        if is_header:
            return "编辑"
        return mark_safe("<a href='{}' class='btn btn-warning'>"
                         "<i class='fa fa-pencil-square-o fa-fw' aria-hidden='true'></i>编辑</a>"
                         .format(self.get_change_url(obj)))

    def del_view(self, obj=None, is_header=False):
        if is_header:
            return "删除"
        # return mark_safe("<a href='{}' class='del_btn' del_id='{}'>"
        #                  "<i class='fa fa-trash fa-fw' aria-hidden='true'></i>删除</a>"
        #                  .format(self.get_delete_url(obj), obj.pk))

        # 使用sweetalert插件，自定义一个按钮
        return mark_safe("<button class='btn btn-danger del_btn' del_id='{}' type='button'>"
                         "<i class='fa fa-trash fa-fw' aria-hidden='true'></i>删除</button>".format(obj.pk))

    def checkbox(self, obj=None, is_header=False):
        if is_header:
            return "选择"
        return mark_safe("<input type='checkbox' value='{}' name='pk_list'>".format(obj.pk))

    def patch_delete(self, queryset):
        queryset.delete()
    patch_delete.desc = "批量删除"

    # 把我们的自定义的删除，编辑，单选框等自定义函数添加到list_display中，
    # 这样无论是默认的配置类，还是用户自定义的配置类，这些就都有了
    def new_list_display(self):
        temp = []
        temp.extend(self.list_display)  # 这里的list_display可能是用户自己的，也有可能是默认的

        if not self.list_display_links:  # 如果没有值，说明使用的是默认的配置类中的 list_display_links，
            # 把编辑链接添加进去，否则不添加编辑，使用用户自己的 list_display_links，见77行
            temp.append(ModelStark.edit)

        temp.append(ModelStark.del_view)
        # 需要注意的是 使用类去调用该方法，因为下面使用的时候，传了参数self,
        # 如果使用self调用该方法，下面就不用传self了
        temp.insert(0, ModelStark.checkbox)
        return temp

    def get_model_form_class(self):
        if self.model_form_class:  # 如果有值，说明用户自定义了ModelForm,我们就要使用用户自己的
            ModelFormClass = self.model_form_class
        else:  # 如果没有就是用我们自己的默认ModelFormClass
            class ModelFormClass(forms.ModelForm):
                class Meta:
                    model = self.model
                    fields = "__all__"
        return ModelFormClass

    def get_search_conditions(self, request):
        """
        获取search的查询条件的 方法
        :param request:
        :return:
        """
        # search功能
        # 重要的语法
        # 该语法的特点是 Q()对象的children中append条件，条件为一个元组，（字段字符串形式，条件）
        condition = request.GET.get("condition", "")
        # 实例化一个Q对象
        search_obj = Q()
        # 多个append(),之间为 “或” 的关系，默认为“且”的关系，加上  search_obj.connector = "or"变为“或”
        search_obj.connector = "or"
        if condition:
            for search_field in self.search_fields:
                # 循环每一个字段，把字段名，和对应的条件加进去
                search_obj.children.append((search_field + "__icontains", condition))
                # 做字符串拼接，做模糊查询，如 "title"+"__icontains" 得到---> "title__icontains"
        # 如果取不到condition, 那么就传一个空的Q对象，则为查询所有数据
        return search_obj

    def get_filter_conditions(self, request):
        """
        获取filter过滤条件的 方法
        :param request:
        :return:
        """
        filter_obj = Q()
        for key, val in request.GET.items():
            # key 为publish, val 为 1
            if hasattr(self.model, key):  # 判断当前模型表类中有没有该字段
                filter_obj.children.append((key, val))
        return filter_obj

    def get_new_form(self, form_obj):
        # from django.forms.boundfield import BoundField 这个类中的初始化方法中 有 self.field  self.name
        for form in form_obj:
            # 打印form是该类的str方法,显示为标签形式
            # print(type(form))  # 全是这个类 <class 'django.forms.boundfield.BoundField'>
            # print(form.field)  .field方法 显示原型
            # 对应的类
            # <django.forms.fields.CharField object at 0x00000229B7DB75C0>
            # <django.forms.fields.DateField object at 0x00000229B7DB7630>
            # <django.forms.fields.DecimalField object at 0x00000229B7DB76A0>
            # <django.forms.models.ModelChoiceField object at 0x00000229B7DB7710>
            #  这个ModelChoiceField类是 OneToOneField 和 ModelMultipleChoiceField 的父类
            # <django.forms.models.ModelMultipleChoiceField object at 0x00000229B7DB7780>
            from django.forms.models import ModelChoiceField
            if isinstance(form.field, ModelChoiceField):  # 如果是多对多字段,
                form.is_pop = True  # 就给form添加一个自定义的属性is_pop,模板根据该属性决定是否渲染那个 加号

                # 这里需要注意,我们点加号是要添加 出版社或者作者,所以,那个url需要拼接;
                # 并且,我们在添加完之后需要把那个数据,返回到我们添加书籍的页面上;
                # 所以我们需要做一些自定义属性;

                # print(form.name)  # title  publishDate  price  publish  authors 所有字段的字符串名
                # 根据字段字符串名称获取字段对象,在获取对应的模型表
                field_obj = self.model._meta.get_field(form.name)  # 根据字段字符串名称获取字段对象
                rel_model = field_obj.rel.to  # 根据字段对象获取对应的模型表 类
                rel_model_name = rel_model._meta.model_name
                rel_app_name = rel_model._meta.app_label
                # 反向解析,获取要添加的url
                _url = reverse("{}_{}_add".format(rel_app_name, rel_model_name))
                # 把这个url做成form的自定义属性
                form.url = _url
                # 在做一个用于返回数据,做dom操作时,具体给那个dom,添加,的自定义属性
                form.pop_back_id = "id_" + form.name  # 因为form组件生成的标签 id值都是  id_"字段名",所以我们这么拼接
        return form_obj

    def view_list(self, request):
        """
        print(self)  # self就是配置类本身
        print(self.model)  # self.model就是模型表

        :param request:
        :return:
        """
        model_name = self.model_name
        app_name = self.app_name
        err_msg = ""

        if request.method == "POST":
            action = request.POST.get("action")  # 获取的select标签提交过来的函数名， 字符串形式
            pk_list = request.POST.getlist("pk_list")  # 获取到所有的选中的checkbox标签提交过来的数据id
            queryset = self.model.objects.filter(pk__in=pk_list)  # 把列表形式的数据 转换为我们需要传参的queryset类型
            if hasattr(self, action):  # 如果有，获取函数并执行
                action = getattr(self, action)  # 反射获取配置类中那个自定义的函数，然后去执行该函数
                action(queryset)
            else:
                err_msg = mark_safe("<i class='fa fa-exclamation-triangle fa-2x fa-fw' aria-hidden='true'></i>"
                                    "您必须先选择一项操作或者一个数据")

        # 注意传参数，这里我们反射是通过，那个配置类对象找到的方法，所以调用执行就相当于是使用self.action,所以不用传参数self

        # 这里也不用返回一个HttpResponse对象,不返回 代码继续往下走，还是渲染我们的查看页面，但是数据库中的数据已经修改，
        # 也就达到了操作的目的了
        # 把单独的功能放到ShowList类中，程序解耦
        all_data = self.model.objects.all()  # 所有的数据
        # 获取search条件
        search_obj = self.get_search_conditions(request)
        # 获取filter条件
        filter_obj = self.get_filter_conditions(request)
        # 根据查询条件，把筛选后的数据传过去，分页显示
        all_data = all_data.filter(search_obj).filter(filter_obj)

        # 错误做法，使用字段，获取对应的字段对象，然后去筛选
        # for field in self.search_fields:
        #     field_obj = self.model._meta.get_field(field)
        # all_data.filter(field_obj=condition)
        #  这中方法报错，找不到对应的字段 Cannot resolve keyword 'field_obj' into field

        show_list = ShowList(self, request, all_data)
        add_url = self.get_add_url()  # 添加按钮使用的url
        list_url = self.get_list_url()  # filter中all的url

        # # 拿着这个条件，页面刷新后，在渲染回去
        condition = request.GET.get("condition", "")

        return render(request, "stark/view_list.html", locals())  # 这里我们把ShowList这个类的对象show_list传到模板去渲染

    def add(self, request):
        form_obj = self.get_model_form_class()()  # 获取ModelFormClass类，然后实例化一个form对象
        model_name = self.model_name
        if request.method == "POST":
            form_obj = self.get_model_form_class()(request.POST)
            if form_obj.is_valid():
                obj = form_obj.save()  # modelform直接save,返回值就是创建的那条对象
                if request.GET.get("pop", ""):  # 如果能拿到值,说明是pop页面的添加
                    text = str(obj)  # 要渲染回去的那个新添加的对象
                    pk = obj.pk  # 添加的那条数据的id
                    return render(request, "stark/pop.html", locals())  # 跳转到pop页面进行操作
                return redirect(self.get_list_url())  # 否则表示正常添加页面,正常跳转到查看页面
        form_obj = self.get_new_form(form_obj)  # 获取我们处理过的form
        return render(request, "stark/add.html", locals())

    def delete(self, request, pk):
        if request.method == "POST":
            self.res["code"] = 0
            self.res["msg"] = self.get_list_url()  # 把查看页面的url返回回去，用于跳转
            self.model.objects.filter(pk=pk).delete()
        return JsonResponse(self.res)

    def change(self, request, pk):
        model_name = self.model_name
        change_obj = self.model.objects.filter(pk=pk).first()
        form_obj = self.get_model_form_class()(instance=change_obj)  # 注意instance传值
        if request.method == "POST":
            form_obj = self.get_model_form_class()(request.POST, instance=change_obj)
            if form_obj.is_valid():
                form_obj.save()
                return redirect(self.get_list_url())
        form_obj = self.get_new_form(form_obj)  # 跟新 form_obj,我们处理过的
        return render(request, "stark/change.html", locals())

    def extra_url(self):
        """
        额外的url的接口
        :return:
        """
        return []

    def get_urls(self):
        temp = [
                url(r"^$", self.view_list, name="{}_{}_list".format(self.app_name, self.model_name)),
                url(r"add/$", self.add, name="{}_{}_add".format(self.app_name, self.model_name)),
                url(r"(\d+)/change/$", self.change, name="{}_{}_change".format(self.app_name, self.model_name)),
                url(r"(\d+)/delete/$", self.delete, name="{}_{}_delete".format(self.app_name, self.model_name)),
            ]
        temp.extend(self.extra_url())  # 把额外的url接口添加进去，如果用户自定义了配置类，就用用户自己的extra_url()方法
        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None


class AdminSite(object):
    """
    stark组件的全局类
    """

    def __init__(self):
        self._registry = {}  # 设置 那个存储不同app注册的模型表

    def register(self, model, admin_class=None):

        # 配置默认的样式类，为我们自己的ModelStark类
        if not admin_class:
            admin_class = ModelStark

        self._registry[model] = admin_class(model)

    def get_urls(self):
        temp = []
        for model, config_obj in self._registry.items():
            model_name = model._meta.model_name  # 拿到模型表名
            app_name = model._meta.app_label  # 拿到app名称
            temp.append(url(r"^{}/{}/".format(app_name, model_name), config_obj.urls))
            # 这里注意，是使用的config_obj.urls，config_obj就是我们的配置类，把二级分发路由写到配置类中，
            # 把对应的视图函数也写在配置类中，这样我们在调用试图函数时，self就是我们的配置类（config_obj），
            # 而且，每一次循环就是其对应的表的配置类，
            # 而self.model就是我们在实例化配置类的时候添加进去的，也就是我们对应的模型表类
        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None  # 路由分发必须返回三个参数： [], None, None


# 单例模式， 每一个app下的stark.py中注册时都是同一个site对象，调用的同一个_registry那个字典，往里面添加键值对
site = AdminSite()


