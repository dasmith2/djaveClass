from django.core.exceptions import AppRegistryNotReady
try:
  from django.contrib.contenttypes.models import ContentType
except AppRegistryNotReady:
  raise Exception(
      'The last time this happened it was because I put '
      '`from djavError.log_error import log_error` in djavError.__init__')
from django.db import models


class BaseKnowsChild(models.Model):
  """
  Let's say you've got a base class Vehicle with child classes Car and Bus.
  Sometimes, given a Vehicle object, you'd like to get the child class
  instance. Well if Vehicle inherits from BaseKnowsChild, then Vehicle
  instances will have a as_child_class() function which will return the
  appropriate Car or Bus object.

  Django struggles with base classes. Do yourself a favor and get this in your
  base class right away. child_class being non-nullable will solve problems
  ahead of time, but it's a pain to add non-nullable fields to existing tables.

  Thank you https://stackoverflow.com/questions/929029/how-do-i-access-the-child-classes-of-an-object-in-django-without-knowing-the-nam  # noqa: E501
  """
  child_class = models.ForeignKey(
      ContentType, editable=False, on_delete=models.PROTECT)

  def save(self, *args, **kwargs):
    self.child_class = self._get_child_class()
    super().save(*args, **kwargs)

  def _get_child_class(self):
    return ContentType.objects.get_for_model(type(self))

  def as_child_class(self):
    return self.child_class.get_object_for_this_type(pk=self.pk)

  class Meta:
    abstract = True


class BaseKnowsChildTransition(BaseKnowsChild):
  """ This class is to help you turn an existing class into a BaseKnowsChild
  class. Start by adding BaseKnowsChildTransition as a base class to your
  existing class, go populatethe child_class field on all existing instances,
  then change the base class to BaseKnowsChild. """
  child_class = models.ForeignKey(
      ContentType, editable=False, on_delete=models.PROTECT, null=True,
      blank=True)

  class Meta:
    abstract = True
