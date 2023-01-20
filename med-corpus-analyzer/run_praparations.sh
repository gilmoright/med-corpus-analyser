# add small corpus to elastic with data scheme #2 
~/anaconda3/envs/med-corpus-analyzer/bin/python PrepareAndUpploadToElastic.py --input_file ~/SAG_MED/RelationExtraction/data/RDRS3_11_07_2022_clean/raw/F03P7S67LA0_medNorm_11072022.jsonlines --input_format artemjsonlines --scheme scheme2 --index rdrs110722_scheme2
# add big corpus to elastic with data scheme #2 
~/anaconda3/envs/med-corpus-analyzer/bin/python PrepareAndUpploadToElastic.py --input_file ~/SAG_MED/med-corpus-analyser/data/raw/ner_800k_jsonl/ner_800k.jsonl --input_format sagnlpjsonlines --scheme scheme2 --index med800k_scheme2