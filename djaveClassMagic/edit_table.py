""" This table is for editing a single instance. It does one row per field.
It's got helptext. """

from djaveClassMagic.model_fields import model_fields
from djaveForm.button import Button
from djaveForm.default_widget import default_widget
from djaveForm.form import Form
from djaveTable.table import Table, Cell
from djaveTable.cell_content import (
    Tooltip, DisappearingFeedback, Feedback, InHref)
from djmoney.money import Money


WIRE_UP_CONFIRM_DELETE = """
$(function() {
  $('.delete').click(function() {
    return confirm('Delete?');
  });
});"""


class EditTable(Table):
  def __init__(
      self, model, request_data, cancel_url, instance=None, extra_buttons=None,
      show_delete=True):
    self.model = model
    self.model_fields = model_fields(model)
    self.request_data = request_data
    self.instance = instance
    self.extra_buttons = extra_buttons or []
    self.show_delete = show_delete

    self.save_button = Button('Save', button_type='submit')
    self.delete_button = Button('Delete', button_type='delete')
    self.cancel_button = InHref('Cancel', cancel_url, button=True)

    self.form = Form(
        [self.save_button, self.delete_button] + self.extra_buttons)
    self._saved = False
    self._deleted = False

    question = 'Delete this {}?'.format(model.__name__)
    confirm_delete_js = WIRE_UP_CONFIRM_DELETE.replace('Delete?', question)
    super().__init__(
        js=confirm_delete_js, classes=['margin-top', 'edit-table'])
    self.append_js(
        "setup_edit_field_turns_yellow('.edit-table', 'tr');")

    # You have to add_rows before you handle_clicks because handle_clicks has
    # to check to see if the widgets are valid.
    self._redo_rows()
    self.handle_clicks()

    if self.saved():
      # But if there's a readonly field that changed based on what the user
      # saved, then the old call to add_rows might have out of date data, so
      # we'd better redo the rows.
      self._redo_rows()
      self.buttons_cell.cell_contents.append(DisappearingFeedback())

  def _redo_rows(self):
    self.rows = []
    self.buttons_cell = Cell([], additional_attrs={'colspan': 2})
    self.add_rows()

  def add_rows(self):
    raise NotImplementedError('add_rows')

  def is_valid(self):
    return self.form.is_valid()

  def save_clicked(self):
    return self.save_button.get_was_clicked(self.request_data)

  def init_new(self):
    return self.model()

  def handle_clicks(self):
    if self.form.a_button_was_clicked(self.request_data):
      self.form.set_form_data(self.request_data)
      if self.save_button.get_was_clicked():
        self.handle_save_click()
      if self.delete_button.get_was_clicked():
        self.handle_delete_click()

  def handle_save_click(self):
    if self.is_valid():
      if not self.instance:
        self.instance = self.init_new()
      for key, value in self.form.to_dict().items():
        # In the case of foreign keys, the user's permission to `value` is
        # already validated by the explain_why_not_valid function on
        # SelectField which makes sure the user chose a value that we sent to
        # them.
        setattr(self.instance, self._get_model_field_key(key), value)
      why_invalid = self.instance.explain_why_invalid()
      if why_invalid:
        self.buttons_cell.cell_contents.append(Feedback(why_invalid))
      else:
        self.instance.save()
        self._saved = True
    return self.saved()

  def handle_delete_click(self):
    if hasattr(self.instance, 'mark_deleted'):
      self.instance.mark_deleted()
    else:
      self.instance.delete()
    self._deleted = True

  def _get_model_field_key(self, field_key):
    is_fk = bool(self._get_model_field(field_key).foreign_key_to)
    if is_fk and field_key[-3:] != '_id':
      return '{}_id'.format(field_key)
    return field_key

  def _get_model_field(self, name):
    return [mf for mf in self.model_fields if mf.name == name][0]

  def saved(self):
    return self._saved

  def deleted(self):
    return self._deleted

  def add_final_row(self):
    buttons = [self.save_button, self.cancel_button]
    if self.instance and self.show_delete:
      buttons.append(self.delete_button)
    if self.extra_buttons:
      buttons.extend(self.extra_buttons)
    self.buttons_cell.cell_contents.extend(buttons)
    self.create_row([self.buttons_cell])

  def add_field_rows(self, *field_names):
    for field_name in field_names:
      self.add_field_row(field_name)

  def add_field_row(self, field_name, widget=None, read_only=False):
    field = self._get_field(field_name)
    current_value = self.get_current_value(field)
    second_cell = current_value

    if not read_only:
      if not widget:
        widget = default_widget(field)
      if current_value:
        widget.default = current_value
      self.form.new_form_element(widget)
      second_cell = widget

    label = field.display_name
    if field.help_text:
      label = Tooltip(field.display_name, field.help_text)
    self.create_row([label, second_cell])

  def get_current_value(self, field):
    value = None
    if self.instance:
      value = getattr(self.instance, field.name)
      if value is not None:
        if isinstance(value, Money):
          value = value.amount
    else:
      return field.default
    return value

  def _get_field(self, field_name):
    for field in self.model_fields:
      if field.name == field_name:
        return field
    raise Exception(
        '{} does not have a {} field'.format(self.model, field_name))
