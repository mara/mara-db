'use strict';
(() => {
    let shown_chart = {};
    window.exportSVGFile = () =>{
        if (!shown_chart.svg){
            window.alert('no schema to export');
            return;
        }

        const fileName = 'schema_chart.svg';

        var fileToSave = new Blob([shown_chart.svg], {
            type: 'image/svg+xml',
            name: fileName
        });
        saveAs(fileToSave, fileName);
    };
    const displaySchemaList = function (db_name, schema_list, hide_columns = false) {
        if (schema_list.length === 0)
            return;
        document.getElementById('svg_display').innerHTML = 'Loading...';
        let r = new XMLHttpRequest();
        r.open("GET", `svg/${db_name}/${schema_list.join('|')}${ hide_columns ? '?no_columns=1' : '' }`, true);
        r.onreadystatechange = function () {
            if (r.readyState !== 4 || r.status !== 200) {
                document.getElementById('svg_display').innerHTML = `Error: ${r.responseText}`;
                return;
            }
            updateSchemaDisplay(JSON.parse(r.responseText));
        };
        r.send();
    };

    const updateSchemaDisplay = function (schema) {
        shown_chart = schema;
        document.getElementById('svg_display').innerHTML = schema.svg;
    };

    document.addEventListener("DOMContentLoaded", function () {
        let selected_schemas = new Set();
        if (localStorage.getItem('database-schema-params')) {
            try {
                JSON.parse(localStorage.getItem('database-schema-params')).forEach(p => selected_schemas.add(p));
            }
            catch (err) {
                // if this fails (maybe a previous version left it borked), don't block everything
                console.error(`something went wrong while parsing the localStorage list of schemas to display`, err);
            }
        }
        document.getElementById('show-columns-flag').addEventListener('change', function () {
            displaySchemaList(location.href.split('/').slice(-1), Array.from(selected_schemas), this.value === 'hide');
        });
        displaySchemaList(location.href.split('/').slice(-1), Array.from(selected_schemas));
        for (let chbox of document.getElementsByClassName('schema_checkbox')) {
            if (chbox.tagName === 'INPUT') {
                if (selected_schemas.has(chbox.dataset.schemaName)) {
                    chbox.checked = true;
                    chbox.parentNode.parentNode.style.cssText = chbox.parentNode.parentNode.dataset.activeStyle;
                }
                else {
                    chbox.selected = false;
                }
                chbox.addEventListener('change', function () {
                    const spanLabel = this.parentNode.parentNode;
                    if (this.checked) {
                        spanLabel.style.cssText = spanLabel.dataset.activeStyle;
                        selected_schemas.add(this.dataset.schemaName);
                    } else {
                        spanLabel.style.cssText = '';
                        selected_schemas.delete(this.dataset.schemaName);
                    }
                    localStorage.setItem('database-schema-params', JSON.stringify(Array.from(selected_schemas)));
                    displaySchemaList(this.dataset.dbName, Array.from(selected_schemas), document.getElementById('show-columns-flag').value === 'hide');
                });
            }
        }
    });

})();
