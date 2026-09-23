#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) dumpdirectorydbmigration.py 2026 AKKODIS INGENIERIE PRODUIT SAS (support@3djuump.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import csv, os, requests, sys, urllib, base64, re, json

if __name__ == '__main__':
	current_dir = os.path.dirname(__file__)
	config_path = os.path.join(current_dir, 'conf.json')

	with open(config_path, 'r') as file:
		config = json.load(file)

	lPool = requests.Session()
	lPool.verify = config.get("verifyssl", True)
	if not lPool.verify:
		requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

	embeded_url_dump = config["embeded_url_dump"]
	dumplocation = config["dump_location"]
 
	lCredentialsMatch = re.match(r'^https:\/\/(.+?):(.+?)@(.*\/directory)$',embeded_url_dump)
	if lCredentialsMatch is None or len(lCredentialsMatch.groups()) != 3:
		raise Exception('Invalid proxy url, fail to extract credentials')
	lDirectoryApiKey = base64.b64encode((urllib.parse.quote_plus(lCredentialsMatch.groups()[0]) + ':' + urllib.parse.quote_plus(lCredentialsMatch.groups()[1])).encode('utf-8')).decode('ascii')
	directory_url_dump = 'https://' + lCredentialsMatch.groups()[2]
	
    # load projectids
	lResponse = ""
	lprojectidids = []
	lprojectidsToRecreate = {}
	lUrl = directory_url_dump + '/api/manage/projects'
	lResponse = lPool.get(lUrl, headers={'Authorization':'Basic %s' % lDirectoryApiKey,'x-infinite-apikey':lDirectoryApiKey})
	if lResponse.status_code != 200:
		print('Invalid return code for get ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
		raise Exception('Invalid return code for get ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
	else:
		response_data = lResponse.json()
		dumpat = dumplocation + "projects.json"
		with open(dumpat, "w", encoding="utf-8") as logfile:
			json.dump(response_data, logfile, indent=4)
		for item in response_data.get("data", []):
			if item["label"]:
				lprojectidids.append(item["label"])
	print('Projects succefully dumped')


	# load list of teams with rights
	lTeams = {}
	lResponse = ""
	lUrl = directory_url_dump + '/api/manage/teams'
	lResponse = lPool.post(lUrl, headers={'Authorization':'Basic %s' % lDirectoryApiKey,'x-infinite-apikey':lDirectoryApiKey})
	if lResponse.status_code != 200:
		raise Exception('Invalid return code for get ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
	else:
		dumpat = dumplocation + "teams.json"
		with open(dumpat, "w", encoding="utf-8") as logfile:
			json.dump(lResponse.json(), logfile, indent=4)
			
	lOldUsers = {}
	lActiveUsers = set()
	print('Teams succefully dumped')
 
	# load users to recreate list
	lResponse = ""	
	lUrl = directory_url_dump + '/api/manage/users'
	lResponse = lPool.post(lUrl, headers={'Authorization':'Basic %s' % lDirectoryApiKey,'x-infinite-apikey':lDirectoryApiKey})
	if lResponse.status_code != 200:
		raise Exception('Invalid return code for get ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
	else:
		dumpat = dumplocation + "users.json"
		with open(dumpat, "w", encoding="utf-8") as logfile:
			json.dump(lResponse.json(), logfile, indent=4)
	print('Users succefully dumped')
 
   #load all assets in a projectid
	lResponse = ""
	for projectid in lprojectidids:
		lUrl = directory_url_dump + '/api/assets/' + projectid
		lResponse = lPool.get(lUrl, headers={'Authorization':'Basic %s' % lDirectoryApiKey,'x-infinite-apikey':lDirectoryApiKey})
		if lResponse.status_code != 200:
			raise Exception('Invalid return code for get ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
		else:
			folder = dumplocation +  "/assets/" 
			dumpat = folder + "/" + projectid + ".ndjson"
			ndjson_lines = lResponse.text.strip().splitlines()
			with open(dumpat, "w", encoding="utf-8") as logfile:
				for line in ndjson_lines:
					logfile.write(line + "\n")
	print('Assets succefully dumped')