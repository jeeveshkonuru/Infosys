import os

import redis
from flask_restplus import Namespace, Resource, fields, reqparse

import ner.core.utils as utils

r = redis.StrictRedis(host='localhost', port=6379, db=0)
api = Namespace('training', description='Operations related to training a custom model')

# training_data_model = api.model('trainingDataModel' ,{
#     'TrainingData': fields.String(required=True, description='Training Dataset used to train the custom model'),
# })

training_file_id = api.model('TrainingFileID',{
    'training_file_id': fields.String(required=True, description='ID used to identify a training dataset'),
})

deleteResp_model = api.model('Delete Response Model', {
    'training_datasetID': fields.String(required=True, description='ID used to identity a training dataset'),
    'success': fields.Boolean(required=True, description='True if the given training dataset is deleted successfully'),
})

newModel = api.model('Build a new Model', {
    'training_datasetID': fields.String(required=True, description='ID used to identity a training dataset'),
    'list_labels': fields.List(fields.String, required=True, description='List of labels that can be identified with the custom model')
})

newModel_resp = api.model('Response to building a new model', {
    'task': fields.String(required=True, description='Details of the task'),
    'requestID': fields.String(required=True, description='ID of this process of training a new model'),
    'modelID': fields.String(required=True, description='ID of the model produced by training')
})

deleteModel_resp = api.model('Delete Existing Model', {
    'modelID': fields.String(required=True, description='ID of the model to be deleted'),
    'success': fields.Boolean(required=True, description='True is deletion of the model is successful')
})


nModel_args = reqparse.RequestParser()
nModel_args.add_argument('training_datasetID', type=str, required=True)
nModel_args.add_argument('labels', type=str, action='append', required=False)
@api.route('/buildModel')
class BuildNewModel(Resource):
    # @api.expect(newModel)
    @api.expect(nModel_args, validate=True)
    @api.marshal_with(newModel_resp)
    def get(self):
        """
        Build a new model given a training dataset ID and the list of labels
        """
        args = nModel_args.parse_args()
        modelID = utils.buildModel(args['training_datasetID'], args['labels'])
        requestID = r.incr('REQUEST_ID')
        return {
            'task': 'Building a new model with training dataset ID: {} with labels: {}'.format(args['training_datasetID'], args['labels']),
            'requestID': str(requestID),
            'modelID': modelID
        }

enhancemodel_args = reqparse.RequestParser()
enhancemodel_args.add_argument('training_datasetID', type=str, required=True)
enhancemodel_args.add_argument('existing_modelID', type=str, required=True)
enhancemodel_args.add_argument('duplicate', type=str, choices=['True', 'False'], required=True, help='Check True if you want a new model to be created out of the existing model')
@api.route('/update')
class UpdateWithoutNLabels(Resource):
    @api.expect(enhancemodel_args)
    @api.marshal_with(newModel_resp)
    def get(self):
        args = enhancemodel_args.parse_args()
        modelID = utils.updateModel(existing_modelID=args['existing_modelID'], training_datasetID=args['training_datasetID'], duplicate=args['duplicate']=='True')
        return {
            'task': 'Enhancing exsiting model {} with training dataset: {} and duplicate: {}'.format(
                args['existing_modelID'], args['training_datasetID'], args['duplicate']),
            'requestID': r.incr('REQUEST_ID'),
            'modelID': modelID
        }

enhancemodel2_args = reqparse.RequestParser()
enhancemodel2_args.add_argument('training_datasetID', type=str, required=True)
enhancemodel2_args.add_argument('list_labels', type=str, action='append')
enhancemodel2_args.add_argument('existing_modelID', type=str, required=True)
enhancemodel2_args.add_argument('duplicate', type=bool, required=True, help='Check True if you want a new model to be created out of the existing model')
@api.route('/updateWithNewLabels')
class updateWithNLabels(Resource):
    @api.expect(enhancemodel2_args)
    @api.marshal_with(newModel_resp)
    def get(self):
        args = enhancemodel2_args.parse_args()
        modelID = utils.enhanceModel(existing_modelID=args['existing_modelID'],
                                     training_datasetID=args['training_datasetID'], duplicate=args['duplicate'], labels=args['list_labels'])
        return {
            'task': 'Enhancing exsiting model {} with training dataset: {} and labels: {}'.format(
                args['existing_modelID'], args['training_datasetID'], args['list_labels']),
            'requestID': r.incr('REQUEST_ID'),
            'modelID': modelID,
        }


@api.route('/deleteModel/<modelID>')
class DeleteModel(Resource):
    @api.marshal_with(deleteModel_resp)
    def delete(self, modelID):
        os.remove('ner\\core\\Models\\{}.tar.gz'.format(modelID))
        return {
            'modelID': modelID,
            'success': True
        }
