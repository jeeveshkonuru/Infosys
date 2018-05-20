from flask_restplus import Namespace, Resource, fields

api = Namespace('status', description='Operations related to Status of a request')

status_model = api.model('status_model', {
    'status': fields.String(required=True, description="The status of the given requestID"),
    'requestID': fields.Integer(required=True, description="The request ID of the model training process"),
})

kill_model = api.model('kill_model', {
    'requestID': fields.Integer(required=True, desciption="The request ID of the model training process"),
    'kill_successful': fields.Boolean(required=True, description="Process Kill successful")
})

@api.route('/<int:id>')
class Status(Resource):
    @api.doc('get_status')
    @api.marshal_with(status_model)
    def get(self, id):

        return {'status': True,
                'requestID': id}

@api.route('/kill/<int:id>')
class Kill(Resource):
    @api.doc('kill_request')
    @api.marshal_with(kill_model)
    def get(self, id):

        return {
            'requestID': id,
            'kill_successful': True
        }
