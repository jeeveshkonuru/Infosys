import os
import uuid
import redis
import werkzeug
from flask_restplus import Namespace, Resource, fields, reqparse

# import sys
# sys.path.insert(0, '')
# from ..core import utils
import ner.core.utils as utils

r = redis.StrictRedis(host='localhost', port=6379, db=0)
api = Namespace('fileHandling', description='Operations related to upload/deletion of testing/training data or models')

""" Models for File/Model Handling """
fileUploadArg = reqparse.RequestParser()
fileUploadArg.add_argument('file', location='files', type=werkzeug.datastructures.FileStorage, required=True)
fileUploadArg.add_argument('type', type=str, choices=['Training', 'Testing'], required=True)

deleteResp_model = api.model('Delete Response Model', {
    'fileID': fields.String(required=True, description='ID used to identity a training/testing dataset'),
    'success': fields.Boolean(required=True, description='True if the given training dataset is deleted successfully'),
})

fileUploadResp = api.model('File Upload Response', {
    'fileID': fields.String(required=True, description='ID used to identity a training/testing dataset'),
    'type': fields.String(required=True, choices=['Training', 'Testing'], description='Type of the dataset that was uploaded')
})

""" APIs """
@api.route('/uploadFile')
class UploadFile(Resource):
    @api.expect(fileUploadArg)
    @api.marshal_with(fileUploadResp)
    def post(self):
        """
        Upload Training or Testing Data onto server
        """
        args = fileUploadArg.parse_args()
        file = args['file']
        if args['type'] == 'Training':
            # file_name = 'trainingDataset_{}'.format(r.incr('TrainingDatasetCounter'))
            file_name = str(uuid.uuid1())
            file.save('ner\\core\\TrainingDataset\\{}'.format(file_name))
            utils.parseReplace('ner\\core\\TrainingDataset\\{}'.format(file_name))
        else:
            # file_name = 'testingDataset_{}'.format(r.incr('TestingDatasetCounter'))
            file_name = str(uuid.uuid1())
            file.save('ner\\core\\TestingDataset\\{}'.format(file_name))
            utils.parseReplace('ner\\core\\TestingDataset\\{}'.format(file_name))

        return {
            'fileID': file_name,
            'type': args['type']
        }

@api.route('/deleteFile/<fileID>')
class DeleteFile(Resource):
    @api.marshal_with(deleteResp_model)
    def delete(self, fileID):
        if os.path.isfile('ner\\core\\TrainingDataset\\{}'.format(fileID)):
            os.remove('ner\\core\\TrainingDataset\\{}'.format(fileID))
        elif os.path.isfile('ner\\core\\TestingDataset\\{}'.format(fileID)):
            os.remove('ner\\core\\TestingDataset\\{}'.format(fileID))
        else:
            api.abort(404, 'Dataset of ID:{} doesn\'t exist!!!'.format(fileID))

        return {
            'fileID': fileID,
            'success': True
        }

