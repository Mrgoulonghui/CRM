from django.db import models

# Create your models here.


class User(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=16)
    roles = models.ManyToManyField(to="Role")

    def __str__(self):
        return self.username


class Role(models.Model):
    title = models.CharField(max_length=32)
    permissions = models.ManyToManyField(to="Permission")

    def __str__(self):
        return self.title


class Permission(models.Model):
    url = models.CharField(max_length=128)
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)

    def __str__(self):
        return self.title
