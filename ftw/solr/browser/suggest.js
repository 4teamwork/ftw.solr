jQuery(function ($) {
    $('#search-results input[name="SearchableText"]').autocomplete({
      source: "@@suggest-terms",
      minLength: 1,
      select: function(event, ui) {
          $(this).parents('form').submit();
      }
    });
});
