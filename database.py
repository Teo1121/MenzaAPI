from concurrent import futures
import grpc
import menza_pb2
import menza_pb2_grpc
from google.protobuf.json_format import MessageToDict

import re
import sqlite3


class Database(menza_pb2_grpc.DatabaseServicer):

    def __init__(self,testing=True) -> None:
        super().__init__()

        if testing:
            self.conn = sqlite3.connect(':memory:',check_same_thread=False)


            cursor = self.conn.cursor()

            cursor.execute("""CREATE TABLE Email ( 
                            id INTEGER PRIMARY KEY, 
                            uuid TEXT UNIQUE,
                            address TEXT 
                            )""")
            cursor.execute("""CREATE TABLE Dish ( 
                            id INTEGER PRIMARY KEY, 
                            name TEXT 
                            )""")
            cursor.execute("""CREATE TABLE Restaurant ( 
                            id INTEGER PRIMARY KEY, 
                            name TEXT 
                            )""")
            cursor.execute("""CREATE TABLE Menu ( 
                            id INTEGER PRIMARY KEY, 
                            name TEXT,
                            meal INTEGER
                            )""")
            cursor.execute("""CREATE TABLE Offer (
                            id INTEGER PRIMARY KEY,
                            id_restaurant INTEGER,
                            id_menu INTEGER,
                            date TIMESTAMP,
                            FOREIGN KEY(id_restaurant) REFERENCES Restaurant(id),
                            FOREIGN KEY(id_menu) REFERENCES Menu(id)
                            )""")
            cursor.execute("""CREATE TABLE DishOffer (
                            id INTEGER PRIMARY KEY,
                            id_dish INTEGER,
                            id_offer INTEGER,
                            FOREIGN KEY(id_dish) REFERENCES Dish(id),
                            FOREIGN KEY(id_offer) REFERENCES Offer(id)
                            )""")
            cursor.execute("""CREATE TABLE Subscription (
                            id INTEGER PRIMARY KEY,
                            id_email INTEGER,
                            id_restaurant INTEGER,
                            FOREIGN KEY(id_email) REFERENCES Email(id),
                            FOREIGN KEY(id_restaurant) REFERENCES Restaurant(id)
                            )""")
            
            self.conn.commit()

            cursor.execute("INSERT INTO Restaurant VALUES (1, 'Teo Pizza')")
            
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'Margerita')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'Slavonska')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'Tunjevina')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'Istarska')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'voda')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'sok')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'bazga')")
            cursor.execute("INSERT INTO Dish VALUES (NULL, 'salata')")

            cursor.execute("INSERT INTO Menu VALUES (NULL, 'Menu 1', 1)")
            cursor.execute("INSERT INTO Menu VALUES (NULL, 'Menu 2', 1)")
            cursor.execute("INSERT INTO Menu VALUES (NULL, 'Menu 1', 2)")
            
            cursor.execute("INSERT INTO Offer VALUES (NULL, 1,1,'2022-04-23T17:26:10')")
            cursor.execute("INSERT INTO Offer VALUES (NULL, 1,2,'2022-04-23T17:26:10')")
            cursor.execute("INSERT INTO Offer VALUES (NULL, 1,1,'2022-04-23T17:26:10')")

            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 1,3)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 5,2)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 1,2)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 2,1)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 8,2)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 3,2)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 5,1)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 6,1)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 7,2)")
            cursor.execute("INSERT INTO DishOffer VALUES (NULL, 4,3)")

            self.conn.commit()
        else:
            self.conn = sqlite3.connect('menza.db',check_same_thread=False)

    def Save(self, request : menza_pb2.Model, context) -> menza_pb2.Response:
        
        model_type = request.WhichOneof("model")
        if model_type == None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('No model provided!')
            return menza_pb2.Response()

        model : dict = MessageToDict(request,
                                    including_default_value_fields=True,
                                    preserving_proto_field_name=True,
                                    use_integers_for_enums=True)[model_type]

        model.pop('id')
        query = "SELECT * FROM {} WHERE {}".format(
                                                ''.join(word.title() for word in model_type.split('_')),
                                                ' AND '.join([key+"='"+str(model[key])+"'" for key in model])
                                                )
        cursor = self.conn.cursor()

        cursor.execute(query)
        duplicate = cursor.fetchall()
        if len(duplicate) > 0:
            context.set_code(grpc.StatusCode.OK)
            return menza_pb2.Response(model_id=duplicate[0][0])

        query = "INSERT INTO {} VALUES (NULL{})".format(''.join(word.title() for word in model_type.split('_'))+' (id, '+', '.join(model.keys())+')',', ?'*len(model))
        cursor.execute(query,tuple(model.values()))
        self.conn.commit()
        
        context.set_code(grpc.StatusCode.OK)
        return menza_pb2.Response(model_id=cursor.lastrowid)

    def Load(self, request : menza_pb2.DatabaseQuery, context) -> menza_pb2.QueryResult:
        where = dict(request.where)
        cursor = self.conn.cursor()
        query = "SELECT {} FROM {} WHERE {}".format(
            request.what,
            request.table,
            ' AND '.join([key+"='"+where[key]+"'" for key in where]) if len(where) > 0 else '1'
        )

        try:
            cursor.execute(query)
        except sqlite3.OperationalError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return menza_pb2.QueryResult()
        model = getattr(menza_pb2,request.table.split(' ')[0])

        res = []
        for item in cursor.fetchall():
            temp = []
            for i, name in enumerate(model.DESCRIPTOR.fields_by_name):
                values = request.what.replace(' ','').split(',')
                if name in values:
                    temp.append((name,item[values.index(name)]))
                elif len(request.what) == 0 or '*' in request.what:
                    temp.append((name,item[i]))
            res.append(menza_pb2.Model(**{re.sub(r'(?<!^)(?=[A-Z])', '_', request.table.split(' ')[0]).lower():model(**dict(temp))}))

        #res = [menza_pb2.Model(**{re.sub(r'(?<!^)(?=[A-Z])', '_', request.table.split(' ')[0]).lower():model(**dict([(name,item[i]) for i,name in enumerate(model.DESCRIPTOR.fields_by_name) if name in request.what or len(request.what) == 0 or '*' in request.what]))}) for item in cursor.fetchall()]
        response = menza_pb2.QueryResult(data=res)
        context.set_code(grpc.StatusCode.OK)
        return response

def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    menza_pb2_grpc.add_DatabaseServicer_to_server(Database(),server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__": 
    main()