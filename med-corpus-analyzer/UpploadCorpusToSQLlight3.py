"""
Скрипт загрузки сохранённых таблиц в базу sqlight3
"""
import os
import json
import sqlite3
import argparse

from Constants import MENTIONS_TYPE_NAMES, SPECIAL_TABLE_NAMES, THESAURI_TABLE_NAMES


def Main(database_path, tables_folder):
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    for fName in os.listdir(tables_folder):
        if ".json" not in fName:
            continue
        table_name = fName.replace(".json", "")
        with open(tables_folder + "/" + fName, "r") as f:
            table = json.load(f)
        placeholders = ",".join("?" * len(table.keys()))
        cur.execute("CREATE TABLE [{}]({})".format(table_name, ", ".join(table.keys())))
        placeholders = ",".join("?" * len(table.keys()))
        try:
            cur.executemany(f"INSERT INTO [{table_name}] VALUES({placeholders})", list(zip(*table.values())))
        except Exception as e:
            print(table_name)
            raise e
        con.commit() 

if __name__=="__main__":
    parser = argparse.ArgumentParser(
                    prog = 'UpploadCorpusToSQLlight3',
                    description = 'Скрипт загрузки сохранённых таблиц в базу sqlight3')
    parser.add_argument('--database_path', type=str, help="Путь к файлу базы данных")
    parser.add_argument('--tables_folder', type=str, help="Путь где сохранены предварительно собранные таблицы")
    args = parser.parse_args()
    Main(args.database_path, args.tables_folder)
    