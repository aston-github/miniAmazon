from flask import current_app as app

class Review:
    def __init__(self, uid, target_id, reviewdate, rating, review):
        self.uid = uid
        self.target_id = target_id
        self.reviewdate = reviewdate
        self.rating = rating
        self.review = review

# gets seller reviews sorted by review date, displayed in seller public profiles
    @staticmethod
    def get_seller_reviews(id):
        rows = app.db.execute("""
    SELECT *
    FROM ReviewsSeller
    WHERE Seller_id = :id
    ORDER BY reviewdate
    """,
                                id=id)
        if not rows:  # id not found
            return None
        else:
            return [Review(*(rows[i][0:])) for i in range(len(rows))]

# finds purchases by the user from the seller, verifies a purchase exists and the user can review the seller
    @staticmethod
    def get_purchased_seller(uid, sid):
        rows = app.db.execute('''
        SELECT *
        FROM Purchases
        WHERE User_id = :User_id
        AND Seller_id = :Seller_id
        AND order_status = 'Ordered'
        ''', User_id= uid, Seller_id = sid)
        return rows

# deletes a review of a seller made by some user
    @staticmethod
    def delete_seller_review(uid, sid):
        rows = app.db.execute("""
    DELETE FROM ReviewsSeller
    WHERE User_id = :uid
    AND Seller_id = :sid
    RETURNING *
    """,
                                uid= uid,
                                sid = sid)
        return None

# deletes a review of a product made by some user
    @staticmethod
    def delete_product_review(uid, pid):
        rows = app.db.execute("""
    DELETE FROM ReviewsProduct
    WHERE User_id = :uid
    AND Product_id = :pid
    RETURNING *
    """,
                                uid= uid,
                                pid = pid)
        return None