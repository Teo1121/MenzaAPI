from concurrent import futures
from datetime import datetime
import grpc
import menza_pb2
import menza_pb2_grpc
from uuid import uuid1

class Mediator(menza_pb2_grpc.MediatorServicer):
    def __init__(self):
        super().__init__()
        self.sql_server = grpc.insecure_channel('localhost:50052')
        self.email_server = grpc.insecure_channel('localhost:50053')
        self.emails2verify = {}
        #stub = menza_pb2_grpc.DatabaseStub(self.sql_server)    

    def WriteEmail(self, request : menza_pb2.Email, context) -> menza_pb2.Response:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        if request.uuid in self.emails2verify:
            new_user = menza_pb2.Email(uuid=request.uuid,address=self.emails2verify[request.uuid])
            try:
                stub.Save(menza_pb2.Model(email=new_user))
            except grpc.RpcError as e:
                context.set_code(e.code())
                context.set_details("Database error: "+e.details())
                return menza_pb2.Response()

            self.emails2verify.pop(request.uuid)

            stub = menza_pb2_grpc.EmailServiceStub(self.email_server)
            response = menza_pb2.Response(msg="Success")
            try:
                stub.SendConfirmation(menza_pb2.ConfirmationMail(email=new_user, has_subscribed=True))
            except grpc.RpcError as e:
                response.msg = "Confirmation mail not sent"
            context.set_code(grpc.StatusCode.OK)

        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Email not found or already verified")
            response = menza_pb2.Response()
        return response
    
    def NewEmail(self, request : menza_pb2.Email, context) -> menza_pb2.Response:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        try:
            if request.address in [model.email.address for model in stub.Load(menza_pb2.DatabaseQuery(what='address',table='Email')).data] or request.address in self.emails2verify.values():
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("Email is waiting to be verified or is already in the database")
                return menza_pb2.Response()
        except grpc.RpcError as e:
            context.set_code(e.code())
            context.set_details("Database error: "+e.details())
            return menza_pb2.Response()

        uuid = str(uuid1())
        self.emails2verify[uuid] = request.address

        stub = menza_pb2_grpc.EmailServiceStub(self.email_server)
        response = menza_pb2.Response(msg="Success")
        try:
            response = stub.SendVerification(menza_pb2.Email(uuid=uuid, address=request.address))
        except grpc.RpcError as e:
            response.msg = "Verification mail not sent"
        context.set_code(grpc.StatusCode.OK)

        return response

    def SubscribeEmail(self, request : menza_pb2.SubscribeMail, context) -> menza_pb2.Response:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        try:
            loaded_email = stub.Load(menza_pb2.DatabaseQuery(what='*', table='Email', where={'uuid':request.email.uuid})).data[0].email
        except grpc.RpcError as e:
            context.set_code(e.code())
            context.set_details("Database error: "+e.details())
            return menza_pb2.Response()
        except IndexError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Email '+request.email.uuid+' was not found in the database')
            return menza_pb2.Response()

        for name in request.restaurants:
            try:
                id_restaurant = stub.Load(menza_pb2.DatabaseQuery(what='*', table="Restaurant", where={'name':name})).data[0].restaurant.id
            except IndexError:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Restaurant '+name+' was not found in the database')
                return menza_pb2.Response()
            stub.Save(menza_pb2.Model(subscription=menza_pb2.Subscription(id_email=loaded_email.id, id_restaurant=id_restaurant)))
        
        stub = menza_pb2_grpc.EmailServiceStub(self.email_server)
        response = menza_pb2.Response(msg="Success")
        try:
            stub.SendConfirmation(menza_pb2.ConfirmationMail(email=loaded_email, has_subscribed=False))
        except grpc.RpcError as e:
            response.msg = "Confirmation mail not sent"
        context.set_code(grpc.StatusCode.OK)

        return response

    def ReadEmails(self, request : menza_pb2.EmailQuery, context) -> menza_pb2.QueryResult:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        try:
            response = stub.Load(menza_pb2.DatabaseQuery(what='*',table='Email',where={}))
        except grpc.RpcError as e:
            context.set_code(e.code())
            context.set_details("Database error: "+e.details())
            return menza_pb2.QueryResult()
        context.set_code(grpc.StatusCode.OK)
        return response

    def WriteMenza(self, request :  menza_pb2.Menza, context) -> menza_pb2.Response:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        try:
            id_restaurant = stub.Save(menza_pb2.Model(restaurant=request.restaurant)).model_id
        except grpc.RpcError as e:
            context.set_code(e.code())
            context.set_details("Database error: "+e.details())
            return menza_pb2.Response()

        ts = datetime.now().replace(microsecond=0,second=0).isoformat()
        for data in request.lunch:
            menu = data.menu
            menu.meal = menza_pb2.Meal.LUNCH
            
            id_menu = stub.Save(menza_pb2.Model(menu=menu)).model_id
            id_offer = stub.Save(menza_pb2.Model(offer=menza_pb2.Offer(id_restaurant=id_restaurant,id_menu=id_menu,date=ts))).model_id
            for dish in data.dishes:
                id_dish = stub.Save(menza_pb2.Model(dish=dish)).model_id
                stub.Save(menza_pb2.Model(dish_offer=menza_pb2.DishOffer(id_dish=id_dish, id_offer=id_offer)))
        
        for data in request.dinner:
            menu = data.menu
            menu.meal = menza_pb2.Meal.DINNER

            id_menu = stub.Save(menza_pb2.Model(menu=menu)).model_id
            id_offer = stub.Save(menza_pb2.Model(offer=menza_pb2.Offer(id_restaurant=id_restaurant,id_menu=id_menu,date=ts))).model_id
            for dish in data.dishes:
                id_dish = stub.Save(menza_pb2.Model(dish=dish)).model_id
                stub.Save(menza_pb2.Model(dish_offer=menza_pb2.DishOffer(id_dish=id_dish, id_offer=id_offer)))
        
        context.set_code(grpc.StatusCode.OK)
        return menza_pb2.Response(msg="Success")

    def ReadMenza(self, request : menza_pb2.MenzaQuery, context) -> menza_pb2.Menza:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        where = {'name':request.restaurant_name} if request.WhichOneof("identifier") == "restaurant_name" else {'id':str(request.restaurant_id)}
        try:
            restaurant = stub.Load(menza_pb2.DatabaseQuery(what='*', table='Restaurant', where=where)).data[0].restaurant
        except grpc.RpcError as e:
            context.set_code(e.code())
            context.set_details("Database error: "+e.details())
            return menza_pb2.Menza()
        except IndexError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Restaurant '+request.restaurant_name+' was not found in the database')
            return menza_pb2.Menza()

        # this should probably be a seperate method inside the database service
        latest_offers = "Offer INNER JOIN (SELECT id_restaurant, max(date) as MaxDate FROM offer GROUP BY id_restaurant) AS tmp on Offer.id_restaurant = tmp.id_restaurant and Offer.date = tmp.MaxDate"
        offers = stub.Load(menza_pb2.DatabaseQuery(what='*' , table=latest_offers, where={'Offer.id_restaurant':str(restaurant.id)})).data

        lunch = []
        dinner = []

        for model in offers:
            menu = stub.Load(menza_pb2.DatabaseQuery(what='*', table='Menu', where={'id':str(model.offer.id_menu)})).data[0].menu
            dish_offers = [model.dish_offer for model in stub.Load(menza_pb2.DatabaseQuery(what='*', table='DishOffer', where={'id_offer':str(model.offer.id)})).data]
            dishes = [stub.Load(menza_pb2.DatabaseQuery(what='*', table='Dish', where={'id':str(dish_offer.id_dish)})).data[0].dish for dish_offer in dish_offers]
            if menu.meal == menza_pb2.Meal.LUNCH:
                lunch.append(menza_pb2.Menza.MenuArray(menu=menu,dishes=dishes))
            elif menu.meal == menza_pb2.Meal.DINNER:
                dinner.append(menza_pb2.Menza.MenuArray(menu=menu,dishes=dishes))

        return menza_pb2.Menza(restaurant=restaurant,lunch=lunch,dinner=dinner)

    def ListRestaurants(self, request : menza_pb2.MenzaQuery, context) -> menza_pb2.QueryResult:
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        try:
            return stub.Load(menza_pb2.DatabaseQuery(what='*', table='Restaurant'))
        except grpc.RpcError as e:
            context.set_code(e.code())
            context.set_details("Database error: "+e.details())
            return menza_pb2.QueryResult()

def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    menza_pb2_grpc.add_MediatorServicer_to_server(Mediator(),server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__": 
    main()