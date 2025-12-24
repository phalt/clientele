from django.db import models


class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username
