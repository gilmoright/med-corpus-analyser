import argparse

from flask import Flask, request, json, jsonify
#from flask_cors import CORS, cross_origin
import elasticsearch
from elasticsearch_dsl import Search, Q

app = Flask(__name__)

ELASTIC_HOST='localhost'
ELASTIC_PORT=9200
ELASTIC_INDEX="med800k_scheme2"
ROWS_COUNT=1000

es = elasticsearch.Elasticsearch(hosts=[{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}])

@app.route('/scheme2_request', methods=['GET', 'POST'])
def getTextFromReactReturnJson():
    print(request.form)
    print(request.form["Indications"])
    query = None
    if request.form.get("Drugnames", "").strip()!="":
        query = Q("match", Drugnames=request.form["Drugnames"].strip())
    if request.form.get("Diseasenames", "").strip()!="":
        if query is None:
            query = Q("match", Diseasenames=request.form["Diseasenames"].strip())
        else:
            query = query | Q("match", Diseasenames=request.form["Diseasenames"].strip())
    if request.form.get("Indications","").strip()!="":
        if query is None:
            query = Q("match", Indications=request.form["Indications"].strip())
        else:
            query = query | Q("match", Indications=request.form["Indications"].strip())
    if request.form.get("ADRs","").strip()!="":
        if query is None:
            query = Q("match", ADRs=request.form["ADRs"].strip())
        else:
            query = query | Q("match", ADRs=request.form["ADRs"].strip())
    search_request = Search(using=es, index=ELASTIC_INDEX).query(query).sort({'Review_count': {"order": "desc"}})
    listed = []
    for hit in search_request[0:ROWS_COUNT]:
    #for hit in s.scan():
        listed.append(hit.to_dict())
    return listed

if __name__ == '__main__':
    #arg_parser = argparse.ArgumentParser(add_help=False)
    #arg_parser.add_argument('--config', type=str, help="Путь к конфиг файлу")
    #args = parser.parse_args()
    
    app.run(debug=True)
    #app.run(host='127.0.0.1', port=3000, threaded = True, debug=True)