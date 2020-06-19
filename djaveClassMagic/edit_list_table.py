""" This table is for editing a list of objects. It does one row per object.
"""

from djaveTable.table import Table


class EditListTable(Table):
  def __init__(self, model, *args, **kwargs):
    self.model = model

    if 'additional_attrs' not in kwargs or kwargs['additional_attrs'] is None:
      kwargs['additional_attrs'] = {}
    kwargs['additional_attrs']['data-model'] = model.__name__

    super().__init__(*args, **kwargs)

  def wire_up_edit_ajax(self, column_or_columns, selector_or_selectors=None):
    if isinstance(column_or_columns, str):
      column_or_columns = [column_or_columns]
    if isinstance(selector_or_selectors, str):
      selector_or_selectors = [selector_or_selectors]

    entries = []
    for i, column in enumerate(column_or_columns):
      selector = '.{}'.format(column)
      if selector_or_selectors and len(selector_or_selectors) >= i:
        selector = selector_or_selectors[i]
      entries.append(
          "wire_up_ajax_save_field('{}', '{}');".format(selector, column))
    self._append_js('\n'.join(entries))

  def wire_up_delete_ajax(self, selector, confirm_question=None):
    if not confirm_question:
      confirm_question = 'Delete {}?'.format(self.model.__name__)
    else:
      confirm_question = confirm_question.replace(
          "'", r"\'").replace('\n', r'\n')
    new_js = "wire_up_ajax_delete_button('{}', '{}');".format(
        selector, confirm_question)
    self._append_js(new_js)

  def _append_js(self, new_js):
    if not self.js:
      self.js = ''
    self.js = '{}\n{}'.format(self.js, new_js)
