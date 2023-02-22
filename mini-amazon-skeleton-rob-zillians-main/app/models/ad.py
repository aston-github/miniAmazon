### ADS API 
# 
# Methods to get ads, then methods to change them.
# You should put pages that change ads using these methods or ones you create into ads.py,
# while pages that simply display a random ad should just integrate it with the instructions at the top of ads.py
# The only thing you need to do for the latter to work is supply a category name somehow.
#
#  ###

from flask import current_app as app

import random

class Ad:
    def __init__(self, id):
        self.id = id

    #Get information about a specific ad if a seller wants to view or edit it
    @staticmethod
    def get_ad(id):
        rows = app.db.execute('''
        SELECT *
        FROM Advertisements
        WHERE id = :id
        ''',
                                id=id
                                )
        return rows[0] if rows is not None else 0
        
    # Get information on all ads a seller has running.
    # The code flow that gets to the sorting buttons is similar in all cases. Cases must be separated by type, so you might count across
    # [id pid sid time_added name price description] 
    # like id 0 pid 1 sid 2 price 3
    # time_added 4
    # name 5 description 6
    # and then create enough if blocks and case statements to cover it all, then put those into the links like "s=4" for all of the buttons in your table header.
    @staticmethod
    def get_all_ads_manager(seller_id, sort, d):
        # If sort is under 3, then we are sorting by an integer value. This distinction is made because the CASE function can only return one data type
        if d and (sort < 7):
            rows = app.db.execute('''
            SELECT *
            FROM Advertisements
            WHERE advertisements.seller_id = :seller_id
            ORDER BY
                CASE
                    WHEN :sort = 0 THEN id
                    WHEN :sort = 1 THEN product_id
                    WHEN :sort = 4 THEN impressions
                    WHEN :sort = 5 THEN clicks
                    WHEN :sort = 6 THEN conversions
                END
            DESC, id ASC
            ''',    seller_id=seller_id,
                    sort=sort)
        # Otherwise, given d=1, we want to sort by a string column.
        elif d:
                        rows = app.db.execute('''
            SELECT *
            FROM Advertisements
            WHERE advertisements.seller_id = :seller_id
            ORDER BY
                CASE
                    WHEN :sort = 7 THEN UPPER(nickname)
                    WHEN :sort = 8 THEN UPPER(description)
                    WHEN :sort = 9 THEN UPPER(category)
                END
            DESC, id ASC
            ''',    seller_id=seller_id,
                    sort=sort)
        # d (=1 if DESC is desired) is not set, so replicate the above two checks by ASCend instead.
        elif sort < 7:
                        rows = app.db.execute('''
            SELECT *
            FROM Advertisements
            WHERE advertisements.seller_id = :seller_id
            ORDER BY
                CASE
                    WHEN :sort = 0 THEN id
                    WHEN :sort = 1 THEN product_id
                    WHEN :sort = 4 THEN impressions
                    WHEN :sort = 5 THEN clicks
                    WHEN :sort = 6 THEN conversions
                END
            ASC, id ASC
            ''',    seller_id=seller_id,
                    sort=sort)
        else:
                        rows = app.db.execute('''
            SELECT *
            FROM Advertisements
            WHERE advertisements.seller_id = :seller_id
            ORDER BY
                CASE
                    WHEN :sort = 7 THEN UPPER(nickname)
                    WHEN :sort = 8 THEN UPPER(description)
                    WHEN :sort = 9 THEN UPPER(category)
                END
            ASC, id ASC
            ''',    seller_id=seller_id,
                    sort=sort)
        return rows if rows is not None else None

    # Create an ad but leave start_time and end_time empty. These are for the "schedule ad" method
    @staticmethod
    def create_ad(sid, pid, nickname, description, image_url, category):
        rows = app.db.execute("""
            INSERT INTO Advertisements(seller_id, product_id, nickname, description, image_url, category)
            VALUES(:sid, :pid, :nickname, :description, :image_url, :category)
            RETURNING id
            """,
                                sid=sid,
                                pid=pid,
                                nickname=nickname,
                                description=description,
                                image_url=image_url,
                                category=category
                                )
        return rows[0][0] if rows is not None else 0

    # Edit an ad but leave start_time and end_time empty. These are for the "schedule ad" method
    @staticmethod
    def edit_ad(sid, id, nickname, description, image_url, category):
        rows = app.db.execute("""
            UPDATE Advertisements SET
            seller_id = :sid,
            nickname = :nickname,
            description = :description,
            image_url = :image_url,
            category = :category
            WHERE id = :id
            RETURNING id
            """,
                                sid=sid,
                                id=id,
                                nickname=nickname,
                                description=description,
                                image_url=image_url,
                                category=category
                                )
        return rows[0][0] if rows is not None else 0

    # Edit an ad but leave start_time and end_time empty. These are for the "schedule ad" method
    @staticmethod
    def schedule_ad(id, start_time, end_time):
        rows = app.db.execute("""
            UPDATE Advertisements SET
            start_time = :start_time,
            end_time = :end_time
            WHERE id = :id
            RETURNING id
            """,
                                id=id,
                                start_time=start_time,
                                end_time=end_time
                                )
        return rows[0][0] if rows is not None else 0

    #Get information about a specific ad if a seller wants to view or edit it
    @staticmethod
    def get_ad_for_category(category):
        ret=0
        rows = app.db.execute('''
        SELECT *
        FROM Advertisements
        WHERE category=:category
        AND start_time < DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5')
        AND end_time > DATE_TRUNC('second', current_timestamp AT TIME ZONE 'UTC+5')
        ''', 
                                category=category
                                )
        if rows:
            ret = rows[random.randint(0, len(rows) - 1)]
        return ret

    # Edit an ad but leave start_time and end_time empty. These are for the "schedule ad" method
    @staticmethod
    def increment_impressions(id):
        rows = app.db.execute("""
            UPDATE Advertisements
            SET impressions = impressions + 1
            WHERE id = :id
            RETURNING *;
            """,
                                id=id
                                )
        return None

    # Edit an ad but leave start_time and end_time empty. These are for the "schedule ad" method
    @staticmethod
    def increment_clicks(id):
        rows = app.db.execute("""
            UPDATE Advertisements
            SET clicks = clicks + 1
            WHERE id = :id
            RETURNING seller_id
            """,
                                id=id
                                )
        return rows[0][0]

    # Edit an ad but leave start_time and end_time empty. These are for the "schedule ad" method
    @staticmethod
    def increment_cart(id, quantity):
        rows = app.db.execute("""
            UPDATE Advertisements
            SET conversions = conversions + :quantity
            WHERE id = :id
            RETURNING id
            """,
                                id=id,
                                quantity=quantity
                                )
        return None
