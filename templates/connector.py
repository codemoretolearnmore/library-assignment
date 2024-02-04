import mysql.connector

conn = mysql.connector.connect(host = 'sql6.freesqldatabase.com', username = 'sql6681622', password = 'jz1dJylwGj', database = 'sql6681622')

my_cursor = conn.cursor()
# my_cursor.execute("insert into users(_id,name,address,phone_no) values(%s, %s, %s, %s)",("123","Pankaj","Ponkh","9166974070"))
# conn.commit()
my_cursor.execute("select * from users")
for x in my_cursor:
    print(x)