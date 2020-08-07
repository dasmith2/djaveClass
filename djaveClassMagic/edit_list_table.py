""" This table is for editing a list of objects. It does one row per object.
"""
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from djaveTable.table import Table, Cell
from djaveTable.cell_content import InHref


def edit_list_table_js():
  context = {
      'ajax_update_url': reverse('ajax_update'),
      'ajax_delete_url': reverse('ajax_delete')}
  return render_to_string('js/edit_list_table.js', context)


class EditListTable(Table):
  def __init__(self, model, *args, **kwargs):
    self.model = model
    # I mean, probably it will, until I find out otherwise.
    self._has_objects = True
    self._create_new_button = None
    self._setup_edit_anything = False

    if 'additional_attrs' not in kwargs or kwargs['additional_attrs'] is None:
      kwargs['additional_attrs'] = {}
    kwargs['additional_attrs']['data-model'] = model.__name__

    super().__init__(*args, **kwargs)

    self.setup_edit_anything_turns_yellow()

  def as_html(self):
    only_show_create_new_button = (
        self._create_new_button and not self._has_objects)
    only_show_nothing = not len(self.rows)
    if only_show_create_new_button or only_show_nothing:
      content = 'Nothing to report'
      if only_show_create_new_button:
        content = self._create_new_button.as_html()
      return mark_safe('<div {}>{}</div>'.format(
          self.css_classes_str(), content))
    return super().as_html()

  def setup_edit_anything_turns_yellow(self):
    if self._setup_edit_anything:
      return
    self.append_js(
        "setup_edit_field_turns_yellow("
        "'table[data-model]', 'tr', turn_on_edit_mode_table_row, "
        "turn_off_edit_mode_table_row);")

  def setup_edit_ajax(self, column_or_columns, selector_or_selectors=None):
    """ Make it so when you change a text box the row turns yellow and the
    buttons change to Save and Cancel. """
    columns, selectors = self._columns_selectors(
        column_or_columns, selector_or_selectors)

    entries = []
    for i, column in enumerate(columns):
      selector = selectors[i]
      entries.append(
          "setup_ajax_save_field('{}', '{}');".format(selector, column))
    self.append_js('\n'.join(entries))

  def _columns_selectors(self, column_or_columns, selector_or_selectors):
    columns = column_or_columns
    if isinstance(column_or_columns, str):
      columns = [column_or_columns]

    if isinstance(selector_or_selectors, list):
      selectors = selector_or_selectors
    elif isinstance(selector_or_selectors, str):
      selectors = [selector_or_selectors]
    else:
      selectors = ['.{}'.format(column) for column in columns]
    return (columns, selectors)

  def setup_delete_ajax(self, selector, confirm_question=None):
    confirm_question_arg = ''
    if confirm_question:
      confirm_question_arg = ", '{}'".format(confirm_question.replace(
          "'", r"\'").replace('\n', r'\n'))
    new_js = "setup_click_deletes('{}'{});".format(
        selector, confirm_question_arg)
    self.append_js(new_js)

  def setup_set_dt_green(
      self, field_name, set_button_text, unset_button_text):
    new_js = render_to_string('js/init_dt_green_mode.js', {
        'data_model_name': self.model.__name__,
        'field_name': field_name,
        'set_button_text': set_button_text,
        'unset_button_text': unset_button_text})
    self.append_js(new_js)

  def setup_click_updates_field(
      self, selector, field_name, new_value, success):
    self.append_js(render_to_string('js/setup_click_updates_field.js', {
        'selector': selector, 'field_name': field_name,
        'new_value': mark_safe(new_value), 'success': mark_safe(success)}))

  def append_create_new_row(self, button_text, href):
    # This is a bit hacky, but the create new row goes last, so if there aren't
    # any other rows yet, that means there must not be any objects in this
    # table. I keep track of that so when I render the table I can not bother
    # to show the headers if there aren't any rows.
    self._has_objects = bool(len(self.rows))
    self._create_new_button = InHref(
        button_text, href, classes=['create_new'], button=True)
    create_new_cell = Cell(
        self._create_new_button,
        additional_attrs={'colspan': len(self.headers)})
    self.create_row([create_new_cell])
    return self._create_new_button

  def setup_display_count(self):
    self.append_js('$(setup_display_count);')
