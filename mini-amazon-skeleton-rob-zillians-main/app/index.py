from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    # get all number of available products for sale:
    inventory_size = Product.get_inventory_size()[0][0]
    rare_products = Product.get_rare()

    ratings = []
    uids = set()
    for row in rare_products:
        avg_rating = []
        rating = Product.get_average_rating(row.id)
        if len(rating) > 0 and row.id not in uids:
            avg_rating.append(rating[0][0])
            avg_rating.append(round(rating[0][1], 2))
            ratings.append(avg_rating)
        if len(rating) == 0 and row.id not in uids:
            avg_rating.append(row.id)
            avg_rating.append("No Reviews")
            ratings.append(avg_rating)

    # render the page by adding information to the index.html file
    return render_template('index.html',
                           rare_products=rare_products,
                           avg_ratings = ratings,
                           inventory_size = inventory_size)
