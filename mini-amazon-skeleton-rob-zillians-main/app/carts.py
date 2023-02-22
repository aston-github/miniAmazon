from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, FloatField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange, Optional
from flask_babel import _, lazy_gettext as _l

from .models.product import Product
from .models.purchase import Purchase
from .models.user import User
from .models.seller import Seller
from datetime import datetime

from flask import Blueprint
bp = Blueprint('carts', __name__)

#LOAD THE CURRENT USER'S CART PAGE AND CONTENTS
@bp.route('/cart')
def cart():
    contents = Purchase.get_uid_cart(current_user.id)
    total = Purchase.get_cart_total(current_user.id)
    return render_template('cart.html', cart_products = contents, total_price = total)

#PLACE AN ORDER
@bp.route('/place_order')
def place_order():
    contents = Purchase.get_uid_cart(current_user.id)
    total = Purchase.get_cart_total(current_user.id)
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #CHECK BALANCE AND INVENTORY
    user_balance = User.get(current_user.id).balance
    if total > user_balance:
        flash('ERROR: Insufficient funds!')
        print('ERROR: Insufficient funds!')
        return redirect(url_for('carts.cart'))

    for item in contents:
        inventory_quantity = Seller.get_inventory_quantity(item[5], item[0])
        print(inventory_quantity)
        if item[3] > inventory_quantity:
            flash("Insufficient stock for {}".format(item[1]))
            print('Insufficient stock')
            return(redirect(url_for('carts.cart')))

    # #UPDATE BALANCE (ADD TRANSACTION)
    # User.change_balance(current_user.id, 'withdraw', total) #Decrement buyer's balance
    # for item in contents: #Increment each seller's balance
    #     purchase_amount = item[2] * item[3]
    #     User.change_balance(item[5], 'deposit', purchase_amount)

    #UPDATE INVENTORY, ORDER_STATUS, TIME_PURCHASED
    Purchase.place_order(current_user.id, contents, time, total)

    #RENDER ORDER SUMMARY PAGE
    order_summary = Purchase.get_order(current_user.id, time, None)
    return render_template('order.html', order_products = order_summary, total_price = total, statuses = 'Ordered')

@bp.route('/view_order') #FOR VIEWING ORDER FROM A SINGLE ITEM FROM: if (seller is looking) SALE HISTORY else (customer is looking) PURCHASE HISTORY
def view_order():
    time_stamp = request.args.get('time')
    oid = request.args.get('oid')

    # Seller-guru: Determine if a seller is looking for this order by using the user id provided to find the order if one is given.
    seller_view = request.args.get('seller_view')
    if (seller_view):
        order_summary = Purchase.get_order(seller_view, time_stamp, current_user.id)
        total = Purchase.get_order_total(seller_view, time_stamp)
        customer_info_for_seller = User.get_profile(seller_view)
    else:
        order_summary = Purchase.get_order(current_user.id, time_stamp, None)
        total = Purchase.get_order_total(current_user.id, time_stamp)
        customer_info_for_seller = 0

    statuses = list(set(x[7] for x in order_summary))
    if len(statuses) > 1:
        statuses = "Partially Fulfilled"
    elif statuses[0] == "Ordered":
        statuses = "Placed"
    else:
        statuses = "Fulfilled"

    return render_template('order.html', order_products = order_summary, total_price = total, seller_view = seller_view, customer_info = customer_info_for_seller, oid=oid, statuses = statuses)

#DELETE LINE ITEM FROM CART
@bp.route('/delete_cart_item')
def delete_cart_item():
    purchase_id = request.args.get('item')
    print(purchase_id)
    Purchase.delete_purchase_item(purchase_id)
    return redirect(url_for('carts.cart'))

#INCREMENT LINE ITEM QUANTITY
@bp.route('/increment_quantity')
def increment_quantity():
    purchase_id = request.args.get('item')
    # print(purchase_id)
    Purchase.increment_quantity(purchase_id)
    return redirect(url_for('carts.cart'))

#DECREMENT LINE ITEM QUANTITY
@bp.route('/decrement_quantity')
def decrement_quantity():
    purchase_id = request.args.get('item')
    # print(purchase_id)
    Purchase.decrement_quantity(purchase_id)
    return redirect(url_for('carts.cart'))

#SAVE ITEM FOR LATER, REMOVING FROM CART
@bp.route('/save_for_later')
def save_for_later():
    purchase_id = request.args.get('item')
    Purchase.save_for_later(purchase_id)
    return redirect(url_for('carts.cart'))

#LOAD USER'S SAVED FOR LATER PAGE AND ITS CONTENTS
@bp.route('/view_saved_for_later')
def view_saved_for_later():
    contents = Purchase.get_saved_for_later(current_user.id)
    if contents:
        return render_template('saved_for_later.html', saved_products = contents)
    flash('No saved items!')
    return redirect(url_for('carts.cart'))

#REMOVES LINE ITEM FROM SAVED FROM LATER AND ADDS BACK TO CART
@bp.route('/add_saved_to_cart')
def add_saved_to_cart():
    purchase_id = request.args.get('item')
    Purchase.add_saved_to_cart(purchase_id)
    return redirect(url_for('carts.view_saved_for_later'))
