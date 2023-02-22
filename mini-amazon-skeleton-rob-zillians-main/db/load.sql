\COPY Users(email, password, firstname, lastname, address) FROM 'data/Users.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Sellers(seller_id) FROM 'data/Sellers.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Categories FROM 'data/Categories.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Products(name, image_url, description, category_name, owner) FROM 'data/Products.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Inventory FROM 'data/Inventory.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Purchases(User_id, Product_id, time_purchased, Seller_id, quantity, order_status) FROM 'data/Purchases.csv' WITH DELIMITER ',' NULL '' CSV
\COPY ReviewsSeller FROM 'data/ReviewsSeller.csv' WITH DELIMITER ',' NULL '' CSV
\COPY ReviewsProduct FROM 'data/ReviewsProduct.csv' WITH DELIMITER ',' NULL '' CSV
\COPY FinalPrice FROM 'data/FinalPrice.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Advertisements(Seller_id, Product_id, nickname, description, image_url, category, start_time, end_time, impressions, clicks, conversions) FROM 'data/Advertisements.csv' WITH DELIMITER ',' NULL '' CSV

-- TEST TRIGGERS
UPDATE ReviewsProduct
 SET rating = 6
 WHERE user_id = 1;

UPDATE ReviewsProduct
 SET rating = -10
 WHERE user_id = 1;

UPDATE ReviewsSeller
 SET rating = -10
 WHERE user_id = 1;

UPDATE ReviewsSeller
 SET rating = 6
 WHERE user_id = 1;

INSERT INTO ReviewsSeller VALUES
(1,5, '2021-10-07 06:23:05', 0, 'bad experience');

INSERT INTO ReviewsProduct VALUES
(1, 8, '2021-10-07 06:23:05', 0, 'bad experience');

INSERT INTO Purchases(User_id, Product_id, time_purchased, Seller_id, fulfillment_time, quantity, order_status) VALUES
(1, 2, '2021-10-05 06:56:05', 4, NULL, 1001, 'Ordered');
