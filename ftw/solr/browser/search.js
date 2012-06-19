jQuery(function ($) {

    function getParameterByName(name) {
        // Returns the value of the query string parameter with the given name.
        // If there's a history hash get the parameter from there.
        var search = History.getHash() ? History.getHash() : window.location.search;
        var match = RegExp('[?&]' + name + '=([^&]*)').exec(search);
        return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
    }

    var History = window.History;

    History.Adapter.bind(window, 'statechange', function() {
        var State = History.getState();
        var qs = State.url.replace(/^.*\?/, '') + '&ajax=1';
        var results_container = $('#search-results-wrapper');
        $.get('@@search', qs, function(data) {
            results_container.hide();
            var $data = $(data);
            $('#portal-searchfacets').html($data.find('#portal-searchfacets').html());
            $('#search-results').html($data.find('#search-results').html());
            $('h1.documentFirstHeading').html($data.find('h1.documentFirstHeading').html());
            results_container.fadeIn(200);
            results_container.highlightSearchTerms({
                terms: [getParameterByName('SearchableText')],
                useLocation: false,
                useReferrer: false
            });
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
    $('#searchform input[name="SearchableText"]').keyup(function () {
        $('input#searchGadget').val($(this).val());
    });

    // Handle search form submission
    $('form.searchPage').submit(function (e) {
        var url = '?' + $(this).serialize();
        History.pushState(null, null, url);
        e.preventDefault();
    });

    // Handle clicks in batch navigation and facets
    $('#portal-searchfacets a, #search-results .listingBar a').live('click', function (e) {
        History.pushState(null, null, jq(this).attr('href'));
        e.preventDefault();
    });

});
