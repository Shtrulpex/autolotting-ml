from flask import Flask, redirect, url_for, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def main():
    return render_template("home.html")

@app.route("/home.html")
def home():
    return redirect(url_for("main"))

@app.route("/order_load_page.html")
def load_order():
    return render_template("order_load_page.html")

@app.route("/order_page.html")
def order():
    return render_template("order_page.html")

@app.route("/orders_page.html")
def orders():
    return render_template("orders_page.html")

@app.route("/lots_page.html")
def lots():
    return render_template("lots_page.html")

@app.route("/print-hello", methods=['POST'])
def print_hello():
    print("Hello")
    return jsonify({"message": "HELLO printed in terminal"}), 200

if __name__ == "__main__":
    app.run()