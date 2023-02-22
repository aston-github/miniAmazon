from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, FloatField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange, Optional, Length
from flask_babel import _, lazy_gettext as _l
import datetime


from .models.user import User
from .models.review import Review
from .models.purchase import Purchase
from .models.seller import Seller


from flask import Blueprint
bp = Blueprint('users', __name__)


# create log in form for user input
class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


# login page from log in button/link, contains log in form with submission and
# redirects to home page with successful login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


# create registration form and registration page, success message appears
# with successful registration and redirected to login
class RegistrationForm(FlaskForm):
    firstname = StringField(_l('First Name'), validators=[DataRequired()])
    lastname = StringField(_l('Last Name'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    address = StringField(_l('Address'), validators=[DataRequired()])
    submit = SubmitField(_l('Register'))

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError(_('Already a user with this email.'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                         form.password.data,
                         form.firstname.data,
                         form.lastname.data,
                         form.address.data):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)

# logs out user and redirects to home page
@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))

# wt form with deposit and withdraw selection fields and amount
class BalanceForm(FlaskForm):
    operation = RadioField(_l('Select Operation'), validators=[DataRequired()], choices=[('deposit','Deposit'),('withdraw','Withdraw')])
    amount = FloatField(_l('Amount'), validators=[DataRequired(), NumberRange(min = 0)])
    submit1 = SubmitField(_l('Process'))

# wt form to specify reciever email and amount to transfer
class VenmoForm(FlaskForm):
    email1 = StringField(_l('Email'), validators=[Email(), DataRequired()])
    amount1 = FloatField(_l('Amount'), validators=[DataRequired(), NumberRange(min = 0)])
    submit3 = SubmitField(_l('Process'))
    def validate_email1(self, email1):
        if not User.email_exists(email1.data):
            raise ValidationError(_('No user with this email.'))

# wt form to edit any profile field, requires correct current password for successful submission
class EditForm(FlaskForm):
    current_password = PasswordField(_l('Current password'), validators = [DataRequired()])
    firstname = StringField(_l('First Name'), validators = [Optional()])
    lastname = StringField(_l('Last Name'), validators = [Optional()])
    email = StringField(_l('Email'), validators=[Email(), Optional()])
    password = PasswordField(_l('Password'), validators = [Optional()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[EqualTo('password')])
    address = StringField(_l('Address'), validators = [Optional()])
    submit2 = SubmitField(_l('Save'))

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError(_('Already a user with this email.'))

    def validate_current_password(self, current_password):
        if User.get_by_auth(User.get_email(current_user.id), current_password.data) is None:
            raise ValidationError(_('Password incorrect'))

# profile page accessed through Profile button, displays all user information and links
# to seller portal (if seller), public profile, and purchase history.
# Includes balance (deposit, withdraw, venmo), edit profile, and authored reviews features.
# Balance form ensures no overdrawing with exception handling (hit db trigger)
# Venmo form ensures no overdrawing by checking balance is greater than venmo amount
@bp.route('/profile', methods=['GET', 'POST'] )
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))
    id = current_user.id
    info = User.get_profile(id)

    # Seller-guru: Determine if a user is a seller or not.
    is_seller = not (User.is_seller(id) is None)

    balanceForm = BalanceForm()
    if balanceForm.submit1.data and balanceForm.validate():
        if User.change_balance(current_user.id,
                        balanceForm.operation.data,
                        balanceForm.amount.data):
            flash('Balance updated (Rounded to 2 decimal places)')
            return redirect(url_for('users.profile'))
        else:
            flash('Error: balance insufficient')

    venmoForm = VenmoForm()
    if venmoForm.submit3.data and venmoForm.validate():
        user_balance = User.get(current_user.id).balance
        if venmoForm.amount1.data > user_balance:
            flash('ERROR: Insufficient funds!')
            return redirect(url_for('users.profile'))
        else:
            reciever = User.get_id_from_email(venmoForm.email1.data)
            # User.change_balance(current_user.id,'withdraw',venmoForm.amount1.data)
            # User.change_balance(reciever,'deposit',venmoForm.amount1.data)
            User.venmo(current_user.id, reciever, venmoForm.amount1.data)
            flash('Balance transfer complete')
            return redirect(url_for('users.profile'))

# edit form updates profile using new form data or defaults to exisiting information
    editForm = EditForm()
    if editForm.submit2.data and editForm.validate():
        email = editForm.email.data if editForm.email.data != '' else info[0].email
        password = generate_password_hash(editForm.password.data) if editForm.password.data != '' else User.get_password(current_user.id)
        firstname = editForm.firstname.data if editForm.firstname.data != '' else info[0].firstname
        lastname = editForm.lastname.data if editForm.lastname.data != '' else info[0].lastname
        address = editForm.address.data if editForm.address.data != '' else info[0].address
        print(User.change_profile(current_user.id, email, password, firstname, lastname, address))
        if User.change_profile(current_user.id, email, password, firstname, lastname, address):
            flash('Profile saved.')
            return redirect(url_for('users.profile'))
        else:
            flash('Error')

    public_profile = url_for('users.public_profile', id=id, is_seller = is_seller)
    purchase_history = url_for('users.purchase_history')

    product_reviews = User.get_product_reviews(id)
    seller_reviews = User.get_seller_reviews(id)

    return render_template('profile.html', title = 'Profile',
                            info = info,
                            balanceForm = balanceForm,
                            editForm = editForm,
                            public_profile = public_profile,
                            purchase_history = purchase_history,
                            product_reviews = product_reviews,
                            seller_reviews = seller_reviews,
                            is_seller = is_seller,
                            venmoForm = venmoForm,
                            id = id)

# wt rating form for seller reviews
class RatingForm(FlaskForm):
    #enforce that the rating is between 0 and 5, and that a rating is submitted
    rating = IntegerField(_l('Rating [0 - 5]'), validators=[DataRequired(), NumberRange(min = 0, max = 5, message = "Rating Must Be Between 0 and 5")])
    review = StringField(_l('Reason for Review'), validators = [Optional(), Length(max = 250)])
    submit1 = SubmitField(_l('Submit'))


# public profile that  displays id and name for regular Users
# public profiles of users who are sellers will also have reviews about them, email, and address
# there is also a seller rating form available
@bp.route('/public_profile', methods=['GET', 'POST'] )
def public_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))
    id = request.args.get('id')
    is_seller = request.args.get('is_seller')
    # not sure how this exactly works, see index.py purchases
    info = User.get_profile(id)
    reviews = Review.get_seller_reviews(id) or []

    now = datetime.datetime.now()
    timestamp = datetime.datetime.timestamp(now)
    form1 = RatingForm()

    redirectLink = url_for('users.public_profile', id=id, is_seller = is_seller)

    checker = []
    if current_user.is_authenticated:
        uid = current_user.id
        checker = Review.get_purchased_seller(uid, id)

    if form1.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Sign-In to review an item')
            return redirect(url_for('users.login'))
        #check that User has purchased product before
        if len(checker) == 0:
             flash('Review Failed: Must purchase from seller before reviewing')
             return redirect(redirectLink)
        if id in [review[1] for review in User.get_seller_reviews(uid)]:
            if User.reviewSeller(int(uid),
                         int(id),
                         int(form1.rating.data),
                         str(form1.review.data)):
                flash('Congratulations, you updated your review')
                return redirect(redirectLink)
        else:
            if User.reviewSeller(int(uid),
                         int(id),
                         int(form1.rating.data),
                         str(form1.review.data)):
                flash('Congratulations, you have reviewed this seller!')
                return redirect(redirectLink)



    return render_template('public_profile.html', title = 'Public_Profile',
                            id = str(id),
                            is_seller = is_seller,
                            info = info,
                            ratingForm = form1,
                            reviews = reviews,
                            numReviews = len(reviews) if reviews else 0,
                            avgRating = round(sum([review.rating for review in reviews])/len(reviews), 2) if reviews else 0,
                            )

# Seller-guru: display the seller's profile page, from which they can access their inventory, sale history and advertisements.
@bp.route('/seller_profile', methods=['GET', 'POST'] )
def seller_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))
    id = current_user.id
    info = User.get_profile(id)

    # If this is a user's first time visiting this page, show them a welcome message.
    if request.args.get('welcome_seller'):
        welcome_seller = User.become_seller(id)
        if welcome_seller:
            flash('Congratulations- You just joined a tight-knit community of self-sufficient sellers. Better update your inventory!')

    return render_template('seller_profile.html', title = 'Seller Profile',
                            info = info)

# gets all purchases by user and displays in reverse chronological order
# due to database design, purchases are individual item orders
# view order links to the overall order
@bp.route('/purchase_history', methods=['GET', 'POST'] )
def purchase_history():
    if not current_user.is_authenticated:
        return redirect(url_for('index.index'))
    purchases = Purchase.get_all_by_uid_since(
    current_user.id, datetime.datetime(1970, 1, 1, 0, 0, 0))
    return render_template('purchase_history.html', title = 'Purchase_History',
                            purchases = purchases)

#Page will not render, but is used to add a product to a user's cart
#It is accessed from a button on the detailed_product page
@bp.route('/delete_review/uid/sid_or_pid/type', methods=['GET', 'POST'])
def delete_review():
    #Determine the product, seller, price, and quantity of the product that the user wants to add to the cart
    #The total price of the item added to the cart will be price * quantity added
    user_id = request.args.get('uid')
    if int(request.args.get('type')) == 0:
        product_id = request.args.get('sid_or_pid')
        if Review.delete_product_review(user_id, product_id):
            flash('Success, review of deleted')
    elif int(request.args.get('type')) == 1:
        seller_id = request.args.get('sid_or_pid')
        if Review.delete_seller_review(user_id, seller_id):
            flash('Success, review of deleted')

    return redirect(url_for('users.profile'))
