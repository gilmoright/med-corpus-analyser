import argparse

from flask import Flask, request, json, jsonify
#from flask_cors import CORS, cross_origin
import elasticsearch
from elasticsearch_dsl import Search, Q

app = Flask(__name__)

ELASTIC_HOST='localhost'
ELASTIC_PORT=9200
ELASTIC_INDEX="med800k_scheme2"
ROWS_COUNT=100

es = elasticsearch.Elasticsearch(hosts=[{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}])
#es = elasticsearch.Elasticsearch(hosts=[{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], http_auth=("elastic", "s+qTmEEAWQQdEjbGIJlv"), use_ssl=True, verify_certs=True, ca_certs="/home/nn/packages/elasticsearch-8.3.3/config/certs/http_ca.crt")

@app.route('/', methods=['GET', 'POST'])
def hello():
    return("hello")

@app.route('/scheme2_request', methods=['GET', 'POST'])
def getTextFromReactReturnJson():
    print("QUERY")
    print(json.loads(request.get_data().decode('utf8').replace("'", '"')))
    request_json = json.loads(request.get_data().decode('utf8').replace("'", '"'))
    query = None
    if request_json.get("Drugnames", "").strip()!="":
        query = Q("match", Drugnames=request_json["Drugnames"].strip())
    if request_json.get("Diseasenames", "").strip()!="":
        if query is None:
            query = Q("match", Diseasenames=request_json["Diseasenames"].strip())
        else:
            query = query & Q("match", Diseasenames=request_json["Diseasenames"].strip())
    if request_json.get("Indications","").strip()!="":
        if query is None:
            query = Q("match", Indications=request_json["Indications"].strip())
        else:
            query = query & Q("match", Indications=request_json["Indications"].strip())
    if request_json.get("ADRs","").strip()!="":
        if query is None:
            query = Q("match", ADRs=request_json["ADRs"].strip())
        else:
            query = query & Q("match", ADRs=request_json["ADRs"].strip())
    search_request = Search(using=es, index=ELASTIC_INDEX).query(query).sort({'Review_count': {"order": "desc"}})
    listed = []
    for hit in search_request[0:ROWS_COUNT]:
    #for hit in s.scan():
        hit = hit.to_dict()
        # это на фронте бы делать, но я хз как
        hit["Review_urls"] = ", ".join(hit["Review_urls"])
        listed.append(hit)
    print("RESPONSE")
    print(listed)
    response = jsonify(listed)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    #arg_parser = argparse.ArgumentParser(add_help=False)
    #arg_parser.add_argument('--config', type=str, help="Путь к конфиг файлу")
    #args = parser.parse_args()
    
    #app.run(debug=True)
    #app.run(host='127.0.0.1', port=3000, threaded = True, debug=True)
    app.run(host='localhost', port=5000, threaded = True, debug=False)