-- Average electricity price by hour
SELECT hour, AVG(price) AS avg_price
FROM electricity_prices
GROUP BY hour
ORDER BY avg_price;

-- Average price by month
SELECT month, AVG(price) AS avg_price
FROM electricity_prices
GROUP BY month
ORDER BY month;

-- Top 5 cheapest hours on average
SELECT hour, AVG(price) AS avg_price
FROM electricity_prices
GROUP BY hour
ORDER BY avg_price ASC
LIMIT 5;

-- Most expensive days
SELECT DATE(datetime) AS day, AVG(price) AS avg_price
FROM electricity_prices
GROUP BY day
ORDER BY avg_price DESC
LIMIT 10;


-- Rolling 6-hour average (simplified window function)
SELECT 
    datetime,
    AVG(price) OVER (
        ORDER BY datetime 
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    ) AS rolling_6h_avg
FROM electricity_prices;
