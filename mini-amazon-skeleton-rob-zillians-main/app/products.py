from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_wtf import FlaskForm
from flask_login import login_user, logout_user, current_user
from wtforms import IntegerField, StringField, SubmitField, FloatField
from wtforms.validators import ValidationError, DataRequired, Length, Optional, NumberRange
from flask_babel import _, lazy_gettext as _l
from datetime import datetime
from operator import itemgetter, attrgetter

from .models.user import User
from .models.seller import Seller
from .models.product import Product
from .carts import cart
from .users import login

from .models.ad import Ad

from flask import Blueprint
bp = Blueprint('products', __name__)

class priceForm(FlaskForm):
    #Create a class that will be used for the creation of a price filter on the search_results page
    #The lowPrice field accepts the lower bound of the price filter, it must be greater than 0 and less than the default upper bound: 1000000000 (see line 31)
    #The highPrice field accepts the upper bound of the price filter, it must be greater than the default lower bound: 0 (see line 31)
    #Both lowPrice and highPrice are optional, as I initialize a default range of [0, 1000000000], which should include all possible search results (the most expensive product is around $500)
    lowPrice = FloatField(_l('Low Price'), validators=[Optional(), NumberRange(min = 0, max = 999999999, message = "Cannot filter by a negative price or minimum price filter too high")])
    highPrice = FloatField(_l('High Price'), validators = [Optional(), NumberRange(min = 0.01, message = "Cannot filter by a negative price")])
    submit1 = SubmitField(_l('Submit'))

# This function allows users to search by some keyword, it will return product information based on
# whether or not the keyword is contained in the name or description of the product, or the keyword is a product category
@bp.route('/search_results', methods=['GET', 'POST'])
def search_results():
    #Recieve the search term from the search bar
    input1 = request.args.get('search')

    #Initialize default values for the pricing filter
    low = 0
    high = 1000000000

    #Initialize an offset value for the purpose of pagination - the offset value will be zero following a user's search
    #product_setup contains all products that match the search result
    #product_info contains the first 100 products (sorted by product id) that match the search results, which will be displayed on the first page
    offset = 0
    product_setup = Product.get_info(input1, low, high)
    product_info = Product.get_info_sortedid(input1, offset, low, high)

    #Calculate the number of pages. Since 100 items are displayed per page, take the cieling of the total number of products that match the search results by taking the floor and adding 1
    #Initialize a list from 1 to the total number of pages for this search term, which will be used by the template file to generate links to more pages at the bottom of this page
    num_pages = (len(product_setup)//100) + 1
    list_pages = []
    for x in range(num_pages):
        y = x + 1
        list_pages.append(y)

    #Initialize a list and set, which are later used for getting average ratings
    ratings = []
    uids = set()

    # Seller-guru: Preserve catalogue add mode if the seller chooses to search for products to add using the header search bar, which leads to this page.
    catalogue_add = 0
    catalogue_add = request.args.get('ca')

    #Initialize the Price Filter form
    #Check if the form is valid based on previously described validators
    #If valid and both a lower and upper bound are inputted by the user, make sure that the lower bound is smaller than the upper bound
    #If the lower bound is greater than the upper bound, return the same page with a message
    #If the inputs are otherwise valid, go to a new page, which contains the filtered products sorted by price from low - high
    form = priceForm()
    if form.validate_on_submit():
        if form.lowPrice.data and form.highPrice.data and form.lowPrice.data > form.highPrice.data:
            flash("Filtering failed, upper bound must be greater than lower bound")
            return redirect(url_for('products.sorted_search_results', search = input1, sort = 0,
                                        page = 1, lowprice = low, highprice = high, ca = catalogue_add))
        return redirect(url_for('products.sorted_search_results', search = input1, sort = 2,
                                        page = 1, lowprice = form.lowPrice.data, highprice = form.highPrice.data, ca = catalogue_add))

    # Seller-guru: Display sorted_search_results instead so we only have to mess with one page.
    if catalogue_add:
        return redirect(url_for('products.sorted_search_results', search = input1, sort = 0,
                                        page = 1, lowprice = form.lowPrice.data, highprice = form.highPrice.data, ca = catalogue_add))

    #Generate a list of lists, where each element is a [product_id, average rating] pair, in order of the products that will be displayed on the page
    #If a product id does not correspond to any ratings, then the average rating will be set to "No Reviews"
    #Since different sellers can sell the same product, and the product will have the same average rating for every seller, only add 1 element per product id - check this with the uids set
    for row in product_info:
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
        uids.add(row.id)

    #Set sort = 0, which is used in the template when someone clicks on the links to 2nd, 3rd, 4th pages.
    #Ensures that the products will remain in order of product id on consecutive pages (unless otherwise specified by the user)
    sort = 0

    #If product_info list contains no products, tell the template, so it can print "No Results" on the page
    no_prods = False
    if len(product_info) == 0:
        no_prods = True

    # render the page by adding information to the search_results.html file
    # Keep track of all user inputs to be used by the template, as buttons will need them to access url's
    return render_template('search_results.html',
                           title = 'Search Results',
                           category = input1,
                           search_results = product_info,
                           avg_ratings = ratings,
                           num_pages = list_pages,
                           sort = sort,
                           priceForm = form,
                           low = low,
                           high = high,
                           no_prods = no_prods,
                           catalogue_add = catalogue_add,
                           page = 1)


#Page can be reached from the search_results page.
#This page takes in a search result, a number indicating how to sort the results, a page indicating what page of the results a user wants to view, and a lower and upper bound on the prices that the user wants to view
@bp.route('/sorted_search_results/search/sort/page/lowprice/highprice', methods=['GET', 'POST'])
def sorted_search_results():
    #Gather all inputs as described
    input1 = request.args.get('search')
    input2 = request.args.get('sort')
    input3 = request.args.get('page')
    input4 = request.args.get('lowprice')
    input5 = request.args.get('highprice')

    # Seller-guru: Initialize catalogue add mode, where sellers can add an existing product to their inventory.
    # Activating the mode leads to this page and stays as the seller sorts and searches for items, possibly visiting search_results above.
    catalogue_add = 0
    catalogue_add = request.args.get('ca')

    #If a user reaches the search results page after not filtering by price, set the lower and upper bounds on price filtering to their default values
    if not input4:
        input4 = 0
    if not input5:
        input5 = 1000000000

    #Initialize the Price Filter form
    #Check if the form is valid based on previously described validators
    #If valid and both a lower and upper bound are inputted by the user, make sure that the lower bound is smaller than the upper bound
    #If the lower bound is greater than the upper bound, return the same page with a message
    #If the inputs are otherwise valid, go to a new page, which contains the filtered products sorted by price from low - high
    form = priceForm()
    if form.validate_on_submit():
        if form.lowPrice.data and form.highPrice.data and form.lowPrice.data > form.highPrice.data:
            flash("Filtering failed, upper bound must be greater than lower bound")
            return redirect(url_for('products.sorted_search_results', search = input1, sort = 0,
                                        page = input3, lowprice = input4, highprice = input5, ca=catalogue_add))
        return redirect(url_for('products.sorted_search_results', search = input1, sort = 2,
                                        page = 1, lowprice = form.lowPrice.data, highprice = form.highPrice.data, ca=catalogue_add))

    #Calculate the offset depending on the page a user is viewing. Example: if input3 == 2, then show results 101 - 200
    offset = (int(input3) - 1)*100

    #product_setup contains all products that match the search result, accounting for a price filter if one has been previously specified
    product_setup = Product.get_info(input1, float(input4), float(input5))

    #Calculate the number of pages based on all products that match the search result, accounting for a price filter if one has been previously specified
    #Initialize a list from 1 to the total number of pages for this search term, which will be used by the template file to generate links to more pages at the bottom of this page
    num_pages = (len(product_setup)//100) + 1
    list_pages = []
    for x in range(num_pages):
        y = x + 1
        list_pages.append(y)

    #If the user specifies to sort by product_id, get 100 matches for the search term sorted by product_id (accounting for the offset)
    if int(input2) == 0:
        product_info = Product.get_info_sortedid(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product name in ascending order, get 100 matches for the search term sorted by name in ascending order (accounting for the offset)
    if int(input2) == 1:
        product_info = Product.get_info_sortednameatoz(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product price in ascending order, get 100 matches for the search term sorted by product price in ascending order (accounting for the offset)
    if int(input2) == 2:
        product_info = Product.get_info_sortedpricelow(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product price in descending order, get 100 matches for the search term sorted by product price in descending order (accounting for the offset)
    if int(input2) == 3:
        product_info = Product.get_info_sortedpricehigh(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product name in descending order, get 100 matches for the search term sorted by name in descending order (accounting for the offset)
    if int(input2) == 4:
        product_info = Product.get_info_sortednameztoa(input1, offset, float(input4), float(input5))

    #Initialize a list and set, which are later used for getting average ratings
    ratings = []
    uids = set()

    #Generate a list of lists, where each element is a [product_id, average rating] pair, in order of the products that will be displayed on the page
    #If a product id does not correspond to any ratings, then the average rating will be set to "No Reviews"
    #Since different sellers can sell the same product, and the product will have the same average rating for every seller, only add 1 element per pr
    for row in product_info:
        avg_rating = []
        rating = []
        rating = Product.get_average_rating(row.id)
        if len(rating) > 0 and row.id not in uids:
            avg_rating.append(rating[0][0])
            avg_rating.append(round(rating[0][1], 2))
            ratings.append(avg_rating)
        if len(rating) == 0 and row.id not in uids:
            avg_rating.append(row.id)
            avg_rating.append("No Reviews")
            ratings.append(avg_rating)
        uids.add(row.id)

    #If product_info list contains no products, tell the template, so it can print "No Results" on the page
    no_prods = False
    if len(product_info) == 0:
        no_prods = True

    # render the page by adding information to the search_results.html file
    # Keep track of all previous user inputs to be used by the template, as buttons will need them to generate url's
    return render_template('search_results.html',
                           title = 'Search Results',
                           category = input1,
                           search_results = product_info,
                           avg_ratings = ratings,
                           num_pages = list_pages,
                           sort = input2,
                           priceForm = form,
                           low = input4,
                           high = input5,
                           no_prods = no_prods,
                           catalogue_add = catalogue_add,
                           page = int(input3))

#Form used for rating a product
#Has a required rating field, whose input value must fall between 0 and 5
#Has an optional review field for providing a reason behind a rating, which can be a maximum of 250 characters
class RatingForm(FlaskForm):
    rating = IntegerField(_l('Rating [0 - 5]'), validators=[DataRequired(), NumberRange(min = 0, max = 5, message = "Rating Must Be Between 0 and 5")])
    review = StringField(_l('Reason for Review'), validators = [Optional(), Length(max = 250, message= "Review must be less than 250 characters")])
    submit1 = SubmitField(_l('Submit'))

#Detailed product page, which shows a product's name and image, all sellers for the product, and all reviews for the product, with space to review the product.
#Users access this page by links on the search results page or from a seller's inventory page.
@bp.route('/detailed_product/prod', methods=['GET', 'POST'])
def detailed_product():

    #Get the product id of the product the user wishes to biew
    product_id = request.args.get('prod')

    #Get all information for the product being viewed and all reviews
    product = Product.get(product_id)
    product_ratings = Product.get_ratings(product.id)

    #Initialize the rating form
    form1 = RatingForm()

    #If a user is logged-in, create a list containing all information on whether or not the user purchased the product
    #If the user has not purchased the product, that user will not be able to review it
    checker = []
    if current_user.is_authenticated:
        uid = current_user.id
        checker = Product.get_purchased_product(uid, product_id)

    #If the form passes all previously mentioned validators, check if the user is logged-in
    #If the user is not logged-in, return to the login page with the flashed message
    #If the user is signed in but has not previously purchased this product, re-render this page with the flashed message (do not submit the review)
    #If the user has purchased the product and already reviewed it (if uid in User.get_users_by_id), update this user's review and re-render the page with a message showing the user the review was updated
    #If the user has purchased the product and not reviewed it yet, create a new review and re-render the page with a message showing the user that the new review was submitted
    if form1.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Sign-In to review an item')
            return redirect(url_for('users.login'))
        if len(checker) == 0:
             flash('Review Failed: Must purchase product before reviewing')
             return redirect(url_for('products.detailed_product', prod = str(product_id)))
        if uid in User.get_users_by_id(product_id):
            if Product.reviews(int(uid),
                         int(product_id),
                         int(form1.rating.data),
                         str(form1.review.data)):
                flash('Congratulations, you updated your review')
                return redirect(url_for('products.detailed_product', prod = str(product_id)))
        if uid not in User.get_users_by_id(product_id):
            if Product.reviews(int(uid),
                         int(product_id),
                         int(form1.rating.data),
                         str(form1.review.data)):
                flash('Congratulations, you have reviewed this product!')
                return redirect(url_for('products.detailed_product', prod = str(product_id)))

    #Get the product image
    img = Product.get_image(product.id)[0][0]

    #Find the sellers of the given product and their associated information, which will be used by the template
    product_vendors = Product.get_all_by_vendor(product.id)
    avg_seller_rating = Product.get_average_rating_seller()

    #Create a list of all vendors for the product, which will be used to check if a vendor has not been reviewd
    helper_list = []
    for seller in avg_seller_rating:
        helper_list.append(seller[0])
    
    #If a vendor has not been reviewed, then add an entry for that vendor to the avg_seller_rating list
    for vendor in product_vendors:
        if vendor[0] not in helper_list:
            avg_seller_rating.append((vendor[0], "No Reviews"))
    

    #Get the average rating of the product
    #If the product has no reviews, set the average rating value to -1 as an indicator
    #If the product has reviews, store the average value in the updated_rating variables
    #Create updated_rating_int for ease of calculations in the html file, and updated_rating for displaying the value of the average review to the hundreths place
    avg_product_rating = Product.get_average_rating(product_id)
    updated_rating = 0
    updated_rating_int = -1
    if avg_product_rating:
        updated_rating = (round(avg_product_rating[0][1],2))
        updated_rating_int = (float(avg_product_rating[0][1]))
    elif not avg_product_rating:
        updated_rating = - 1

    ad = Ad.get_ad_for_category(product.category_name)
    if ad: 
        Ad.increment_impressions(ad.id)
    
    click = request.args.get('click') if request.args.get('click') else 0
    if request.args.get('click'):
        s = Ad.increment_clicks(request.args.get('click'))
    else:
        s = None

    # render the page by adding information to the detailed_product.html file
    return render_template('detailed_product.html',
                           title = 'Detailed Product Page',
                           ratingForm = form1,
                           product_ratings = product_ratings,
                           curr_product = product,
                           image = img,
                           sellers_of_product = product_vendors,
                           seller_ratings = avg_seller_rating,
                           avg_product = updated_rating,
                           avg_product_2 = updated_rating_int,
                           num_ratings = len(product_ratings),
                           ad=ad,
                           click=click,
                           s=s)

#Page will not render, but is used to add a product to a user's cart
#It is accessed from a button on the detailed_product page
@bp.route('/added_to_cart/sid/price/pid/quantity', methods=['GET', 'POST'])
def added_to_cart():
    #Determine the product, seller, price, and quantity of the product that the user wants to add to the cart
    #The total price of the item added to the cart will be price * quantity added
    product_id = request.args.get('pid')
    seller_id = request.args.get('sid')
    price = float(request.args.get('price'))
    quantity = int(request.args.get('quantity'))
    click = request.args.get('click')
    Total_price = price * quantity

    if seller_id == request.args.get('s'):
        Ad.increment_cart(click, quantity)

    #Get the user's id if the user is logged-in
    #If the user is not logged-in, redirect to the login page with a message
    if current_user.is_authenticated:
        uid = current_user.id
    if not current_user.is_authenticated:
        flash('Sign-In to purchase an item')
        return redirect(url_for('users.login'))

    #Add the product to the user's cart and bring the user to the cart page
    if Product.purchases(uid, product_id, seller_id, quantity):
        flash("Congratulations, you have updated your cart" )
        return redirect(url_for('carts.cart'))

    return render_template('added_to_cart.html'
                           )

#Link allows users to browse products by category. The page will display all categories that begin with a given letter with links to all product categories
@bp.route('/browse_by_category/letter', methods=['GET', 'POST'])
def browse_by_category():
    #Get the letter for which the user wants to view all categories
    input1 = request.args.get('letter')

    #Get all categories containing a product that begin with the specified letter
    all_categories = Product.get_all_categories_with_products(input1)

    #Check if there are no categories associated with a given letter. Pass the boolean to the template, so it prints "No Categories Begin with /letter" if there are no categories that begin with a specified letter
    no_cats = False
    if len(all_categories) == 0:
        no_cats = True
    return render_template('browse.html',
                           categories = all_categories,
                           letter = input1,
                           cats = no_cats
                           )

#Page is accessed through the browse category page and shows a list of products related to a category
#Page can also be accessed by clicking on links to categories through the search results page
#Different from regular search result page in that it shows only products belonging to a specific category, rather than products whose name or description include a keyword
@bp.route('/category_search_results/search', methods=['GET', 'POST'])
def category_search_results():

    #Recieve the category from the previous link
    input1 = request.args.get('search')

    #Initialize default values for the price filter
    low = 0
    high = 1000000000


    #Initialize an offset value for the purpose of pagination - the offset value will be zero following a user's choice to browse by category
    #product_setup contains all products that belong to a category
    #product_info contains the first 100 products (sorted by product id) that belong to the category
    offset = 0
    product_setup = Product.get_info_cat(input1, low, high)
    product_info = Product.get_info_sortedid_cat(input1, offset, low, high)

    #Calculate the number of pages. Since 100 items are displayed per page, take the cieling of the total number of products that match the search results by taking the floor and adding 1
    #Initialize a list from 1 to the total number of pages for this search term, which will be used by the template file to generate links to more pages at the bottom of this page
    num_pages = (len(product_setup)//100) + 1
    list_pages = []
    for x in range(num_pages):
        y = x + 1
        list_pages.append(y)

    #Initialize a list and set, which are later used for getting average ratings
    ratings = []
    uids = set()

    #Initialize the Price Filter form
    #Check if the form is valid based on previously described validators
    #If valid and both a lower and upper bound are inputted by the user, make sure that the lower bound is smaller than the upper bound
    #If the lower bound is greater than the upper bound, return the same page with a message
    #If the inputs are otherwise valid, go to a new page, which contains the filtered products sorted by price from low - high
    form = priceForm()
    if form.validate_on_submit():
        if form.lowPrice.data and form.highPrice.data and form.lowPrice.data > form.highPrice.data:
            flash("Filtering failed, upper bound must be greater than lower bound")
            return redirect(url_for('products.sorted_search_results_cat', search = input1, sort = 0,
                                        page = 1, lowprice = low, highprice = high))
        return redirect(url_for('products.sorted_search_results_cat', search = input1, sort = 2,
                                        page = 1, lowprice = form.lowPrice.data, highprice = form.highPrice.data))

    #Generate a list of lists, where each element is a [product_id, average rating] pair, in order of the products that will be displayed on the page
    #If a product id does not correspond to any ratings, then the average rating will be set to "No Reviews"
    #Since different sellers can sell the same product, and the product will have the same average rating for every seller, only add 1 element per product id - check this with the uids set
    for row in product_info:
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
        uids.add(row.id)

    #Set sort = 0, which is used in the template when someone clicks on the links to 2nd, 3rd, 4th pages.
    #Ensures that the products will remain in order of product id on consecutive pages (unless otherwise specified by the user)
    sort = 0

    # render the page by adding information to the sorted_search_results.html file
    # Keep track of inputs to be used in url generation on the html template
    # set no_prods = False, as all categories should have products initially (as ensured by line 322)
    return render_template('sorted_search_results.html',
                           title = 'Search Results',
                           category = input1,
                           search_results = product_info,
                           avg_ratings = ratings,
                           num_pages = list_pages,
                           sort = sort,
                           priceForm = form,
                           low = low,
                           high = high,
                           no_prods = False,
                           page = 1)

#Like the sorted_search_results_page, this function takes in a specific category name, a number indicating how to sort the products in the category, a page indicating what page of the results a user wants to view, and a lower and upper bound on the prices that the user wants to view
#The function sorts based on all products belonging to a specific category (rather than a user inputted keyword)
@bp.route('/sorted_search_results_cat/search/sort/page/lowprice/highprice', methods=['GET', 'POST'])
def sorted_search_results_cat():
    #Gather all inputs as described
    input1 = request.args.get('search')
    input2 = request.args.get('sort')
    input3 = request.args.get('page')
    input4 = request.args.get('lowprice')
    input5 = request.args.get('highprice')

    #If a user reaches the search results page after not filtering by price, set the lower and upper bounds on price filtering to their default values
    if not input4:
        input4 = 0
    if not input5:
        input5 = 1000000000

    #Initialize the Price Filter form
    #Check if the form is valid based on previously described validators
    #If valid and both a lower and upper bound are inputted by the user, make sure that the lower bound is smaller than the upper bound
    #If the lower bound is greater than the upper bound, return the same page with a message
    #If the inputs are otherwise valid, go to a new page, which contains the filtered products sorted by price from low - high
    form = priceForm()
    if form.validate_on_submit():
        if form.lowPrice.data and form.highPrice.data and form.lowPrice.data > form.highPrice.data:
            flash("Filtering failed, upper bound must be greater than lower bound")
            return redirect(url_for('products.sorted_search_results_cat', search = input1, sort = 0,
                                        page = input3, lowprice = input4, highprice = input5))
        return redirect(url_for('products.sorted_search_results_cat', search = input1, sort = 2,
                                        page = 1, lowprice = form.lowPrice.data, highprice = form.highPrice.data))

    #Calculate the offset depending on the page a user is viewing. Example: if input3 == 2, then show results 101 - 200
    offset = (int(input3) - 1)*100

    #product_setup contains all products that belong to the category, accounting for a price filter if one has been previously specified
    product_setup = Product.get_info_cat(input1, float(input4), float(input5))

    #Calculate the number of pages based on all products that belong to the category, accounting for a price filter if one has been previously specified
    #Initialize a list from 1 to the total number of pages for this search term, which will be used by the template file to generate links to more pages at the bottom of this page
    num_pages = (len(product_setup)//100) + 1
    list_pages = []
    for x in range(num_pages):
        y = x + 1
        list_pages.append(y)

    #If the user specifies to sort by product_id, get 100 products that belong to the category sorted by product_id (accounting for the offset)
    if int(input2) == 0:
        product_info = Product.get_info_sortedid_cat(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product name in ascending order, get 100 products that belong to the category sorted by name in ascending order (accounting for the offset)
    if int(input2) == 1:
        product_info = Product.get_info_sortednameatoz_cat(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product price in ascending order, get 100 products that belong to the category sorted by product price in ascending order (accounting for the offset)
    if int(input2) == 2:
        product_info = Product.get_info_sortedpricelow_cat(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product price in descending order, get 100 products that belong to the category sorted by product price in descending order (accounting for the offset)
    if int(input2) == 3:
        product_info = Product.get_info_sortedpricehigh_cat(input1, offset, float(input4), float(input5))
    #If the user specifies to sort by product name in descending order, get 100 matches for the search term sorted by name in descending order (accounting for the offset)
    if int(input2) == 4:
        product_info = Product.get_info_sortednameztoa_cat(input1, offset, float(input4), float(input5))

    #Initialize a list and set, which are later used for getting average ratings
    ratings = []
    uids = set()

    #Generate a list of lists, where each element is a [product_id, average rating] pair, in order of the products that will be displayed on the page
    #If a product id does not correspond to any ratings, then the average rating will be set to "No Reviews"
    #Since different sellers can sell the same product, and the product will have the same average rating for every seller, only add 1 element per product id - check this with the uids set
    for row in product_info:
        avg_rating = []
        rating = []
        rating = Product.get_average_rating(row.id)
        if len(rating) > 0 and row.id not in uids:
            avg_rating.append(rating[0][0])
            avg_rating.append(round(rating[0][1], 2))
            ratings.append(avg_rating)
        if len(rating) == 0 and row.id not in uids:
            avg_rating.append(row.id)
            avg_rating.append("No Reviews")
            ratings.append(avg_rating)
        uids.add(row.id)

    #If product_info list contains no products, tell the template, so it can print "No Results" on the page
    no_prods = False
    if len(product_info) == 0:
        no_prods = True

    # render the page by adding information to the sorted_search_results.html file
    # Keep track of all previous user inputs to be used by the template, as buttons will need them to generate url's
    return render_template('sorted_search_results.html',
                           title = 'Search Results',
                           category = input1,
                           search_results = product_info,
                           avg_ratings = ratings,
                           num_pages = list_pages,
                           sort = input2,
                           priceForm = form,
                           low = input4,
                           high = input5,
                           no_prods = no_prods,
                           page = int(input3))
