from collections import namedtuple
import re

from django.db.models.fields.reverse_related import ManyToOneRel

ModelField = namedtuple('ModelField', [
    'name', 'display_name', 'help_text', 'can_filter', 'type',
    'foreign_key_to', 'max_length', 'required', 'editable'])

DATE_TIME = 'DateTime'
DATE = 'Date'
FLOAT = 'Float'
INTEGER = 'Integer'
TEXT = 'Text'
CHAR = 'Char'
BOOLEAN = 'Boolean'
TYPES = [DATE_TIME, DATE, FLOAT, INTEGER, TEXT, CHAR, BOOLEAN]


def _get_django_model_fields(cls):
  if hasattr(cls, 'get_model_fields'):
    return cls.get_model_fields()
  return cls._meta.get_fields()


def model_fields(model, specific_field=None):
  fields = []
  for field in _get_django_model_fields(model):
    name = field.name
    is_ptr_to_base_class = re.compile(r'\w+_ptr').findall(name)
    if is_ptr_to_base_class:
      continue
    if isinstance(field, ManyToOneRel):
      continue

    can_filter = field.db_index
    help_text = field.help_text
    field_type = field.get_internal_type()
    required = not field.null
    editable = field.editable
    foreign_key_to = None
    max_length = None

    is_id = name == 'id'
    if is_id:
      required = False
      can_filter = False
      editable = False
      help_text = 'What is the primary key for this object?'
      field_type = 'Integer'
    else:
      field_type = field_type.replace('Field', '')
      if field_type in ['ForeignKey', 'OneToOne', 'OneToOneOrNone']:
        try:
          field.get_prep_value(1)
        except ValueError:
          raise Exception(
              'The API doesnt know how to handle non-integer primary keys '
              'yet. See filter_model in djaveAPI.filters specifically')
        field_type = INTEGER
        foreign_key_to = field.related_model
      if field_type == 'PositiveInteger':
        field_type = INTEGER
      if field_type == 'Decimal':
        field_type = FLOAT
      if field_type == CHAR:
        max_length = field.max_length
      if field_type not in TYPES:
        raise Exception(
            'I am not familiar with the {} type'.format(field_type))

    field = ModelField(
        name, _display_name(name), help_text, can_filter, field_type,
        foreign_key_to, max_length, required, editable)
    if name == specific_field:
      return field
    else:
      fields.append(field)
  if specific_field:
    return None
  return fields


def _display_name(field_name):
  return field_name.capitalize().replace('_', ' ')
