# from flask_restplus import Api
#
# from .namespace1 import api as ns1
# from .namespace2 import api as ns2
#
# api = Api(
#     title='My Title',
#     version='1.0',
#     description='A description',
#     # All API metadatas
# )
#
# api.add_namespace(ns1)
# api.add_namespace(ns2)

# from ner.core import utils
from flask_restplus import Api

from .StatusNS import api as ns1
from .TestingNS import api as ns2
from .TrainingNS import api as ns3
from .FileUploadDelNS import api as ns4

api = Api(
    title='Infosys NLP-NER APIs',
    version='1.0',
    description='Functional NLP-Named Entity Extraction API for Infosys',
    contact='Rohit Naik Jarupla', contact_email='rohit.jarupla@gmail.com', contact_url='http://www.cse.iitd.ac.in/~cs1140224'
)

api.add_namespace(ns1)
api.add_namespace(ns2)
api.add_namespace(ns3)
api.add_namespace(ns4)