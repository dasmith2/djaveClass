"""
The manager of any class that wants to periodically delete everything over
a month old should inherit from RmOldManager. The class itself should have a
created datetime field.
"""
from datetime import timedelta

from django.db import models
from util.timezone import now


class RmOldManager(models.Manager):
  def rm_old(self, days_ago=60, verbose=False):
    when = now() - timedelta(days=days_ago)
    which = self.filter(created__lt=when)
    if verbose:
      print('Deleting {} {}.'.format(which.count(), str(self.model)))
    which.delete()
