from concurrent import futures
from datetime import datetime
import grpc
import menza_pb2
import menza_pb2_grpc

class Mediator(menza_pb2_grpc.MediatorServicer):
    def __init__(self) -> None:
        super().__init__()
        self.sql_server = grpc.insecure_channel('localhost:50052')
        #stub = menza_pb2_grpc.DatabaseStub(self.sql_server)    

    def WriteEmail(self, request, context):
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        response = stub.Save(menza_pb2.Model(email=request))
        context.set_code(grpc.StatusCode.OK)
        return response

    def ReadEmails(self, request, context):
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        response = stub.Load(menza_pb2.DatabaseQuery(what='*',table='Email',where={}))
        return response

    def WriteMenza(self, request, context):
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        id_restaurant = stub.Save(menza_pb2.Model(restaurant=request.restaurant)).model_id
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

    def ReadMenza(self, request, context):
        stub = menza_pb2_grpc.DatabaseStub(self.sql_server)
        restaurant_query_result = stub.Load(menza_pb2.DatabaseQuery(what='*', table='Restaurant', where={'name':request.restaurant_name}))
        if len(restaurant_query_result.data) == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Restaurant '+request.restaurant_name+' was not found in the database')
            return menza_pb2.Menza()
        restaurant = restaurant_query_result.data[0].restaurant

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

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
menza_pb2_grpc.add_MediatorServicer_to_server(Mediator(),server)
server.add_insecure_port('[::]:50051')
server.start()
server.wait_for_termination()