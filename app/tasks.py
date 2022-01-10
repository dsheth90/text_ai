from .AI import TrainingModelSentiment, ModelEvaluationSentiment
from .model import TaskModel, TrainingModel, TaskResultModel
from tensorflow.keras.models import load_model
from configparser import ConfigParser
import tensorflow as tf
from app import celery
import pandas as pd
import logging
import pickle
import time
import sys
import json


log_format = '%(asctime)s %(levelname)s %(filename)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=log_format)

config = ConfigParser()
config.read('config.ini')


@celery.task()
def make_file(fname, content):
    """Testing purpose"""
    time.sleep(100)
    with open(fname, "w") as f:
        f.write(content)
    job_id = make_file.request.id
    TaskModel.change_status(job_id, 1)


@celery.task()
def training_model(filename, model_id, user_id):
    try:
        logging.info('Reading file')
        train_obj = TrainingModelSentiment(filename, model_id, user_id)
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
        job_id = training_model.request.id
        TrainingModel.update_status_job_id(job_id, 1)
        TrainingModel.update_finish_time(job_id)
        TrainingModel.update_error_flag(job_id, 0)
        logging.info('Successfully Updated DB')
    except Exception as e:
        job_id = training_model.request.id
        TrainingModel.update_status_job_id(job_id, 2)
        TrainingModel.update_finish_time(job_id)
        TrainingModel.update_error_flag(job_id, 1)
        TrainingModel.update_error_msg(job_id, str(e))


@celery.task()
def evaluate_result(text, model_id, model_type, user_id):
    try:
        time.sleep(1)
        graph = tf.compat.v1.get_default_graph()

        if model_type == 'General':
            model = load_model('app/AI/weights/general/Weights-012--0.45829.hdf5')
            with open('app/AI/weights/general/tokenizer.pickle', 'rb') as handle:
                tokenizer = pickle.load(handle)
        else:
            model = load_model('app/AI/weights/custom/'+user_id+'/'+model_id+'/'+'model.hdf5')
            with open('app/AI/weights/custom/'+user_id+'/'+model_id+'/'+'tokenizer.pickle', 'rb') as handle:
                tokenizer = pickle.load(handle)

        pred_obj = ModelEvaluationSentiment(model, tokenizer, text)
        logging.info('Filtering data')
        pred_obj.filter_data()
        logging.info('Filtering data')
        pred_obj.cleaning()
        logging.info('Performing word embedding')
        pred_obj.word_embedding_X()
        logging.info('Evaluating data')
        pred_obj.model_evaluation(graph)
        logging.info('Sending response')
        json_output = pred_obj.model_output()
        json_output = json.loads(json_output)
        print("json_output =", json_output, type(json_output))
        data = pd.DataFrame(json_output)
        job_id = evaluate_result.request.id
        data['job_id_fk'] = job_id
        data['model_id_fk'] = model_id
        data = data.to_json(orient='records')
        data = json.loads(data)
        for d in data:
            task_res_db = TaskResultModel(**d)
            task_res_db.save_to_db()
        TaskModel.update_status_job_id(job_id, 1)
        TaskModel.update_finish_time(job_id)
        TaskModel.update_error_flag(job_id, 0)
        logging.info('Successfully Updated DB')
    except Exception as e:
        job_id = evaluate_result.request.id
        TaskModel.update_status_job_id(job_id, 2)
        TaskModel.update_finish_time(job_id)
        TaskModel.update_error_flag(job_id, 1)
        TaskModel.update_error_msg(job_id, str(e))
