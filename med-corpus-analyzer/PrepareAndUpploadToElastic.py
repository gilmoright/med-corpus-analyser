# *-* coding: utf-8 *-*
"""
TODO:
Похоже нужны дополнительные поля для: подсказок при поиске, и групбаев (чтоб не использовать конкатенацию строк, которая зависит от порядка)
"""

from elasticsearch import Elasticsearch
import elasticsearch_dsl as es_dsl
import os
import xml.etree.cElementTree as et
import json
import argparse
import re
import itertools
from collections import defaultdict
from Constants import MENTIONS_TYPE_NAMES

analysis_1 = { 
    "filter": {
        "word_delimiter": {
            "catenate_all": "true",
            "type": "word_delimiter",
            "preserve_original": "true"
        },
        "russian_stemmer": {
          "type":       "stemmer",
          "language":   "russian"
        },
        "russian_stop": {
          "type":       "stop",
          "stopwords":  "_russian_" 
        }
    },
    "char_filter": {
        "yo_filter": {
            "type": "mapping",
            "mappings": [
                "ё => е",
                "Ё => Е"
            ]
        }
    },            
    "analyzer" : {
            "phrase_analyzer" : {
                "filter": [
                    "lowercase"
                    #"russian_morphology",
                    #"word_delimiter",
                    #"russian_stop",
                    #"russian_stemmer"
                ],
                "char_filter": [
                    "yo_filter"
                ],
                "type": "custom",
                "tokenizer": "standard"
            }
    }
}

textField = {
    "type":     "text",
    "analyzer": "phrase_analyzer"
}

keywordField = {
    "type":     "keyword"  # analyzer? почему-то не работает тот же, что и для текста. надо бы выяснить.
}

def get_elastic_client():
    # простой вариант для отладки с незащищённым эластиком
    #esClient = Elasticsearch(timeout=30)
    # с использованием пароля и сертификата
    esClient = Elasticsearch(timeout=30, http_auth=("elastic", "s+qTmEEAWQQdEjbGIJlv"), use_ssl=True, verify_certs=True, ca_certs="/home/nn/packages/elasticsearch-8.3.3/config/certs/http_ca.crt")
    return esClient

class medreview_doctype(es_dsl.Document):
    fields = {"text": textField, "kw": keywordField}
    Drugname = es_dsl.Text(fields = fields)  # fields = fields
    DrugBrand = es_dsl.Text(fields = fields)
    Drugform = es_dsl.Text(fields = fields)
    Drugclass = es_dsl.Text(fields = fields)
    MedMaker = es_dsl.Text(fields = fields)
    MedMakerOrigin = es_dsl.Keyword()  # fields = {"keyword": keywordField}
    DrugnameOrigin = es_dsl.Keyword()
    Frequency = es_dsl.Text(fields = fields)
    Dosage = es_dsl.Text(fields = fields)
    Duration = es_dsl.Text(fields = fields)
    Route = es_dsl.Text(fields = fields)
    SourceInfodrug = es_dsl.Text(fields = fields)
    ADR = es_dsl.Text(fields = fields)
    Diseasename = es_dsl.Text(fields = fields)
    Indication = es_dsl.Text(fields = fields)
    ADR_flag = es_dsl.Boolean()
    Negated_ADE_flag = es_dsl.Boolean()
    Neg_flag = es_dsl.Boolean()
    Pos_flag = es_dsl.Boolean()
    review_url = es_dsl.Keyword()

    
def artemjsonlines_to_medreview_doctype(input_file_path, indexName):
    esClient = get_elastic_client()
    index = es_dsl.Index(indexName, using=esClient)
    index.delete(ignore=404)
    index.settings(number_of_shards=1, number_of_replicas=0, analysis = analysis_1)
    #index.create()
    
    index.document(medreview_doctype)
    medreview_doctype.init(using=esClient)
    with open(input_file_path, "r") as inf:
        l_i = 0
        for line in inf:
            if l_i % 100 == 0:
                print(l_i)
            l_i += 1
            artemjson = json.loads(line)
            artemjson.pop("raw")
            artemjson.pop("sentences")    
            # Попытка восстановить url
            review_id = artemjson["meta"]["fileName"].replace(".xmi", "")
            url = f"http://otzovik.com/review_{review_id}.html"
            review_id = int(review_id)
            elasticdoc = medreview_doctype()
            setattr(elasticdoc, "review_url", url)
            adr_flag, neg_flag, negated_flag, pos_flag = False, False, False, False

            mentions_list = defaultdict(list)
            DrugnameOrigins, MedMakerOrigins = set(), set()

            for mention in artemjson["objects"]["MedEntity"]:
                mention_type = None
                if mention["MedEntityType"]=="Medication":
                    mention_type = mention["MedType"]
                elif mention["MedEntityType"]=="Disease":
                    mention_type = mention["DisType"]
                else:
                    mention_type = mention["MedEntityType"]

                mentions_list[mention_type].append(mention["text"])

                if mention_type=="Drugname":
                    DrugnameOrigins.add(mention.get("MedFrom", "Undefined"))
                elif mention_type=="MedMaker":
                    MedMakerOrigins.add(mention.get("MedMaker", "Undefined"))                                           
                if mention_type=="ADR":
                    adr_flag = True
                elif mention_type=="BNE-Pos":
                    pos_flag = True
                elif mention_type == "NegatedADE":
                    negated_flag = True
                if mention_type in ["NegatedADE", "ADE-Neg", "Worse", "ADR"]:
                    neg_flag = True
            setattr(elasticdoc, "ADR_flag", adr_flag)
            setattr(elasticdoc, "Negated_ADE_flag", negated_flag)
            setattr(elasticdoc, "Neg_flag", neg_flag)
            setattr(elasticdoc, "Pos_flag", pos_flag)
            for mention_type, v in mentions_list.items():
                setattr(elasticdoc, mention_type+"_text", ", ".join(v))
                setattr(elasticdoc, mention_type+"_kw", v)
            if len(DrugnameOrigins) == 1:
                setattr(elasticdoc, "DrugnameOrigin", list(DrugnameOrigins)[0])
            else:
                setattr(elasticdoc, "DrugnameOrigin", "Undefined")
            if len(MedMakerOrigins) == 1:
                setattr(elasticdoc, "MedMakerOrigin", list(MedMakerOrigins)[0])
            else:
                setattr(elasticdoc, "MedMakerOrigin", "Undefined")
            elasticdoc.save(using=esClient)

class scheme2_doctype(es_dsl.Document):
    #fields = {"text": textField}
    #fields2 = {"kw": keywordField}
    Drugnames = es_dsl.Text()  # fields = fields
    Diseasenames = es_dsl.Text()
    Indications_text = es_dsl.Text()
    ADRs_text = es_dsl.Text()
    Indications_meddra = es_dsl.Keyword()
    ADRs_meddra = es_dsl.Keyword()
    
    ADR_reviews_count = es_dsl.Integer()
    Negated_ADE_reviews_count = es_dsl.Integer()
    Neg_reviews_count = es_dsl.Integer()
    Pos_reviews_count = es_dsl.Integer()
    Review_count = es_dsl.Integer()
    Review_urls = es_dsl.Keyword()

def artemjsonlines_to_scheme2(input_file_path, indexName):
    raise ValueErrot("Deprecated! Use sagnlpjsonlines_to_scheme2() or update this one to be similar to sagnlpjsonlines_to_scheme2() ")
    esClient = get_elastic_client()
    index = es_dsl.Index(indexName, using=esClient)
    index.delete(ignore=404)
    index.settings(number_of_shards=1, number_of_replicas=0, analysis = analysis_1)
    #index.create()
    
    index.document(scheme2_doctype)
    scheme2_doctype.init(using=esClient)
    table_dict = defaultdict(lambda : {
        "indications_text": set(),
        "adrs_text": set(),
        "ADR_reviews_count": 0, 
        "Negated_ADE_reviews_count": 0, 
        "Neg_reviews_count": 0, 
        "Pos_reviews_count": 0, 
        "review_count": 0, 
        "review_urls": []
    })
    with open(input_file_path, "r") as inf:
        l_i = 0
        for line in inf:
            if l_i % 100 == 0:
                print(l_i)
            l_i += 1
            artemjson = json.loads(line)
            artemjson.pop("raw")
            artemjson.pop("sentences")    
            # Попытка восстановить url
            review_id = artemjson["meta"]["fileName"].replace(".xmi", "")
            url = f"http://otzovik.com/review_{review_id}.html"
            review_id = int(review_id)
            adr_flag, neg_flag, negated_flag, pos_flag = False, False, False, False
            drugnames, diseasenames, indications_meddra, adrs_meddra = set(), set(), set(), set()
            indications_text, adrs_text = set(), set()
            for mention in artemjson["objects"]["MedEntity"]:
                mention_type = None
                if re.search("[а-яА-Яa-zA-ZёЁ]{3,}", mention["text"]) is None:
                    continue
                if mention["MedEntityType"]=="Medication":
                    mention_type = mention["MedType"]
                elif mention["MedEntityType"]=="Disease":
                    mention_type = mention["DisType"]
                else:
                    mention_type = mention["MedEntityType"]
                    
                if mention_type=="Drugname":
                    #drugnames.add(mention["text"].lower())
                    drugnames.add(mention["norm_form"].lower())
                elif mention_type=="Diseasename":
                    #diseasenames.add(mention["text"].lower())
                    diseasenames.add(mention["norm_form"].lower())
                elif mention_type=="Indication":
                    indications_text.add(mention["text"].lower())
                    indications_meddra.add(mention["MedDRA_code"][0].lower())
                    
                if mention_type=="ADR":
                    adrs_text.add(mention["text"].lower())
                    adrs_meddra.add(mention["MedDRA_code"][0].lower())
                    adr_flag = True
                elif mention_type=="BNE-Pos":
                    pos_flag = True
                elif mention_type == "NegatedADE":
                    negated_flag = True
                if mention_type in ["NegatedADE", "ADE-Neg", "Worse", "ADR"]:
                    neg_flag = True
            drugnames = tuple(sorted(list(drugnames))) 
            diseasenames = tuple(sorted(list(diseasenames)))
            indications_meddra = tuple(sorted(list(indications_meddra)))
            adrs_meddra = tuple(sorted(list(adrs_meddra)))
            if mention_type=="Drugname":
                drugnames.add(mention["text"].lower())
            if adr_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["ADR_reviews_count"] += 1
            if neg_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["Neg_reviews_count"] += 1
            if negated_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["Negated_ADE_reviews_count"] += 1
            if pos_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["Pos_reviews_count"] += 1
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["review_count"] += 1
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["review_urls"].append(url)
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["indications_text"].update(indications_text)
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["adrs_text"].update(adrs_text)

        for (drugnames, diseasenames, indications_meddra, adrs_meddra), stat in table_dict.items():
            elasticdoc = scheme2_doctype()
            setattr(elasticdoc, "Drugnames", ", ".join(drugnames))
            setattr(elasticdoc, "Diseasenames", ", ".join(diseasenames))
            setattr(elasticdoc, "Indications_text", ", ".join(indications))
            setattr(elasticdoc, "ADRs_text", ", ".join(adrs))
            setattr(elasticdoc, "Indications_meddra", indications_meddra)
            setattr(elasticdoc, "ADRs_meddra", adrs_meddra)
            setattr(elasticdoc, "ADR_reviews_count", stat["ADR_reviews_count"])
            setattr(elasticdoc, "Negated_ADE_reviews_count", stat["Negated_ADE_reviews_count"])
            setattr(elasticdoc, "Neg_reviews_count", stat["Neg_reviews_count"])
            setattr(elasticdoc, "Pos_reviews_count", stat["Pos_reviews_count"])
            setattr(elasticdoc, "Review_count", stat["review_count"])
            setattr(elasticdoc, "Review_urls", stat["review_urls"])
            elasticdoc.save(using=esClient)

def sagnlpjsonlines_to_scheme2(input_file_path, indexName):
    esClient = get_elastic_client()
    index = es_dsl.Index(indexName, using=esClient)
    index.delete(ignore=404)
    index.settings(number_of_shards=1, number_of_replicas=0, analysis = analysis_1)
    #index.create()
    
    index.document(scheme2_doctype)
    scheme2_doctype.init(using=esClient)
    table_dict = defaultdict(lambda : {
        "indications_text": set(),
        "adrs_text": set(),
        "ADR_reviews_count": 0, 
        "Negated_ADE_reviews_count": 0, 
        "Neg_reviews_count": 0, 
        "Pos_reviews_count": 0, 
        "review_count": 0, 
        "review_urls": []
    })
    with open(input_file_path, "r") as inf:
        l_i = 0
        for line in inf:
            if l_i % 1000 == 0:
                print(l_i, len(table_dict.keys()))
            l_i += 1
            sagnlpjson = json.loads(line)
            if "text" in sagnlpjson:
                sagnlpjson.pop("text")
            if "text_id" in sagnlpjson:
                sagnlpjson.pop("text_id") 
            url = sagnlpjson["meta"]["url"]
            adr_flag, neg_flag, negated_flag, pos_flag = False, False, False, False
            drugnames, diseasenames, indications_meddra, adrs_meddra = set(), set(), set(), set()
            indications_text, adrs_text = set(), set()
            for m_i, mention in sagnlpjson["entities"].items():
                if re.search("[а-яА-Яa-zA-ZёЁ]{3,}", mention["text"]) is None:
                    continue
                if type(mention["tag"])==list:
                    tag = mention["tag"][0]  # вроде у всех по одному только предсказано
                elif type(mention["tag"])==str:
                    tag = mention["tag"]
                if "Domestic" in tag or "Foreign" in tag:
                    continue
                mention_type = None
                if tag.split(":")[0]=="Medication":
                    mention_type = re.search("MedType(\w+)", tag).group(1)
                elif tag.split(":")[0]=="Disease":
                    mention_type = re.search("DisType([\w\\-]+)", tag).group(1)
                else:
                    mention_type = tag
                if mention_type not in MENTIONS_TYPE_NAMES:
                    print(mention_type)
                assert mention_type in MENTIONS_TYPE_NAMES
                if mention_type=="Drugname":
                    #drugnames.add(mention["text"].lower())
                    drugnames.add(mention["norm_form"].lower())
                elif mention_type=="Diseasename":
                    #diseasenames.add(mention["text"].lower())
                    diseasenames.add(mention["norm_form"].lower())
                elif mention_type=="Indication":
                    indications_text.add(mention["text"].lower())
                    indications_meddra.add(mention["MedDRA_code"][0].lower())
                    
                if mention_type=="ADR":
                    adrs_text.add(mention["text"].lower())
                    adrs_meddra.add(mention["MedDRA_code"][0].lower())
                    adr_flag = True
                elif mention_type=="BNE-Pos":
                    pos_flag = True
                elif mention_type == "NegatedADE":
                    negated_flag = True
                if mention_type in ["NegatedADE", "ADE-Neg", "Worse", "ADR"]:
                    neg_flag = True
            drugnames = tuple(sorted(list(drugnames))) 
            diseasenames = tuple(sorted(list(diseasenames)))
            indications_meddra = tuple(sorted(list(indications_meddra)))
            adrs_meddra = tuple(sorted(list(adrs_meddra)))
            # вряд ли есть смысл смотреть отзывы без препаратов (ну или с невыделенными)
            if len(drugnames)==0:
                continue
            if adr_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["ADR_reviews_count"] += 1
            if neg_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["Neg_reviews_count"] += 1
            if negated_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["Negated_ADE_reviews_count"] += 1
            if pos_flag:
                table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["Pos_reviews_count"] += 1
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["review_count"] += 1
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["review_urls"].append(url)
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["indications_text"].update(indications_text)
            table_dict[(drugnames, diseasenames, indications_meddra, adrs_meddra)]["adrs_text"].update(adrs_text)
            
        print("Unique tuples (rows for db):", len(table_dict.keys()))
        t_i = 0
        for (drugnames, diseasenames, indications_meddra, adrs_meddra), stat in table_dict.items():
            if t_i % 1000 == 0:
                print(t_i)
            t_i += 1
            elasticdoc = scheme2_doctype()
            setattr(elasticdoc, "Drugnames", ", ".join(drugnames))
            setattr(elasticdoc, "Diseasenames", ", ".join(diseasenames))
            setattr(elasticdoc, "Indications_text", ", ".join(list(stat["indications_text"])) if len(stat["indications_text"])>0 else None)
            setattr(elasticdoc, "ADRs_text", ", ".join(list(stat["adrs_text"])) if len(stat["adrs_text"])>0 else None)
            setattr(elasticdoc, "Indications_kw", indications_meddra if len(indications_meddra)>0 else None)
            setattr(elasticdoc, "ADRs_kw", adrs_meddra if len(adrs_meddra)>0 else None)
            setattr(elasticdoc, "ADR_reviews_count", stat["ADR_reviews_count"])
            setattr(elasticdoc, "Negated_ADE_reviews_count", stat["Negated_ADE_reviews_count"])
            setattr(elasticdoc, "Neg_reviews_count", stat["Neg_reviews_count"])
            setattr(elasticdoc, "Pos_reviews_count", stat["Pos_reviews_count"])
            setattr(elasticdoc, "Review_count", stat["review_count"])
            setattr(elasticdoc, "Review_urls", stat["review_urls"])
            elasticdoc.save(using=esClient)

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(
                    prog = 'PrepareCorpus',
                    description = 'Cкрипт для предобработки корпуса и загрузки в elasticsearch')
    parser.add_argument('--input_file', type=str, help="Путь к файлу с разобранными отзывами в json формате")
    parser.add_argument('--input_format', type=str, choices=["artemjsonlines", "sagnlpjsonlines"], help="Формат входных файлов")
    parser.add_argument('--scheme', type=str, choices=["scheme1", "scheme2"], help="Схема таблицы индекса. \n\t-scheme1 - количество строк=количество отзывов, в строках собраны все сущности в этих отзывах. \n\t- scheme2 - ")
    parser.add_argument('--index', type=str,
                        help='Index name to create')
    args = parser.parse_args()
    if args.input_format=="artemjsonlines" and args.scheme=="scheme1":
        artemjsonlines_to_medreview_doctype(args.input_file, args.index)
    elif args.input_format=="artemjsonlines" and args.scheme=="scheme2":
        artemjsonlines_to_scheme2(args.input_file, args.index)
    elif args.input_format=="sagnlpjsonlines" and args.scheme=="scheme2":
        sagnlpjsonlines_to_scheme2(args.input_file, args.index)
    
    print("Done")
