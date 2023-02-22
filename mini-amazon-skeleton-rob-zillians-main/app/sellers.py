from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,FloatField, IntegerField, HiddenField, FloatField
from wtforms.validators import ValidationError, DataRequired, NumberRange, Length
from flask_babel import _, lazy_gettext as _l

from .models.user import User
from .models.seller import Seller
from .models.purchase import Purchase
from .models.product import Product

from flask import Blueprint
bp = Blueprint('sellers', __name__)

from datetime import datetime

from sqlalchemy import desc

# Allow the seller to update their stock for a particular item. Used in inventory next to every product.
class ChangeQuantity(FlaskForm):
    pid = HiddenField()
    new_quantity = IntegerField(_l('Delta'), validators = [DataRequired(), NumberRange(min = 0, message = "No negative quantities!")])
    update1 = SubmitField(_l('Update'))

# Allow the seller to update their price for a particular item. Used in inventorynext to every product.
class ChangePrice(FlaskForm):
    pid = HiddenField()
    new_price = FloatField(_l('Delta'), validators = [DataRequired(), NumberRange(min = 0.01, message = "Prices must be positive")])
    update2 = SubmitField(_l('Update'))

# Display a seller's entire inventory. Includes buttons to create new products, add existing ones for their inventory, remove products from inventory or edit ones they own.
@bp.route('/inventory', methods=['GET', 'POST'] )
def inventory():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))
    id = current_user.id
    info = User.get_profile(id)

    # The update variable keeps track of which product a user has recently interacted with. CSS and anchors help them quickly revisit this product.
    update = 0
    update = request.args.get('update')
    
    # If a seller is coming from catalogue add mode, the product id to add to their inventory is in update. Update their inventory here.
    if update:
        Seller.catalogue_add(id, update)
        flash('You just added a new product to your inventory. If you did not create the product, your stock is set to 0 and your price matches your lowest competitor.')
    
    if request.args.get('e'):
        update = request.args.get('e')
        flash('You just edited a product, stock or price.')

    # Change seller's stock for a product.
    changeQuantity = ChangeQuantity()
    if request.method == 'POST' and changeQuantity.update1():
        if changeQuantity.new_quantity.data or changeQuantity.new_quantity.data == 0:
            new_quantity = int(changeQuantity.new_quantity.data or 0)
            pid = changeQuantity.pid.data
            # Validate the new quantity
            if new_quantity >= 0:
                Seller.update_quantity(id, pid, new_quantity)
                update = pid
                flash('You just edited a product, stock or price.')
            elif new_quantity < 0:
                update = pid
                flash('You tried to enter a negative stock; impossible!')

    # Change seller's price point for a product.
    changePrice = ChangePrice()
    if request.method == 'POST' and changePrice.update2():
        if changePrice.new_price.data or changePrice.new_price.data == 0:
            new_price = float(changePrice.new_price.data or 0)
            pid = changePrice.pid.data
            # Validate the new price
            if new_price > 0:
                Seller.update_price(id, pid, new_price)
                update = pid
                flash('You just edited a product, stock or price.')
            elif new_price <= 0 :
                update = pid
                flash('You tried to enter a negative price or give it away for free. We don\'t recommend either!')

    # If a seller has chosen to remove an item from their inventory, the page reloads without that item. Remove it here.
    remove = request.args.get('r')
    if remove:
        Seller.remove_item(id, remove)
    

    # Get information about sorting. d is set to 1 if the order is to be descending and sort correspods to the column number to sort in seller.py (get_inventory)
    d = int(request.args.get('d')) if request.args.get('d') else 0
    sort = int(request.args.get('s')) if request.args.get('s') else 0
    # Get the seller's current inventory. Default d = 0 and sort = 0 which means ascending by product id.
    inventory = Seller.get_inventory(id, sort, d)

    # Initialize the variable, which means a seller is viewing the inventory to choose a product to advertise. They don't need access to the other buttons, so this variable removes those from inventory.html.
    ads = int(request.args.get('ad')) if request.args.get('ad') else 0

    return render_template('inventory.html', title = 'Seller Inventory',
                            info=info,
                            inventory = inventory,
                            changeQuantity=changeQuantity,
                            changePrice=changePrice,
                            update=update,
                            id=id,
                            ads=ads)

# From which appears for every line item in a seller's sale history, allowing them to mark the order as fulfilled.
class Fulfill(FlaskForm):
    id = HiddenField("Field 1")
    update = SubmitField(_l('Fulfill'))

# Seller's list of orders that have been fulfilled or need be fulfilled.
@bp.route('/sale_history', methods=['GET', 'POST'] )
def sale_history():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))

    # If the seller wants to fulfill a line item, get the time and mark it as fulfilled at that time.
    # update and prev keep track of the order id being fulfilled and previous order status, fulfillment_time respectively.
    # If the order has not been fulfilled, prev[1] will be now.
    update = 0
    prev = 0
    fulfill_from_order = request.args.get('f')
    if fulfill_from_order:
        now = datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")
        prev = Seller.fulfill_order(fulfill_from_order, time)
        update = fulfill_from_order
        # Give the seller a time for their records
        if prev[0] != 'Fulfilled':
            flash('You just fulfilled an order on ' + str(time))
        # Let the seller know when they first clicked Fulfill for this order
        else:
            flash('You already fulfilled this order on ' +  str(prev[1]))

    a = int(request.args.get('a')) if request.args.get('a') else 0
    sort = int(request.args.get('s')) if request.args.get('s') else 0

    # Get history of line items.
    purchases = Seller.get_sale_history(
    current_user.id, datetime(1980, 9, 14, 0, 0, 0), sort, a)

    # Update is used with Jinja and css to highlight an order that has just been interacted with.
    return render_template('sale_history.html', title = 'Sale History',
                            purchases = purchases,
                            update=update)

# Form used below for creating OR editing products.
class AddProduct(FlaskForm):
    productname = StringField(_l('Product Name'), validators = [DataRequired(), Length(max = 255, message = "Name too long")])
    description = StringField(_l('Description'), validators = [DataRequired(), Length(max = 512, message = "Description too long")])
    image = StringField(_l('Image URL'), validators= [DataRequired(), Length(max = 512, message = "URL too long for database")])
    category = StringField(_l('Category'), validators= [DataRequired()])
    quantity = IntegerField(_l('Quantity'), validators= [NumberRange(min = 0, message = "Quantities must be positive")])
    price = FloatField(_l('Price'), validators= [DataRequired(), NumberRange(min = 0.01, message = "Prices must be positive")])
    submitproduct = SubmitField(_l('Submit'))

    # Ensure that the image url is valid, by checking if it begins with https://
    def validate_image(self, image):
        image = str(image.data)
        if not image.startswith('https://'):
            raise ValidationError(_('Must provide a valid url (it should begin with https://)'))

    # Determine whether the category the seller has entered matches an existing one or not.
    def validate_category(self, category):
        categories_init = Product.get_all_categories()
        categories_test = []
        for category1 in categories_init:
            categories_test.append(category1[0])
        if category.data not in categories_test:
            raise ValidationError(_('Must choose from pre-existing product categories found below. Inputs are case sensitive.'))

# Allow the seller to create or edit a product. If 'e' is set, then they are editing a product and the current product/inventory information must be placed into the form fields.
# A seller must have created a product for the "edit product" link to appear in the first place. Denoted by 'owner' corresponding to their user id.
@bp.route('/ce_product', methods=['GET', 'POST'] )
def create_edit_product():
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    # If the current user is not a seller, return the user to their profile page with a message (do not let the user create a product)
    if current_user.id not in Seller.get_all():
        flash('Must be seller to add a product')
        return redirect(url_for('users.profile'))
    
    # Get the current user's id and information
    id = current_user.id
    info = User.get_profile(id)

    # Initialize the form for adding a product
    addProduct = AddProduct()

    # Determine if the seller has clicked to edit a product, for which 'e' will equal its ID, or if the seller intends to create a new product.
    # The same infomation fields are relevant in both cases.
    editonly = request.args.get('e')
    if editonly:
        product_info = Seller.get_product(id, editonly)
    else:
        product_info = 0

    # If the seller intends to create a product: validate their entries. Make sure the product name, description and category are not replicated anywhere else in the store. 
    # Then, create the product entry and update their inventory.
    if not editonly:
        if addProduct.validate_on_submit():
            if Product.exists(addProduct.productname.data, 
                                        addProduct.description.data,
                                        addProduct.category.data):
                flash("Product already exists, try adding to your inventory")
                return redirect(url_for('sellers.create_edit_product'))
            if Product.create_product(addProduct.productname.data, 
                                        addProduct.description.data,
                                        addProduct.image.data,
                                        addProduct.category.data,
                                        id):
                pid = Product.get_id(addProduct.productname.data, 
                                        addProduct.description.data,
                                        addProduct.category.data)
                if Product.add_to_inventory(id,
                                        pid,
                                        addProduct.quantity.data,
                                        addProduct.price.data):
                    return redirect(url_for('sellers.inventory', update=pid))
    # If the seller intends to edit a product: validate their entries. Make sure the product name, description and category are not replicated anywhere else in the store. 
    # Then, update the product entry and update their inventory.
    else:
        if addProduct.validate_on_submit():

            # If the seller has not changed the name, description, or category, then their product will return "exists" if we check. So, only check if they have changed one of these three.
            if product_info.name != addProduct.productname.data or product_info.description != addProduct.description.data or product_info.category_name != addProduct.category.data:
                if Product.exists(addProduct.productname.data, addProduct.description.data, addProduct.category.data):
                    flash("A product with this name, description and category already exists. Please update your entry or try adding it to your inventory from the catalogue")
                    return redirect(url_for('sellers.create_edit_product', e = editonly))
            
            Product.edit_product(id, editonly,
                                addProduct.productname.data, 
                                addProduct.description.data,
                                addProduct.image.data,
                                addProduct.category.data)
            Seller.update_quantity(id, editonly, addProduct.quantity.data)
            Seller.update_price(id, editonly, addProduct.price.data)
            return redirect(url_for('sellers.inventory', e=editonly))

    #Get a list of all possible product categories, which will be listed below the form for the sellers reference
    categories = Product.get_all_categories()
    #Render the template
    return render_template('add_edit_product.html', title = 'Manage Product',
                            info = info,
                            addProduct=addProduct,
                            categories = categories,
                            editonly=editonly,
                            product=product_info)

