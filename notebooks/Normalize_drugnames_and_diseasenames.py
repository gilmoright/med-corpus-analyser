import pymorphy2
import json
from collections import defaultdict
import logging

morph = pymorphy2.MorphAnalyzer()

norm_and_variations_drug = defaultdict(set)
norm_and_variations_disease = defaultdict(set)
with open("../data/raw/ner_800k_jsonl/short_ner_800k.jsonl", "r") as f, open("../data/raw/ner_800k_jsonl/short_ner_800k_norms.jsonl", "w") as outf:
    counter = 0
    for line in f:
        if counter % 1000 == 0:
            logging.warning(str(counter))
        counter += 1
        docData = json.loads(line)
        for k, v in docData["entities"].items():
            if "Drugname" in v["tag"] or "Diseasename" in v["tag"]:
                norm_form = []
                for word in v["text"].split():
                    parse = morph.parse(word)
                    norm_word = None
                    for variant in parse:
                        if "NOUN" in variant.tag or "ADJF" in variant.tag:
                            norm_word = variant.inflect({"nomn"}).word
                            break
                    if norm_word is None:
                        norm_word = parse[0].normal_form
                    norm_form.append(norm_word)
                v["norm_form"] = " ".join(norm_form)
                if "Drugname" in v["tag"]:
                    norm_and_variations_drug[v["norm_form"]].add(v["text"])
                else:
                    norm_and_variations_disease[v["norm_form"]].add(v["text"])
        outf.write(json.dumps(docData) + "\n")

for k, v in norm_and_variations_drug.items():
    norm_and_variations_drug[k] = sorted(list(v))
for k, v in norm_and_variations_disease.items():
    norm_and_variations_disease[k] = sorted(list(v))

with open("../data/raw/ner_800k_jsonl/norm_variants_drug", "w") as f:
    json.dump(norm_and_variations_drug, f)
with open("../data/raw/ner_800k_jsonl/norm_variants_disease", "w") as f:
    json.dump(norm_and_variations_disease, f)