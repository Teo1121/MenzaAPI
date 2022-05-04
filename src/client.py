import grpc
import menza_pb2
import menza_pb2_grpc
from google.protobuf.json_format import MessageToDict

with grpc.insecure_channel('localhost:50051') as channel:
    stub = menza_pb2_grpc.MediatorStub(channel)
    try:
        #response = stub.NewEmail(menza_pb2.Email(address='teo.ferenac@gmail.com'))
        #print(response)
        #response = stub.WriteEmail(menza_pb2.Email(uuid='42ee8dd1-c655-11ec-ac29-e86a64bbce9c'))
        #print(response)
        response = stub.ReadEmails(menza_pb2.EmailQuery())
        print(response)
        #response = stub.VerifiedEmail(menza_pb2.VerificationMail(email=menza_pb2.Email(uuid="ecf2b89a-c598-11ec-9300-e86a64bbce9c"),restaurants=['Teo Pizza','Studentski restoran Pula']))
        #response = stub.WriteMenza(menza_pb2.Menza(**{'restaurant': {'name': 'Teo Pizza'}, 'lunch': [{'menu': {'name': 'Menu 1'}, 'dishes': [{'name': 'Napoletana'}, {'name': 'voda'}, {'name': 'sok'}]}, {'menu': {'name': 'Menu 2'}, 'dishes': [{'name': 'voda'}, {'name': 'Margerita'}, {'name': 'salata'}, {'name': 'Milanese'}, {'name': 'bazga'}]}], 'dinner': [{'menu': {'name': 'Menu 1'}, 'dishes': [{'name': 'Margerita'}, {'name': 'Istriana'}]}]}))
        #print(response)
        #response = stub.ReadMenza(menza_pb2.MenzaQuery(restaurant_name='Teo Pizza'))
        #print(MessageToDict(response))
        #response = stub.ReadMenza(menza_pb2.MenzaQuery(restaurant_name='Studentski restoran Pula'))
        #print(MessageToDict(response))
        #response = stub.ReadMenza(menza_pb2.MenzaQuery(restaurant_name='RESTORAN INDEX'))
        #print(MessageToDict(response))
        #response = stub.WriteMenza(menza_pb2.Data(data={"email":"teo.ferenac@gmail.com"}))
        #print(response)
    except grpc.RpcError as e:
        #print(e)
        print(e.code())
        print(e.details())
