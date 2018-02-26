var SchemaPage = function(baseUrl, dbAlias) {

    function localStorageKey(schema) {
        return 'db-schema-' + dbAlias + '-' + schema;
    }

    $('.schema-checkbox').each(function (n, checkbox) {
       if (localStorage.getItem(localStorageKey(checkbox.value)) == 'true') {
           checkbox.checked = true;
       }
    });

    if (localStorage.getItem('db-schema-hide-columns') == 'true') {
        $('#hide-columns-checkbox')[0].checked = true;
    }

    var url = '';

    function updateUI() {
        var selectedSchemas = [];
        $('.schema-checkbox').each(function (n, checkbox) {
            if (checkbox.checked) {
                selectedSchemas.push(checkbox.value);
            }
            localStorage.setItem(localStorageKey(checkbox.value), checkbox.checked);
        });
        localStorage.setItem('db-schema-hide-columns', $('#hide-columns-checkbox')[0].checked);


        if (selectedSchemas.length > 0) {
            $('#schema-container').html(spinner());
            url = baseUrl + '/' + selectedSchemas.join('/');
            if ($('#hide-columns-checkbox')[0].checked) {
                url += '?hide-columns=true'
            }
            loadContentAsynchronously('schema-container', url);
        } else {
            $('#schema-container').html('<i>No schemas selected</i>');
        }

    }

    function downloadSvg() {
        window.location.href = url;
    }

    $('.schema-checkbox').change(updateUI);
    $('#hide-columns-checkbox').change(updateUI);

    updateUI();

    return {'downloadSvg': downloadSvg}
};
