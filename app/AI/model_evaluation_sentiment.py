import pandas as pd
from nltk.corpus import stopwords
import re
import logging
import sys
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import langid
from emot.emo_unicode import UNICODE_EMOJI

log_format = '%(asctime)s %(levelname)s %(filename)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=log_format)


class ModelEvaluationSentiment:

    def __init__(self, model, tokenizer_model_name, data):
        """
          Initialize all the variables
          :param model (loaded AI model): string
          :param tokenizer_model_name (load tokenizer model): string
          :param data (requested json data): dict
          :return:
        """
        try:
            self.df = pd.DataFrame(data)
            self.df = self.df.drop('text_id', axis=1)
            self.df_out = pd.DataFrame(data)
            self.model = model
            self.filtered_list = []
            self.filtered_sentence = []
            self.replace_by_space_re = re.compile('[/(){}\[\]\|@,;_!.?]')
            self.bad_symbol_re = re.compile('[^0-9a-z #+_]')
            self.stopwords_english = set(stopwords.words('english'))
            self.X = None
            self.accr = None
            self.labels = [0, 1, 2, 3, 4, 5]
            self.tokenizer = tokenizer_model_name
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def filter_data(self):
        """
            filter each rows by removing # tags, links, etc.
        """
        try:
            df1 = pd.DataFrame()
            for lead in range(0, len(self.df)):
                leads = self.df['text'][lead]
                leads = leads.lower().strip()
                leads = leads.encode('ascii', errors='ignore')
                leads = str(leads)
                language = langid.classify(leads)
                df1 = df1.append({'text': leads}, ignore_index=True)
            self.df = df1
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def clean_text(self, text):
        """
            helper function of cleaning.
        """
        try:
            text = str(text)
            text = text.lower()
            text = self.replace_by_space_re.sub(' ', text)
            text = self.bad_symbol_re.sub('', text)
            text = ' '.join(word for word in text.split() if word not in self.stopwords_english)
            for emot in UNICODE_EMOJI:
                text1 = "_".join(UNICODE_EMOJI[emot].replace(",", "").replace(":", "").split())
                text1 = text1.replace('_', ' ') + ' '
                text = text.replace(emot, text1)
            return text
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def cleaning(self):
        """
            clean the data by making all lower case, removing all non alphabetic text, removing stopwords, etc.
        """
        try:
            self.df = self.df.reset_index(drop=True)
            self.df['text'] = self.df.apply(lambda x: ModelEvaluationSentiment.clean_text(self, x.text), axis=1)
            self.df['text'] = self.df['text'].str.replace('\d+', '')
        except Exception as e:
            print("Error", e)

    def word_embedding_X(self):
        """
            perform word embeddings on the leads and convert wheat and chaff into one hot encoding"
        """
        try:
            self.X = self.tokenizer.texts_to_sequences(self.df['text'].values)
            self.X = pad_sequences(self.X, maxlen=200)
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def model_evaluation(self, graph):
        """
            evaluate accuracy, classification report, and confusion matrix
        """
        try:
            self.accr = self.model.predict(self.X)
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def model_output(self):
        """
            Add extra row in the input file which includes prediction of each leads
        """
        try:
            out_list = [self.labels[np.argmax(row)] for row in self.accr]
            labels_dict = {0: 'sadness', 1: 'joy', 2: 'love', 3: 'anger', 4: 'fear', 5: 'surprise'}
            out_list  = [*map(labels_dict.get, out_list)]
            self.df_out['emotion'] = out_list
            # self.df_out = self.df_out[['text_id', 'emotion']]
            return self.df_out.to_json(orient='records')
        except Exception as e:
            logging.error('ERROR {}'.format(e))
