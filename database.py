import sqlite3
import pandas as pd
import numpy as np


def create_database(): # sozdanie bd
    conn = sqlite3.connect('data_visualization.db')
    cursor = conn.cursor()
    # с помощью функции cursor будем управлять нашей БД
    # tablica dlya infy o datasetah
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER,
            column_count INTEGER
        )
    ''')

    # primery dlya proverki
    create_sample_data(conn)

    conn.commit()
    conn.close()
    print("База данных 'data_visualization.db' создана успешно!")
    print("Примеры датасетов загружены: sales_data, student_data, weather_data")


def create_sample_data(conn): # заполняем простыми данными БД
    # данные о продажах
    sales_data = {
        'date': pd.date_range('2023-01-01', periods=100, freq='D'),
        'product': ['A', 'B', 'C'] * 33 + ['A'],
        'sales': np.random.randint(50, 200, 100),
        'revenue': np.random.uniform(1000, 5000, 100),
        'region': ['North', 'South', 'East', 'West'] * 25
    }
    sales_df = pd.DataFrame(sales_data)
    sales_df.to_sql('sales_data', conn, if_exists='replace', index=False)

    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO datasets (name, description, row_count, column_count)
        VALUES (?, ?, ?, ?)
    ''', ('sales_data', 'Данные о продажах компании', len(sales_df), len(sales_df.columns)))

    # успеваемость студентов
    student_data = {
        'student_id': range(1, 51),
        'math_score': np.random.randint(50, 100, 50),
        'reading_score': np.random.randint(50, 100, 50),
        'writing_score': np.random.randint(50, 100, 50),
        'attendance': np.random.randint(70, 100, 50),
        'grade': np.random.choice(['A', 'B', 'C', 'D'], 50)
    }
    student_df = pd.DataFrame(student_data)
    student_df.to_sql('student_data', conn, if_exists='replace', index=False)

    cursor.execute('''
        INSERT OR IGNORE INTO datasets (name, description, row_count, column_count)
        VALUES (?, ?, ?, ?)
    ''', ('student_data', 'Успеваемость студентов', len(student_df), len(student_df.columns)))

    # погодные данные
    weather_data = {
        'date': pd.date_range('2023-06-01', periods=30, freq='D'),
        'temperature': np.random.randint(15, 35, 30),
        'humidity': np.random.randint(30, 90, 30),
        'pressure': np.random.randint(1000, 1020, 30),
        'rainfall': np.random.uniform(0, 10, 30)
    }
    weather_df = pd.DataFrame(weather_data)
    weather_df.to_sql('weather_data', conn, if_exists='replace', index=False)

    cursor.execute('''
        INSERT OR IGNORE INTO datasets (name, description, row_count, column_count)
        VALUES (?, ?, ?, ?)
    ''', ('weather_data', 'Метеорологические данные', len(weather_df), len(weather_df.columns)))


if __name__ == "__main__":
    create_database()