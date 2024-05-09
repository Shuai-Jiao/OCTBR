from object_centric_token_based_replay import token_based_replay
from ocpa.objects.log.importer.csv import factory as csv_import_factory
from ocpa.objects.log.importer.ocel import factory as ocel_import_factory
import time
import pickle
from multiset import *
from collections import Counter

'''
==========Application: Evaluate the real-life object-centric event log BPI2017-Final.csv
with a reference model using object-centric token-based replay.=============
'''

ocpn_path = './sample_logs/ocpn/BPI_model.pkl'
with open(ocpn_path, "rb") as file:
    ocpn = pickle.load(file)
BPI = './sample_logs/csv/BPI2017-Final.csv'
object_types = ["application", "offer"]
parameters = {"obj_names":object_types,
              "val_names":[],
              "act_name":"event_activity",
              "time_name":"event_timestamp",
              "sep":","}
ocel = csv_import_factory.apply(file_path=BPI,parameters = parameters)

time0 = time.time()
result = token_based_replay(ocel,ocpn)
time1 = time.time()

print(f"Computation time:{time1-time0}\n\
      Fitness: {result['fitness']}\n\
      Number of consumed tokens: {result['c']}\n\
      Number of produced tokens: {result['p']}\n\
      Number of missing tokens: {result['m']}\n\
      Number of implicit missing tokens: {len(result['implicit_missing_tokens'])}\n\
      Number of remaining tokens: {result['r']}\n\
      Numner of frozen tokens: {result['f']}\n\
      Number of solved backward replay: {result['solved_backward_replay']}\n\
      Number of unsolved backward replay: {result['unsolved_backward_replay']}\n\
      Problematic activities: {result['unenabled_transitions']}\n\
      Frozen tokens: {result['frozen_tokens']}\n\
      Frozen places: {Counter([ele[0] for ele in list(result['frozen_tokens'])])}\n\
      Frozen objects: {Counter([ele[1] for ele in list(result['frozen_tokens'])])}\n\
      Explicit missing tokens: {result['explicit_missing_tokens']}\n\
      Explicit missing places: {Counter([ele[0] for ele in list(result['explicit_missing_tokens'])])}\n\
      Explicit missing objects: {Counter([ele[1] for ele in list(result['explicit_missing_tokens'])])}\n\
      Implicit missing tokens: {result['implicit_missing_tokens']}\n\
      Implicit missing places: {Counter([ele[0] for ele in list(result['implicit_missing_tokens'])])}\n\
      Remaining tokens: {result['remaining_tokens']}\n\
      Remaining places: {Counter([ele[0] for ele in list(result['remaining_tokens'])])}\n\
      Remaining objects: {Counter([ele[1] for ele in list(result['remaining_tokens'])])}\n")