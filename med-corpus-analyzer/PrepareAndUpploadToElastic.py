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

analysis = { 
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


def Main(input_file, input_format, indexName):
    esClient = Elasticsearch(timeout=30)
    index = es_dsl.Index(indexName, using=esClient)
    index.delete(ignore=404)
    index.settings(number_of_shards=1, number_of_replicas=0, analysis = analysis)
    index.document(medreview_doctype)
    medreview_doctype.init(using=esClient)

    #index.create()
    
    if input_format=="artemjsonlines":
        with open(input_file, "r") as inf:
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
    print ("all good!")


if __name__ == '__main__':    
    parser = argparse.ArgumentParser(
                    prog = 'PrepareCorpus',
                    description = 'Cкрипт для предобработки корпуса и загрузки в elasticsearch')
    parser.add_argument('--input_file', type=str, help="Путь к файлу с разобранными отзывами в json формате")
    parser.add_argument('--input_format', type=str, choices=["artemjsonlines", "sagnlpjson"], help="Формат входных файлов")
    parser.add_argument('--index', type=str,
                        help='Index name to create')
    args = parser.parse_args()
    Main(args.input_file, args.input_format, args.index)
