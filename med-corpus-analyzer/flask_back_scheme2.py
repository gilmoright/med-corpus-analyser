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

es = elasticsearch.Elasticsearch(hosts=[{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}], http_auth=("elastic", "s+qTmEEAWQQdEjbGIJlv"), use_ssl=True, verify_certs=True, ca_certs="/home/nn/packages/elasticsearch-8.3.3/config/certs/http_ca.crt")
#es = elasticsearch.Elasticsearch(hosts=[{'host': ELASTIC_HOST, 'port': ELASTIC_PORT}])

@app.route('/', methods=['GET', 'POST'])
def hello():
    return("hello")

@app.route('/scheme2_request/', methods=['GET', 'POST'])
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
            query = Q("match", Indications_text=request_json["Indications"].strip())
        else:
            query = query & Q("match", Indications_text=request_json["Indications"].strip())
    if request_json.get("ADRs","").strip()!="":
        if query is None:
            query = Q("match", ADRs_text=request_json["ADRs"].strip())
        else:
            query = query & Q("match", ADRs_text=request_json["ADRs"].strip())
    search_request = Search(using=es, index=ELASTIC_INDEX).query(query).source(["Drugnames", "Diseasenames", "Indications_kw", "ADRs_kw", "ADR_reviews_count", 
                                                                   "Negated_ADE_reviews_count", "Neg_reviews_count", "Pos_reviews_countg",
                                                                   "Review_count", "Review_urls"]).sort({'Review_count': {"order": "desc"}})
    listed = []
    for hit in search_request[0:ROWS_COUNT]:
    #for hit in s.scan():
        hit = hit.to_dict()
        print(hit.keys())
        # это на фронте бы делать, но я хз как
        hit["Review_urls"] = ", ".join(hit["Review_urls"])
        if "ADRs_kw" in hit:
            hit["ADRs"] = ", ".join(hit.pop("ADRs_kw"))
        if "Indications_kw" in hit:
            hit["Indications"] = ", ".join(hit.pop("Indications_kw"))
        listed.append(hit)
    print("RESPONSE len", len(listed))
    #print(listed)
    response = jsonify(listed)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    #arg_parser = argparse.ArgumentParser(add_help=False)
    #arg_parser.add_argument('--config', type=str, help="Путь к конфиг файлу")
    #args = parser.parse_args()
    
    #app.run(debug=True)
    #app.run(host='127.0.0.1', port=3000, threaded = True, debug=True)
    app.run(host='localhost', port=8086, threaded = True, debug=False)