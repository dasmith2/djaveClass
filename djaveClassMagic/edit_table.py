""" This table is for editing a single instance. It does one row per field.
It's got helptext. """

from djaveClassMagic.model_fields import model_fields
from djaveForm.button import Button
from djaveForm.default_widget import default_widget
from djaveForm.form import Form
from djaveTable.table import Table, Cell
from djaveTable.cell_content import Tooltip, DisappearingFeedback, Feedback
from djmoney.money import Money


WIRE_UP_CONFIRM_DELETE = """
<script>
$(function() {
  $('.delete').click(function() {
    return confirm('Delete?');
  });
});
</script>
"""


class EditTable(Table):
  def __init__(self, model, request_data, instance=None, extra_buttons=None):
    self.model = model
    self.model_fields = model_fields(model)
    self.request_data = request_data
    self.instance = instance
    self.extra_buttons = extra_buttons

    self.save_button = Button('Save', button_type='submit')
    self.delete_button = Button('Delete', button_type='delete')

    self.form = Form([self.save_button, self.delete_button])
    self._saved = False
    self._deleted = False

    question = 'Delete this {}?'.format(model.__name__)
    confirm_delete_js = WIRE_UP_CONFIRM_DELETE.replace('Delete?', question)
    super().__init__(js=confirm_delete_js, classes=['margin-top'])

    self.buttons_cell = Cell([], additional_attrs={'colspan': 2})
    self.add_rows()
    self.handle_clicks()
    if self.saved():
      self.buttons_cell.cell_contents.append(DisappearingFeedback())

  def add_rows(self):
    raise NotImplementedError('add_rows')

  def is_valid(self):
    return self.form.is_valid()

  def save_clicked(self):
    return self.save_button.get_was_clicked(self.request_data)

  def init_new(self):
    return self.model()

  def handle_clicks(self):
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
    buttons = [self.save_button]
    if self.instance:
      buttons.append(self.delete_button)
    if self.extra_buttons:
      buttons.extend(self.extra_buttons)
    self.buttons_cell.cell_contents.extend(buttons)
    self.create_row([self.buttons_cell])

  def add_field_rows(self, *field_names):
    for field_name in field_names:
      self.add_field_row(field_name)

  def add_field_row(self, field_name, widget=None):
    field = self._get_field(field_name)
    if not widget:
      widget = default_widget(field)
    if self.instance:
      default = getattr(self.instance, field_name)
      if default is not None:
        if isinstance(default, Money):
          default = default.amount
        widget.default = default
    label = field.display_name
    if field.help_text:
      label = Tooltip(field.display_name, field.help_text)
    self.create_row([label, widget])
    self.form.new_form_element(widget)

  def _get_field(self, field_name):
    for field in self.model_fields:
      if field.name == field_name:
        return field
    raise Exception(
        '{} does not have a {} field'.format(self.model, field_name))
