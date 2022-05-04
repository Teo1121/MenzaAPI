from flask import Flask, request

import grpc
from werkzeug.exceptions import InternalServerError, BadRequest
import menza_pb2
import menza_pb2_grpc
from google.protobuf.json_format import MessageToDict

def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    api = grpc.insecure_channel('localhost:50051')
    stub = menza_pb2_grpc.MediatorStub(api)

    @app.route('/hello')
    def hello():
        return {"message":"Hello world!"}
    
    @app.route('/menza/list')
    def get_menza_list():
        try:
            return {"code":200, "data":[MessageToDict(model.restaurant) for model in stub.ListRestaurants(menza_pb2.MenzaQuery()).data]}
        except grpc.RpcError as e:
            raise InternalServerError(e.details() + " " + str(e.code()), original_exception=e)

    @app.route('/menza/<identifier>')
    def get_menza(identifier):
        if identifier.isdigit():
            query = menza_pb2.MenzaQuery(restaurant_id=int(identifier))
        else:
            query = menza_pb2.MenzaQuery(restaurant_name=identifier)
        try:
            return {"code":200, "data":MessageToDict(stub.ReadMenza(query))}
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise BadRequest("Bad request: "+e.details())
            else:
                raise InternalServerError(e.details() + " " + str(e.code()), original_exception=e)
  
    @app.route('/email', methods=['POST'])
    def post_email():
        data = request.get_json()
        try:
            response = stub.NewEmail(menza_pb2.Email(address=data["email"]))
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise BadRequest("Bad request: "+e.details())
            else:
                raise InternalServerError(e.details() + " " + str(e.code()), original_exception=e)
        except KeyError as e:
            raise BadRequest("Bad request: no 'email' found in request body")

        return {"code":200, "message":response.msg}
    
    @app.route('/email/sub', methods=['POST'])
    def post_sub():
        data : dict = request.get_json()
        if "names" in data:
            restaurants = [menza_pb2.MenzaQuery(restaurant_name=name) for name in data["names"]]
        elif "ids" in data:
            restaurants = [menza_pb2.MenzaQuery(restaurant_id=int(id)) for id in data["ids"]]
        else:
            raise BadRequest("Bad request: no resturant identifier found in request body")
        try:
            response = stub.SubscribeEmail(menza_pb2.SubscribeMail(email=menza_pb2.Email(uuid=data["uuid"]), restaurants=restaurants))
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise BadRequest("Bad request: "+e.details())
            else:
                raise InternalServerError(e.details() + " " + str(e.code()), original_exception=e)
        except KeyError as e:
            raise BadRequest("Bad request: no 'uuid' found in request body")

        return {"code":200, "message":response.msg}

    @app.route('/verify/<uuid>')
    def verify_email(uuid):
        try:
            response = stub.WriteEmail(menza_pb2.Email(uuid=uuid))
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise BadRequest("Bad request: "+e.details())
            else:
                raise InternalServerError(e.details() + " " + str(e.code()), original_exception=e)

        return {"code":200, "message":response.msg}


    @app.errorhandler(404)
    def page_not_found(error):
        return ({"code":404, "message":error.description},404)
    
    @app.errorhandler(405)
    def not_allowed(error):
        return ({"code":405, "message":error.description},405)

    @app.errorhandler(400)
    def bad_request(error):
        return ({"code":400, "message":error.description},400)

    @app.errorhandler(500)
    def server_error(error):
        return ({"code":500, "message":error.description },500)

    return app

def main():
    create_app().run(host="0.0.0.0",port="8081")

if __name__ == "__main__":
    main()