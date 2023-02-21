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
    data jsonb,
    row BIGINT GENERATED ALWAYS AS IDENTITY
);
