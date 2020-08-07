/* Stuff that comes up when I'm enabling tables for AJAX. Well, now I'm putting
 * edit table stuff in here too. */

function find_pk($element) {
  // Search up the dom for a data-pk attribute. So you might do something like
  // my_button.click(function() { var pk = find_pk($(this)); });
  if ($element.attr('data-pk')) {
    return $element.attr('data-pk');
  }
  return $element.parents('[data-pk]').attr('data-pk');
}

function find_model($element) {
  if ($element.attr('data-model')) {
    return $element.attr('data-model');
  }
  return $element.parents('[data-model]').attr('data-model');
}

function row_by_pk(pk) {
  return $('tr[data-pk=' + pk + ']');
}

function remove_row(pk) {
  var row = row_by_pk(pk);
  var table = row.parents('table');
  row.remove();
  if (!table.find('tbody tr').length) {
    $('<p class="margin-top">Nothing to report</p>').insertAfter(table);
    table.hide();
  }
}

function setup_click_deletes(selector, confirm_question) {
  var do_something = function(model, pk, feedback, always) {
    var data = {'type': model, 'pk': pk};
    var success = function() {
      remove_row(pk);
    };
    post('{{ ajax_delete_url }}', data, success, always, feedback)
  };
  setup_click_does_something(selector, confirm_question, do_something);
}

function setup_click_updates_field(
    selector, field_name, new_value, success, confirm_question) {
  var do_something = function(model, pk, feedback, always) {
    update_field(
        model, pk, field_name, new_value, success, always, feedback);
  };
  setup_click_does_something(selector, confirm_question, do_something);
}

function setup_click_does_something(selector, confirm_question, do_something) {
  $(selector).click(function() {
    var button = $(this).prop('disabled', true);
    var always = function() {
      button.prop('disabled', false);
    };
    if (!confirm_question || confirm(confirm_question)) {
      var model = find_model(button);
      var pk = find_pk(button);
      var feedback = get_feedback_elt_after(button);
      do_something(model, pk, feedback, always);
    } else {
      always();
    }
  });
}

function setup_ajax_save_field(selector_or_elt, field_name) {
  /* This is for text boxes or whatever in tables so you can edit inline with
   * AJAX. Once you start editing, this hides all the other buttons and gives
   * the user "Save" and "Cancel" buttons. selector_or_elt can be a string or a
   * jQuery object. Closures are a little tricky here because I want the same
   * save button to save all editing fields. */
  $(selector_or_elt).each(function() {
    var elt = $(this);
    elt.attr('data-field-name', field_name);
  });
}

function setup_edit_list_table_buttons_cell(row) {
  var save_button = buttons_cell(row).find('.save-row');
  var cancel_save_button = buttons_cell(row).find('.cancel-save-row');

  if (!save_button.length) {
    var save_html = '<button class="save-row" type="button">Save</button>';
    save_button = $(save_html).appendTo(buttons_cell(row)).hide();
    var cancel_html =
        '<button class="cancel-save-row" type="button">Cancel</button>';
    cancel_save_button = $(cancel_html).appendTo(buttons_cell(row)).hide();

    save_button.click(function() {
      save_button.prop('disabled', true);
      cancel_save_button.prop('disabled', true);

      var data = {pk: find_pk(row), type: find_model(row)};

      var got_all_elts = all_elts(row);
      var first_feedback = null;
      var last_edited_elt = null;
      for (var i = 0; i < got_all_elts.length; i++) {
        var elt = $(got_all_elts[i]);
        if (is_editing(elt)) {
          if (first_feedback === null) {
            first_feedback = get_feedback_elt_after(elt);
          }
          data[elt.attr('data-field-name')] = elt.val()
          last_edited_elt = elt;
        }
      }

      var handle_elt_was_saved = function(elt) {
        var feedback = get_feedback_elt_after(elt);
        feedback.show().text(SAVED);
        elt.attr('data-saved-value', elt.val());
        window.setTimeout(function() {
          feedback.text('');
        }, 1000);
      };

      var success = function(response) {
        if (!show_problem(response, first_feedback)) {
          for (var i = 0; i < got_all_elts.length; i++) {
            var elt = $(got_all_elts[i]);
            if (is_editing(elt)) {
              handle_elt_was_saved(elt);
            }
          }
          // The save button disappears and you lose your tab location
          // otherwise.
          last_edited_elt.focus();
        }
        calc_edit_mode_4_edit_list_table(row);
      };
      // DON'T use update_field here because data may have multiple fields.
      post('{{ ajax_update_url }}', data, success, null, first_feedback);
    });

    cancel_save_button.click(function() {
      row.find('.feedback').hide();
      var got_all_elts = all_elts(row);
      for (var i = 0; i < got_all_elts.length; i++) {
        var elt = $(got_all_elts[i]);
        elt.val(elt.attr('data-saved-value'));
        if (elt[0].tagName == 'TEXTAREA') {
          resize_textarea(elt);
        }
      }
      calc_edit_mode_4_edit_list_table(row);
    });
  }
}

function calc_edit_mode_4_edit_list_table(row) {
    calc_edit_mode(
        row, turn_on_edit_mode_table_row, turn_off_edit_mode_table_row);
}

function turn_on_edit_mode_table_row(row) {
  if (row.attr('data-pk')) {
    setup_edit_list_table_buttons_cell(row);
    var save_cancel_buttons = buttons_cell(row).find(
        '.save-row,.cancel-save-row');
    other_buttons(row).hide();
    save_cancel_buttons.show().prop('disabled', false);
  }
}

var SAVED = 'Saved!';

function turn_off_edit_mode_table_row(row) {
  if (row.attr('data-pk')) {
    other_buttons(row).show();
    buttons_cell(row).find('.save-row,.cancel-save-row').hide();
    // Maybe you tried to blank out a field, hit save, got a required error,
    // typed your original back in, that turns off edit mode, but we should now
    // hide the required message. On the other hand, if you just successfully
    // clicked save, we don't want to instantly remove the "Saved!" message.
    row.find('.feedback').each(function() {
      if ($(this).text() != SAVED) {
        $(this).hide();
      }
    });
  }
}

function setup_set_clear_dt_green_mode(
    table_finder, field_name, set_button_text, unset_button_text,
    set_mode_callback, unset_mode_callback) {
  /* You have a model where, when a field is set, the row should be colored
   * green, but when the field is not set, the row is uncolored. You need
   * buttons that switch between the modes and set the field to either now or
   * null. For instance, ToDos have a `done` field and invoices have a `paid`
   * field. */

  var set_mode = function(pk) {
    var row = row_by_pk(pk).addClass('green');
    var buttons = buttons_cell(row);
    buttons.find('.set').remove();
    // This code uses the .unset class, but the web tests probably find it
    // makes more sense to search for the .not_done button or whatever.
    var unset = $('<button type="button"></button>').text(
        unset_button_text).addClass('unset').addClass('not_' + field_name);

    unset.click(function() {
      _update_field(row, null, unset_mode);
    });

    buttons.append(unset);

    if (set_mode_callback) {
      set_mode_callback(row);
    }
  };

  var unset_mode = function(pk) {
    var row = row_by_pk(pk).removeClass('green');
    var buttons = buttons_cell(row);
    buttons.find('.unset').remove();
    // This code uses the .set class, but the web tests probably find it makes
    // more sense to search for the, like, .done button or whatever.
    var set = $('<button type="button"></button>').text(
        set_button_text).addClass('set').addClass(field_name);

    set.click(function() {
      _update_field(row, 'now', set_mode);
    });

    buttons.append(set);

    if (unset_mode_callback) {
      unset_mode_callback(row);
    }
  };

  var _update_field = function(row, new_value, success) {
    var feedback = get_feedback_elt_append(buttons_cell(row));
    return update_field(
        find_model(row), find_pk(row), field_name, new_value, success,
        null, feedback);
  };

  var rows = $(table_finder).find('tr[data-pk]');
  for (var i = 0; i < rows.length; i++) {
    // I used a for loop so if I throw an exception the loop stops.
    var row = $(rows[i]);
    if (buttons_cell(row).length == 0) {
      window.log_error(
          'Unable to find the buttons cell for a row in ' + table_finder);
      return;
    }
    var field_data_attr = 'data-' + field_name;
    var field_data_val = row.attr(field_data_attr);
    if (field_data_val != 'True' && field_data_val != 'False') {
      var message = (
          table_finder + ' rows should have a True or False '
          + field_data_attr);
      // Don't throw message because then Firefox just hands blank information
      // to onerror.
      window.log_error(message);
      return;
    }
    var is_set = field_data_val == 'True';
    if (is_set) {
      set_mode(find_pk(row));
    } else {
      unset_mode(find_pk(row));
    }
  }
}

function px_to_int(px) {
  return parseInt(px.replace('px', ''));
}

function setup_display_count() {
  $('table[data-model]').each(function() {
    var table = $(this);
    if (!table.attr('data-displayed-count')) {
      table.attr('data-displayed-count', 'yep');
      var count = table.find('tr[data-pk]').length;
      if (count > 3) {
        var colspan = $(table.find('tr')[0]).find('td,th').length;
        var tr = $('<tr></tr>').appendTo(table);
        $('<td></td>').attr('colspan', colspan).addClass(
            'bold-grey-text').text('Count: ' + count).appendTo(tr);
      }
    }
  });
}
