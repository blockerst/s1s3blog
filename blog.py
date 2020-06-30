from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from wtforms import StringField,TextAreaField,PasswordField,validators,Form
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from functools import wraps

#kullanıcı giriş decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Giriş yapmanız gerekli","warning")
            return redirect(url_for("login"))
    return decorated_function

#kullanıcı kayıt formu

class Registerform(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 3,max = 25),validators.DataRequired(message= "İsim Soyisim Giriniz")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 4,max = 20)])
    email = StringField("Email Adresi",validators=[validators.Email(message="Lütfen geçerli bir e-mail adresi giriniz")])
    password = PasswordField("Parola",validators=[  
        validators.DataRequired(message= "Parola Giriniz"),
        validators.EqualTo(fieldname="confirm",message="Aynı Parolayı Giriniz")
    ])
    confirm = PasswordField("Parola Doğrulama")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")

app = Flask(__name__)
app.secret_key = "s1s3blog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "S1S3 Blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    

    return render_template("index.html", )

@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarılı","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Yanlış parola","danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullanıcı bulunmuyor","danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/register",methods = ["GET","POST"])
def register():

    form = Registerform(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla kayıt oldunuz","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
#logout 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
    

#addarticle
@app.route("/addarticle",methods = ["GET","POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles (title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makaleniz eklendi","success")
        return redirect(url_for("dashboard"))


    return render_template("addarticle.html",form = form)

#makale sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")
#detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")


#makale silme

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete From articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya silme yetkiniz yok","danger")
        return redirect(url_for("index"))


#makale güncelleme
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya güncellemeye yetkiniz yok")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else:
        #post request
        form = ArticleForm(request.form)

        newtitle = form.title.data
        newcontent = form.content.data
        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))
        mysql.connection.commit()
        flash("Makale Güncellendi","info")
        return redirect(url_for("dashboard"))

#arama url
@app.route("/search", methods = ["GET","POST"])
def search():
        if request.method == "GET":
            return redirect(url_for("articles"))
        else:
            keyword = request.form.get("keyword")
            cursor = mysql.connection.cursor()
            sorgu = "Select * from articles where title  like '%" + keyword + "%'"
            result = cursor.execute(sorgu)
            if result == 0:
                flash("Aranan kelimeye uygun makale bulunamadı","warning")
                return redirect(url_for("articles"))
            else:
                articles = cursor.fetchall()
                return render_template("articles.html", articles = articles)


#Makale formu
class ArticleForm(Form):
    title  = StringField("Makale Başlığı",validators=[validators.length(min = 3, max= 90,message=("başlık 3 ve 90 karakter aralığında olmalı"))])
    content = TextAreaField("Makale",validators=[validators.length(min=1)])
if __name__ == "__main__":
    app.run(debug=True)


































