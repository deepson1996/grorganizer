from cs50 import SQL
from flask import Flask, render_template, redirect, request, session, url_for,jsonify
from flask_mail import Mail, Message
import secrets
from helpers import apology, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.DEBUG)

from flask_session import Session

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7) 
Session(app)

app.config["MAIL_SERVER"] = "sandbox.smtp.mailtrap.io"
app.config["MAIL_PORT"] = 465
# app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "23f1ceba46b08b"  # Replace with your email
app.config["MAIL_PASSWORD"] = "a6bd449222d39d"  # Replace with your email password
app.config["MAIL_DEFAULT_SENDER"] = "pokhreldipshan1996@gmail.com"

mail = Mail(app)


db = SQL("sqlite:///grocery.db")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "GET":
        return render_template("auth/register.html")
    else:
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        if not email or not password or not name:
            return apology("Please fillup all the fields", 403)
        if password != confirm:
            return apology("must match password and confirm password", 400)
        
        existing = db.execute("SELECT * FROM users where email = ?", email)
        if len(existing) != 0:
            return apology("duplicate user", 400)
        
        user_id = db.execute("INSERT INTO users (name, email, password) values(?, ?, ?)",
                             name, email, generate_password_hash(password))
        session["user_id"] = user_id
        session["user_name"] = name
        
        return redirect("/dashboard")

@app.route("/", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember_me = request.form.get("remember_me")
        
        if not email or not password:
            return apology("Please provide valid credentials", 403)
        
        users = db.execute("SELECT * FROM users WHERE email=?", email)
        
        if len(users) != 1 or not check_password_hash(
            users[0]["password"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)
        if remember_me:
            session.permanent = True
        else:
            session.permanent = False
        session["user_id"] = users[0]["id"]
        session["user_name"] = users[0]["name"]
        return redirect("/dashboard")
        
    else:
        return render_template("auth/login.html")
    
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "GET":
        return render_template("auth/forgot.html")
    else:
        email = request.form.get("email")
        if not email:
            return apology("Please provide email")
        users = db.execute("SELECT * FROM users WHERE email = ?", email)
        if(len(users) != 1):
            return apology("Invalid Email")
        token = secrets.token_urlsafe(16)

        expiration_time = datetime.utcnow() + timedelta(hours=1)
        db.execute("UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?",
                   token, expiration_time, email)

        reset_url = url_for('reset_password', token=token, _external=True)

        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Click the following link to reset your password: {reset_url}"
        try:
            mail.send(msg)
            return redirect("/")
        except:
            return apology("Failed to send email. Please try again later.")

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = db.execute("SELECT * FROM users WHERE reset_token = ?", token)
    
    if len(user) != 1:
        return apology("Invalid or expired token")
    
    user = user[0]
    reset_token_expiry = datetime.strptime(user["reset_token_expiry"], "%Y-%m-%d %H:%M:%S")
    
    if datetime.utcnow() > reset_token_expiry:
        return apology("Token has expired")
    
    if request.method == "POST":
        new_password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if not new_password or not confirmation:
            return apology("Fillup all the fields")
        
        if new_password != confirmation:
            return apology("Passwords donot match")

        # Update the user's password in the database
        db.execute("UPDATE users SET password = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?",
                   generate_password_hash(new_password), user["id"])
        
        return redirect("/")
    
    return render_template("auth/reset.html", token=token)
        
@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changePassword():
    if request.method=="GET":
        return render_template("auth/changepassword.html")
    else:
        old = request.form.get("oldpassword")
        new = request.form.get("password")
        confirm = request.form.get("confirmation")
        
        if not old or not new:
            return apology("Please fillup all the fields", 400)
        if new != confirm:
            return apology("must match password and confirm password", 400)
        
        users = db.execute("SELECT * FROM users where id = ?", session.get("user_id"))

        if len(users) != 1 or not check_password_hash(
            users[0]["password"], old
        ):
            return apology("invalid old password", 400)
        db.execute("UPDATE users SET password = ? WHERE id = ?",
                             generate_password_hash(new), session.get("user_id"))
        return redirect("/dashboard")
        
@app.route("/profile", methods=["GET", "POST"])
@login_required 
def profile():
    users = db.execute("SELECT * FROM users where id = ?", session.get("user_id"))
    if len(users) != 1:
        return apology("User not found", 400)
    if request.method == "GET":
        return render_template("auth/profile.html", user=users[0])
    else:
        name = request.form.get("name")
        email = request.form.get("email")
        if not name or not email:
            return apology("Please fillup all the fields", 403)
        db.execute("UPDATE users SET name = ?, email = ? WHERE id = ?",
                             name, email, session.get("user_id"))
        return redirect("/profile")
        
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

def compute_grocery(groceries):
    for grocery in groceries:
        item_count_per_place = db.execute("""
            SELECT places.place, COUNT(grocery_items.id) as count 
            FROM grocery_items 
            JOIN places ON grocery_items.place_id = places.id 
            WHERE grocery_items.grocery_id = ? 
            GROUP BY places.place
        """, grocery["id"])
        total_spent = db.execute("SELECT SUM(price) as total FROM grocery_items WHERE grocery_id = ?", grocery["id"])[0]["total"]
        grocery["item_count_per_place"] = item_count_per_place
        grocery["total_spent"] = total_spent if total_spent else 0
        
    return groceries

@app.route("/dashboard")
@login_required
def index():
    groceries = db.execute("SELECT * FROM groceries WHERE user_id = ? ORDER BY updated_at DESC", session.get("user_id"))
    
    shared = db.execute("SELECT groceries.*, shared_groceries.id as sid FROM shared_groceries JOIN groceries ON groceries.id = shared_groceries.grocery_id WHERE shared_groceries.shared_to = ? ORDER BY groceries.updated_at DESC", session.get("user_id"))
    
    my_groceries = compute_grocery(groceries)
    shared_groceries = compute_grocery(shared)
    
    return render_template("index.html", groceries=my_groceries, shared_groceries=shared_groceries)

@app.route("/groceries/create", methods=["GET", "POST"])
@login_required
def create_grocery():
    if request.method == "GET":
        return render_template("add_groceries.html")
    else:
        name = request.form.get("name")    
        balance = float(request.form.get("balance"))

        if not name:
            return apology("Name is required")
        if balance < 0:
            return apology("Balance cannot be negative")
        
        gid = db.execute("INSERT INTO groceries (name, balance, user_id) VALUES (?, ?, ?)", name, balance, session.get("user_id"))
        
        return redirect(f"/groceries/items/{gid}")

@app.route("/groceries/delete/<id>")
@login_required
def delete_grocery(id):
    db.execute("DELETE FROM groceries WHERE id = ?", id)
    return redirect(request.referrer) 

@app.route("/groceries/share/<id>", methods=["GET", "POST"])
@login_required
def share_grocery(id):
    if request.method == "GET":
        contacts = db.execute("SELECT users.*, contacts.id as cid, contacts.created_by, contacts.user_contact_id FROM contacts JOIN users ON contacts.user_contact_id = users.id WHERE contacts.created_by = ?", session.get("user_id"))
        
        for contact in contacts:
            contact["shared"] = False
            shared = db.execute("SELECT * FROM shared_groceries WHERE shared_by = ? AND shared_to = ? AND grocery_id = ?", contact["created_by"], contact["user_contact_id"], id)
            if(len(shared) > 0):
                contact["shared"] = True
                contact['sharedg_id'] = shared[0]["id"]
        return render_template("share_list.html", contacts=contacts)
    else:
        cids = request.form.getlist('contacts[]')
        if not cids:
            return apology("You need to select at least 1 contact")
        for cid in cids:
            db.execute("INSERT INTO shared_groceries (shared_by, shared_to, grocery_id) VALUES (?, ?, ?)", session.get("user_id"),  cid, id)
        return redirect(request.referrer) 

@app.route("/groceries/undoshare/<id>")
@login_required
def undo_share_grocery(id):
    db.execute("DELETE FROM shared_groceries WHERE id = ?", id)
    return redirect(request.referrer)

@app.route("/groceries/edit/<id>", methods=["GET", "POST"])
@login_required
def edit_grocery(id):
    grocery = db.execute("SELECT * FROM groceries WHERE id = ?", id)
    if len(grocery) != 1:
        return apology("Grocery not found", 400)
    if request.method == "GET":          
        return render_template("edit_groceries.html", grocery = grocery[0])
    else:
        name = request.form.get("name")
        balance = float(request.form.get("balance"))
        if not name:
            return apology("Name is required")
        if balance < 0:
            return apology("Balance cannot be negative")
        db.execute("UPDATE groceries SET name = ?, balance = ? WHERE id = ?", name, balance, id)
        return redirect("/dashboard")
        
@app.route("/groceries/shop/<id>")
@login_required
def shop(id):
    grocery = db.execute("SELECT balance FROM groceries WHERE id = ?", id)
    if(len(grocery) != 1):
        return apology("Grocery Not Found")
    places = db.execute("SELECT * FROM places WHERE id IN (SELECT place_id from grocery_items where grocery_id = ?) ORDER BY place", id)
    items_by_place = {}
    expenditure = 0
    for place in places:
        items = db.execute("""
            SELECT grocery_items.id, grocery_items.name, grocery_items.price, grocery_items.bought, 
                   categories.category 
            FROM grocery_items 
            JOIN categories ON grocery_items.category_id = categories.id 
            WHERE grocery_items.grocery_id = ? AND grocery_items.place_id = ? 
            ORDER BY categories.category
        """, id, place["id"])
        items_by_place[place["place"]] = items
    total_price = db.execute("SELECT SUM(price) as price FROM grocery_items WHERE grocery_id = ?", id)
    
    return render_template("shop.html", items_by_place=items_by_place, budget = grocery[0]["balance"], expenditure = total_price[0]["price"])

def update_total(id):
    # print(id, "hello")
    grocery_items = db.execute("SELECT * FROM grocery_items WHERE grocery_id = ?", id)
    # print(grocery_items)
    grocery_total = 0
    completed = True
    for item in grocery_items:
        # print(item)
        if(item["bought"] == 1):
            grocery_total += item['price']
        if(item['bought']) == 0:
            completed = False
    db.execute("UPDATE groceries SET completed = ?, expenditure = ? WHERE id = ?", completed, grocery_total, id)

@app.route("/shop/buy/<id>", methods=["GET"])
@login_required
def buy(id):
    found = db.execute("SELECT * FROM grocery_items WHERE id = ?", id)
    if len(found) != 1:
        return apology("Grocery item not found")
    price = float(request.args.get("price"))
    if price < 0:
        return apology("You cannot have negative price")
    db.execute("UPDATE grocery_items SET price = ?, bought = 1 WHERE id = ?", price, id)
    
    # Update Grocery Total
    # Update Completed or not
    # print(found)
    update_total(found[0]["grocery_id"])
    
    return redirect(request.referrer)

@app.route("/shop/notbuy/<id>")
@login_required
def notbuy(id):
    found = db.execute("SELECT * FROM grocery_items WHERE id = ?", id)
    # print(found)
    if len(found) != 1:
        return apology("Grocery item not found")
    
    db.execute("UPDATE grocery_items SET  bought = -1, price = 0 WHERE id = ?", (id))
    # print(found)
    update_total(found[0]["grocery_id"])
    return redirect(request.referrer)

@app.route("/shop/undobuy/<id>")
@login_required
def undobuy(id):
    found = db.execute("SELECT * FROM grocery_items WHERE id = ?", id)
    # print(found)
    if len(found) != 1:
        return apology("Grocery item not found")
    
    db.execute("UPDATE grocery_items SET  bought = 0 WHERE id = ?", id)

    # print(found)
    update_total(found[0]["grocery_id"])
    return redirect(request.referrer)
    

@app.route("/groceries/items/<id>", methods=["GET", "POST"])
@login_required
def groceries_items(id):
    grocery = db.execute("SELECT * FROM groceries WHERE id = ?", id)
    if len(grocery) != 1:
        return apology("Invalid url")
    if request.method == "GET":
        category_id = request.args.get('category_id')
        place_id = request.args.get('place_id')
        categories = db.execute("SELECT * FROM categories")
        places = db.execute("SELECT * FROM places")
        items = db.execute("SELECT grocery_items.*, categories.category, places.place FROM grocery_items JOIN categories ON categories.id = grocery_items.category_id JOIN places ON places.id = grocery_items.place_id WHERE grocery_id = ? ORDER BY updated_at DESC", id)
        
        return render_template("grocery_items.html", categories = categories, places=places, items=items, grocery=grocery[0], category_id = category_id, place_id=place_id)
    else:
        place_id = request.form.get("place")
        category_id = request.form.get("category")
        name = request.form.get("name")
        
        if not place_id or not category_id or not name:
            return apology("Please provide all the details")
        
        place = db.execute("SELECT * FROM places where id = ?", place_id)
        category = db.execute("SELECT * FROM categories where id = ?", category_id)
        
        if len(place) != 1 or len(category) != 1:
            return apology("Place or category not found")
        
        db.execute("INSERT INTO grocery_items (name, price, grocery_id, category_id, place_id) VALUES (?, ?, ?, ?, ?)", name, 0, id, category_id, place_id)
        
        return redirect(url_for('groceries_items', id=id, category_id=category_id, place_id=place_id))
        
@app.route("/grocery/items/delete/<id>")
@login_required
def delete_grocery_items(id):
    db.execute("DELETE FROM grocery_items WHERE id = ?", id)
    return redirect(request.referrer)      
                    

@app.route("/categories")
@login_required
def categories():
    categories = db.execute("SELECT * FROM categories")
    return render_template("categories.html", categories=categories)

@app.route("/categories/create", methods=["GET", "POST"])
@login_required
def add_categories():
    if request.method == "GET":
        return render_template("add_categories.html")
    else:
        category = request.form.get("category")
        
        if not category:
            return apology("Category cannot be null", 400)
        existing = db.execute("SELECT * FROM categories WHERE category = ?", category)
        if len(existing) != 0:
            return apology("Duplicate category")
        
        db.execute("INSERT INTO categories (category, description) VALUES (?, ?)", category, request.form.get("description"))
        
        return redirect("/categories")

@app.route("/categories/delete/<id>")
@login_required
def delete_categories(id):
    db.execute("DELETE FROM categories WHERE id = ?", id)
    return redirect("/categories")

@app.route("/categories/edit/<id>", methods=["GET", "POST"])
@login_required
def edit_categories(id):
    category = db.execute("SELECT * FROM categories WHERE id = ?", id)
    if len(category) != 1:
        return apology("Category not found", 400)
    if request.method == "GET":
        return render_template("edit_categories.html", category=category[0])
    else:
        new_category = request.form.get("category")
        existing = db.execute("SELECT * FROM categories WHERE category = ? AND id != ?", new_category, id)
        if len(existing) != 0:
            return apology("Duplicate category")
        
        db.execute("UPDATE categories SET category = ?, description = ? WHERE id = ?", new_category, request.form.get("description"), id)
        
        return redirect("/categories")

@app.route("/places")
@login_required
def places():
    places = db.execute("SELECT * FROM places")
    return render_template("places.html", places=places)

@app.route("/places/create", methods=["GET", "POST"])
@login_required
def add_places():
    if request.method == "GET":
        return render_template("add_places.html")
    else:
        place = request.form.get("place")
        
        if not place:
            return apology("place cannot be null", 400)
        existing = db.execute("SELECT * FROM places WHERE place = ?", place)
        if len(existing) != 0:
            return apology("Duplicate place")
        
        db.execute("INSERT INTO places (place, description) VALUES (?, ?)", place, request.form.get("description"))
        
        return redirect("/places")

@app.route("/places/delete/<id>")
@login_required
def delete_places(id):
    db.execute("DELETE FROM places WHERE id = ?", id)
    return redirect("/places")

@app.route("/places/edit/<id>", methods=["GET", "POST"])
@login_required
def edit_places(id):
    place = db.execute("SELECT * FROM places WHERE id = ?", id)
    if len(place) != 1:
        return apology("place not found", 400)
    if request.method == "GET":
        return render_template("edit_places.html", place=place[0])
    else:
        new_place = request.form.get("place")
        existing = db.execute("SELECT * FROM places WHERE place = ? AND id != ?", new_place, id)
        if len(existing) != 0:
            return apology("Duplicate place")
        
        db.execute("UPDATE places SET place = ?, description = ? WHERE id = ?", new_place, request.form.get("description"), id)
        
        return redirect("/places")
        
    
@app.route("/contacts", methods=["GET", "POST"])
@login_required
def contacts():
    if request.method == "GET":
        users = db.execute("SELECT contacts.*, users.name, users.email FROM contacts JOIN users ON users.id = contacts.user_contact_id WHERE contacts.created_by = ?", session.get("user_id"))
        return render_template("contacts.html", contacts = users)
    else:
        email = request.form.get("email")
        if not email:
            return apology("Please provide email.")
        user = db.execute("SELECT * FROM users WHERE email = ?", email)
        if len(user) != 1:
            return apology("User not found")
        if user[0]["id"] == session.get("user_id"):
            return apology("You cannot add yourself")
        created_by = session.get("user_id")
        user_contact_id = user[0]["id"]
        existing = db.execute("SELECT * FROM contacts where created_by = ? and user_contact_id = ?", created_by, user_contact_id)
        if(len(existing) != 0):
            return apology("Duplicate contact")
        db.execute("INSERT INTO contacts (created_by, user_contact_id) VALUES (?, ?)", created_by, user_contact_id)
        
        return redirect("/contacts")
        
@app.route("/contacts/delete/<id>")
@login_required
def delete_contacts(id):
    db.execute("DELETE FROM contacts WHERE id = ?", id)
    return redirect("/contacts")

@app.route("/reports")
@login_required
def reports():
    # Extract filter parameters from request.args
    user_id = session.get("user_id")
    filters = {
        "grocery_name": request.args.get("grocery_name"),
        "budget_min": request.args.get("budget_min"),
        "budget_max": request.args.get("budget_max"),
        "exp_min": request.args.get("exp_min"),
        "exp_max": request.args.get("exp_max"),
        "grocery_completed": request.args.get("grocery_completed"),
        "item_name": request.args.get("item_name"),
        "item_price_min": request.args.get("item_price_min"),
        "item_price_max": request.args.get("item_price_max"),
        "item_status": request.args.get("item_status"),
        "category_name": request.args.get("category_name"),
        "place_name": request.args.get("place_name"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
    }

    # Base query
    query = "SELECT * FROM report_generation WHERE user_id = ?"
    values = [user_id]
    
    # Add filters to the query dynamically
    clauses = []

    if filters["grocery_name"]:
        clauses.append("grocery_name LIKE ?")
        values.append(f"%{filters['grocery_name']}%")
    
    if filters["budget_min"]:
        clauses.append("grocery_balance >= ?")
        values.append(filters["budget_min"])
    
    if filters["budget_max"]:
        clauses.append("grocery_balance <= ?")
        values.append(filters["budget_max"])
    
    if filters["exp_min"]:
        clauses.append("grocery_expenditure >= ?")
        values.append(filters["exp_min"])
    
    if filters["exp_max"]:
        clauses.append("grocery_expenditure <= ?")
        values.append(filters["exp_max"])
    
    if filters["grocery_completed"] is not None and filters["grocery_completed"] != "":
        clauses.append("grocery_completed = ?")
        values.append(filters["grocery_completed"])
    
    if filters["item_name"]:
        clauses.append("item_name LIKE ?")
        values.append(f"%{filters['item_name']}%")
    
    if filters["item_price_min"]:
        clauses.append("item_price >= ?")
        values.append(filters["item_price_min"])
    
    if filters["item_price_max"]:
        clauses.append("item_price <= ?")
        values.append(filters["item_price_max"])
    
    if filters["item_status"] is not None and filters["item_status"] != "":
        clauses.append("item_bought = ?")
        values.append(filters["item_status"])
    
    if filters["category_name"]:
        clauses.append("category_name = ?")
        values.append(filters["category_name"])
    
    if filters["place_name"]:
        clauses.append("place_name = ?")
        values.append(filters["place_name"])
    
    if filters["start_date"]:
        clauses.append("DATE(grocery_updated_at) >= ?")
        values.append(filters["start_date"])
    
    if filters["end_date"]:
        clauses.append("DATE(grocery_updated_at) <= ?")
        values.append(filters["end_date"])

    # If we have clauses, append them to the base query
    if clauses:
        query += " AND " + " AND ".join(clauses)
    
    # Fetch categories and places for the dropdowns
    categories = db.execute("SELECT DISTINCT category_name FROM report_generation WHERE user_id = ? AND category_name IS NOT NULL", user_id)
    places = db.execute("SELECT DISTINCT place_name FROM report_generation WHERE user_id = ? AND place_name IS NOT NULL", user_id)

    # Execute the query with the dynamic parameters
    details = db.execute(query, *values)
    
    # Render the template
    return render_template("reports.html", details=details, categories=categories, places=places)


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")

@app.route('/api/analytics')
@login_required
def analytics_data():
    user_id = session.get("user_id")
    
    category_expenditure = db.execute(
        "SELECT category_name, SUM(item_price) AS expenditure FROM report_generation WHERE user_id = ? AND item_bought = 1 GROUP BY category_name HAVING  expenditure > 0", 
        user_id
    )
    
    place_expenditure = db.execute(
        "SELECT place_name, SUM(item_price) AS expenditure FROM report_generation WHERE user_id = ? AND item_bought = 1 GROUP BY place_name HAVING  expenditure > 0", 
        user_id
    )

    daily_expences = db.execute(
        "SELECT DATE(grocery_updated_at) AS date, SUM(item_price) AS expences FROM report_generation WHERE user_id = ? AND item_bought = 1 GROUP BY DATE(grocery_updated_at) HAVING expences > 0",
        user_id
    )
    gr = {}
    gr["completed"] = db.execute("SELECT COUNT(*) count FROM groceries WHERE completed = 1 AND user_id = ?", user_id)[0]['count']
    gr["incomplete"] = db.execute("SELECT COUNT(*) count FROM groceries WHERE completed = 0 AND user_id=?", user_id)[0]['count']
    
    item_prices = db.execute("SELECT item_price FROM report_generation WHERE item_bought = 1 AND user_id = ?", user_id)
    
    budgetexp = db.execute("SELECT DATE(updated_at) AS date, SUM(balance) AS budget, SUM(expenditure) AS expenditure FROM GROCERIES WHERE user_id = ? GROUP BY DATE(updated_at)", user_id)
    
    
    logging.debug(budgetexp)
    return jsonify({
        "category_expenditure": category_expenditure,
        "daily_expences": daily_expences,
        "place_expenditure" : place_expenditure,
        "gr" : gr,
        "item_prices": item_prices,
        "budgetexp": budgetexp
    })

if __name__ == '__main__':
    app.run(debug=True)