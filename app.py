# from flask import Flask, render_template, request, redirect, url_for,send_file
# from flask_mysqldb import MySQL
# import io
from flask import Flask, render_template, request, redirect, url_for, jsonify,send_file,session
from flask_mysqldb import MySQL
import pandas as pd
import io
import MySQLdb.cursors
from flask import session
import datetime
app = Flask(__name__)


# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'        # change if needed
app.config['MYSQL_PASSWORD'] = ''        # change if needed
app.config['MYSQL_DB'] = 'product'       # your database name

mysql = MySQL(app)

# -----------------------
# Home page
# -----------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/products')
def product_list():
    cur = mysql.connection.cursor()
    search = request.args.get('search')

    if search:
        cur.execute(
            "SELECT * FROM products WHERE name LIKE %s OR name LIKE %s ORDER BY id DESC",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cur.execute("SELECT * FROM products ORDER BY id DESC")

    data = cur.fetchall()
    cur.close()
    return render_template('category.html', products=data, search=search)

# -----------------------
# Add new product
# -----------------------
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            name = request.form['name']
            price = float(request.form['price'])
            stock = int(request.form['stock'])

            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                (name, price, stock)
            )
            mysql.connection.commit()
            cur.close()

            return redirect('/products')
        except Exception as e:
            return f"Database Error: {e}"

    # If GET → show the form
    return render_template('add.html')



@app.route('/products/process')
def process_sale():
    return render_template('process_sale.html')

    
@app.route('/products/edit/<int:id>', methods=['GET','POST'])
def edit_product(id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        # Get updated values from form
        name = request.form['name']
        price = float(request.form['price'])
        stock = int(request.form['stock'])

        # Update database
        cur.execute("""
            UPDATE products
            SET name=%s, price=%s, stock=%s
            WHERE id=%s
        """, (name, price, stock, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("product_list"))

    else:
        # GET method: fetch product to show in form
        cur.execute("SELECT * FROM products WHERE id=%s", (id,))
        product = cur.fetchone()
        cur.close()
        if product:
            return render_template('edit.html', product=product)
        else:
            return "Product not found", 404

@app.route('/products/delete/<int:id>')
def delete_product(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM products WHERE id=%s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect('/products')
    except Exception as e:
        return f"Error: {e}"
# -----------------------
# Dashboard
# -----------------------
@app.route('/category')
def dashboard():
    cur = mysql.connection.cursor()

    # Count products
    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    # Sum of stock
    cur.execute("SELECT SUM(stock) FROM products")
    total_stock = cur.fetchone()[0] or 0

    # Count chat messages
    cur.execute("SELECT COUNT(*) FROM chat")
    total_messages = cur.fetchone()[0]

    cur.close()
    return render_template('category.html',
                           total_products=total_products,
                           total_stock=total_stock,
                           total_messages=total_messages)

@app.route('/category')
def product_research():
    cur = mysql.connection.cursor()
    search = request.args.get('search')

    if search:
        # search by name or category
        cur.execute("SELECT * FROM products WHERE name LIKE %s OR category LIKE %s ORDER BY id DESC",
                    (f"%{search}%", f"%{search}%"))
    else:
        # show all products
        cur.execute("SELECT * FROM products ORDER BY id DESC")

    data = cur.fetchall()
    cur.close() 
    return render_template('category.html', products=data, search=search) 
# ----------------------- 
# Run Flask app 
# -----------------------
@app.route('/download/excel')
def download_excel():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, price, stock FROM products")
    data = cur.fetchall()
    cur.close()

    # Convert to pandas DataFrame
    df = pd.DataFrame(data, columns=['ID', 'Name', 'Price', 'Stock'])

    # Save Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')

    output.seek(0)

    # Send file to user for download
    return send_file(output,
                     download_name="products.xlsx",
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/products/view_sale')
def view():
    return render_template('view.html')

@app.route('/products/aba')
def aba_pay():
    return render_template('aba.html')


@app.route('/products/final', methods=['GET', 'POST'])
def final_receipt():
    if request.method == "POST":
        try:
            customer_name = request.form['customer_name']
            product_name = request.form['name']
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create receipt dictionary
            receipt = {
                'customer_name': customer_name,
                'name': product_name,
                'price': price,
                'stock': stock,
                'date': date
            }

            # Render template with receipt
            return render_template('final_receipt.html', receipt=receipt)

        except Exception as e:
            return f"Error: {e}"

    # GET request → show form, no receipt yet
    return render_template('final_receipt.html', receipt=None)


@app.route('/products/admin')
def admin():
    return render_template('admin_account.html')

if __name__ == '__main__':
    app.run(debug=True)
# app.run(debug=True)