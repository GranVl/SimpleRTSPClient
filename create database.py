import psycopg2
from psycopg2 import Error

try:
    # Подключиться к существующей базе данных
    connection = psycopg2.connect(user="postgres",
                                  # пароль, который указали при установке PostgreSQL
                                  password="admin",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="postgres_db")

    # Создайте курсор для выполнения операций с базой данных
    cursor = connection.cursor()
    # SQL-запрос для создания новой таблицы
    create_table_query = ('''
                            CREATE TABLE images
                          (ID INT PRIMARY KEY     NOT NULL,
                           NAME_IMAGE TEXT    NOT NULL);
                          ''' ,
                          
                          '''CREATE TABLE detection
                          (ID INT PRIMARY KEY     NOT NULL,
                           IMAGE_ID INTEGER REFERENCES images (ID) ON DELETE CASCADE, 
                           X0 INT    NOT NULL,
                           Y0 INT    NOT NULL,
                           X1 INT    NOT NULL,
                           Y1 INT    NOT NULL,
                           Confidense REAL    NOT NULL,
                           Class VARCHAR    NOT NULL); ''')
    # Выполнение команды: это создает новую таблицу
    for command in create_table_query:
            cursor.execute(command)
    #cursor.execute('''DROP TABLE images CASCADE''')
    #cursor.execute('''DROP TABLE detection''')
    connection.commit()
    print("Таблица успешно создана в PostgreSQL")

except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")