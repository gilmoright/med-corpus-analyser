"""
TODO:
- добавить таблицу для review
- решить, хранить одну большую таблицу или для каждого атрибута разные? Всё в одной - большая и дополнительная колонка с типом. И не понятно, как джоины делать, через view?
- Добавить нормализацию в базу. Загвоздка в том, как хранить разные уровни и тезаурусы.
- Добавить возможность работы с сагнлп.
- Посмотреть, в каком формате хранит савелий, если не сагнлпи, то добавить третий формат.
- Подумать, в чем хранить выходные файлы, json накладно, нет? гзипнуть? а может и пофиг.


Cкрипт для предобработки корпуса. Удаляет лишнее и переводит в json, подходящей для загрузки таблицы в базу данных. 
Колонки:
- index
- text - текст сущности
- mention_type - в случае, если храним все в одной таблице
- context - номер контекста (одного). Если у упоминия несколько контекстов, то будет несколько строк, где это поле отличается.
- origin - задан только у Drugname и MedMaker в зависимости от атрибута MedFrom и MedMaker
- review_id 
- norm_value - результат нормализации. не атомарный атрибут =/ # пока без него, нужны id и таблицы тезаурусов.
"""

import json
import argparse
from Constants import MENTIONS_TYPE_NAMES, SPECIAL_TABLE_NAMES, THESAURI_TABLE_NAMES


def From_artemjson_to_OnebigTable(artemjson, tables):
    """
    Функция проходится по сущностям из json данных, сохранённых мной из xmi, и сохраняет их в списки записей для базы данных.    
    params:
        artemjson - json, полученный из xmi файла с помощью скрипта https://github.com/sag111/TextCorporaReaders/blob/master/TextCorporaReaders/Readers/Webanno/RDRxmi.py
        tables - словарь со списками записей для таблицы. Ожидаются все заколовки из MENTIONS_TYPE_NAMES + SPECIAL_TABLE_NAMES
    """
    # Удаление ненужных полей для базы данных
    artemjson.pop("raw")
    artemjson.pop("sentences")    
    # Попытка восстановить url
    filename = artemjson["meta"]["fileName"]
    review_id = filename.replace(".xmi", "")
    url = f"http://otzovik.com/review_{review_id}.html"
    review_id = int(review_id)
    
    for mention in artemjson["objects"]["MedEntity"]:
        mention_type = None
        if mention["MedEntityType"]=="Medication":
            mention_type = mention["MedType"]
        elif mention["MedEntityType"]=="Disease":
            mention_type = mention["DisType"]
        else:
            mention_type = mention["MedEntityType"]
        # Если надо какие-то типы убрать или игнорировать, добавить тут соответствующую обработку вместо ассерта
        assert mention_type in MENTIONS_TYPE_NAMES  
        """
        Нужно добавить нормализацию, пока решил не заморачиваться.
        """
        for c in mention["Context"].split(","):
            tables["BigTable"]["id"].append(0 if len(tables["BigTable"]["id"])==0 else tables["BigTable"]["id"][-1]+1)
            tables["BigTable"]["text"].append(mention["text"])
            tables["BigTable"]["mention_type"].append(mention_type)
            tables["BigTable"]["context"].append(int(c))
            tables["BigTable"]["origin"].append(mention.get("MedMaker", mention.get("MedFrom", None)))
            tables["BigTable"]["review_id"].append(review_id)

def From_artemjson_to_bigTables(artemjson, tables):
    """
    Функция проходится по сущностям из json данных, сохранённых мной из xmi, и сохраняет их в списки записей для базы данных.    
    params:
        artemjson - json, полученный из xmi файла с помощью скрипта https://github.com/sag111/TextCorporaReaders/blob/master/TextCorporaReaders/Readers/Webanno/RDRxmi.py
        tables - словарь со списками записей для таблицы. Ожидаются все заколовки из MENTIONS_TYPE_NAMES + SPECIAL_TABLE_NAMES
    """
    # Удаление ненужных полей для базы данных
    artemjson.pop("raw")
    artemjson.pop("sentences")    
    # Попытка восстановить url
    filename = artemjson["meta"]["fileName"]
    review_id = filename.replace(".xmi", "")
    url = f"http://otzovik.com/review_{review_id}.html"
    review_id = int(review_id)
    
    for mention in artemjson["objects"]["MedEntity"]:
        mention_type = None
        if mention["MedEntityType"]=="Medication":
            mention_type = mention["MedType"]
        elif mention["MedEntityType"]=="Disease":
            mention_type = mention["DisType"]
        else:
            mention_type = mention["MedEntityType"]
        # Если надо какие-то типы убрать или игнорировать, добавить тут соответствующую обработку вместо ассерта
        assert mention_type in MENTIONS_TYPE_NAMES  
        """
        Нужно добавить нормализацию, пока решил не заморачиваться.
        """
        for c in mention["Context"].split(","):
            tables[mention_type]["id"].append(0 if len(tables[mention_type]["id"])==0 else tables[mention_type]["id"][-1]+1)
            tables[mention_type]["text"].append(mention["text"])
            tables[mention_type]["context"].append(int(c))
            if mention_type in ["Drugname", "MedMaker"]:
                tables[mention_type]["origin"].append(mention.get("MedMaker", mention.get("MedFrom", None)))
            tables[mention_type]["review_id"].append(review_id)

def Main(input_file, input_format, output_folder):
    tables_records_dict = {}
    """
    # пробовал все запихнуть в одну таблицу - сомнительный вариант
    tables_records_dict["BigTable"] = {
        "id" : [],
        "text" : [],
        "mention_type" : [],
        "context" : [],
        "origin" : [],
        "review_id" : []
    }
    """
    for table_name in MENTIONS_TYPE_NAMES:
        tables_records_dict[table_name] = {
            "id" : [],
            "text" : [],
            "context" : [],
            "review_id" : []
        }
        if table_name in ["Drugname", "MedMaker"]:
            tables_records_dict[table_name]["origin"] = []
    if input_format=="artemjsonlines":
        with open(input_file, "r") as inf:
            for line in inf:
                docData = json.loads(line)
                #From_artemjson_to_OnebigTable(docData, tables_records_dict)
                From_artemjson_to_bigTables(docData, tables_records_dict)
    else:
        raise ValueError(f"Unrecognized input file format: {input_format}")

    for table_name, table in tables_records_dict.items():
        with open(output_folder + f"/{table_name}.json", "w") as outf:
            json.dump(table, outf)

if __name__=="__main__":
    parser = argparse.ArgumentParser(
                    prog = 'PrepareCorpus',
                    description = 'Cкрипт для предобработки корпуса. Удаляет лишнее и переводит какой-то из входных форматов в один. ')
    parser.add_argument('--input_file', type=str, help="Путь к файлу с разобранными отзывами в json формате")
    parser.add_argument('--input_format', type=str, choices=["artemjsonlines", "sagnlpjson"], help="Формат входных файлов")
    parser.add_argument('--output_folder', type=str, help="Папка, куда сохранять таблицы для БД")
    args = parser.parse_args()
    Main(args.input_file, args.input_format, args.output_folder)
                                                     
    