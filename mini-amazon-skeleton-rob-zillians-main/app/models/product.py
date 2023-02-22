from flask import current_app as app
from .user import User
from flask_login import UserMixin

from .user import User
from .purchase import Purchase

class Product:
    def __init__(self, id, name, description, category_name):
        self.id = id
        self.name = name
        self.description = description
        self.category_name = category_name

    #Get the basic information for a product based on an inputted Product_id
    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, name, description, category_name
FROM Products
WHERE id = :id
''',
                              id=id)
        return Product(*(rows[0])) if rows is not None else None

    #Get the basic information for a product if it is a "last chance buy"
    #A "last chance buy" refers to the 20 products with the smallest inventory
    @staticmethod
    def get_rare():
        rows = app.db.execute('''
SELECT id, image_url, name, description, category_name
FROM Products
WHERE id IN
(SELECT Product_id FROM Inventory WHERE quantity_in_stock > 0 ORDER BY quantity_in_stock
LIMIT 20);
''',
)
        return rows

    #Get number of in stock listings in Inventory
    @staticmethod
    def get_inventory_size():
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Inventory
WHERE quantity_in_stock > 0;
''',
)
        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products whose name or description contain a keyword - or, whose category is the keyword
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product id, as this will be the default method of getting product information
    #Use the result in the search_results pages to determine the number of paginations to create
    @staticmethod
    def get_info(category, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE (T.category_name = :category
OR T.name LIKE CONCAT('%',:category,'%')
OR T.description LIKE CONCAT('%',:category,'%'))
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.id
''', category = category,
     lowPrice = low,
     highPrice = high,
)
        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products whose name or description contain a keyword - or, whose category is the keyword
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product id
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortedid(category, offset, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE (T.category_name = :category
OR T.name LIKE CONCAT('%',:category,'%')
OR T.description LIKE CONCAT('%',:category,'%'))
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.id
LIMIT 100 OFFSET :offset
''', category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)

        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products whose name or description contain a keyword - or, whose category is the keyword
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product name in ascending order, accounting for case and quotation marks and apostrophes (as a few products have these special characters at the beginning of their name)
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortednameatoz(category, offset, low, high):
        rows = app.db.execute("""
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE (T.category_name = :category
OR T.name LIKE CONCAT('%',:category,'%')
OR T.description LIKE CONCAT('%',:category,'%'))
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY REPLACE(REPLACE(lower(T.name), '"', ''), '''', '') ASC
LIMIT 100 OFFSET :offset
""", category = category,
    offset = offset,
    lowPrice = low,
    highPrice = high,
)

        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products whose name or description contain a keyword - or, whose category is the keyword
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product name in descending order, accounting for case and quotation marks and apostrophes (as a few products have these special characters at the beginning of their name)
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortednameztoa(category, offset, low, high):
        rows = app.db.execute("""
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE (T.category_name = :category
OR T.name LIKE CONCAT('%',:category,'%')
OR T.description LIKE CONCAT('%',:category,'%'))
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY REPLACE(REPLACE(lower(T.name), '"', ''), '''', '') DESC
LIMIT 100 OFFSET :offset
""", category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)

        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products whose name or description contain a keyword - or, whose category is the keyword
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product price in ascending order
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortedpricelow(category, offset, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE (T.category_name = :category
OR T.name LIKE CONCAT('%',:category,'%')
OR T.description LIKE CONCAT('%',:category,'%'))
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.price ASC
LIMIT 100 OFFSET :offset
''', category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)
        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products whose name or description contain a keyword - or, whose category is the keyword
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product price in descending order
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortedpricehigh(category, offset, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE (T.category_name = :category
OR T.name LIKE CONCAT('%',:category,'%')
OR T.description LIKE CONCAT('%',:category,'%'))
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.price DESC
LIMIT 100 OFFSET :offset
''', category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)

        return rows

    #Based on a specific product id, get all (Seller, price, quantity) tuples for the product
    #Used by the detailed product page for a given product
    @staticmethod
    def get_all_by_vendor(id):
        rows = app.db.execute('''
SELECT seller_id, price, quantity_in_stock
FROM Inventory
WHERE product_id = :id
''', id = id,
)
        return rows

    #Based on a specific product id, get all (user, rating, review, timestamp) tuples for the product - i.e. get all reviews for a product
    #Used by the detailed product page for a given product
    @staticmethod
    def get_ratings(id):
        rows = app.db.execute('''
SELECT user_id, rating, review, reviewdate
FROM ReviewsProduct
WHERE product_id = :Product_id
ORDER BY reviewdate DESC
''', Product_id = id,
)
        return rows

    #Get a product's image based on it's id
    #Used by the detailed_product page for a given product
    @staticmethod
    def get_image(id):
        rows = app.db.execute('''
SELECT image_url
FROM Products
WHERE id = :Product_id
''', Product_id = id,
)
        return rows

    #For a given product id, calculate the product's average rating
    #Use on the search results pages in addition to information from the get_info functions
    @staticmethod
    def get_average_rating(id):
        rows = app.db.execute('''
SELECT product_id, AVG(rating)
FROM ReviewsProduct
WHERE ReviewsProduct.product_id = :id
GROUP BY product_id
''', id = id,
)
        return rows

    #Use data from the review form on the detailed product page for a given product to create/ update a review
    #Rating and review are user inputted values
    #If the user has already reviewed the product (checked in line 244), update the user's review
    #If the user has not yet reviewed the product, create a new review
    @staticmethod
    def reviews(uid, pid, rating,review):
        try:
            if uid in User.get_users_by_id(pid):
                rows = app.db.execute("""
UPDATE ReviewsProduct
SET rating = :rating, review = :review, reviewdate = DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5')
WHERE User_id = :User_id
AND Product_id = :Product_id
RETURNING User_id
""",
                                  User_id=uid,
                                  Product_id=pid,
                                  rating=rating,
                                  review = review
                                  )
            else:
                rows = app.db.execute("""
INSERT INTO ReviewsProduct(User_id, Product_id, rating, review)
VALUES(:User_id, :Product_id, :rating, :review)
RETURNING User_id
""",                              User_id=uid,
                                  Product_id=pid,
                                  rating=rating,
                                  review = review
                                  )
            id = rows[0][0]
            print("SUCCESS")
            return User.get(id)
        except Exception as e:
            print(e)
            return None

    #Get a list of information recording the times when a user has purchased a specific product
    #Use to confirm that a user has purchased a product prior to reviewing it
    #If the user has not yet purchased the product, then that user will not be able to review it
    @staticmethod
    def get_purchased_product(uid, pid):
        rows = app.db.execute('''
SELECT *
FROM Purchases
WHERE User_id = :User_id
AND Product_id = :Product_id
AND order_status = 'Ordered'
''',
                              User_id= uid,
                              Product_id = pid)
        return rows

    #Function used to add a purchase to a user's cart from the detailed product page
    #If the user already has the specific item in their cart (from the same seller), then increment the amount of the item in their cart by quantity
    #Otherwise, add a new line item to the user's cart based on the number "quantity"
    @staticmethod
    def purchases(uid, pid, seller_id, quantity):
        try:
            if uid in Purchase.get_incart_by_uid(uid, pid, seller_id):
                rows = app.db.execute("""
UPDATE Purchases
SET quantity = quantity + :quantity
WHERE User_id = :User_id
AND Product_id = :Product_id
AND Seller_id = :seller_id
AND order_status = 'In cart'
RETURNING User_id
""",
                                  User_id=uid,
                                  Product_id= pid,
                                  seller_id = seller_id,
                                  quantity = quantity,
                                  order_status = "In cart"
                                  )
            else:
                rows = app.db.execute("""
INSERT INTO Purchases(User_id, Product_id, seller_id, quantity, order_status)
VALUES(:User_id, :Product_id, :seller_id, :quantity, :order_status)
RETURNING User_id
""",
                                  User_id=uid,
                                  Product_id=pid,
                                  seller_id = seller_id,
                                  quantity = quantity,
                                  order_status = "In cart"
                                  )
            id = rows[0][0]
            print("SUCCESS")
            print(User.get(id))
            return User.get(id)
        except Exception as e:
            print(str(e))
            return None

    #Used to decrement a seller's inventory by quantity
    @staticmethod
    def update_inventory(sid, pid, quantity):
        try:
            rows = app.db.execute("""
UPDATE Inventory
SET quantity_in_stock = quantity_in_stock - :quantity
WHERE Seller_id = :sid
AND Product_id = :pid
RETURNING Seller_id
""",
                                  sid=sid,
                                  pid= pid,
                                  quantity = quantity
                                  )
            print("SUCCESS")
            return 1
        except Exception as e:
            print(str(e))
            return None

    #Get all product categories
    #Use for sellers' reference when creating a new product (as categories are pre-defined)
    @staticmethod
    def get_all_categories():
        rows = app.db.execute("""
SELECT name
FROM Categories
ORDER BY name
""",
                                  )
        return rows

    #Use to add a product into a seller's inventory
    #Quantity refers to the amount of the product that the seller wants to add to the inventory
    #Price refers to the price that the sellers wish to sell the inventoy at
    @staticmethod
    def add_to_inventory(seller_id, pid, quantity, price):
        try:
            rows = app.db.execute("""
INSERT INTO Inventory(Seller_id, Product_id, quantity_in_stock, price)
VALUES(:sid, :pid, :quantity, :price)
RETURNING Seller_id
""",
                                  sid = seller_id,
                                  pid = pid,
                                  quantity = quantity,
                                  price = price)
            print("SUCCESS")
            return 1
        except Exception as e:
            print(e)
            return None

    #Create a new product before it is added to a seller's inventory
    #Use on the add product page with the add_to_inventory function
    #The owner id is kept track of, so that only the seller who creates the product can update it
    @staticmethod
    def create_product(name, description, image_url, category, oid):
        try:
            rows = app.db.execute("""
INSERT INTO Products(name, description, image_url, category_name, owner)
VALUES(:name, :description, :image_url, :category, :seller_id)
RETURNING :seller_id
""",
                                  name = name,
                                  description = description,
                                  image_url=image_url,
                                  category = category,
                                  seller_id = oid)
            print("SUCCESS")
            return 1
        except Exception as e:
            print(e)
            return None

    #Check if a product exists when attempting to create it.
    @staticmethod
    def exists(name, description, category):
        rows = app.db.execute("""
SELECT *
FROM Products
WHERE name = :name
AND description = :description
AND category_name = :category
""",
                                  name = name,
                                  description = description,
                                  category = category,
                                  )
        return rows

    #Check if a product exists before creating a new version of it
    #A product "exists" already if the new product shares the same name, description and category as the old product
    @staticmethod
    def edit_product(sid, pid, name, description, image_url, category_name):
        if not Product.exists(name, description, category_name):
            try:
                owner = app.db.execute("""
                SELECT owner
                FROM products
                WHERE id = :pid
                """,   pid=pid)

                if owner[0][0] == sid:
                    rows = app.db.execute("""
                    UPDATE products
                    SET name = :name, description = :description, image_url = :image_url, category_name = :category_name
                    WHERE id = :pid
                    RETURNING id
                    """,
                                        pid=pid,
                                        name=name,
                                        description=description,
                                        image_url=image_url,
                                        category_name=category_name
                                        )
                print("SUCCESS")
                return 1
            except Exception as e:
                print(e)
                return None
        else:
            return None

    #Get a product's id based on it's name, description and category
    #Use to add the product to a seller's inventory after it has just been created on the add product page
    @staticmethod
    def get_id(name, description, category):
        rows = app.db.execute('''
SELECT id
FROM Products
WHERE name = :name
AND description = :description
AND category_name = :category
''',
                              name = name,
                              description = description,
                              category = category)
        return rows[0][0]

    #Get the average reating for all sellers
    #Use to report average seller ratings on the detailed product page
    @staticmethod
    def get_average_rating_seller():
        rows = app.db.execute('''
SELECT Seller_id, CAST(AVG(rating) AS DECIMAL(10,2))
FROM ReviewsSeller
GROUP BY Seller_id
''',
)
        return rows

    #Get all categories that begin with a specific letter
    #Some products whose name begins with a whitespace before the first letter, so we check if the second letter of a product's name matches the letter (note: it is previously enforced that the letter is upper-case)
    #Use for the browse by category button
    @staticmethod
    def get_all_categories_with_products(let):
        rows = app.db.execute("""
SELECT DISTINCT T.category_name
FROM (Categories JOIN Products ON Categories.name = Products.category_name) as T
WHERE T.category_name LIKE CONCAT(:letter,'%')
OR T.category_name LIKE CONCAT('_',:letter,'%')
ORDER BY T.category_name
""",
                    letter = let,
                                  )
        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products belonging to a specified category
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product id, as this will be the default method of getting product information
    #Use the result in the search_results pages to determine the number of paginations to create
    @staticmethod
    def get_info_cat(category, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE T.category_name = :category
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.id
''', category = category,
     lowPrice = low,
     highPrice = high,
)
        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products belonging to a specified category
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product id
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortedid_cat(category, offset, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE T.category_name = :category
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.id
LIMIT 100 OFFSET :offset
''', category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)

        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products belonging to a specified category
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product name in ascending order, accounting for case and quotation marks and apostrophes (as a few products have quotations at the beginning of their name)
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortednameatoz_cat(category, offset, low, high):
        rows = app.db.execute("""
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE T.category_name = :category
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY REPLACE(REPLACE(lower(T.name), '"', ''), '''', '') ASC
LIMIT 100 OFFSET :offset
""", category = category,
    offset = offset,
    lowPrice = low,
    highPrice = high,
)

        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products belonging to a specified category
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product name in descending order, accounting for case and quotation marks and apostrophes (as a few products have these special characters at the beginning of their name)
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortednameztoa_cat(category, offset, low, high):
        rows = app.db.execute("""
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE T.category_name = :category
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY REPLACE(REPLACE(lower(T.name), '"', ''), '''', '') DESC
LIMIT 100 OFFSET :offset
""", category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)

        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products belonging to a specified category
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product price in ascending order
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortedpricelow_cat(category, offset, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE T.category_name = :category
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.price ASC
LIMIT 100 OFFSET :offset
''', category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)
        return rows

    #Get the id, sellerid, image, name, description, category, and price for all products belonging to a specified category
    #Filter by the user-inputted lower bound (low) and upper bound (high), or the default program-set values
    #Order by product price in descending order
    #Offset is determined from the products.py file based on the current page number a user is viewing
    #Output 100 (or fewer) ordered results for the purpose of clean pagination
    #Output to be displayed on the search results page
    @staticmethod
    def get_info_sortedpricehigh_cat(category, offset, low, high):
        rows = app.db.execute('''
SELECT T.id, T.seller_id, T.image_url, T.name, T.description, T.category_name, T.price
FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
WHERE T.category_name = :category
AND T.price >= :lowPrice
AND T.price <= :highPrice
ORDER BY T.price DESC
LIMIT 100 OFFSET :offset
''', category = category,
     offset = offset,
     lowPrice = low,
     highPrice = high,
)

        return rows
