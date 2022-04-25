import grpc
import menza_pb2
import menza_pb2_grpc
from google.protobuf.json_format import MessageToDict

with grpc.insecure_channel('localhost:50051') as channel:
    stub = menza_pb2_grpc.MediatorStub(channel)
    #response = stub.WriteEmail(menza_pb2.Email(uuid='test123',mail='test@unipu.hr'))
    #print(response)
    #response = stub.WriteEmail(menza_pb2.Email(uuid='test123',mail='test@unipu.hr'))
    #print(response)
    #response = stub.ReadEmails(menza_pb2.Query())
    #print(response)
    #response = stub.WriteMenza(menza_pb2.Menza(**{'restaurant': {'name': 'Teo Pizza'}, 'lunch': [{'menu': {'name': 'Menu 1'}, 'dishes': [{'name': 'Napoletana'}, {'name': 'voda'}, {'name': 'sok'}]}, {'menu': {'name': 'Menu 2'}, 'dishes': [{'name': 'voda'}, {'name': 'Margerita'}, {'name': 'salata'}, {'name': 'Milanese'}, {'name': 'bazga'}]}], 'dinner': [{'menu': {'name': 'Menu 1'}, 'dishes': [{'name': 'Margerita'}, {'name': 'Istriana'}]}]}))
    #print(response)
    response = stub.ReadMenza(menza_pb2.Query(what='Teo Pizza'))
    print(MessageToDict(response))
    response = stub.ReadMenza(menza_pb2.Query(what='Studentski restoran Pula'))
    print(MessageToDict(response))
    response = stub.ReadMenza(menza_pb2.Query(what='RESTORAN INDEX'))
    print(MessageToDict(response))
    #response = stub.WriteMenza(menza_pb2.Data(data={"email":"teo.ferenac@gmail.com"}))
    #print(response)