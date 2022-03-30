from flask import Flask, request
import xmlrpc.client

from menza_error_codes import RPCCodes 

def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')

    @app.route('/hello')
    def hello():
        return {"message":"Hello world!"}
    
    @app.route('/menza')
    def get_menza():
        return {"code":200,"data":api.read_menza()}

    @app.route('/email', methods=['POST'])
    def post_email():
        data = request.get_json()
        try:
            response = api.verify_email(data["email"])
        except KeyError as e:
            return bad_request(e)

        if response == RPCCodes.DUPLICATE:
            return ({"code":400,"message":"email already in database"},400)
        if response == RPCCodes.SERVER_ERROR:
            return ({"code":500, "message":"Server error"},500)

        return {"code":200,"message":"A verification email has been sent"}
    
    @app.route('/verify/<uuid>')
    def verify_email(uuid):
        response = api.write_email(uuid)
        if response == RPCCodes.SUCCESS:
            return {"code":200,"message":"Thank you for subscribing"}
        if response == RPCCodes.DUPLICATE:
            return ({"code":400,"message":"email already subscribed"},400)
        if response == RPCCodes.NOT_FOUND:
            return ({"code":400,"message":"identifier not found"},400) 
        return ({"code":500, "message":"Server error"},500)

    @app.route('/delete/<uuid>')
    def delete_email(uuid):
        response = api.delete_email(uuid)
        if response == RPCCodes.NOT_FOUND:
            return ({"code":400,"message":"identifier not found"},400)
        return {"code":200,"message":"You have been unsubscribed"}
        
    @app.errorhandler(404)
    def page_not_found(error):
        return ({"code":404, "message":"This page does not exist"},404)
    
    @app.errorhandler(405)
    def not_allowed(error):
        return ({"code":405, "message":"This method is not allowed"},405)

    @app.errorhandler(400)
    def bad_request(error):
        return ({"code":400, "message":"Bad request"},400)

    @app.errorhandler(500)
    def server_error(error):
        return ({"code":500, "message":"Server error"},500)

    return app

def main():
    create_app().run(port="8081")

if __name__ == "__main__":
    main()