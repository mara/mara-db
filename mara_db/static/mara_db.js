'use strict';
const updateSchemaDisplay = function(schema) {
    document.getElementById('svg_display').innerHTML = schema.svg;

};

document.addEventListener("DOMContentLoaded", function () {
    let selected_schemas = new Set();
    for (let chbox of document.getElementsByClassName('schema_checkbox')) {
        if (chbox.tagName === 'INPUT') {
            chbox.addEventListener('change', function () {
                const spanLabel = this.parentNode.parentNode;
                if (this.checked) {
                    spanLabel.style.cssText = spanLabel.dataset.activeStyle;
                    selected_schemas.add(this.dataset.schemaName);
                } else {
                    spanLabel.style.cssText = '';
                    selected_schemas.delete(this.dataset.schemaName);
                }
                let r = new XMLHttpRequest();
                r.open("GET", `svg/${this.dataset.dbName}/${Array.from(selected_schemas).join('|')}`, true);
                r.onreadystatechange = function () {
                    if (r.readyState !== 4 || r.status !== 200) return;
                    updateSchemaDisplay(JSON.parse(r.responseText));
                };
                r.send();
            });
        }
    }
});