CREATE TABLE electricity_prices (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    price_eur_kwh FLOAT,
    year INT,
    month INT,
    day INT,
    hour INT
);