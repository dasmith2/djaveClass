$(function() {
  var table_finder = 'table[data-model="{{ data_model_name }}"]';
  var field_name = '{{ field_name }}';
  setup_set_clear_dt_green_mode(
      table_finder, field_name,
      '{{ set_button_text }}', '{{ unset_button_text }}');
});
