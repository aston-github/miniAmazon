from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

from .. import login


class User(UserMixin):
    # Create User class with all attributes corresponding to database Users table attributes
    def __init__(self, id, email, firstname, lastname, balance, address):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.balance = balance
        self.address = address

    # authenticates user login using email and password
    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
SELECT password, id, email, firstname, lastname, balance, address
FROM Users
WHERE email = :email
""",
                              email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            # print('HERE')
            return None
        else:
            return User(*(rows[0][1:]))

# get email of user using user id
    @staticmethod
    def get_email(id):
        rows = app.db.execute("""
SELECT email
FROM Users
WHERE id = :id
""",
                              id=id)
        if not rows:  # id not found
            return None
        else:
            return rows[0][0]

#get user id of user from email, used for Venmo feature
    @staticmethod
    def get_id_from_email(email):
        rows = app.db.execute("""
SELECT id
FROM Users
WHERE email = :email
""",
                              email=email)
        if not rows:  # id not found
            return None
        else:
            return rows[0][0]

# get password of a given user id, utilized for password security in edit profile
    @staticmethod
    def get_password(id):
        rows = app.db.execute("""
SELECT password
FROM Users
WHERE id = :id
""",
                              id=id)
        if not rows:  # id not found
            return None
        else:
            return rows[0][0]

# checks if a given email already exists in the database, used in validator to ensure unique emails
    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
SELECT email
FROM Users
WHERE email = :email
""",
                              email=email)
        return len(rows) > 0

# registers a user using register form data, creates a new user with input attribute information
# defaults the new user balance to $0
    @staticmethod
    def register(email, password, firstname, lastname, address):
        try:
            rows = app.db.execute("""
INSERT INTO Users(email, password, firstname, lastname, address, balance)
VALUES(:email, :password, :firstname, :lastname, :address, :balance)
RETURNING id
""",
                                  email=email,
                                  password=generate_password_hash(password),
                                  firstname=firstname,
                                  lastname=lastname,
                                  address = address,
                                  balance = 0)
            id = rows[0][0]
            print("SUCCESS")
            print(User.get(id))
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and
            # reporting needed
            print("EXCEPTION")
            print(e)
            return None

# gets User information given a user id, returns User class
    @staticmethod
    @login.user_loader
    def get(id):
        rows = app.db.execute("""
SELECT id, email, firstname, lastname, balance, address
FROM Users
WHERE id = :id
""",
                              id=id)
        return User(*(rows[0])) if rows else None

# gets User information given a user id, returns 2D array
    @staticmethod
    def get_profile(id):
        try:
            row = app.db.execute("""
    SELECT id, email, firstname, lastname, balance, address
    FROM Users
    WHERE id = :id
    """,
                                  id=id)
            return row
        except Exception as e:
            return None

# given a deposit or withdraw operation, changes user balance by given amount
# exception handling occurs when withdraw trigger encountered (insufficient funds)
# utilized in venmo, deposit, and withdraw features
    @staticmethod
    def change_balance(id, operation, amount):
        print(amount)
        try:
            print("HERE")
            if operation == 'deposit':
                rows = app.db.execute("""
    UPDATE Users
    SET balance = balance + ROUND(:amount, 2)
    WHERE id = :id
    RETURNING id
    """,
                                id = id,
                                amount = amount)
            else:
                rows = app.db.execute("""
    UPDATE Users
    SET balance = balance - ROUND(:amount, 2)
    WHERE id = :id
    RETURNING id
    """,
                                id = id,
                                amount = amount)
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            return None

    @staticmethod
    def venmo(curr_id, reciever, amount):
        print(amount)
        with app.db.engine.begin() as conn:
            try:
                conn.execute(text('UPDATE Users SET balance = balance + ROUND(:amount, 2) WHERE id = :id RETURNING id'),
                                dict(id = reciever,
                                amount = amount))
                print("HERE")
                rows = conn.execute(text('UPDATE Users SET balance = balance - ROUND(:amount, 2) WHERE id = :id RETURNING id'),
                                dict(id = curr_id,
                                amount = amount)).fetchall()
                id = rows[0][0]
                return User.get(id)
            except Exception as e:
                print(str(e))
                conn.rollback()
                return None


# changes User information using edit profile form data
    @staticmethod
    def change_profile(id, email, password, firstname, lastname, address):
        try:
            rows = app.db.execute("""
UPDATE Users
SET email = :email, password = :password, firstname = :firstname, lastname = :lastname, address = :address
WHERE id = :id
RETURNING id
""",
                                  id = id,
                                  email=email,
                                  password=password,
                                  firstname=firstname,
                                  lastname=lastname,
                                  address = address)
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and
            # reporting needed
            print(e)
            return None

# given a user id, checks if the user is a seller and returns the user id if True
# else, return None
# used to change public profile frontend for sellers
    @staticmethod
    def is_seller(id):
        rows = app.db.execute("""
    SELECT Seller_id
    FROM Sellers
    WHERE Seller_id = :id
    """,
                                id=id)
        if not rows:  # id not found
            return None
        else:
            return rows[0][0]

# called when user selects to become seller in profile, adds user id to Sellers table
    @staticmethod
    def become_seller(id):
        rows = app.db.execute("""
        INSERT INTO Sellers VALUES (:id)
        RETURNING Sellers.Seller_id
        """, id=id)
        return rows[0][0]

    #For a given product, get all users that have reviewed the product
    #Use to determine whether a user's review should be updated, or if a new review should be created in the product model
    @staticmethod
    def get_users_by_id(pid):
        rows = app.db.execute("""
    SELECT User_id
    FROM ReviewsProduct
    WHERE Product_id = :pid
    """,
                                  pid=pid)
        updatedRows = []
        for x in rows:
            updatedRows.append(x[0])
        return updatedRows

    @staticmethod
    def get_product_reviews(id):
        rows = app.db.execute('''
        SELECT user_id, product_id, rating, review, reviewdate, name
        FROM ReviewsProduct
        INNER JOIN Products ON ReviewsProduct.product_id = Products.id
        WHERE user_id = :id
        ORDER BY reviewdate DESC
        ''', id = id,
        )
        return rows

    @staticmethod
    def get_seller_reviews(id):
        rows = app.db.execute('''
        SELECT user_id, Seller_id, rating, review, reviewdate, firstname, lastname
        FROM ReviewsSeller
        INNER JOIN Users ON ReviewsSeller.Seller_id = Users.id
        WHERE user_id = :id
        ORDER BY reviewdate DESC
        ''', id = id,
        )
        return rows

    @staticmethod
    def reviewSeller(uid, sid, rating,review):
        try:
            if sid in [review[1] for review in User.get_seller_reviews(uid)]:
                rows = app.db.execute("""
UPDATE ReviewsSeller
SET rating = :rating, review = :review, reviewdate = DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5')
WHERE User_id = :User_id
AND Seller_id = :Seller_id
RETURNING User_id
""",
                                  User_id=uid,
                                  Seller_id=sid,
                                  rating=rating,
                                  review = review
                                  )
            else:
                rows = app.db.execute("""
INSERT INTO ReviewsSeller(User_id, Seller_id, rating, review)
VALUES(:User_id, :Seller_id, :rating, :review)
RETURNING User_id
""",                              User_id=uid,
                                  Seller_id=sid,
                                  rating=rating,
                                  review = review
                                  )
            id = rows[0][0]
            print("SUCCESS")
            print(User.get(id))
            return User.get(id)
        except Exception as e:
            print(e)
            return None
