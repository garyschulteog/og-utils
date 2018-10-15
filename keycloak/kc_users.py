#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
import json
import base64
import argparse

parser = argparse.ArgumentParser(description='Process config arguments.')
parser.add_argument('config', type=str, nargs = '?', default='test.json',
                    help='json file with delphius and keycloak configs')
args = parser.parse_args()

usersUri = "/auth/admin/realms/opengov/users?first=0&max=2000"
tokenUri = "/auth/realms/opengov/protocol/openid-connect/token"

conf = {}
with open(args.config) as f:
    conf = json.load(f)

basicAuth = "Basic " + base64.b64encode("{0}:{1}".format(conf['clientId'], conf['clientSecret']))
authHeaders = {
    "Authorization": basicAuth,
    "Accept": "application/json,application/x-www-form-urlencoded;q=0.9",
    "Content-Type" : "application/x-www-form-urlencoded" 
    }

authPayload = {
    "grant_type": "password",
    "username" : conf['username'],
    "password" : conf['password']
}

def main():
    authResponse = requests.post(conf['keycloakUrl'] + tokenUri, headers=authHeaders, verify=True, data=authPayload)

    if(authResponse.ok):

        authData = json.loads(authResponse.content)

        usersResponse = requests.get(conf['keycloakUrl'] + usersUri, headers={"Authorization" : "Bearer " + authData["access_token"]})

        if (usersResponse.ok):
            jData = json.loads(usersResponse.content)

        print("The response contains {0} properties".format(len(jData)))
        print("\n")
        for key in jData:
            #print "checking " + key['username']
            for delphUrl in getDelphUrl(key):
                #print delphUrl + "\n\t" + "Token token=%s" % conf['delphiusToken']
                delphiusResponse = requests.get(delphUrl, headers={"Authorization": "Token token=%s" % conf['delphiusToken']})
                dData = {}
                if (delphiusResponse.ok):
                    dData = json.loads(delphiusResponse.content)
    
                    if ('users' in dData and len(dData['users']) > 0):
                        dData = dData['users'][0]

                    if ('uuid' in dData):
                        if (dData['uuid'] != key['id']):
                            print "mismatch for " + key['username'] + ": " + key['id'] + " != " + dData['uuid']
                    else: 
                        print "FAILED to lookup " + key['username']
    else:
      # If response code is not ok (200), print the resulting http error code with description
        authResponse.raise_for_status()


def getDelphUrl(jsonBody) :
    if ('attributes' in jsonBody and 'delphius_id' in jsonBody['attributes']):
        #print key['id'] + ":" + key['username'] + ":" + str(key['attributes']['delphius_id'])
        return [conf['delphiusUrl'] + "/" + str(jsonBody['attributes']['delphius_id'][0])]
    else: 
        if ('email' in jsonBody):
            #print "\tfalling back to email lookup for " + jsonBody['id'] + ":" + jsonBody['username'] + ":" + jsonBody['email']
            return [conf['delphiusUrl'] + "?email=" + jsonBody['email']]
        else:
            print "MISSING delphius info to lookup " + jsonBody['username'] + ":" + jsonBody['id']
            return []

main()





