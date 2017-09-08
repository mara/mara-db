'use strict';

const displaySchemaList = function (db_name, schema_list) {
    let r = new XMLHttpRequest();
    r.open("GET", `svg/${db_name}/${schema_list.join('|')}`, true);
    r.onreadystatechange = function () {
        if (r.readyState !== 4 || r.status !== 200) return;
        updateSchemaDisplay(JSON.parse(r.responseText));
    };
    r.send();
};

const updateSchemaDisplay = function (schema) {
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

    displaySchemaList(location.href.split('/').slice(-1), Array.from(selected_schemas));
    for (let chbox of document.getElementsByClassName('schema_checkbox')) {
        if (chbox.tagName === 'INPUT') {
            console.log(selected_schemas);
            console.log(chbox.dataset.schemaName);
            console.log(selected_schemas.has(chbox.dataset.schemaName));
            if (selected_schemas.has(chbox.dataset.schemaName)){
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
                displaySchemaList(this.dataset.dbName, Array.from(selected_schemas));
            });
        }
    }
});