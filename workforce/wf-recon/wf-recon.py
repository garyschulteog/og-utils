#!/usr/bin/env python

import requests
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict

CE_URL = "https://controlpanel.opengov.com/api/wf_dataset_service/v1/cost_elements"
WF_URL = "https://controlpanel.opengov.com//api/wf_dataset_service/v2/workforces"
OGQL_URL = "https://controlpanel.opengov.com/api/ogql/v0/select"


def dateParse(dateStr):
  return datetime.strptime(dateStr.replace("-999999999","0001").replace('999999999','9999'), '%Y-%m-%d')


def getEntityDefs(entityList, token):
  params = {'view_id': 'entities', 'fast_return': 'true'}
  headers = {'Content-Type': 'application/x-sql', 'Authorization': 'Token token={}'.format(token)}
  body = "select id, subdomain, name where id in ({})".format(",".join(map(str,entityList)))
  r = requests.post(url = OGQL_URL, params = params, headers = headers, data = body)

  if r.status_code != requests.codes.ok:
    bard_r.raise_for_status()

  entities = {}
  cols = r.json()['columns']
  data = r.json()['data']
  for entity in data:
    #print entity
    entities[entity[0]] = {cols[0]['name']:entity[0], cols[1]['name']:entity[1], cols[2]['name']:entity[2]}

  return entities


def getWorkforces(entity):

  sys.stderr.write("fetching workforces for entity: {}\n".format(entity['name']))
  ret = {}

  r = requests.get(url = WF_URL, params = {"entityId":entity['id']})
  for workforce in r.json()['data']:
    ret[workforce['_id']] = workforce
  return ret
  

def checkWorkforce(workforce):

  sys.stderr.write("fetching cost elements for workforce: {}\n".format(workforce['configuration']['name']))
  ret = []
  params = {'start':'', 'end':'', 'workforceId': workforce['_id']}
  r = requests.get(url = CE_URL, params = params)
  data = r.json()['data']

  for ce in data:
      if ce['configuration']['effectiveEndDate'] and dateParse(ce['configuration']['effectiveEndDate']) < dateParse(workforce['configuration']['fiscalYearEndDate']):
          sys.stderr.write("\tERROR: cost element FY end date mismatch for workforce {} ce: {}\n".format(workforce['_id'], ce['_id']))
          ret.append("FY end {} is after CE end {}".format(workforce['configuration']['fiscalYearEndDate'], ce['configuration']['effectiveEndDate']))

      if ce['configuration']['effectiveStartDate'] and dateParse(ce['configuration']['effectiveStartDate']) > dateParse(workforce['configuration']['fiscalYearStartDate']):
          sys.stderr.write("\tERROR: cost element FY end date mismatch for workforce {} ce: {}\n".format(workforce['_id'], ce['_id']))
          ret.append("FY start {} is before CE start {}".format(workforce['configuration']['fiscalYearStartDate'], ce['configuration']['effectiveStartDate']))
  return ret


def reportOn(entity, workforces, mismatches):
  if len(mismatches) > 0: 
    print "entity {}({}) workforce {}({})"
    for mismatch in mismatches:
       print "\t{}".format(mismatch)  


def main(argv):
  me = argv[0]
  file = argv[1]
  token = argv[2]


  with open(file) as json_file:
    entityList = json.load(json_file)
    #print(getEntityDefs(entityList, token))
    entities = getEntityDefs(entityList, token)
    for entity in entities:
      workforces = getWorkforces(entities[entity])  
      for workforce in workforces:
        reportOn(entity, workforces[workforce], checkWorkforce(workforces[workforce]))




main(sys.argv)





