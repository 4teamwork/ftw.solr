jQuery(function ($) {

    var History = window.History;

    History.Adapter.bind(window, 'statechange', function() {
        var State = History.getState();
        var qs = State.url.replace(/^.*\?/, '');
        var results_container = $('#search-results-wrapper');
        $.get('@@search-results', qs, function(data) {
            results_container.hide();
            results_container.html(data);
            results_container.fadeIn(200);
        });
    });

    // Returns query string values from a querystring.
    // function qs_values(qs) {
    //     var a = qs.split('&');
    //     if (a === "") return {};
    //     var b = {};
    //     for (var i = 0; i < a.length; ++i)
    //     {
    //         var p=a[i].split('=');
    //         if (!b[p[0]]) {
    //             b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
    //         } else {
    //             if (typeof(b[p[0]])=='string') {
    //                 b[p[0]] = [b[p[0]]];
    //             }
    //             b[p[0]].push(decodeURIComponent(p[1].replace(/\+/g, " ")));
    //         }
    //     }
    //     return b;
    // }

    // We need to update the site-wide search field (at the top right in
    // stock Plone) when the main search field is updated
    $('#search-field input[name="SearchableText"]').keyup(function () {
        $('input#searchGadget').val($(this).val());
    });


    $('form.searchPage').submit(function (e) {
        var url = '@@search?' + $(this).serialize();
        History.pushState(null, null, url);
        e.preventDefault();
    });

    $('#portal-searchfacets a, #search-results .listingBar a').live('click', function (e) {
        History.pushState(null, null, jq(this).attr('href'));
        e.preventDefault();
    });

});
