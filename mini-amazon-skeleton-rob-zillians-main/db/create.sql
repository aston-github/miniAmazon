-- Create the Users table, which stores all information regarding a specific user (the user's id, email, password, firstname, lastname, balance, and address)
-- A user's balance refers to the amount of money that person has to spend on products
CREATE TABLE Users (
    id INT GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    email VARCHAR NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    firstname VARCHAR(255) NOT NULL,
    lastname VARCHAR(255) NOT NULL,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0,
    address VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);

-- Create the Sellers table. Sellers are a subset of users that can create products and fulfill orders
CREATE TABLE Sellers
(Seller_id INT NOT NULL REFERENCES Users(id),
 PRIMARY KEY(Seller_id)
);

-- Create the Categories table, which will store a list of pre-defined categories within which new products must be categorized.
CREATE TABLE Categories
(name VARCHAR(64) NOT NULL,
	PRIMARY KEY(name)
);

-- Create the Products table, which stores all products
-- Each product is uniquely identified by an id, and has a name, image, description and category (from the categories table) that it is associated with
-- A product's default image will be a picture of a vanilla ice cream carton
-- Keep track of the owner (i.e. creator of a product) of a product, as this person will be the only one allowed to update that product's information
CREATE TABLE Products (
    id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image_url VARCHAR(512) NOT NULL DEFAULT 'db/data/images/vanilla.webp',
    description VARCHAR NOT NULL,
    category_name VARCHAR(64) REFERENCES Categories(name),
    owner INT NOT NULL REFERENCES Users(id)
);

-- Create the Purchases table, which stores information about line items for users
-- A line item exists in a user's cart, saved-for-later page, or as part of a previously-placed order
-- Order_status can be 'Ordered', 'In Cart', or 'Saved for later'
-- By default, set time_purchased to the current time (and update as it is saved for later or when the order is place). Truncate the timestamp to only extend to the seconds place for improved readability.
-- Each purchase is uniquely identified by a purchase id
-- Fulfillment time is NULL unless an order has been fulfilled (this is used to track order fulfillment)
CREATE TABLE Purchases (
    id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    User_id INT NOT NULL REFERENCES Users(id),
    Product_id INT NOT NULL REFERENCES Products(id),
    time_purchased timestamp without time zone DEFAULT DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5'),
    Seller_id INT NOT NULL REFERENCES Sellers(Seller_id),
    fulfillment_time timestamp without time zone,
    quantity INT NOT NULL,
    order_status VARCHAR(255) NOT NULL
);

-- Create the ReviewsSeller table, which contains all Seller reviews
-- Use User_id and Seller_id as the primary key, as a user can only review a seller once (though the user will be allowed to update that review)
-- Set review date to the current (truncated) time by default, so a review's time is saved as the time the review was submitted
-- Store the rating (between 0 and 5), and reason for the rating (which we call 'review')
CREATE TABLE ReviewsSeller
(User_id INT REFERENCES Users(id),
 Seller_id INT REFERENCES Sellers(Seller_id),
 reviewdate TIMESTAMP without time zone NOT NULL DEFAULT DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5'),
 rating INT NOT NULL,
 review VARCHAR(512),
 PRIMARY KEY(User_id, Seller_id)
);

-- Create the ReviewsProduct table, which contains all product reviews
-- Use User_id and Product_id as the primary key, as a user can only review a product once (though the user will be allowed to update that review)
-- Set review date to the current (truncated) time by default, so a review's time is saved as the time the review was submitted
-- Store the rating (between 0 and 5), and reason for the rating (which we call 'review')
CREATE TABLE ReviewsProduct
(User_id INT REFERENCES Users(id),
 Product_id INT REFERENCES Products(id),
 reviewdate TIMESTAMP without time zone NOT NULL DEFAULT DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5'),
 rating INT NOT NULL,
 review VARCHAR(512),
 PRIMARY KEY(User_id, Product_id)
);

-- Keep track of line items for all sellers. That is, the Inventory table contains all (Seller, product) tuples with information about how much of that product a seller has in stock and the price the seller is offering it for.
-- Use primary key of (Seller_id, Product_id), because we assume a seller cannot offer the same product at two different prices
CREATE TABLE Inventory
(Seller_id INTEGER REFERENCES Sellers(Seller_id),
 Product_id INTEGER REFERENCES Products(id),
 quantity_in_stock INTEGER NOT NULL,
 price DECIMAL(10,2) NOT NULL,
 PRIMARY KEY(Seller_id, Product_id)
);

-- Create the FinalPrice table, which references purchases
-- Use this table to store the price of a purchase at the time the purchase was made. This is to ensure that changes to prices made by Sellers do not effect the prices of our historical record of orders.
CREATE TABLE FinalPrice
(
  purchase_id INTEGER REFERENCES Purchases(id) PRIMARY KEY,
  final_price DECIMAL(10,2) NOT NULL
);

-- Create the advertisements table, which will be used for the purpose of generating ads. As it is an additional feature, we did not have time to integrate it with the rest of the database
-- Ads have a nickname set by the seller, as well as a description and image associated with it
-- Clicks keeps track of the number of clicks on the ad, conversions keeps track of the number of times a user purchased a product featured on the ad, and impressions keeps track of the number of viewers for an ad
-- Start and end time keep track of the range dates that the seller wishes for the ad to be displayed on
-- Category and product_id are used to keep track of which product the ad has been created for
-- Keep track of the seller who created the add using a seller id
CREATE TABLE Advertisements (
    id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    seller_id INT,
    product_id INT,
    nickname VARCHAR(255) NOT NULL,
    description VARCHAR,
    image_url VARCHAR,
    category VARCHAR(64) NOT NULL REFERENCES Categories(name),
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    impressions INT DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0
);

--Trigger that enforces every product reviewed must fall between 0 and 5. If the review above or belowe these bounds
--we will raise an exception so that the reviewer is aware of them.
CREATE FUNCTION TF_REVIEWBOUNDSPRODUCT() RETURNS TRIGGER AS $$
BEGIN
  IF New.rating > 5 THEN RAISE EXCEPTION 'rating must fall between 0 and 5';
  END IF;
  If New.rating < 0 THEN RAISE EXCEPTION 'rating must fall between 0 and 5';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER TG_REVIEWBOUNDSPRODUCT
  BEFORE INSERT OR UPDATE ON ReviewsProduct
  FOR EACH ROW
  EXECUTE PROCEDURE TF_REVIEWBOUNDSPRODUCT();

--Trigger that enforces every seller reviewed must fall between 0 and 5. If the review above or belowe these bounds
--we will raise an exception so that the reviewer is aware of them.
CREATE FUNCTION TF_REVIEWBOUNDSSELLER() RETURNS TRIGGER AS $$
BEGIN
  IF New.rating > 5 THEN RAISE EXCEPTION 'rating must fall between 0 and 5';
  END IF;
  If New.rating < 0 THEN RAISE EXCEPTION 'rating must fall between 0 and 5';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER TG_REVIEWBOUNDSELLER
  BEFORE INSERT OR UPDATE ON ReviewsSeller
  FOR EACH ROW
  EXECUTE PROCEDURE TF_REVIEWBOUNDSSELLER();


--Trigger that enforces that every user has enough balance to withdraw
CREATE FUNCTION TF_NEGBALANCE() RETURNS TRIGGER AS $$
BEGIN
  IF new.balance < 0 THEN RAISE EXCEPTION 'withdraw amount greater than balance';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER TG_NEGBALANCE
  BEFORE UPDATE ON Users
  FOR EACH ROW
  EXECUTE PROCEDURE TF_NEGBALANCE();

-- Enforce that a User's purchase cannot overdraw from a Seller's inventory
-- CREATE FUNCTION TF_INVENTORYCHECK() RETURNS TRIGGER AS $$
BEGIN
  IF New.order_status = 'Ordered' AND NOT EXISTS(SELECT * FROM Inventory WHERE New.Product_id = Product_id AND New.Seller_id = Seller_id AND New.quantity <= quantity_in_stock) THEN RAISE EXCEPTION 'seller % does not have the inventory', New.Seller_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER TG_INVENTORYCHECK
  BEFORE INSERT OR UPDATE ON Purchases
  FOR EACH ROW
  EXECUTE PROCEDURE TF_INVENTORYCHECK();

-- Enforce that order details cannot change once the order has been placed
-- I removed this as it makes it impossible for a seller to fulfill an order
-- CREATE FUNCTION TF_ORDERCHECK() RETURNS TRIGGER AS $$
-- BEGIN
--   IF Old.order_status = 'Ordered' THEN RAISE EXCEPTION 'cannot update already placed orders';
--   END IF;
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- CREATE TRIGGER TG_ORDERCHECK
--   BEFORE UPDATE OR DELETE ON Purchases
--   FOR EACH ROW
--   EXECUTE PROCEDURE TF_ORDERCHECK();

-- Enforce that Users can only review Sellers from whom they have purchased items
CREATE FUNCTION TF_KNOWSSELLER() RETURNS TRIGGER AS $$
BEGIN
  IF NOT EXISTS(SELECT * FROM Purchases AS R WHERE New.User_id = R.User_id AND New.Seller_id = R.Seller_id AND R.order_status = 'Ordered') THEN RAISE EXCEPTION 'User % has not purchased from Seller %', New.User_id, New.Seller_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER TG_KNOWSSELLER
  BEFORE INSERT OR UPDATE ON ReviewsSeller
  FOR EACH ROW
  EXECUTE PROCEDURE TF_KNOWSSELLER();

-- Enforce that Users can only review Sellers from whom they have purchased items
CREATE FUNCTION TF_BOUGHTPRODUCT() RETURNS TRIGGER AS $$
BEGIN
  IF NOT EXISTS(SELECT * FROM Purchases AS R WHERE New.User_id = R.User_id AND New.Product_id = R.Product_id AND R.order_status = 'Ordered') THEN RAISE EXCEPTION 'User % has not purchased Product %', New.User_id, New.Product_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER TG_BOUGHTPRODUCT
  BEFORE INSERT OR UPDATE ON ReviewsProduct
  FOR EACH ROW
  EXECUTE PROCEDURE TF_BOUGHTPRODUCT();
