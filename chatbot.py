import os
import json
import pandas
import yaml

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier


class ChatBot:
    def chat_bot_start():
        """start the module to chat with the bot"""
        os.chdir("english/")
        files = os.listdir(os.getcwd())

        text_clf = Pipeline([('vect', CountVectorizer()),
                             ('tfidf', TfidfTransformer()),
                             ('clf', SGDClassifier(loss='hinge', penalty='l2',
                                                   alpha=1e-3, random_state=42,
                                                   max_iter=5, tol=None)),
                             ])
        readX = []
        readY = []
        for file in files:
            print(file)
            with open(file, 'r') as stream:
                dict = yaml.load(stream)

            jsonDump = json.dumps(dict, indent=4, sort_keys=True)

            read = pandas.read_json(jsonDump)
            readX.extend(read[0])
            readY.extend(read[1])

        text_clf.fit(readX, readY)
        return text_clf
