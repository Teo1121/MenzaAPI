from flask import Flask
import xmlrpc.client 

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

    @app.route('/error')
    def error():
        raise Exception("test exception")

    @app.errorhandler(404)
    def page_not_found(error):
        return ({"code":404, "message":"This page does not exist"},404)
    
    @app.errorhandler(400)
    def ban_request(error):
        return ({"code":400, "message":"Bad request"},400)

    @app.errorhandler(500)
    def server_error(error):
        return ({"code":500, "message":"Server error"},500)

    return app

def main():
    create_app().run(port="8081")

if __name__ == "__main__":
    main()