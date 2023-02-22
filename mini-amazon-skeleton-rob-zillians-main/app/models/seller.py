from flask import current_app as app


class Seller:
    def __init__(self, id):
        self.id = id
    
    @staticmethod
    def get(id):
        rows = app.db.execute('''
        SELECT seller_id
        FROM Sellers
        WHERE seller_id = :id
        ''', id=id)
        return rows[0][0] if rows is not None else None

    # Get all seller IDs. Used to check whether a user is a seller or not.
    @staticmethod
    def get_all():
        rows = app.db.execute('''
        SELECT Seller_id
        FROM Sellers
        ''',)
        updatedRows = []
        for x in rows:
            updatedRows.append(x[0])
        return updatedRows

    
    # Get relevant details to display on a seller's inventory page for all products they currently have.
    @staticmethod
    def get_inventory(id, sort, d):
        # If sort is under 3, then we are sorting by an integer value. This distinction is made because the CASE function can only return one data type
        if d and sort < 3:
            rows = app.db.execute('''
            SELECT id, quantity_in_stock, price, name, description, category_name, owner
            FROM (Inventory JOIN Products ON Inventory.Product_id = Products.id)
            WHERE inventory.seller_id = :id
            ORDER BY 
                CASE WHEN :sort = 0 THEN id
                    WHEN :sort = 1 THEN quantity_in_stock
                    WHEN :sort = 2 THEN price
                END
            DESC, id ASC
            ''',    id=id,
                    sort=sort)
        # Otherwise, given d=1, we want to sort by a string column.
        elif d:
                        rows = app.db.execute('''
            SELECT id, quantity_in_stock, price, name, description, category_name, owner
            FROM (Inventory JOIN Products ON Inventory.Product_id = Products.id)
            WHERE inventory.seller_id = :id
            ORDER BY 
                CASE
                    WHEN :sort = 3 THEN UPPER(name)
                    WHEN :sort = 4 THEN UPPER(description)
                    WHEN :sort = 5 THEN UPPER(category_name)
                END
            DESC, id ASC
            ''',    id=id,
                    sort=sort)
        # d (=1 if DESC is desired) is not set, so replicate the above two checks by ASCend instead.
        elif sort < 3:
                        rows = app.db.execute('''
            SELECT id, quantity_in_stock, price, name, description, category_name, owner
            FROM (Inventory JOIN Products ON Inventory.Product_id = Products.id)
            WHERE inventory.seller_id = :id
            ORDER BY 
                CASE WHEN :sort = 0 THEN id
                    WHEN :sort = 1 THEN quantity_in_stock
                    WHEN :sort = 2 THEN price
                END
            ASC, id ASC
            ''',    id=id,
                    sort=sort)
        else:
                        rows = app.db.execute('''
            SELECT id, quantity_in_stock, price, name, description, category_name, owner
            FROM (Inventory JOIN Products ON Inventory.Product_id = Products.id)
            WHERE inventory.seller_id = :id
            ORDER BY 
                CASE
                    WHEN :sort = 3 THEN UPPER(name)
                    WHEN :sort = 4 THEN UPPER(description)
                    WHEN :sort = 5 THEN UPPER(category_name)
                END
            ASC, id ASC
            ''',    id=id,
                    sort=sort)
        return rows if rows is not None else None

    # Allow seller to quickly update their stock from inventory.
    @staticmethod
    def update_quantity(seller_id, product_id, new_quantity):
        rows = app.db.execute("""
        UPDATE Inventory SET quantity_in_stock = :new_quantity
        WHERE Seller_id = :seller_id AND Product_id = :product_id
        RETURNING quantity_in_stock
        """,
                              seller_id=seller_id,
                              product_id=product_id,
                              new_quantity=new_quantity)
        return len(rows) > 0

    # Allow seller to quickly update the price they want to charge from inventory.
    @staticmethod
    def update_price(seller_id, product_id, new_price):
        rows = app.db.execute("""
        UPDATE Inventory SET price = :new_price
        WHERE Seller_id = :seller_id AND Product_id = :product_id
        RETURNING price
        """,
                              seller_id=seller_id,
                              product_id=product_id,
                              new_price=new_price)
        return len(rows) > 0
    
    # Update a line item that is to be fulfilled by a seller, indicating completion of the order on their part. Called from inventory.
    @staticmethod
    def fulfill_order(id, time):
        prev = app.db.execute(""" 
        SELECT order_status, fulfillment_time 
        FROM purchases 
        WHERE id = :id
        """,
        id=id)
        if prev[0][0] != 'Fulfilled':
            rows = app.db.execute("""
            UPDATE purchases SET order_status = 'Fulfilled', fulfillment_time = :time
            WHERE id = :id
            RETURNING order_status, fulfillment_time
            """,
                                id=id,
                                time=time)
        return prev[0]

    # Add an existing product to the seller's inventory from sorted_search_results or search_results in catalogue add mode.
    # The quantity is set to zero so that the seller must indicate that they have some before it gets ordered
    # Price is set to the lowest existing price.
    @staticmethod
    def catalogue_add(seller_id, product_id):
        try:
            rows = app.db.execute("""
            INSERT INTO Inventory(Seller_id, Product_id, quantity_in_stock, price)
            VALUES(:seller_id, :product_id, 0, (SELECT MIN(T.price)
                FROM (Products JOIN Inventory ON Products.id = Inventory.product_id) AS T
                WHERE T.id = :product_id))
            RETURNING product_id
            """,
                                  seller_id=seller_id,
                                  product_id=product_id)
            product_id = rows[0][0]
            return product_id
        except Exception as e:
            print("EXCEPTION")
            print(e)
            return None

    # Cart-guru: Get the seller's current inventory quantity for a product involved in an order.
    # Use to determine whether they have enough in stock to fulfill this order.
    @staticmethod
    def get_inventory_quantity(sid, pid):
        rows = app.db.execute('''
        SELECT quantity_in_stock
        FROM Inventory
        WHERE seller_id = :sid AND product_id = :pid
        ''', 
                              sid=sid,
                              pid=pid
                              )
        return rows[0][0] if rows is not None else 0

    # Remove an item from the seller's inventory.
    @staticmethod
    def remove_item(id, pid):
        app.db.execute('''
        DELETE FROM Inventory
        WHERE seller_id = :id AND product_id = :pid
        RETURNING *
        ''', 
                              id=id,
                              pid=pid
                              )
        return None

    # Get details for a product the seller is editing, including descriptive ones from "Products" and quantity/price.
    @staticmethod
    def get_product(sid, pid):
        rows = app.db.execute('''
        SELECT *
        FROM Products JOIN Inventory ON Products.id = Inventory.product_id
        WHERE Products.id = :pid AND Inventory.seller_id = :sid
        ''',
                              pid=pid,
                              sid=sid
                              )
        return rows[0] if rows is not None else 0

    # Get all orders that a seller is to fulfill or has fulfilled given their id.
    # Use in the seller's sale history page.
    @staticmethod
    def get_sale_history(Seller_id, since, sort, a):
        if a and sort < 2:
            rows = app.db.execute('''
            SELECT purchase_id, User_id, Product_id, time_purchased, Seller_id, fulfillment_time, quantity, order_status, final_price, address, quantity*final_price AS total
            FROM (Purchases JOIN FinalPrice ON Purchases.id = FinalPrice.purchase_id) AS purchase_table
            RIGHT JOIN Users ON purchase_table.User_id = Users.id
            WHERE Seller_id = :Seller_id
            AND time_purchased >= :since
            ORDER BY 
                CASE
                    WHEN :sort = 0 THEN time_purchased
                    WHEN :sort = 1 THEN fulfillment_time
                END
            ASC, purchase_id ASC
            ''',
                                Seller_id=Seller_id,
                                since=since,
                                sort=sort)
        elif a:
            rows = app.db.execute('''
            SELECT purchase_id, User_id, Product_id, time_purchased, Seller_id, fulfillment_time, quantity, order_status, final_price, address, quantity*final_price AS total
            FROM (Purchases JOIN FinalPrice ON Purchases.id = FinalPrice.purchase_id) AS purchase_table
            RIGHT JOIN Users ON purchase_table.User_id = Users.id
            WHERE Seller_id = :Seller_id
            AND time_purchased >= :since
            ORDER BY 
                CASE
                    WHEN :sort = 2 THEN purchase_id
                    WHEN :sort = 3 THEN User_id
                    WHEN :sort = 4 THEN Product_id
                    WHEN :sort = 5 THEN quantity
                    WHEN :sort = 6 THEN final_price
                    WHEN :sort = 7 THEN quantity*final_price
                END
            ASC, purchase_id ASC
            ''',
                                Seller_id=Seller_id,
                                since=since,
                                sort=sort)
        elif sort < 2:
            rows = app.db.execute('''
            SELECT purchase_id, User_id, Product_id, time_purchased, Seller_id, fulfillment_time, quantity, order_status, final_price, address, quantity*final_price AS total
            FROM (Purchases JOIN FinalPrice ON Purchases.id = FinalPrice.purchase_id) AS purchase_table
            RIGHT JOIN Users ON purchase_table.User_id = Users.id
            WHERE Seller_id = :Seller_id
            AND time_purchased >= :since
            ORDER BY 
                CASE
                    WHEN :sort = 0 THEN time_purchased
                    WHEN :sort = 1 THEN fulfillment_time
                END
            DESC, purchase_id ASC
            ''',
                                Seller_id=Seller_id,
                                since=since,
                                sort=sort)
        else:
            rows = app.db.execute('''
            SELECT purchase_id, User_id, Product_id, time_purchased, Seller_id, fulfillment_time, quantity, order_status, final_price, address, quantity*final_price AS total
            FROM (Purchases JOIN FinalPrice ON Purchases.id = FinalPrice.purchase_id) AS purchase_table
            RIGHT JOIN Users ON purchase_table.User_id = Users.id
            WHERE Seller_id = :Seller_id
            AND time_purchased >= :since
            ORDER BY 
                CASE
                    WHEN :sort = 2 THEN purchase_id
                    WHEN :sort = 3 THEN User_id
                    WHEN :sort = 4 THEN Product_id
                    WHEN :sort = 5 THEN quantity
                    WHEN :sort = 6 THEN final_price
                    WHEN :sort = 7 THEN quantity*final_price
                END
            DESC, purchase_id ASC
            ''',
                                Seller_id=Seller_id,
                                since=since,
                                sort=sort)
        return [row for row in rows]
    
    
