import os
import sqlite3 as sq
import pandas as pd
import openpyxl


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def request_db():
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT время FROM time WHERE занято = '-'")
        row = cur.fetchall()
    return row


def request_all_db_t(date):
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT date FROM schedule")
        row = cur.fetchall()
    return row


def update_time(cur_time):
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("UPDATE time SET занято = '+' WHERE время = ?", (cur_time,))


def add_request(user_id, name, business, experience, time):
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO Record (user_id, name, business, experience, time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, business, experience, time))


def add_time(date, time):
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        for exits_date in request_all_db_t(date):
            if date in exits_date:
                raise ValueError
        cur.execute("""
                        INSERT INTO schedule (date, time, status)
                        VALUES (?, ?, ?)
                        """, (date, time, '-'))


def delete_time_from_db(time_user):
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        print(f"Удаляю из базы: {time_user!r}")
        try:
            cur.execute("""
                        DELETE FROM time
                        WHERE "время" = ?
                        """, (time_user,))
        except Exception as e:
            print(f"❌ Ошибка: {e}")


def id_user_from_db(user_id):
    with sq.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT user_id FROM Record WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row is not None


def sqlite_to_excel_pandas(excel_path: str, table_name: str = None):
    try:
        with sq.connect(DB_PATH) as con:
            if table_name:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", con)
                df.to_excel(excel_path, sheet_name=table_name, index=False)
            else:
                tables = pd.read_sql_query(
                    "SELECT name FROM sqlite_master WHERE type='table'", con
                )['name'].tolist()

                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    for table in tables:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", con)
                        df.to_excel(writer, sheet_name=table, index=False)
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def clear_all_tables():
    with sq.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Record;")
        cur.execute("DELETE FROM time;")

        cur.execute("DELETE FROM sqlite_sequence WHERE name='Record';")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='time';")

    with sq.connect(DB_PATH) as conn:
        conn.execute("VACUUM;")

