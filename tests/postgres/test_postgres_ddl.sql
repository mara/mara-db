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

CREATE TABLE accounts_json
(
    data jsond,
    row BIGINT GENERATED ALWAYS AS IDENTITY
);
