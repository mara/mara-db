CREATE TABLE names
(
    id INT,
    name TEXT
);

CREATE TABLE names_with_header
(
    id INT,
    name TEXT
);

CREATE SEQUENCE row_seq START 1;

CREATE TABLE accounts_json
(
    data JSON,
    row INTEGER PRIMARY KEY DEFAULT nextval('row_seq')
);
