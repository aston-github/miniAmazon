from flask import current_app as app
from sqlalchemy import text



class Purchase:
    def __init__(self, id, uid, pid, time_purchased, sid, fulfillment_time, quantity, status, final_price):
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_purchased = time_purchased
        self.sid = sid
        self.fulfillment_time = fulfillment_time
        self.quantity = quantity
        self.status = status
        self.final_price = final_price

    # Get a purchase from its purchase ID.
    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT *
FROM Purchases
WHERE id = :id
''',
                              id=id)
        return Purchase(*(rows[0])) if rows else None

    # Get all of a user's purchases since a provided date and time
    @staticmethod
    def get_all_by_uid_since(User_id, since):
        rows = app.db.execute('''
SELECT id, User_id, Product_id, time_purchased, Seller_id, fulfillment_time, quantity, order_status, final_price
FROM Purchases JOIN FinalPrice ON Purchases.id = FinalPrice.purchase_id
WHERE User_id = :User_id
AND time_purchased >= :since
AND order_status != 'In cart'
ORDER BY time_purchased DESC
''',
                              User_id=User_id,
                              since=since)
        return [Purchase(*row) for row in rows]

    # Get all of a user's cart contents and information on them
    @staticmethod
    def get_uid_cart(User_id):
        rows = app.db.execute('''
SELECT Products.id AS id, Products.name AS name, Inventory.price AS price, Purchases.quantity AS quantity, Purchases.id AS purchase_id, Inventory.Seller_id AS Seller_id, Products.image_url AS image_url
FROM Purchases JOIN Products ON Purchases.Product_id = Products.id JOIN Inventory ON Inventory.Product_id = Products.id
WHERE Purchases.User_id = :User_id
AND Purchases.Seller_id = Inventory.Seller_id
AND Purchases.order_status = 'In cart'
ORDER BY Products.id
''',
                              User_id=User_id)
        return rows #Is "if rows else None" needed?

    # Get the total price of all items in a user's cart
    @staticmethod
    def get_cart_total(User_id): #QUERY IS WRONG
        rows = app.db.execute('''
SELECT SUM(Inventory.price * Purchases.quantity) AS total
FROM Purchases JOIN Inventory ON Inventory.Product_id = Purchases.Product_id
WHERE Purchases.User_id = :User_id
AND Purchases.Seller_id = Inventory.Seller_id
AND Purchases.order_status = 'In cart'
''',
                              User_id=User_id)
        return rows[0][0] if rows else 0

    # Delete a row from Purchases table, used when deleting items from cart
    @staticmethod
    def delete_purchase_item(id):
        app.db.execute('''
DELETE FROM Purchases
WHERE id = :id
RETURNING *;
''',
                              id=id)
        return None

    # Increment line item quantity in cart
    @staticmethod
    def increment_quantity(id):
        app.db.execute('''
UPDATE Purchases
SET quantity = quantity + 1
WHERE id = :id
RETURNING *;
''',
                              id=id)
        return None

    # Decrement line item quantity in cart
    @staticmethod
    def decrement_quantity(id):
        app.db.execute('''
UPDATE Purchases
SET quantity = quantity - 1
WHERE id = :id
RETURNING *;
''',
                              id=id)
        return None

    @staticmethod
    def get_incart_by_uid(User_id, pid, sid):
        rows = app.db.execute('''
SELECT User_id
FROM Purchases
WHERE User_id = :User_id
AND Seller_id = :Seller_id
AND Product_id = :Product_id
AND order_status = 'In cart'
''',
                              User_id=User_id,
                              Product_id = pid,
                              Seller_id = sid
                              )
        updatedRows = []
        for x in rows:
            updatedRows.append(x[0])
        return updatedRows

    # Get's a specicic order based on uid of customer and time it was placed. If called by a seller, will only select order items that were provided by the seller.
    # Otherwise, shows all items in the order.
    @staticmethod
    def get_order(User_id, time, seller_id):
        if seller_id:
            rows = app.db.execute('''
            SELECT pu.id, pu.Product_id, pu.Seller_id, pr.name, pu.time_purchased, pu.fulfillment_time, pu.quantity, pu.order_status, f.final_price, pr.image_url
            FROM Purchases pu JOIN FinalPrice f ON pu.id = f.purchase_id JOIN Products pr ON pu.Product_id = pr.id
            WHERE pu.User_id = :User_id AND pu.Seller_id = :seller_id
            AND pu.time_purchased = :time_purchased
            ''',
                                        User_id=User_id,
                                        time_purchased = time,
                                        seller_id = seller_id
                                        )
        else:
            rows = app.db.execute('''
            SELECT pu.id, pu.Product_id, pu.Seller_id, pr.name, pu.time_purchased, pu.fulfillment_time, pu.quantity, pu.order_status, f.final_price, pr.image_url
            FROM Purchases pu JOIN FinalPrice f ON pu.id = f.purchase_id JOIN Products pr ON pu.Product_id = pr.id
            WHERE pu.User_id = :User_id
            AND pu.time_purchased = :time_purchased
            ''',
                                        User_id=User_id,
                                        time_purchased = time
                                        )
        return rows

    # Get the total price of items in an order.
    @staticmethod
    def get_order_total(User_id, time):
        rows = app.db.execute('''
SELECT SUM(final_price * quantity) FROM
(SELECT pu.id, pu.Product_id, pu.Seller_id, pr.name, pu.time_purchased, pu.fulfillment_time, pu.quantity quantity, pu.order_status, f.final_price final_price
FROM Purchases pu JOIN FinalPrice f ON pu.id = f.purchase_id JOIN Products pr ON pu.Product_id = pr.id
WHERE pu.User_id = :User_id
AND pu.time_purchased = :time_purchased) AS order_items
''',
                              User_id=User_id,
                              time_purchased = time
                              )
        return rows[0][0] if rows else 0

    # Place order transaction
    @staticmethod
    def place_order(curr_user, items, time, total):
        with app.db.engine.begin() as conn:
            try:
                # User.change_balance(current_user.id, 'withdraw', total) #Decrement buyer's balance
                conn.execute(text("""
    UPDATE Users
    SET balance = balance - ROUND(:amount, 2)
    WHERE id = :id
    RETURNING id
    """),
                                dict(id = curr_user,
                                amount = total))
                for item in items: #Increment each seller's balance
                    purchase_amount = item[2] * item[3]
                    # User.change_balance(item[5], 'deposit', purchase_amount)
                    conn.execute(text("""
        UPDATE Users
        SET balance = balance + ROUND(:amount, 2)
        WHERE id = :id
        RETURNING id
        """),
                                    dict(id = item[5],
                                    amount = purchase_amount))
                for i in items:
                    product_id = i[0]
                    price = i[2]
                    purchase_id = i[4]
                    seller_id = i[5]
                    conn.execute(text('''
        UPDATE Inventory
        SET quantity_in_stock = quantity_in_stock - (SELECT quantity FROM Purchases WHERE id = :purchase_id)
        WHERE Seller_id = :seller_id AND Product_id = :product_id
        RETURNING *;
        '''),
                                      dict(product_id=product_id,
                                      purchase_id=purchase_id,
                                      seller_id=seller_id
                                      ))

                    conn.execute(text('''
        UPDATE Purchases
        SET order_status = 'Ordered', time_purchased = :time
        WHERE id = :purchase_id
        RETURNING *;
        '''),
                                      dict(purchase_id=purchase_id,
                                      time=time
                                      ))

                    conn.execute(text('''
        INSERT INTO FinalPrice
        VALUES (:purchase_id, :price)
        RETURNING *;
        '''),
                                      dict(purchase_id=purchase_id,
                                      price=price
                                      ))
            except Exception as e:
                print(str(e))
                conn.rollback()
                return None
        return None

    # Saves an item for later, removing from cart
    @staticmethod
    def save_for_later(id):
        app.db.execute('''
UPDATE Purchases
SET order_status = 'Saved'
WHERE id = :id
RETURNING *;
''',
                              id=id)

    # Gets user's saved for later items
    @staticmethod
    def get_saved_for_later(User_id):
        rows = app.db.execute('''
SELECT Products.id AS id, Products.name AS name, Inventory.price AS price, Purchases.quantity AS quantity, Purchases.id AS purchase_id, Inventory.Seller_id AS Seller_id
FROM Purchases JOIN Products ON Purchases.Product_id = Products.id JOIN Inventory ON Inventory.Product_id = Products.id
WHERE Purchases.User_id = :User_id
AND Purchases.Seller_id = Inventory.Seller_id
AND Purchases.order_status = 'Saved'
ORDER BY Products.id
''',
                              User_id=User_id)
        return rows

    # Adds a saved item back to cart
    @staticmethod
    def add_saved_to_cart(id):
        app.db.execute('''
UPDATE Purchases
SET order_status = 'In cart'
WHERE id = :id
RETURNING *;
''',
                              id=id)
        return None
