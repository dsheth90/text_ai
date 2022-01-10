from tqdm import tqdm
from datetime import datetime
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.layers import Embedding
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from tensorflow.keras.callbacks import ModelCheckpoint
from configparser import ConfigParser
import pickle
import pandas as pd
import re
import logging
import sys
import os
import langid
from emot.emo_unicode import UNICODE_EMOJI
import tensorflow as tf

tqdm.pandas()
log_format = '%(asctime)s %(levelname)s %(filename)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=log_format)

config = ConfigParser()
config.read('config.ini')


class TrainingModelSentiment:

    def __init__(self, filename, model_id, user_id):
        """
          Initialize all the variables
          :param filename (load file): string
          :return:
        """
        try:
            if filename.split(".")[-1] == 'xlsx' or filename.split(".")[-1] == 'xls':
                self.df = pd.read_excel(filename, encoding='latin1')
            elif filename.split(".")[-1] == 'csv':
                self.df = pd.read_csv(filename, encoding='latin1')
            self.filtered_list = []
            self.filtered_sentence = []
            self.replace_by_space_re = re.compile('[/(){}\[\]\|@,;_!.?]')
            self.bad_symbol_re = re.compile('[^0-9a-z #+_]')
            self.stopwords_english = set(stopwords.words('english'))
            self.X = None
            self.y = None
            self.model = None
            self.X_train = None
            self.X_test = None
            self.y_train = None
            self.y_test = None
            self.accr = None
            self.labels = [0, 1, 2, 3, 4, 5]
            # This is fixed.
            self.embedding_dim = 128
            # The maximum number of words to be used. (most frequent)
            self.max_nb_words = 25000
            # Max number of words in each complaint.
            self.max_sequence_length = 200
            self.model_id = model_id
            self.user_id = user_id
            if not os.path.exists('app/AI/weights/custom/'+self.user_id+'/'+self.model_id):
                os.makedirs('app/AI/weights/custom/'+self.user_id+'/'+self.model_id)
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
                if language[0] == 'en':
                    df1 = df1.append({'text': leads, 'label': self.df['label'][lead]}, ignore_index=True)
            self.df = df1
            logging.info('Total labels {}'.format(self.df.label.value_counts()))
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
            self.df['text'] = self.df.apply(lambda x: TrainingModelSentiment.clean_text(self, x.text), axis=1)
            self.df['text'] = self.df['text'].str.replace('\d+', '')
            logging.info('X:input feature shape  {}'.format(self.df["text"].values.shape))
            logging.info('y:output feature shape {}'.format(self.df.drop(['text'], axis=1).values.shape))
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def word_embedding(self):
        """
            perform word embeddings on the leads and convert wheat and chaff into one hot encoding"
        """
        try:
            splitting_ratio = config.get('training_parameters', 'splitting_ratio')
            tokenizer = Tokenizer(num_words=self.max_nb_words, filters='!"$%&()*+,-./:;<=>?@[\]^_`{|}~',
                                  lower=True)
            tokenizer.fit_on_texts(self.df['text'].values)
            word_index = tokenizer.word_index
            logging.info('Found {} unique tokens'.format(len(word_index)))
            tokenizer_model = config.get('training_parameters', 'save_tokenizer_model')
            with open('app/AI/weights/custom/' + self.user_id + '/' + self.model_id + '/' + tokenizer_model,
                      'wb') as handle:
                pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
            self.X = tokenizer.texts_to_sequences(self.df['text'].values)
            self.X = pad_sequences(self.X, maxlen=self.max_sequence_length)
            logging.info('Shape of data tensor {}'.format(self.X.shape))
            self.y = pd.get_dummies(self.df['label']).values
            logging.info('Shape of label tensor {}'.format(self.y.shape))
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y,
                                                                                    test_size=float(
                                                                                        splitting_ratio),
                                                                                    random_state=42)
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def model_architecture(self):
        """
            Train the deep learning architecture
        """
        try:
            epochs = config.get('training_parameters', 'epochs')
            num_of_classes = config.get('training_parameters', 'num_of_classes')
            batch_size = config.get('training_parameters', 'batch_size')
            validation_split = config.get('training_parameters', 'validation_split')
            self.model = Sequential()
            self.model.add(Embedding(self.max_nb_words, self.embedding_dim, input_length=self.X.shape[1]))
            self.model.add(LSTM(128, dropout=0.2, recurrent_dropout=0.2))
            self.model.add(Dense(int(num_of_classes), activation='softmax'))
            self.model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
            checkpoint_name = 'model.hdf5'
            checkpoint = ModelCheckpoint('app/AI/weights/custom/'+self.user_id+'/'+self.model_id+'/'+checkpoint_name,
                                         monitor='val_loss', verbose=1, save_best_only=True, mode='auto')
            callbacks_list = [checkpoint]
            self.model.fit(self.X_train, self.y_train, batch_size=int(batch_size), epochs=int(epochs),
                           verbose=1, validation_split=float(validation_split), callbacks=callbacks_list)
        except Exception as e:
            logging.error('ERROR {}'.format(e))

    def model_evaluation(self):
        """
            evaluate accuracy, classification report, and confusion matrix
        """
        try:
            is_split = config.get('training_parameters', 'is_split')
            if is_split == 'True':
                self.accr = self.model.predict(self.X_test)
                logging.info('Accuracy {}'.format(accuracy_score(self.y_test.argmax(axis=1), self.accr.argmax(axis=1))))
                logging.info('Confusion matrix {}'.format(confusion_matrix(self.y_test.argmax(axis=1),
                                                                           self.accr.argmax(axis=1))))
                logging.info('classification report {}'.format(classification_report(self.y_test.argmax(axis=1),
                                                                                     self.accr.argmax(axis=1))))
            else:
                self.accr = self.model.predict(self.X_train)
                logging.info(
                    'Accuracy {}'.format(accuracy_score(self.y_train.argmax(axis=1), self.accr.argmax(axis=1))))
                logging.info('Confusion matrix {}'.format(confusion_matrix(self.y_train.argmax(axis=1),
                                                                           self.accr.argmax(axis=1))))
                logging.info('classification report {}'.format(classification_report(self.y_train.argmax(axis=1),
                                                                                     self.accr.argmax(axis=1))))
        except Exception as e:
            logging.error('ERROR {}'.format(e))



if __name__ == "__main__":
    input_file_name = config.get('training_parameters', 'load_file')
    logging.info('Reading file')
    train_obj = TrainingModelSentiment(input_file_name, '1', '2')
    logging.info('filtering data')
    train_obj.filter_data()
    train_obj.cleaning()
    logging.info('Applying word embedding')
    train_obj.word_embedding()
    logging.info('Starting model training...')
    train_obj.model_architecture()
    logging.info('Model evaluation')
    train_obj.model_evaluation()
    logging.info('Successfully completed')

