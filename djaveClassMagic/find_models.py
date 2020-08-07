""" Functions for locating models. More precisely, functions for locating
classes in the `models` and `web_test` modules of INSTALLED_APPS. By default
these functions pull back django.db.models.Model subclasses but you can specify
a different base class. """
from importlib import import_module
import re

from django.conf import settings
from django.db.models import Model


def model_from_name(model_name, subclass_of=None):
  """ Given just the name of the model, return the model itself. The point is
  not to have to also specify an app. """
  for model in all_models(subclass_of=subclass_of):
    if model.__name__ == model_name:
      return model
  raise Exception('I was unable to find the {} model, subclass_of {}'.format(
      model_name, subclass_of))


def all_models(subclass_of=None):
  """ By default this returns all Django models. But you can have it return a
  list of all classes that subclass anything, as long as those classes are
  directly in the models module of Django apps. """
  to_return = []
  for app_name in settings.INSTALLED_APPS:
    to_return.extend(models_in_app(app_name, subclass_of=subclass_of))
  return to_return


def models_in_app(app_name, subclass_of=None):
  # This turns 'djaveAPI.tests.apps.DjaveAPITestsConfig' into 'djaveAPI.tests'
  app_name = re.compile(r'\.apps\..+Config').sub('', app_name)

  subclass_of = subclass_of or Model
  to_return = []
  for possible_sub_module in ['models', 'browser']:
    try:
      sub_module = import_module('{}.{}'.format(app_name, possible_sub_module))
      for model_name, cls in sub_module.__dict__.items():
        # cls has to be a type, it has to be derived from subclass_of, but it
        # can't actually be subclass_of
        if isinstance(cls, type) and issubclass(cls, subclass_of) and (
            cls is not subclass_of):
          to_return.append(cls)
    except ModuleNotFoundError:
      pass
  return to_return
