from werkzeug.security import generate_password_hash
import csv
from faker import Faker
import random
import json
import pandas as pd

num_users = 100
num_purchases = 4500
num_sellers = 40
num_inventory = 5000
num_seller_reviews = 1000
num_prod_reviews = 1000


Faker.seed(0)
fake = Faker()

# this script generates our realistic database that powers the mini-amazon project


def get_csv_writer(f):
    return csv.writer(f, dialect='unix')

# generate fake user data using faker, number of users given
def gen_users(num_users):
    with open('Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        users = {}
        for uid in range(1,num_users+1):
            users[uid] = 0
            if uid % 10 == 0:
                print(f'{uid}', end=' ', flush=True)
            profile = fake.profile()
            email = profile['mail']
            plain_password = f'pass{uid}'
            password = generate_password_hash(plain_password)
            name_components = profile['name'].split(' ')
            firstname = name_components[0]
            lastname = name_components[-1]
            address = profile['address'].replace("\n", " ")
            # address = address.replace(",", "")
            writer.writerow([email, password, firstname, lastname, address])
        print(f'{num_users} generated')
    return users

# selects random users to be sellers given number of sellers desired
def gen_sellers(num_sellers, users):
    with open('Sellers.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Sellers...', end=' ', flush=True)
        sellers = {}
        sellers_count = 0
        while sellers_count < num_sellers:
            if sellers_count % 10 == 0:
                print(f'{sellers_count}', end=' ', flush=True)

            seller_id = random.choice(list(users.keys()))
            if seller_id not in sellers:
                sellers_count +=1
                sellers[seller_id] = 0
                writer.writerow([seller_id])
        print(f'{num_sellers} generated')
    return sellers

df = pd.read_csv("real_amazon.csv")
df = df[["Product Name", "About Product", "Image", "Category"]]
df = df[df['Category'].notnull()]
df = df.reset_index(drop=True)
print(type(df["Category"][0]))

# reading from real amazon data, make categories based on the item categories
def gen_categories():
    with open('Categories.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Categories...', end=' ', flush=True)
        categories = {}
        for i, row in df.iterrows():
            if i % 10 == 0:
                print(f'{i}', end=' ', flush=True)
            for c in row["Category"].split("|"):
                if c.strip() not in categories:
                    categories[c.strip()] = 0
                    writer.writerow([c.strip()])
        print(f'{len(categories)} generated')
    return categories

# reading from real amazon data, make products with realisitic names,
# descriptions, and images. A random seller is assign owner for edit
# product features
def gen_products(sellers):
    products = {}

    with open('Products.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        df.index += 1

        for pid, row in df.iterrows():
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)
            name = row['Product Name']
            description = row["About Product"]
            category = row["Category"].split("|")[0].strip()
            image = row["Image"].split("|")[0]
            owner = random.choice(list(sellers.keys()))
            products[pid]=0
            writer.writerow([name, image, description, category, owner])
        print(f'{len(products)} generated')
    return products


# creates random item listings with random price and quantity given
# inventory size and dictionaries of product ids and seller ids
def gen_inventory(num_inventory, products, sellers):
    inventory = {}
    with open('Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for i in range(num_inventory):
            if i % 100 == 0:
                print(f'{i}', end=' ', flush=True)
            seller_id = random.choice(list(sellers.keys()))
            pid = random.choice(list(products.keys()))
            quantity = fake.random_int(min=1, max=500)
            price = f'{str(fake.random_int(max=500))}.{fake.random_int(max=99):02}'
            if (seller_id, pid) not in inventory:
                inventory[(seller_id, pid)] = [quantity,price]
                writer.writerow([seller_id, pid, quantity, price])
        print(f'{num_inventory} generated')
    return inventory

# given desired number of purchases, generate random purchase history for users that are ordered or in cart
# unavailable dictionary stores product ids with exhausted inventory
def gen_purchases(num_purchases, inventory):
    buyFrom = {}
    buyWhat = {}
    final_price = []
    with open('Purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        unavailable = {}
        for id in range(1,num_purchases+1):
            if id % 100 == 0:
                print(f'{id}', end=' ', flush=True)
            uid = fake.random_int(min=1, max=num_users)
            line_item = random.choice(list(set(list(inventory.keys())) - set(list(unavailable.keys()))))
            pid = line_item[1]
            time_purchased = fake.date_time()
            seller_id = line_item[0]
            quantity = fake.random_int(min=1, max=20)
            if inventory[line_item][0] - quantity < 0:
                quantity = inventory[line_item][0]
                unavailable[line_item]=0
            order_status = random.choice(["In cart", "Ordered"])
            if order_status == "Ordered":
                buyFrom[(uid, seller_id)] = 0
                buyWhat[(uid, pid)] = 0
                final_price.append([id,inventory[line_item][1]])
            writer.writerow([uid, pid, time_purchased, seller_id, quantity, order_status])
        print(f'{num_purchases} generated')
    return [buyFrom, buyWhat, final_price]

# creates final price data for the generated purchases, protects information if seller changes prices
def gen_final_price(final_price):
    with open('FinalPrice.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Final prices...', end=' ', flush=True)
        for i in final_price:
            writer.writerow([i[0], i[1]])
        print(f'{num_purchases} generated')
    return

# generate fake ratings and reviews for a seller, given the buyFrom dictionary from purchase generation
# buyFrom stores which sellers users have bought items from
def gen_seller_reviews(num_seller_reviews, buyFrom):
    with open('ReviewsSeller.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Review sellers...', end=' ', flush=True)
        reviews = {}
        reviews_count = 0
        keys = list(buyFrom.keys())
        while reviews_count < num_seller_reviews:
            if reviews_count % 10 == 0:
                print(f'{reviews_count}', end=' ', flush=True)

            r = random.choice(keys)
            if r not in reviews:
                reviews_count +=1
                reviews[r] = 0
                uid = r[0]
                seller_id = r[1]
                reviewdate = fake.date_time()
                rating = fake.random_int(min=1, max=5)
                review = fake.sentence(nb_words=10, variable_nb_words=True)
                writer.writerow([uid, seller_id, reviewdate, rating, review])
        print(f'{num_seller_reviews} generated')
    return

# generate fake ratings and reviews for a product, given the buyWhat dictionary from purchase generation
# buyWhat stores which products users have bought
def gen_prod_reviews(num_prod_reviews, buyWhat):
    with open('ReviewsProduct.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Review products...', end=' ', flush=True)
        reviews = {}
        reviews_count = 0
        keys = list(buyWhat.keys())
        while reviews_count < num_prod_reviews:
            if reviews_count % 10 == 0:
                print(f'{reviews_count}', end=' ', flush=True)

            r = random.choice(keys)
            if r not in reviews:
                reviews_count +=1
                reviews[r] = 0
                uid = r[0]
                pid = r[1]
                reviewdate = fake.date_time()
                rating = fake.random_int(min=1, max=5)
                review = fake.sentence(nb_words=10, variable_nb_words=True)
                writer.writerow([uid, pid, reviewdate, rating, review])
        print(f'{num_prod_reviews} generated')
    return

def gen_ads(num_ads, inventory):
    with open('Advertisements.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Ads...', end=' ', flush=True)
        ad_count = 0
        keys = list(inventory.keys())
        while ad_count < num_ads:
            if ad_count % 10 == 0:
                print(f'{ad_count}', end=' ', flush=True)

            k = random.choice(keys)
            i = inventory[k]
            ad_count +=1
            seller = k[0]
            pid = k[1]
            print(pid)
            info = df.iloc[pid]
            name = info["Product Name"]
            description = info["About Product"]
            image = info["Image"].split("|")[0]
            if random.randint(0,1) == 0:
                category = info["Category"].split("|")[0].strip()
            else:
                category = random.choice(list(categories.keys()))
            start = fake.date_this_year()
            end = fake.date_this_year(after_today= True)
            impressions = fake.random_int(min=1, max=100)
            clicks = fake.random_int(min=1, max=100)
            conversions = fake.random_int(min=1, max=100)
            writer.writerow([seller, pid+1, name, description, image, category, start, end, impressions, clicks, conversions])
        print(f'{num_ads} generated')
    return


users = gen_users(num_users)
sellers = gen_sellers(num_sellers, users)
categories = gen_categories()
products = gen_products(sellers)
inventory = gen_inventory(num_inventory, products, sellers)
purchases = gen_purchases(num_purchases, inventory)
gen_seller_reviews(num_seller_reviews, purchases[0])
gen_prod_reviews(num_prod_reviews, purchases[1])
gen_final_price(purchases[2])
gen_ads(2000, inventory)
