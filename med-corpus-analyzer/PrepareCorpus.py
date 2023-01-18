"""
TODO:
- Добавить нормализацию в базу. Загвоздка в том, как хранить разные уровни и тезаурусы.
- Добавить возможность работы с сагнлп.
- Посмотреть, в каком формате хранит савелий, если не сагнлпи, то добавить третий формат.
- Подумать, в чем хранить выходные файлы, json накладно, нет? гзипнуть? а может и пофиг.
- Режимы full, to_records, minimize - хрень какая-то получилась, может убрать надо будет.


Cкрипт для предобработки корпуса. Удаляет лишнее и переводит какой-то из входных форматов в один. 
Схема данных сейчас такая:
Под каждый атрибут своя таблица с упоминаниями, где строки - выделенные упоминания, а колонки:
- mention_index
- text - текст сущности
- MedFrom - только для драгнейма
- MedMaker - тодлько для MedMaker
дополнительные таблицы:

тройки упоминание-ревью-контекст
- triplet_mrc_index
- mention_index
- review_id - 
- context - номер контекста (одного). Если у упоминия несколько контекстов, то будет несколько строк, где это поле отличается.
- mention_type - тип сущности, одинаковый с названием таблицы сущностей.

Нормализационные пары - таблица под каждый атрибут+название тезауруса. Вопрос, хранить ли пары для всех уровней или только для нижнего.
- pair_n_index
- mention_index - индекс одной сущности
- norm_term_index - индекс одного термина

Нормализационные тезаурусы. под каждый тезаурус отдельная таблица. Вопрос, как иерархию сохранить
- norm_term_index
- term
- parent(s) ? или level? 

reviews
- review_id
- review_url
"""

import json
import argparse
from Constants import MENTIONS_TYPE_NAMES, SPECIAL_TABLE_NAMES, THESAURI_TABLE_NAMES


def From_artemjson_to_table(artemjson, tables):
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
    tables["Reviews"]["review_id"].append(review_id)
    tables["Reviews"]["review_url"].append(url)
    
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
        tables[mention_type]["mention_index"].append(0 if len(tables[mention_type]["mention_index"])==0 else tables[mention_type]["mention_index"][-1]+1)
        tables[mention_type]["text"].append(mention["text"])
        if mention_type=="Drugname":
            if "MedFrom" in mention:
                tables[mention_type]["MedFrom"].append(mention["MedFrom"])
            else:
                tables[mention_type]["MedFrom"].append(None)
        if mention_type=="MedMaker":
            tables[mention_type]["MedMaker"].append(mention["MedMaker"])
        """
        Нужно добавить нормализацию, пока решил не заморачиваться.
        """
        for c in mention["Context"].split(","):
            tables["Mention-Review-Context"]["triplet_mrc_index"].append(0 if len(tables["Mention-Review-Context"]["triplet_mrc_index"])==0 else tables["Mention-Review-Context"]["triplet_mrc_index"][-1]+1)
            tables["Mention-Review-Context"]["mention_index"].append(tables[mention_type]["mention_index"][-1])
            tables["Mention-Review-Context"]["review_id"].append(review_id)
            tables["Mention-Review-Context"]["context"].append(int(c))
    
def Main(input_file, input_format, output_folder):
    tables_records_dict = {}
    for table_name in MENTIONS_TYPE_NAMES:
        tables_records_dict[table_name] = {
            "mention_index": [],
            "text": []
        }
        if table_name=="Drugname":
            tables_records_dict[table_name]["MedFrom"] = []
        if table_name=="MedMaker":
            tables_records_dict[table_name]["MedMaker"] = []
    tables_records_dict["Reviews"] = {
        "review_id" : [],
        "review_url" : []
    }
    tables_records_dict["Mention-Review-Context"] = {
        "triplet_mrc_index" : [],
        "mention_index" : [],
        "review_id" : [],
        "context" : []
    }

    if input_format=="artemjsonlines":
        with open(input_file, "r") as inf:
            for line in inf:
                docData = json.loads(line)
                From_artemjson_to_table(docData, tables_records_dict)
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
                                                     
    