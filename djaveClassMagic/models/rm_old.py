""" Run rm_old daily. It'll find all your classes with an objects attribute
that's an RmOldManager, and run rm_old on them. """
from datetime import timedelta

from django.db import models
from djaveClassMagic.find_models import all_models
from djaveDT import now


def rm_old(verbose=False):
  for cls in find_rm_old_classes():
    cls.objects.rm_old(verbose=verbose)


def find_rm_old_classes():
  rm_old_classes = []
  for cls in all_models():
    if hasattr(cls, 'objects'):
      if isinstance(cls.objects, RmOldManager):
        rm_old_classes.append(cls)
  return rm_old_classes


class RmOldManager(models.Manager):
  """
  The manager of any class that wants to periodically delete everything over
  a month old should inherit from RmOldManager. The class itself should have a
  created datetime field.

  Then when you call djaveClassMagic.models.rm_old.rm_old it'll rm_old from your new
  class now too."""
  def keep_for_days(self):
    return 60

  def rm_old(self, days_ago=None, verbose=False):
    days_ago = days_ago or self.keep_for_days()
    when = now() - timedelta(days=days_ago)
    which = self.filter(created__lt=when)
    if verbose:
      print('Deleting {} {}.'.format(which.count(), str(self.model)))
    which.delete()


class RmOld(models.Model):
  created = models.DateTimeField(auto_now_add=True)

  class Meta:
    abstract = True
