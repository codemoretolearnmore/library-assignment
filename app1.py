from flask import Flask, render_template, jsonify,request
import math
from datetime import datetime
import pandas as pd
import uuid
import mysql.connector
from mysql.connector import Error, errorcode
import requests
conn = mysql.connector.connect(host = 'sql6.freesqldatabase.com', username = 'sql6681622', password = 'jz1dJylwGj', database = 'sql6681622')

my_cursor = conn.cursor()

app = Flask(__name__)

# exceptions 

class NotEnoughStockError(Exception):
    pass

class DueLimitExceedError(Exception):
    pass

class DuplicateBookError(Exception):
    pass

class NoUserException(Exception):
    pass

class UserUpdateException(Exception):
    pass

endUserID = 'd3da860f-d259-4c5d-8309-2c5b1386788d'


# books routes

def add_book(my_cursor,book,conn):
    quantity = 1
    # first check if book is already in db
    check_book_query = 'select bookID from books where bookID = %s'
    my_cursor.execute(check_book_query,(book['bookID'],))
    row = my_cursor.fetchone()
    if not row or row[0]=='':
        get_user_query = (
            "INSERT IGNORE INTO books (bookID, title, authors, average_rating, isbn_13, language_code,num_pages, ratings_count, text_reviews_count, publisher, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        values = (
            book['bookID'], book['title'], book['authors'], book['average_rating'],
            book['isbn13'], book['language_code'], book['  num_pages'], book['ratings_count'],
            book['text_reviews_count'], book['publisher'], quantity,
        )
        my_cursor.execute(get_user_query,values)
        conn.commit()
        print('reached',my_cursor.rowcount)
        return my_cursor.rowcount
    else:
        update_book_quantity = 'update books set quantity = quantity+ %s where bookID = %s'
        my_cursor.execute(update_book_quantity,(quantity,book['bookID'],))
        conn.commit()
        return my_cursor.rowcount
    

@app.route('/')
def index():
    return render_template('profile.html')


@app.route('/books',methods = ['GET'])
def load_books_page():
    return render_template('books1.html',data=[{}])

#get books data route

@app.route('/books/data', methods =['GET'])
def get_books_data():
    keyword = request.args.get('keyword', '').lower()
    keyword = keyword.strip()
    try:
        if len(keyword)==0:
            get_book_query = 'SELECT DISTINCT * FROM books LIMIT 20'
            df = pd.read_sql(get_book_query, conn)
            books_data =  df.to_dict(orient='records')
        else:
            # get_book_query = "SELECT DISTINCT * FROM books WHERE lower(title) LIKE '%" + keyword + "%'"
            get_book_query = "SELECT DISTINCT * FROM books WHERE lower(title) LIKE %s"
            # df = pd.read_sql(get_book_query, conn,('%' + keyword + '%',))
            my_cursor.execute(get_book_query,('%' + keyword + '%',))
            results = my_cursor.fetchall()
            columns = ['bookID','title', 'authors','average_rating','isbn_13','langauge_code','num_pages','ratings_count','text_reviews_count','publisher','quantity']
            df = pd.DataFrame(results, columns=columns)
            books_data =  df.to_dict(orient='records')
            print(books_data)
        response_data = {
            'data':books_data,
            'success':1,
            'message':'Fetched Data Successfully'
        }
        return jsonify(response_data),200
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            
            response_data = {
                'data':[],
                'success':0,
                'message':'Internal Server Error'
            }
            return jsonify(response_data),500
        print(mysql_error)
        return jsonify({
                'data':[],
                'success':0,
                'message':'Internal Server Error'
            }),500
    except Exception as e:
        print(f"Database Error: {str(e)}")
        error_message = "An Error Occured while retrieving data from database"
        response_data = {
            'data':[],
            'success':0,
            'message':error_message
        }
        return jsonify(response_data),500

    
    # return render_template('books1.html', data=[{"bookID":"39763","title":"The Mystical Poems of Rumi 1:  The Mystical Poems of Rumi 1: The Mystical Poems of Rumi 1: First Selection That is truth  Poems 1-200","authors":"Rumi/A.J. Arberry","average_rating":"4.28","isbn":"0226731510","isbn13":"9780226731513","language_code":"eng","  num_pages":"208","ratings_count":"114","text_reviews_count":"8","publication_date":"3/15/1974","publisher":"University Of Chicago Press"},{"bookID":"17946","title":"Seven Nights","authors":"Jorge Luis Borges/Eliot Weinberger","average_rating":"4.33","isbn":"0811209059","isbn13":"9780811209052","language_code":"eng","  num_pages":"121","ratings_count":"1037","text_reviews_count":"60","publication_date":"5/29/1985","publisher":"New Directions Publishing Corporation"}])


@app.route('/books', methods=["POST"])
def add_books():
    data = request.get_json()
    keyword = data['keyword']
    quantity = int(data['quantity'])
    total_loop_count = math.ceil(quantity/20)
    val = 0
    books=[]
    success_enteries=[]
    try:
        for i in range(total_loop_count):
            url = "https://frappe.io/api/method/frappe-library?title="+keyword+"&page="+str(i+1)
            res = requests.get(url)
            if res.status_code ==200:
                result = res.json()
                books = result['message']
                print(books)
                for book in books:
                    rowCount = add_book(my_cursor,book,conn)
                    if rowCount!=1:
                        response_data = {
                            'success_enteries':success_enteries,
                            'success':0,
                            'message':'Added '+str(val)+' unique books'
                        }
                        return jsonify(response_data),201
                    else:
                        success_enteries.append(book)
                        val+=1
            else:
                response_data ={
                    'success_enteries':success_enteries,
                    'success':0,
                    'message':'Error Occured while fetching books data from API'
                }
                # third party api failed
                return jsonify(response_data),502
        response_data = {
            'success_enteries':success_enteries,
            'success':1,
            'message':'Added '+str(len(success_enteries))+" successfully"
        }
        return jsonify(response_data),201
    except Exception  as e:
        response_data = {
            'success_enteries':success_enteries,
            'success':0,
            'message':'Error Occured while saving data '
        }
        print(e)
        return jsonify(response_data),500

    


# # users routes

@app.route('/users',methods = ['GET'])
def load_user_page():
    return render_template('users.html', data=[{}])

##user profile data

@app.route('/user/profile',methods = ['GET'])
def load_ProfileData():
    userID = request.headers.get('userID')
    try:
        get_profile_query = 'select name, email, phone_no, address from users where _id = %s'
        row = my_cursor.execute(get_profile_query,(userID,))
        row = my_cursor.fetchone()
        print(userID,row)
        if not row:
            raise NoUserException("No User Found with this ID")
        name, email,phone_no,address = row[0],row[1],row[2],row[3]
        
        data = {
            'data':{'name':name, 'email':email,'phone_no':phone_no,'address':address},
            'message':'ok',
            'success':1
        }
        return jsonify(data),200
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            return jsonify({'data':{},'message':'Intenal Server Error Occured', 'success':0}),500
        return jsonify({'data':{},'message':'Internal Error','success':0}),500
    except Exception as e:
        print(e)
        return jsonify({'data':{},'message':'Internal Server Error', 'success':0}),500

@app.route('/users/data', methods =['GET'])
def get_users_data():
    try:
        get_user_query = 'select distinct * from users limit 20'
        df = pd.read_sql(get_user_query,conn)
        myresult = df.to_dict(orient="records")
        response_data = {
            'data':myresult,
            'success':1,
            'message':'Retreived users successfully'
        }
        return jsonify(response_data),200
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            response_data = {
                'data':[],
                'success':0,
                'message':'Internal Server Error'
            }
            return jsonify(response_data),500
    except Exception as e:
        response_data = {
            'data':[],
            'success':0,
            'message':'Error Occured while retreiving data'
        }
        return jsonify(response_data),500

# create new user
@app.route('/user',methods =["POST"])
def add_user():
    data = request.get_json()
    name,address,email,mobile_no = data['name'],data['address'],data['email'],data['mobile_no']
    user_id = str(uuid.uuid4())
    try:

        add_user_query = "insert ignore into users(_id, name, address, email, phone_no) values(%s, %s, %s, %s, %s)"
        my_cursor.execute(add_user_query,(user_id,name,address,email,mobile_no,))
        conn.commit()
        if my_cursor.rowcount==1:
            response_data = {
                'data':{'name':name,'address':address, 'email':email, 'mobile_no':mobile_no},
                'success':1,
                'message':'User Created Successfully'
            }
            return jsonify(response_data),201
        else:
            response_data = {
                'data':{},
                'success':0,
                'message':'Email Already Exists'
            }
            # 409 code for duplicate entry in user table
            return jsonify(response_data),409
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            response_data = {
                'data':{},
                'success':0,
                'message':'Internal Server Error'
            }
            return jsonify(response_data),500
    except Exception as e:
        response_data ={
            'data':{},
            'success':0,
            'message':'Error Occured while saving data'
        }
        return jsonify(response_data),500


## delete existing user

@app.route('/user', methods = ['DELETE'])
def delete_user():
    try:
        data = request.get_json()
        # user_id = data['user_id']
        user_id = endUserID
        delete_user_query = 'delete from users where _id = %s'
        my_cursor.execute(delete_user,(user_id,))
        conn.commit()
        if my_cursor.rowcount>0:
            return '',204
        else:
            raise NoUserException("No User Found with provided data")
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            return jsonify({'message':'Internal Server Error'}),500
    except NoUserException:
        return jsonify({'message':'No user found with provided data'})
    except:
        return jsonify({'message':'Internal Server Error'}),500


# ##update users details

@app.route('/user', methods = ['PUT'])
def update_user():
    try:
        data = request.get_json()
        user_id = request.headers.get('userID')
        name = request.headers.get('name')
        address = request.headers.get('address')
        mobile_no = request.headers.get('phone_no')
        # name = data['name']
        # address = data['address']
        # mobile_no = data['phone_no']

        user_update_query = 'update users set name = %s, address = %s, phone_no= %s where _id = %s'
        my_cursor.execute(user_update_query,(name,address,mobile_no,user_id,))
        conn.commit()
        response_data ={
            'name':name,
            'address':address,
            'mobile_no':mobile_no
        }
        if my_cursor.rowcount>0:
            return jsonify({'user':response_data,'message':'user details saved','success':1}),200
        else:
            raise UserUpdateException('No User Found with provided data')
    except UserUpdateException:
        return jsonify({'user':{},'message':'No User Found with provided data', 'success':0}),400
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            return jsonify({'user':{},'message':'Internal Server Error','success':0}),500
        print(mysql_error)
        return jsonify({'user':{},'message':'no message'})
    except Exception as e:
        print(e)
        return jsonify({'user':{},'message':'Internal Server Error','success':0})

# # transaction routes
    
@app.route('/purchase', methods = ['GET'])
def load_purchase_page():
    return render_template('purchase.html',data=[{}])


@app.route('/purchase/data', methods= ['GET'])
def get_purchase_data():
    try:
        userID = request.headers.get('userID')
        print(userID)
        get_purchase_query = "select distinct title, purchase_id, transaction_date, qty, total_amount, return_date from purchase as a left join books as b on a.book_id = b.bookID where user_id = %s limit 20"
        my_cursor.execute(get_purchase_query,(userID,))
        data =my_cursor.fetchall()
        columns = ['title', 'purchase_id', 'transaction_date','qty','total_amount','return_date']
        
        df = pd.DataFrame(data, columns=columns)
        df['total_amount'].fillna(0, inplace=True)
        print(data)
        myresult = df.to_dict(orient="records")
        
        response_data = {
            'data':myresult,
            'success':1,
            'message':0
        }
        return jsonify(response_data),200
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            response_data = {
                'data':[],
                'success':0,
                'message':'Internal Server Error'
            }
            return jsonify(response_data),500
        print(mysql_error)
        return jsonify(response_data = {
                'data':[],
                'success':0,
                'message':'Internal Server Error'
            }),500
    except Exception as e:
        print(e)
        response_data = {
            'data':[],
            'success':0,
            'message':'Error Occured while fetching purchase data'
        }
        return jsonify(response_data),500
    


# add purchase
@app.route('/purchase', methods = ['POST'])
def add_purchase():
    data = request.get_json()
    userID = request.headers.get('userID')
    bookID, qty = data['bookID'], data['qty']
    qty = 1
    global my_cursor
    purchase_id = str(uuid.uuid4())
    
    try:
        conn.start_transaction()
        # conn.commit()
        # get total dues of user

        get_total_due_query = 'select sum(25*datediff(current_date,transaction_date)) as total_dues from purchase where return_date is null and user_id=%s'
        df = pd.read_sql(get_total_due_query,conn,params=(userID,))
        myresult = df.to_dict(orient="records")
        print('dues,', myresult)
        if(myresult[0]['total_dues'] is not None and myresult[0]['total_dues']>=500):
            raise DueLimitExceedError("Your dues exceeding 500 rupees. Please clear that firt")
        
        #checking inventory
        available_stock_query = 'select quantity from books where bookID =%s for update'
        my_cursor = conn.cursor(dictionary=True)
        my_cursor.execute(available_stock_query,(bookID,))
        row = my_cursor.fetchone()
        print('inventory,',row)
        if not row or row['quantity']<qty:
            raise NotEnoughStockError("Not Enough Inventory for this book")
        
        update_quantity_query = 'update books set quantity = quantity-%s where bookID = %s'
        my_cursor.execute(update_quantity_query, (qty,bookID,))
        
        purchase_time = datetime.now()
        purchase_time = purchase_time.strftime('%Y-%m-%d %H:%M:%S')
        add_purchase_query = "insert ignore into purchase(purchase_id, user_id, book_id, transaction_date, qty) values(%s, %s, %s, %s, %s)"
        my_cursor.execute(add_purchase_query,(purchase_id,userID,bookID,purchase_time,qty))
        conn.commit()
        if my_cursor.rowcount>0:
            purchase_details = {
                'bookID':bookID, 
                'purchase_id':purchase_id, 
                'qty':qty, 
                'purchase_time': purchase_time
            }
            conn.commit()
            return jsonify({'purchase_details':purchase_details,'message':'book purchased', 'success':1}), 201
        else:
            raise Exception("Error Occured")
    except mysql.connector.Error as mysql_error:
        conn.rollback()
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            response_data = {
                'data':{},
                'success':0,
                'message':'Internal Server Error'
            }
            return jsonify({response_data}),500
        print('reached here', mysql_error)
        return jsonify({'data':{},'success':0,'message':'Server Error'}),500
    except NotEnoughStockError as e:
        conn.rollback()
        return jsonify({'data':{},'message':'Stock not available for this book', 'success':0}), 409
    except DueLimitExceedError as e:
        conn.rollback()
        return jsonify({'data':{},'message':'Your dues exceeding limit 500 rupees', 'success':0}),409
    except Exception as e:
        print(e)
        conn.rollback()
        return jsonify({'data':{},'message':'Internal Server Error', 'success':0}),500
    finally:
        conn.autocommit = True
        # my_cursor.close()
        # conn.close()
    
@app.route('/purchase', methods = ['PUT'])
def returnBook():
    data = request.get_json()
   
    purchase_id = data['purchase_id']
    purchase_date = data['transaction_date']
    purchase_date = datetime.strptime(purchase_date,"%m/%d/%Y")
    return_time = datetime.now()
    diff = return_time-purchase_date
    hours_diff = diff.total_seconds()/3600
    total_amount = (25.0*hours_diff)/24
    return_time = return_time.strftime('%Y-%m-%d %H:%M:%S')
    update_query = 'update purchase set return_date=%s, total_amount = %s where purchase_id = %s'
    try:
        my_cursor.execute(update_query,(return_time,total_amount, purchase_id,))
        conn.commit()
        if my_cursor.rowcount>0:
            return '',204
        else: 
            response_data = {
                'message':'No purchase found'
            }
            return jsonify(response_data),400
    except mysql.connector.Error as mysql_error:
        if mysql_error.errno == errorcode.CR_SERVER_LOST or mysql_error.errno == errorcode.CR_SERVER_GONE_ERROR:
            return jsonify({'message':'Internal Server Error'}),500
        return jsonify({'message':'Internal Server Error'}),500
    except Exception as e:
        return jsonify({'message':'Internal Server Error'}),500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    # app.run(debug=True)
    
