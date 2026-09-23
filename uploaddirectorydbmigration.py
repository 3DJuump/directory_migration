#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) uploaddirectorydbmigration.py 2026 AKKODIS INGENIERIE PRODUIT SAS (support@3djuump.com)
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

import os, requests, base64, re, json

if __name__ == '__main__':
	current_dir = os.path.dirname(__file__)
	config_path = os.path.join(current_dir, 'conf.json')

	with open(config_path, 'r') as file:
		config = json.load(file)

	lPool = requests.Session()
	lPool.verify = config.get("verifyssl", True)
	if not lPool.verify:
		requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

	dumplocation = config["dump_location"]
	lDirectoryApiKey = base64.b64encode((config.get("infinite_admin_username_up", "infinite") + ':' + config["infinite_admin_password_up"]).encode('utf-8')).decode('ascii')
	lDirectoryApiUrl =  config["directoryurlup"]

	# ---------------------------------- upload projects start ---------------------------------- #
	lProjects = {}
	projectdump = dumplocation + "/projects.json"
	with open(projectdump,'r') as j:
		data = json.load(j)
		for item in data.get("data", []):
			if item["label"]:
				lProjects[item["label"]] = item["properties"]["projectcomment"]
	for project in lProjects:
		projectname = lProjects[project]
		projectname = projectname.strip()
		projectname = projectname.replace(':', '_')
		projectname = projectname.replace(' ', '_')

		projectname = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', projectname)
		project_Json = {
			"projectcomment": projectname,
		}
		# Upload projects
		lUrl = lDirectoryApiUrl + '/api/manage/projects/' +  project
		lResponse = lPool.put(lUrl,json=project_Json, headers={'Authorization':'Basic %s' % lDirectoryApiKey})
		if lResponse.status_code != 200 and lResponse.status_code != 201:
			print('Invalid return code for put ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
			raise Exception('Invalid return code for put ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
		else:
			print('Reponse project: ' + str(lResponse.reason) +'  ' + project + ' : '+  projectname)
	# ---------------------------------- upload projects end --------------------------------- #
 
	# ---------------------------------- upload teams start ---------------------------------- #
	lTeamname = {}
	lTeamdownloads = {}
	lTeamViews = {}
	lTeam2D = {}
	lTeam3D = {}
	teamsdump = dumplocation + "/teams.json"

	with open(teamsdump, 'r') as j:
		data = json.load(j)
		for item in data.get("data", []):
			teamuuid = item.get("teamuuid")
			if teamuuid:
				teamname = item.get("teamname")
				if teamname:
					lTeamname[teamuuid] = teamname
				accessrights = item.get("accessrights", [])
				
				if "download" in accessrights:
					ldownloads = accessrights.get('download', [])
					for i, download in enumerate(ldownloads):
						download = download.strip()
						download = download.replace(':', '_').replace(' ', '_')
						download = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', download)
						ldownloads[i] = download
					lTeamdownloads[teamuuid] = ldownloads

				if "view" in accessrights:
					lviews = accessrights.get('view', [])
					for i, v in enumerate(lviews):
						v = v.strip()
						v = v.replace(':', '_').replace(' ', '_')
						v = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', v)
						lviews[i] = v 
					lTeamViews[teamuuid] = lviews

				if "export2d" in accessrights:
					lexport2d = accessrights.get('export2d', [])
					for i, export2d in enumerate(lexport2d):
						export2d = export2d.strip()
						export2d = export2d.replace(':', '_').replace(' ', '_')
						export2d = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', export2d)
						lexport2d[i] = export2d
					lTeam2D[teamuuid] = lexport2d

				if "export3d" in accessrights:
					lexport3d = accessrights.get('export3d', [])
					for i, export3d in enumerate(lexport3d):
						export3d = export3d.strip()
						export3d = export3d.replace(':', '_').replace(' ', '_')
						export3d = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', export3d)
						lexport3d[i] = export3d
					lTeam3D[teamuuid] = lexport3d

	for teamuuid, teamname in lTeamname.items():
		teamname = teamname.strip()
		teamname = teamname.replace(':', '_')
		teamname = teamname.replace(' ', '_')

		teamname = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', teamname)
		accessrights = {}
		
		if teamuuid in lTeamdownloads:
			ldownloadsfinal = list(set(lTeamdownloads[teamuuid]))
			accessrights["download"] = ldownloadsfinal
		else:
			accessrights["download"] = []
		if teamuuid in lTeamViews:
			lviewsfinal = list(set(lTeamViews[teamuuid]))
			accessrights["view"] = lviewsfinal
		else:
			accessrights["view"] = []
		if teamuuid in lTeam2D:
			l2Dfinal = list(set(lTeam2D[teamuuid]))
			accessrights["export2d"] = l2Dfinal
		else:
			accessrights["export2d"] = []
		if teamuuid in lTeam3D:
			l3Dfinal = list(set(lTeam3D[teamuuid]))
			accessrights["export3d"] = l3Dfinal
		else:
			accessrights["export3d"] = []

		team_json= {
			"accessrightsupdate": {
				"replace": accessrights
			},
			"teamname": teamname
		}
		test = lTeamViews[teamuuid]

		# Upload teams
		lUrl = lDirectoryApiUrl + '/api/manage/teams/' + teamuuid
		lResponse = lPool.put(lUrl,json=team_json, headers={'Authorization':'Basic %s' % lDirectoryApiKey})
		if lResponse.status_code != 200 and lResponse.status_code != 201:
			raise Exception('Invalid return code for PUT ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
		else:
			print('Reponse team: ' + str(lResponse.reason) +'  ' + teamuuid + ' : '+  teamname)

	
	# --------------------------------- upload teams end ----------------------------------- #
 	# -------------------------------- upload users start ---------------------------------- #
	lUsers = {}
	lUserEnabled = {}
	lAdmin = {}
	lUserTeams = {}
	lAccessRights = {}

	userdump = dumplocation + "/users.json"
	with open(userdump, 'r') as j:
		data = json.load(j)
		for item in data.get("data", []):
			userinfo = item.get("userinfo", {})
			email = userinfo.get("email")
			if email:
				lUsers[item.get("oidcsub")] = email
			oidcsub = item.get("oidcsub")
			if not oidcsub:
				continue

			enabled = item.get("enabled")
			if enabled is not None:
				lUserEnabled[oidcsub] = enabled
    
			frontendaccess = item.get("frontendaccess")
			if frontendaccess is not None:
				lAdmin[oidcsub] = frontendaccess
    
			teams = item.get("teams")
			if teams:
				lUserTeams[oidcsub] = teams
    
			accessrights = item.get("accessrights")
			if accessrights:
				lAccessRights[oidcsub] = accessrights

	for user in lUsers:
		AccessRights = []
		if lAccessRights.get(user):
				AccessRights = lAccessRights[user]
				print(AccessRights)
		for right in AccessRights:
			cleaned_tags = []
			for tag in AccessRights[right]:
				tag = tag.strip()
				tag = tag.replace(':', '_')
				tag = tag.replace(' ', '_')
				tag = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', tag)
				if len(tag) > 64:
					tag = tag[:64]
				cleaned_tags.append(tag)
			AccessRights[right] = cleaned_tags
		print(AccessRights)
		userJson = {
			"email": lUsers[user],
			"teamsupdate":  {
				"replace": [team.get("teamuuid") for team in lUserTeams.get(user, [])]
			},
		}
  
		if lUserEnabled.get(user):
			userJson["enabled"] = lUserEnabled[user]
			if lUserEnabled[user] == True:
				userJson["clientappaccess"] = "yes"
			else:
				userJson["clientappaccess"] = "no"
		if lAdmin.get(user):
			if lAdmin[user] == True:
				userJson["adminrights"] = ["full"]
		if AccessRights != []:
			userJson["accessrightsupdate"] = {
				"replace": AccessRights
			}


		lUrl = lDirectoryApiUrl + '/api/manage/users/' + user 
		lResponse = lPool.put(lUrl,json=userJson,  headers={'Authorization':'Basic %s' % lDirectoryApiKey})
		if lResponse.status_code != 200 and lResponse.status_code != 201:
			raise Exception('Invalid return code for PUT ' + str(lResponse.status_code) + ' ' + lResponse.reason + ' ' + str(lResponse.text))
		else:
				print('Reponse user: ' + str(lResponse.reason) +'  ' + user + ' : '+  lUsers[user])
		
	# ---------------------------------- upload users end ---------------------------------- #
