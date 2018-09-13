#!/usr/bin/env python
# -*- coding:utf8 -*-

from app01 import models
from stark.service.sites import site, ModelStark
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import HttpResponse, redirect, render
from django.http import JsonResponse


site.register(models.School)
site.register(models.Order)
site.register(models.Department)
site.register(models.UserInfo)
site.register(models.Course)


class ClassConfig(ModelStark):

    def display_start_data(self, obj=None, is_header=False):
        if is_header:
            return "开班日期"
        return obj.start_date.strftime("%Y-%m-%d")

    list_display = ["school", "course", "semester", display_start_data, "teachers", "tutor"]
    # list_display_links = ["course", "school"]


site.register(models.ClassList, ClassConfig)


class CustomerConfig(ModelStark):

    def display_gender(self, obj=None, is_header=False):
        if is_header:
            return "性别"
        return obj.get_gender_display  # 固定写法， get_字段名_display
        # 获取表中字段（以choices的元组形式存的(1,"男")的真实数据，数据库存的1，我们需要的是那个"男"

    def display_status(self, obj=None, is_header=False):
        if is_header:
            return "状态"
        return obj.get_status_display

    def display_course(self, obj=None, is_header=False):
        if is_header:
            return "咨询课程"
        courses = obj.course.all()
        course_links_list = []
        for course in courses:
            course_links_list.append(
                "<a href='/stark/app01/course/'>{}</a>".format(course.name)
            )
        return mark_safe(" ".join(course_links_list))

    list_display = ["name", display_gender, "consultant", display_course, display_status]


site.register(models.Customer, CustomerConfig)
site.register(models.ConsultRecord)


class StudentConfig(ModelStark):

    def display_score(self, obj=None, is_header=False):
        if is_header:
            return "详细信息"
        return mark_safe("<a href='/stark/app01/student/{}/info/'>详细信息</a>".format(obj.pk))

    list_display = ["customer", "class_list", display_score]

    def extra_url(self):
        return [url(r"(\d+)/info/$", self.student_info)]

    def student_info(self, request, sid):
        if request.is_ajax():
            print(666)
            # 返回需要制作成柱状图的数据
            cls_id = request.GET.get("cls_id")
            # 该学生在该班级下的所有记录
            student_study_record_obj_list = models.StudentStudyRecord.objects.filter(
                student=sid, classstudyrecord__class_obj=cls_id)
            # 构建柱状图所需要的数据类型
            data = [["day".format(student_study_record_obj.classstudyrecord.day_num), student_study_record_obj.score]
                    for student_study_record_obj in student_study_record_obj_list]
            return JsonResponse(data, safe=False)

        student_obj = models.Student.objects.filter(pk=sid).first()
        return render(request, "student_info.html", locals())


site.register(models.Student, StudentConfig)


class ClassStudyRecordConfig(ModelStark):

    def display_info(self, obj=None, is_header=False):
        if is_header:
            return "详细信息"
        return mark_safe("<a href='/stark/app01/studentstudyrecord/?classstudyrecord={}'>详细信息</a>".format(obj.pk))

    def handle_score(self, obj=None, is_header=False):
        if is_header:
            return "录入成绩"
        return mark_safe("<a href='{}/record_score/'>录入成绩</a>".format(obj.pk))

    def extra_url(self):
        """
        录入成绩的url
        :return:
        """
        return [url(r"(\d+)/record_score/$", self.record_score)]

    def record_score(self, request, pk):
        """
        录入成绩的视图函数
        :param request:
        :param pk:
        :return:
        """
        if request.is_ajax():
            # ajax修改成绩，批语
            action = request.POST.get("action")  # score或者homework_note
            s_study_id = request.POST.get("s_study_id")  # 对应的学生的学习记录 的id
            val = request.POST.get("val")  # 对应的值，score或者homework_note
            print(action, s_study_id, val)
            models.StudentStudyRecord.objects.filter(pk=s_study_id).update(**{action: val})
            # **{action: val} 等同于 action=val传值
            return HttpResponse("ok")

        if request.method == "POST":
            print(request.POST)
            # <QueryDict: {'csrfmiddlewaretoken': ['JwqRhYnk7x8rwuCsGkCZ7azddWe9hanatmKqaiZ8iIufnqwnhw6NZiVktvyS4vh5'],
            # 'score_1': ['90'], 'homework_note_1': ['454'], 'score_4': ['80'], 'homework_note_4': ['123']}>
            dic = {}
            for key, val in request.POST.items():
                if key == "csrfmiddlewaretoken":
                    continue
                field, student_study_id = key.rsplit("_", 1)  # 从右分割，只分割一次
                #  这样写可以，但是每个记录都要跟新2次，不好
                # models.StudentStudyRecord.objects.filter(pk=student_study_id).update(**{field: val})

                # 我们这样写，构建一个这样的字典
                '''
                {
                  1:{score:50,homework_note:12323},
                  2:{score:80,homework_note:456},
                }

                '''

                if student_study_id not in dic:
                    dic[student_study_id] = {field: val}  # 不在，先创建字段
                else:
                    dic[student_study_id][field] = val  # 在，直接添加一个键值对
            print(dic)
            for pk, data in dic.items():
                models.StudentStudyRecord.objects.filter(pk=pk).update(**data)
            return redirect(request.path)  # 往当前页面跳转

        class_study_record_obj = models.ClassStudyRecord.objects.filter(pk=pk).first()  # 班级学习记录对象
        student_study_obj_list = class_study_record_obj.studentstudyrecord_set.all()  # 对应班级学习记录的学生学习记录对象
        score_choices = models.StudentStudyRecord.score_choices  # 成绩选项

        return render(request, "record_score.html", locals())

    list_display = ["class_obj", "day_num", "teacher", "homework_title", display_info, handle_score]

    def patch_init(self, queryset):
        for class_stu_obj in queryset:
            student_obj_list = class_stu_obj.class_obj.student_set.all()  # 外键关系，先正向，在反向查询 表名小写_set，
            # print(student_obj_list)  # 拿到所有的学生对象
            student_stu_obj_list = []
            for student_obj in student_obj_list:  # 先创建所有的学生学习记录对象，然后在批量入库；
                student_stu_obj_list.append(models.StudentStudyRecord(student=student_obj,  # 只需添加这两个字段，其他字段都可为空
                                                                      classstudyrecord=class_stu_obj))
            models.StudentStudyRecord.objects.bulk_create(student_stu_obj_list)  # 批量创建

    patch_init.desc = "创建关联班级所有学生的初始记录"
    actions = [patch_init]


site.register(models.ClassStudyRecord, ClassStudyRecordConfig)


class StudentStudyRecordConfig(ModelStark):

    def patch_late(self, queryset):
        """
        批量修改 学生的出勤 为请假
        :param queryset:
        :return:
        """
        queryset.update(record="vacate")
    patch_late.desc = "请假"
    actions = [patch_late]

    def display_record(self, obj=None, is_header=False):
        if is_header:  # 这里使用ajax发送请求的代码 放在头部,避免放在内容中,每一条记录都有script标签,修改一次,都发请求
            # 在头部，只会生成一个Script标签
            jquery_ele = "<script src='https://cdn.bootcss.com/jquery/3.3.1/jquery.min.js'></script>"
            script_start = "<script>"
            script_ele = "$(function () {" \
                         "$('.record').change(function () {" \
                         "var edit_id = $(this).attr('pk');" \
                         "var val = $(this).val();" \
                         "$.ajax({" \
                         "url: '/stark/app01/studentstudyrecord/' + edit_id + '/edit_record/'," \
                         "type: 'post'," \
                         "data: " \
                         "{csrfmiddlewaretoken:$('[name=csrfmiddlewaretoken]').val()," \
                         "record: val}," \
                         "success:function (res) {" \
                         "console.log(res)" \
                         "}" \
                         "}) " \
                         "})})"
            script_end = "</script>"
            return mark_safe("出勤情况" + jquery_ele + script_start + script_ele + script_end)
        select_ele = "<select class='record' name='record' pk='{}'>".format(obj.pk)
        record_choices = obj.record_choices
        option_ele = ""
        for choice_tuple in record_choices:
            if obj.record == choice_tuple[0]:
                option_ele += "<option value='{}' selected>{}</option>".format(choice_tuple[0], choice_tuple[1])
            else:
                option_ele += "<option value='{}'>{}</option>".format(choice_tuple[0], choice_tuple[1])
        select_end = "</select>"

        return mark_safe(select_ele + option_ele + select_end)

    def extra_url(self):
        """
        修改出勤记录的额外url
        :return:
        """
        temp = []
        temp.append(url(r"(\d+)/edit_record/$", self.edit_record),)
        return temp

    def edit_record(self, request, pk):
        """
        ajax发送请求修改出勤记录,的视图函数
        :param request:
        :param pk:
        :return:
        """
        record = request.POST.get("record")
        models.StudentStudyRecord.objects.filter(pk=pk).update(record=record)  # ajax发送请求修改出勤记录
        return HttpResponse("ok")

    def display_score(self, obj=None, is_header=False):
        if is_header:
            return "成绩"
        return obj.get_score_display

    list_display = ["student", "classstudyrecord", display_record, display_score]


site.register(models.StudentStudyRecord, StudentStudyRecordConfig)


