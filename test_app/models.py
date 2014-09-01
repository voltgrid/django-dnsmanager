from django.db import models
from django.contrib.auth.models import User


class Domain(models.Model):

    user = models.ForeignKey(User, related_name='domains')
    name = models.CharField(max_length=253, unique=True, help_text='Domain Name')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return "%s" % self.name