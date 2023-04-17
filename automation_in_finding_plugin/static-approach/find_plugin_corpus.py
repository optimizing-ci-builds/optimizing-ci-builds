import xml.etree.ElementTree as ET
from sklearn.feature_extraction.text import TfidfVectorizer
import sys
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

pomFile=sys.argv[1]
unnecessary_directory=sys.argv[2]
# Load the XML file
tree = ET.parse(pomFile)

# Get the root element of the XML file
root = tree.getroot()
print(root)
#root = ET.fromstring(pomFile)
# find the element with the given localname
plugin_corpora_dict = {}
#my_dict["key1"].append("value1")

# if the element is found, traverse its children and descendants
plugin_count=0
target_element = None
for elem in root.iter():
    if elem.tag.endswith('}' + 'build'):
        target_element = elem
        break
if target_element is not None:
    for child1 in target_element.iter():
        if child1.tag.endswith('}' + 'plugins'):
            for child2 in child1.iter():
                if child2.tag.endswith('}' + 'plugin'):
                    corpora_list=[]
                    plugin_count +=1
                    for child3 in child2.iter():
                        if child3.text.strip()!= "":
                            #print("tag="+child3.tag +",text="+child3.text)
                            corpora_list.append(child3.text)               
                    key="plugin"+str(plugin_count)
                    plugin_corpora_dict[key]=corpora_list
                    #print("HI*****************") 
print(plugin_count)

for key, value in plugin_corpora_dict.items():
    print(key, value)

unnecessary_list_corpora=unnecessary_directory.split("/")
print(unnecessary_list_corpora)

###SIMILARITY SCORE CALCULATE
max_sim=0.0
plugin=""
for key, value in plugin_corpora_dict.items():
    print(value)
    vectorizer = TfidfVectorizer()
    vectorizer.fit(unnecessary_list_corpora + value)
    # Transform the lists into TF-IDF vectors
    tfidf_list1 = vectorizer.transform(unnecessary_list_corpora)
    tfidf_list2 = vectorizer.transform(value)
    cosine_sim = cosine_similarity(tfidf_list1, tfidf_list2)
    print(cosine_sim)
    local_max_sim = np.max(cosine_sim)
    if local_max_sim > max_sim:
        max_sim=local_max_sim     
        plugin=key
        #print("similarity=")
        #print(local_max_sim)
print(plugin, str(max_sim))
