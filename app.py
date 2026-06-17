from flask import Flask,render_template,request,redirect,url_for,session
from database import get_connection, init_db
app=Flask(__name__); app.secret_key="devops"; init_db()

@app.route("/")
def index():
    conn=get_connection(); p=conn.execute("select * from products").fetchall(); conn.close()
    return render_template("index.html",products=p)

@app.route("/product/<int:id>")
def product(id):
    conn=get_connection(); p=conn.execute("select * from products where id=?",(id,)).fetchone(); conn.close()
    return render_template("product.html",product=p)

@app.route("/add-to-cart/<int:id>")
def add(id):
    cart=session.get("cart",{})
    cart[str(id)]=cart.get(str(id),0)+1
    session["cart"]=cart
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    conn=get_connection(); items=[]; total=0
    for pid,q in session.get("cart",{}).items():
        p=conn.execute("select * from products where id=?",(pid,)).fetchone()
        subtotal=p["price"]*q; total+=subtotal; items.append((p,q,subtotal))
    conn.close()
    return render_template("cart.html",items=items,total=total)

@app.route("/checkout")
def checkout():
    conn=get_connection(); total=0; cart=session.get("cart",{})
    for pid,q in cart.items():
        p=conn.execute("select * from products where id=?",(pid,)).fetchone()
        total+=p["price"]*q
    cur=conn.cursor(); cur.execute("insert into orders(total_amount) values(?)",(total,))
    oid=cur.lastrowid
    for pid,q in cart.items():
        p=conn.execute("select * from products where id=?",(pid,)).fetchone()
        cur.execute("insert into order_items(order_id,product_id,quantity,price) values(?,?,?,?)",(oid,pid,q,p["price"]))
    conn.commit(); conn.close(); session["cart"]={}
    return redirect(url_for("orders"))

@app.route("/orders")
def orders():
    conn=get_connection(); o=conn.execute("select * from orders order by id desc").fetchall(); conn.close()
    return render_template("orders.html",orders=o)

@app.route("/admin")
def admin():
    conn=get_connection(); p=conn.execute("select * from products").fetchall(); conn.close()
    return render_template("admin.html",products=p)

@app.route("/admin/add",methods=["GET","POST"])
def addp():
    if request.method=="POST":
        conn=get_connection(); conn.execute("insert into products(name,description,price,stock,image) values(?,?,?,?,?)",
        (request.form["name"],request.form["description"],request.form["price"],request.form["stock"],request.form["image"]))
        conn.commit(); conn.close(); return redirect("/admin")
    return render_template("add_product.html")

@app.route("/health")
def health(): return {"status":"UP"}
@app.route("/version")
def version(): return {"version":"1.0.0"}
@app.route("/metrics")
def metrics():
    conn=get_connection(); c=conn.execute("select count(*) from products").fetchone()[0]; conn.close()
    return f"product_count {c}\n"


@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    conn = get_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    ).fetchone()

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        stock = request.form["stock"]
        image = request.form["image"]

        conn.execute("""
            UPDATE products
            SET name=?,
                description=?,
                price=?,
                stock=?,
                image=?
            WHERE id=?
        """,
        (name, description, price, stock, image, id))

        conn.commit()
        conn.close()

        return redirect("/admin")

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )


@app.route("/admin/delete/<int:id>")
def delete_product(id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

if __name__=="__main__": app.run(host="0.0.0.0",port=5000)


