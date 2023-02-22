### ADS API
# 
# To use ads on your page, go to the bp_route method that generates it. At the top of the file:
#
    # from .models.ad import Ad
#
# Then in the method you want to use:
#
    # ad = Ad.get_ad_for_category({{{---SOMETHING---}}}}}.category_name)
    # if ad: 
    #     Ad.increment_impressions(ad.id)

    # click = request.args.get('click') if request.args.get('click') else 0
    # if request.args.get('click'):
    #     s = Ad.increment_clicks(request.args.get('click'))
    # else:
    #     s = None
# 
# And as a parameter in render_template:
#
# ad=ad,
# click=click,
# s=s
#
# And finally at the top of your html doc:
#
    # {% if ad %}
    # <a href="{{ url_for('products.detailed_product', prod=ad.product_id, click=ad.id) }}" style="text-decoration:none">
    # <div style="justify-content:center;display:flex;color:black;background-color:cornsilk;align-items:center;border: 1px solid black;width:50%;margin-left:25%;margin-right:25%">
    #   <img style="flex-basis:30%" src= "{{ad.image_url}}" width = 120 height = 120>
    #   <span class="ad_text" style="padding-left:40px">{{ad.description}}</span>
    # </div>
    # </a>
    # {% endif %}
# 
#  ###

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, DateField
from wtforms.validators import ValidationError, DataRequired, Optional
from flask_babel import _, lazy_gettext as _l

from .models.seller import Seller
from .models.product import Product
from .models.ad import Ad

from datetime import datetime

from flask import Blueprint
bp = Blueprint('ads', __name__)

# Additional feature: Advertising manager where sellers can Create advertisements for products and modify existing ones.
@bp.route('/ads_manager', methods=['GET', 'POST'] )
def ads_manager():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))

    d = int(request.args.get('d')) if request.args.get('d') else 0
    sort = int(request.args.get('s')) if request.args.get('s') else 0
    update = int(request.args.get('update')) if request.args.get('update') else 0

    # Get history of line items.
    ads = Ad.get_all_ads_manager(current_user.id, sort, d)

    # See one of your ads on screen as if you were another user
    view = request.args.get('v') if request.args.get('v') else 0
    if view:
        ad = Ad.get_ad(view)
    else:
        ad = 0

    # Determine which ads are currently running
    date=datetime.now()

    # Update is used with Jinja and css to highlight an order that has just been interacted with.
    return render_template('ads_manager.html', title = 'Advertisements',
                            ads=ads,
                            update=update,
                            date=date,
                            ad=ad
                            )

class AdForm(FlaskForm):
    pid = HiddenField()
    nickname = StringField(_l('Campaign Nickname'), validators = [DataRequired()])
    description = StringField(_l('Description Text (will appear on the ad)'), validators= [DataRequired()])
    image_url = StringField(_l('Image to use for the ad (defaults to the current product image URL)'), validators= [DataRequired()])
    category = StringField(_l('Category to advertise to'), validators= [DataRequired()])
    start_time = DateField(_l('Start time (optional, but an end time must be specified in THIS form if there is a start time and vice versa)'), validators=[Optional()])
    end_time = DateField(_l('End Time'), validators=[Optional()])
    submit_ad = SubmitField(_l('Submit'))

    
    # Determine whether the category the seller has entered matches an existing one or not.
    def validate_category(self, category):
        categories_init = Product.get_all_categories()
        categories_test = []
        for category1 in categories_init:
            categories_test.append(category1[0])
        if category not in categories_test:
            raise ValidationError(_('Must choose from pre-existing product categories found below'))

# create an ad if 'c' is set, edit an ad if 'e' is set, view an ad otherwise.
@bp.route('/manage_ad', methods=['GET', 'POST'] )
def manage_ad():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))
    
    id = current_user.id

    a = int(request.args.get('a')) if request.args.get('a') else 0
    sort = int(request.args.get('s')) if request.args.get('s') else 0
    update = int(request.args.get('update')) if request.args.get('update') else 0

    adform=AdForm()

    # Get product info to use as default values for the ad if creating
    create = int(request.args.get('c')) if request.args.get('c') else 0
    if create:
        ad = Seller.get_product(id, create)

    # Determine if the seller has clicked to edit an ad, for which 'e' will equal its ID, or if the seller intends to create a new ad.
    # The same infomation fields are relevant in both cases.
    editonly = request.args.get('e') if request.args.get('e') else 0
    if editonly:
        ad = Ad.get_ad(editonly)

    # If the seller intends to create a product: validate their entries. Make sure the product name, description and category are not replicated anywhere else in the store. 
    # Then, create the product entry and update their inventory.
    if create:
        if request.method == 'POST' and adform.submit_ad():
            update = Ad.create_ad(id, adform.pid.data, 
                                        adform.nickname.data,
                                        adform.description.data,
                                        adform.image_url.data,
                                        adform.category.data)
            if not adform.start_time.data:
                    flash('You just created a new ad campaign, but it\'s currently inactive. You can schedule it below.')
                    return redirect(url_for('ads.ads_manager', update=update))
            else:
                if Ad.schedule_ad(update, adform.start_time.data, adform.end_time.data):
                    flash('You just created an ad, and it\'s currently scheduled for ' + str(adform.start_time.data) + ' to ' + str(adform.end_time.data))
                    return redirect(url_for('ads.ads_manager', update=update))
    # If the seller intends to edit a product: validate their entries. Make sure the product name, description and category are not replicated anywhere else in the store. 
    # Then, update the product entry and update their inventory.
    else:
        if request.method == 'POST' and adform.submit_ad():
            update = Ad.edit_ad(id, adform.pid.data, 
                                        adform.nickname.data,
                                        adform.description.data,
                                        adform.image_url.data,
                                        adform.category.data)
            if not adform.start_time.data:
                    flash('You just edited a campaign, but it\'s still inactive. You can schedule it below.')
                    return redirect(url_for('ads.ads_manager', update=update))
            else:
                if Ad.schedule_ad(update, adform.start_time.data, adform.end_time.data):
                    if adform.start_time.data < datetime.date(datetime.now()) and adform.end_time.data > datetime.date(datetime.now()):
                        flash('Your ad is now running!')
                    else:
                        flash('Your ad has been scheduled!')
                    return redirect(url_for('ads.ads_manager', update=update))

    categories = Product.get_all_categories()

    # Update is used with Jinja and css to highlight an order that has just been interacted with.
    return render_template('add_edit_ad.html', title = 'Manage Ad',
                            ad=ad,
                            adform=adform,
                            categories=categories,
                            c=create,
                            e=editonly,
                            update=update
                            )