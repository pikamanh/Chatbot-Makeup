import mysql.connector

def load_database(database, host='localhost', user='root', password=''):
    try:
        db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        return db
    except Exception as e:
        print("❌ Kết nối đến database thất bại.")
        print(e)