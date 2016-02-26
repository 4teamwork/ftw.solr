/*
Go trough the filter by hitting tab. This will focus the filter.

Controls on the filter:
- right arrow: open the focused filter
- down arrow: open the focused filter
- enter: open the focused filter

Controls on open filter:
- escape: close the open filter
- left arrow: close the open filter
- down arrow: focus next facet
- up arrow: focus previous facet
 */

(function(global) {
  'use strict';

  var context = "#filter-form";

  var facets = {
    filter: null,
    currentFacet: null,
    facets: [],
    next: function() {
      if(this.currentFacet === this.facets.length - 1) {
        this.currentFacet = 0;
      } else {
        this.currentFacet++;
      }
      this.focus();
    },
    prev: function() {
      if(this.currentFacet === 0) {
        this.currentFacet = this.facets.length - 1;
      } else {
        this.currentFacet--;
      }
      this.focus();
    },
    init: function(filter) {
      this.filter = filter;
      this.currentFacet = 0;
      this.facets = filter.find(".facet");
      this.focus();
    },
    focus: function() {
      focus(this.facets.eq(this.currentFacet));
    }
  };

  var currentFilter = $();

  function focus(target) {
    blur();
    $(context + " .active").removeClass("active");
    target.addClass("active accessibility-tab-focus").focus();
  }

  function blur() {
    $(".accessibility-tab-focus").removeClass("accessibility-tab-focus");
  }

  function openFilter(filter) {
    currentFilter = filter;
    $(context + " .filter").not(filter).find(".facets").hide();
    filter.find(".facets").show().attr("aria-hidden", false);
  }

  function toggleFilter(filter) {
    $(context + " .filter").not(filter).find(".facets").hide();
    var facets = filter.find(".facets");
    facets.toggle().attr("aria-hidden", facets.attr("aria-hidden") !== "true");
  }

  function closeFilter() {
    focus(currentFilter.find(">a"));
    $(context + " .facets").hide().attr("aria-hidden", true);
  }

  $(document).on("click", function(event) {
    var target = $(event.target);
    if(!(target.hasClass("filter") || target.parent().hasClass("filter"))) {
      closeFilter();
      blur();
    }
  });

  $(document).on("click", ".filter", function(event) {
    var filter = $(event.currentTarget);
    var target = $(event.target);

    if(target.parent().hasClass("filter")) {
      event.preventDefault();
      toggleFilter(filter);
    }
  });

  $(document).on("keydown", ".filter", function(event) {
    var filter = $(event.currentTarget);
    var target = $(event.target);
    if(!target.parents().hasClass("filter")) {
      return;
    }
    switch (event.which) {
      case $.ui.keyCode.DOWN:
        event.preventDefault();
        if(target.hasClass("facet")) {
          facets.next();
        } else {
          openFilter(filter);
          facets.init(filter);
        }
        break;
      case $.ui.keyCode.UP:
        event.preventDefault();
        facets.prev();
        break;
      case $.ui.keyCode.RIGHT:
        event.preventDefault();
        openFilter(filter);
        facets.init(filter);
        break;
      case $.ui.keyCode.LEFT:
        event.preventDefault();
        closeFilter();
        break;
      case $.ui.keyCode.ESCAPE:
        event.preventDefault();
        closeFilter();
        blur();
        break;
      case $.ui.keyCode.ENTER:
        if(target.hasClass("filter")) {
          event.preventDefault();
          openFilter(filter);
          facets.init(filter);
        }
        break;
    }
  });

}(window));
