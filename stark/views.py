from django.shortcuts import render, redirect, HttpResponse

# Create your views here.


def view_list(request):
    return HttpResponse("view_list")


def add(request):
    return HttpResponse("add")


def delete(request, pk):
    return HttpResponse("delete")


def change(request, pk):
    return HttpResponse("change")