from flask_restplus import Namespace, Resource, fields, reqparse

# import sys
# sys.path.insert(0, '')
# from ..core import utils
from ner.core import utils

api = Namespace('testing', description="Operations related to testing a piece of text with different models")

testing_model = api.model('testing_model', {
    'text': fields.String(required=True, description='Text Fragment for extracting named entities'),
    'list_labels': fields.List(fields.String, required=True, description='List of entity labels'),
})

testing_model_arg = reqparse.RequestParser()
testing_model_arg.add_argument('text', type=str, required=True)
testing_model_arg.add_argument('list_labels', type=str, action='append', choices=['PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LANGUAGE', 'MISC'])

metrics_model_arg = reqparse.RequestParser()
metrics_model_arg.add_argument('testing_datasetID', type = str, required=True)
metrics_model_arg.add_argument('matching', type=str, required=True, choices=['Exact Match', 'Partial Match'], default='Exact Match')
metrics_model_arg.add_argument('list_labels', type=str, action='append', choices=['PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LANGUAGE', 'MISC'])

ctesting_model_arg = reqparse.RequestParser()
ctesting_model_arg.add_argument('text', type=str, required=True)
ctesting_model_arg.add_argument('list_labels', type=str, action='append', required=True)

cmetrics_model_arg = reqparse.RequestParser()
cmetrics_model_arg.add_argument('testing_datasetID', type=str, required=True)
cmetrics_model_arg.add_argument('matching', type=str, required=True, choices=['Exact Match', 'Partial Match'], default='Exact Match')
cmetrics_model_arg.add_argument('list_labels', type=str, action='append')

custom_training_model = api.model('custom_training_model', {
    # 'modelID': fields.String(required=True, description='ModelID of the custom model to be used for NER'),
    'text': fields.String(required=True, description='Text Fragment for extracting named entities'),
    'list_labels': fields.List(fields.String, required=True, description='List of entity labels'),
})

entity_fields = api.model('Entity', {
    'entity': fields.String(required=True, description="The actual entity extracted"),
    'type': fields.String(required=True, description="The type of entity"),
    'start': fields.Integer(required=True, description="Start offset of the entity"),
    'end': fields.Integer(required=True, description="End offset of the entity"),
})

resp_metrics_model = api.model('metrics', {
    'entity': fields.String(required=True, description='The entity being considered'),
    'precision': fields.Float(required=True, description='Precision of the given entity'),
    'recall': fields.Float(required=True, description='Recall of the given entity'),
    'f1-score': fields.Float(required=True, description='F1-score fo the given entity'),
    'true_positive': fields.String(required=True, description='True Positives'),
    'false_negative': fields.String(required=True, description='False Negatives'),
    'false_positive': fields.String(required=True, description='False Positive')
})

@api.route('/')
class DefaultModel(Resource):
    @api.expect(testing_model_arg)
    @api.marshal_list_with(entity_fields)
    def get(self):
        """
        Named Entity Recognition using the default Spacy Model
        """
        arg = testing_model_arg.parse_args()
        return utils.entities(arg['text'], arg['list_labels'])

@api.route('/metrics')
class DefaultMetrics(Resource):
    @api.expect(metrics_model_arg)
    @api.marshal_list_with(resp_metrics_model)
    def get(self):
        """
        Calculating Recall and Precision on a given testing dataset
        """
        args = metrics_model_arg.parse_args()
        return utils.defaultMetrics(args['testing_datasetID'], args['list_labels'], args['matching'] == 'Exact Match')

@api.route('/<modelID>')
class CustomModel(Resource):
    @api.expect(ctesting_model_arg)
    @api.marshal_list_with(entity_fields)
    def get(self, modelID):
        """
        Named Entity Recognition using the custom user-defined Model
        """
        arg = ctesting_model_arg.parse_args()
        return utils.entitiesCustom(modelID, arg['text'], arg['list_labels'])

@api.route('/metrics/<modelID>')
class CustomMetrics(Resource):
    @api.expect(cmetrics_model_arg)
    @api.marshal_list_with(resp_metrics_model)
    def get(self, modelID):
        """
        Calculating Recall and Precision on a given testing dataset using custom model
        """
        print('in get')
        args = metrics_model_arg.parse_args()
        return utils.customMetrics(modelID, args['testing_datasetID'], args['list_labels'], args['matching'] == 'Exact Match')