(function() {

  "use strict";

  var selectItem = function(event, ui) { window.location = ui.item.url; };

  var options = {
    source: "ftw_solr_livesearch_reply",
    minLength: 3,
    position: { my: "right top+5", at: "right bottom", collision: "none" },
    select: selectItem,
    messages: {
      noResults: $("#search-no-results-message").text(),
      results: function( amount ) {
        amount = amount - $(".ui-menu-item .no-result").length;
        if (amount !== 0) {
          return amount + ( amount > 1 ? $("#search-amount-results-found-message").text() : $("#search-one-result-found-message").text());

        } else {
          return $("#search-no-results-message").text();
        }
      }
    }
  };

  var source = options.source;

  var renderMenu = function(ul, items) {
    var self = this;
    $.each( items, function( index, item ) {
      self._renderItemData( ul, item );
    });
    ul.prepend($("#currentfolder_item").children().clone());
    $(".folder_path", ul).on("change", function() {
      if(this.checked) {
        self.option("source", source + "?path=" + this.value);
      } else {
        self.option("source", source);
      }
      $("#currentfolder_item .folder_path").prop("checked", this.checked);
      self.search();
    });
  };

  var renderItem = function(ul, item) {

    var autocompleteItem = { label: item.title, value: item.title, url: item.url };

    var li = $("<li>").data("ui-autocomplete-item", autocompleteItem);

    var anchor = $("<a>").attr("href", item.url).addClass(item.cssclass);

    var title = $("<span>").text(item.title)
                           .addClass("title");

    var description = $("<span>").text(item.description)
                                 .addClass("description");

    var itemText = $("<div>").append(title).append(description);

    if(item.firstOfGroup) {
      li.addClass("firstOfGroup");
      var group = $("<span>").text(item.type)
                             .addClass("group");
      li.append(group);
    }

    anchor.append(item.icon).append(itemText);

    li.append(anchor);

    return ul.append(li);
  };

  var init = function() {
    var searchbox = $(".searchField");
    // Always empty on init
    searchbox.val('');
    var widget = $.ui.autocomplete(options, searchbox);
    widget._renderItem = renderItem;
    widget._renderMenu = renderMenu;
    searchbox.on("focus", function() { widget.search(); });

    // Uncheck by default initially
    $(".folder_path").prop("checked", false);

    // Override autocomplete default close function
    // to prevent hiding the results when clicking or scrolling
    // on mobile devices.
    var originalCloseFunction = widget.close;
    widget.close = function(event) {
      if(event && event.type === "blur") {
        event.preventDefault();
      } else {
        originalCloseFunction.call(widget);
      }
    };
    $(document).on("mousedown click", function(event) {
      if(!$(event.target).is("#searchGadget") && !$(event.target).parents(".ui-autocomplete").length) {
        widget.close();
      }
    });
  };

  $(init);

})(window);