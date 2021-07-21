import psycopg2
from psycopg2 import Error
import random
from datetime import datetime
import asyncio

def get_last_id():
    try:
        connection = psycopg2.connect(user="postgres",
                                    # пароль, который указали при установке PostgreSQL
                                    password="admin",
                                    host="127.0.0.1",
                                    port="5432",
                                    database="postgres_db")

        cursor = connection.cursor()
        cursor.execute("SELECT ID from images ORDER BY ID DESC LIMIT 1")
        record = cursor.fetchall()
        main_index = record[0][0]
        print("Результат1", record[0][0])

        cursor.execute("SELECT ID from detection ORDER BY ID DESC LIMIT 1")
        record = cursor.fetchall()
        secondary_index = record[0][0]
        print("Результат2", record[0][0])
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
    return main_index + 1, secondary_index + 1

def send_entry_main(index, filename):
    try:
        connection = psycopg2.connect(user="postgres",
                                    # пароль, который указали при установке PostgreSQL
                                    password="admin",
                                    host="127.0.0.1",
                                    port="5432",
                                    database="postgres_db")

        cursor = connection.cursor()
        insert_query = """ INSERT INTO images (ID, NAME_IMAGE) VALUES ({0}, '{1}')""".format(index, filename)
        cursor.execute(insert_query)
        connection.commit()
        print("Строка в PostgreSQL [Images] добавлена")
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")

async def send_entry_secondary(index, primary_index, p):
    try:
        # Подключиться к существующей базе данных
        connection = psycopg2.connect(user="postgres",
                                    # пароль, который указали при установке PostgreSQL
                                    password="admin",
                                    host="127.0.0.1",
                                    port="5432",
                                    database="postgres_db")

        cursor = connection.cursor()
        #cursor.execute("INSERT INTO detection (ID, IMAGE_ID, X0, Y0, X1, Y1, Confidense, Class) VALUES(%s, %s, %s, %s, '%s)",[index, 3, p[0], p[1], p[2], p[3], p[4], p[5]])
        insert_query = """ 
            INSERT INTO detection (ID, IMAGE_ID, X0, Y0, X1, Y1, Confidense, Class) VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, '{7}')""".format(index, primary_index, p[0], p[1], p[2], p[3], p[4], p[5])
        cursor.execute(insert_query)
        connection.commit()
        print("Строка в PostgreSQL [Detection] добавлена")

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")

if __name__ == '__main__':
    send_entry_main(0, "test")
