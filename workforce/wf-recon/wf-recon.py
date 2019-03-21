#!/usr/bin/env python

import requests
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta

CE_URL = "https://controlpanel.opengov.com/api/wf_dataset_service/v1/cost_elements"
WF_URL = "https://controlpanel.opengov.com//api/wf_dataset_service/v2/workforces/"

def defList():
	return defaultdict(list)

def dateParse(dateStr):
	return datetime.strptime(dateStr.replace("-999999999","0001").replace('999999999ls','9999'), '%Y-%m-%d')

FY_MISMATCH = defaultdict(defList)
wfs = {}

with open('data/prod-subset-non-test-workforces.json') as json_file:
	workforces = json.load(json_file)
	for wf in workforces:
		params = {'start':'', 'end':'', 'workforceId': wf['_id']}
		sys.stderr.write("fetching workforce: {}\n".format(wf['_id']))
		r = requests.get(url = WF_URL + wf['_id'])
		workforce = r.json()['data']
		wfs[wf['_id']] = workforce

		sys.stderr.write("fetching cost elements for {}\n".format(wf['_id']))
		r = requests.get(url = CE_URL, params = params)
		data = r.json()['data']

		for ce in data:

			if ce['configuration']['effectiveEndDate'] and dateParse(ce['configuration']['effectiveEndDate']) < dateParse(workforce['configuration']['fiscalYearEndDate']):
				sys.stderr.write("cost element FY end date mismatch for workforce {} ce: {}\n".format(wf['_id'], ce['_id']))
				FY_MISMATCH[wf['entityId']][wf['_id']].append("FY end {} is after CE end {}".format(workforce['configuration']['fiscalYearEndDate'], ce['configuration']['effectiveEndDate']))

			if ce['configuration']['effectiveStartDate'] and dateParse(ce['configuration']['effectiveStartDate']) > dateParse(workforce['configuration']['fiscalYearStartDate']):
				sys.stderr.write("cost element FY end date mismatch for workforce {} ce: {}\n".format(wf['_id'], ce['_id']))
				FY_MISMATCH[wf['entityId']][wf['_id']].append("FY start {} is before CE start {}".format(workforce['configuration']['fiscalYearStartDate'], ce['configuration']['effectiveStartDate']))


for entity in FY_MISMATCH:
	print "entity {}, found {} FY mismatched workforces".format(entity, len(FY_MISMATCH[entity]))
	for wfkey in FY_MISMATCH[entity]:
		print "\tworkforce: {} ({}) with {} FY mismatched cost elements".format(wfkey, wfs[wfkey]['configuration']['name'], len(FY_MISMATCH[entity][wfkey]))
		for line in FY_MISMATCH[entity][wfkey]:
		  print "\t\t{}".format(line)
