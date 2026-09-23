#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) assestmigration.py 2026 AKKODIS INGENIERIE PRODUIT SAS (support@3djuump.com)
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

usage = """
    Usage : Run a command line to retrieve an ndjson from a 3.3 directory
	ex : curl "https://infinite:pass@my_directory/directory/api/assets/{projectid} > assets.ndjson"
	
	MigrateAssets.py <json_description_file>
	json description file must follow the provided conf.schema.json
	Please refer to README
"""

try :
	import requests, jsonschema
except:
	print('please run pip install requirements.txt')

import os, sys, json, io, base64, uuid, datetime, re

global oldAssetValidator
global newAssetAssetValidator

asset_file = "asset_file"
http_username = "http_username"
max_chunk_size = "max_chunk_size"
verifyssl = "verifyssl"
http_password = "http_password"
owner_users = "owner_users"

newAssetAssetValidator = None
oldAssetValidator = None

class MultipartContent:
	def __init__(self):
		self._mCurrentBatch = io.BytesIO()
		self._mBoundary = ('--===========================' + str(uuid.uuid4())).encode('utf-8')
		self._mPartSeparator = b'--' + self._mBoundary + b'\r\n'
		self._mFirstPart = True
	
	def getBoundary(self) :
		return self._mBoundary.decode('utf-8')
	
	def writeNewLine(self) :
		self._mCurrentBatch.write(b'\r\n')
	
	def writeBytes(self, pContent) :
		self._mCurrentBatch.write(pContent)
		
	def startNewPart(self, pName, pFileName, pPartHeaders, pContent) :
		if not self._mFirstPart :
			self.writeNewLine()
		
		self._mFirstPart = False
		self.writeBytes(self._mPartSeparator)
		
		if len(pName) > 0 or len(pFileName) > 0 :
			self.writeBytes(('content-disposition: form-data;name="' + pName + '";filename="' + pFileName + '"\r\n').encode('utf-8'))
		
		if not pPartHeaders is None :
			for lHeader in pPartHeaders :
				self.writeBytes(lHeader.encode('utf-8'))
				self.writeNewLine()
		
		self.writeNewLine()
		self.writeBytes(pContent)

	def getBufferSize(self) :
		return self._mCurrentBatch.getbuffer().nbytes

	def finalizeWrite(self) :
		if not self._mFirstPart:
			self.writeNewLine()

		self.writeBytes(self._mPartSeparator[0:len(self._mPartSeparator) - 2])
		self.writeBytes('--\r\n'.encode('utf-8'))
		self._mFirstPart = True
		lNewBuffer = self._mCurrentBatch.getvalue()
		self._mCurrentBatch.truncate(0)
		return lNewBuffer

def migrateCommitType(pCommitType):
	lTypes = []
	if pCommitType & 0x1 != 0:
		lTypes.append('creation')
	else :
		if pCommitType & 0x2 != 0:
			lTypes.append('content')
		if pCommitType & 0x4 != 0:
			lTypes.append('access_rights')
		if pCommitType & 0x8 != 0:
			lTypes.append('freeze')
		if pCommitType & 0x10 != 0:
			lTypes.append('unfreeze')
		if pCommitType & 0x20 != 0:
			lTypes.append('build')
	return lTypes

def migrateDate(pDate):
	if not pDate.endswith('Z') :
		return -1
	curDate = datetime.datetime.strptime(pDate[0:len(pDate) - 1], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)
	return int(curDate.timestamp()* 1000)


def migrateHistory(pAssetId, old_history, asset_translation, result) :
	old_history['commitTypes'] = migrateCommitType(old_history['typecommit'])	
	old_history['date'] = migrateDate(old_history['savedate'])
	if old_history['date'] < 0 :
		result['errors'].append(
			{ 'id' : pAssetId, 'error' : 'asset date could not be parsed'})
		return False
	
	old_history['user'] = asset_translation.translateUser(old_history['saveuser'])
	old_history['username'] = old_history['saveusername']

	for item in ['typecommit', 'savedate', 'saveuser', 'saveusername', 'computername', 'builddate'] :
		del old_history[item]
	return True

def migrateCredentials(pAssetId, pUserOrTeamList, asset_translation, result) :
	for i in range(len(pUserOrTeamList)) :
		curItem = pUserOrTeamList[i]
		if len(curItem) < 2 :
			return False
		if curItem[0] == 'U':
			pUserOrTeamList[i] = 'U' + asset_translation.translateUser(curItem[1:])
		elif curItem[0] == 'T':
			pUserOrTeamList[i] = 'T' + asset_translation.translateTeam(curItem[1:])
		else :
			result['errors'].append(
				{ 'id' : pAssetId, 'error' : 'migrated asset contains an unknown team or user %s' % curItem})
			return False
	return True

def migrateAsset(old_asset, pConf, asset_translation, result):
	errors = sorted(oldAssetValidator.iter_errors(old_asset), key=str)
	if len(errors) > 0:
		# print('discarding asset %s since it does not comply with the schema' % json.dumps(old_asset))
		# for error in errors:
		# 	print(error.message)
		result['errors'].append(
			{ 'id' : old_asset['_id'] if '_id' in old_asset else '0', 'error' : 'asset is not compliant with schema'})
		return (None, None)
	newContent = {}
	for item in ['type', 'appver', 'contents', 'resources'] :
		newContent[item] = old_asset[item]
		del old_asset[item]
	
	for old_key, new_key in { '_id' : 'id', '_rev' : 'rev', 'desc' : 'description'}.items() :
		old_asset[new_key] = old_asset[old_key]
		del old_asset[old_key]
	
	for old_key in ['ts', 'creationdate', 'creationuser', 'creationusername'] :
		del old_asset[old_key]
	
	old_history = old_asset['revinfo']
	lAssetId = old_asset['id']
	old_asset['revinfo'] = old_history['revisionhistory']
	revhistory = old_history.get('revisionhistory')
	securitydescriptor = old_asset.get('securitydescriptor')
	for revhist in revhistory:
		revhist['buildcomment'] = None
		revhist['securitytags'] = ['test']
		revhist['openingbuildtags'] = None
	rlistunsorted = securitydescriptor.get('r')
	rsorted = sorted(rlistunsorted)
	securitydescriptor['r'] = rsorted
	if pConf.get(owner_users):
		securitydescriptor['rw'] = list(pConf[owner_users])
	appname = asset_translation.getApplicationName()
	if appname == "3D Juump Infinite Native Client":
		newappname = "com.3djuump.nativeclient"
		old_asset['appname'] = newappname
	else:
		raise Exception('App is not handled')
	old_asset['ver'] = '4.0'
	ltag = old_asset.get('tags')
	if not ltag == []: 
		lTag = lTag.strip()
		lTag = lTag.replace(':', '_')
		lTag = lTag.replace(' ', '_')

		lTag = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', lTag)
		ltag = sorted(ltag)
		old_asset['tags'] = lTag
 
	
	if not migrateCredentials(lAssetId, old_asset['securitydescriptor']['r'], asset_translation, result) :
		return (None, None)
	if not migrateCredentials(lAssetId, old_asset['securitydescriptor']['rw'], asset_translation, result) :
		return (None, None)

	#Need to get project tag
	#We will get the projectid from the dump location
	lProjects = {}
	assloc = pConf[asset_file]
	projectdump = assloc.split("/migration_dump/")[0]
	projectdumpfile = projectdump + "/migration_dump/projects.json"
	projID = securitydescriptor.get('prj')
	with open(projectdumpfile,'r') as j:
		data = json.load(j)
		for item in data.get("data", []):
			if item["label"]:
				lProjects[item["label"]] = item["properties"]["projectcomment"]
	for project in lProjects:	
		if project != None:
			if project == projID:
				projectname = lProjects[project]
				projectname = projectname.strip()
				projectname = projectname.replace(':', '_')
				projectname = projectname.replace(' ', '_')

				projectname = re.sub(r'[^\x21\x23-\x39\x3c-\x5B\x5d-\x7e]', '_', projectname)
				old_asset['securitydescriptor']['securitytags'] = [projectname]
	

	for item in old_asset['revinfo'] :
		if not migrateHistory(lAssetId, item, asset_translation, result) :
			return (None, None)

	if not newAssetAssetValidator is None :
		errors = sorted(newAssetAssetValidator.iter_errors(old_asset), key=str)
		if len(errors) > 0:
			# print('discarding asset %s since it does not comply with the schema' % json.dumps(old_asset))
			# for error in errors:
			# 	print(error.message)
			result['errors'].append(
				{ 'id' : lAssetId, 'error' : 'migrated asset is not compliant with schema'})
	return (old_asset, newContent)

def sendRequest(pCurMultipart, pAssets, pUrl, pHeaders, pSession, pConf, result) :
	lHttpAuth = base64.b64encode((pConf[http_username] + ":" + pConf[http_password]).encode('utf-8')).decode('ascii')
	
	lHeaders = {
		'Authorization': 'Basic ' + lHttpAuth,
		'Content-Type': 'application/json; charset=utf-8'
	}
	deleteurl = pConf["directoryurl"] + '/api/assets/delete'
    
	pAssets.sort(key=lambda asset_full: asset_full[0]['id'], reverse=True)

	while len(pAssets) > 0:
		(asset_header, content) = pAssets.pop()
		pCurMultipart.startNewPart(
			'asset_header_json',
			'header.json',
			['Content-Type: application/json; charset=utf-8'],
			json.dumps(asset_header).encode('utf-8'))
		pCurMultipart.startNewPart(
			'asset_content', 
			'content.bin', 
			['Content-Type: application/octet-stream'], 
			json.dumps(content).encode('utf-8')
	)
	todelete = []
	lBuffer = pCurMultipart.finalizeWrite()
	todelete.append(asset_header["id"])
	
	lResponse = pSession.post(deleteurl, json=todelete, headers=lHeaders)
	if lResponse.status_code != 200 :
		print(lResponse.text)
	
	lResponse = pSession.post(pUrl, data=lBuffer, headers=pHeaders)
	if lResponse.status_code != 200 :
		print(lResponse.text)
		raise Exception('Cannot send asset to backend')
	http_result = lResponse.json()
	for item in http_result['failed'] :
		if item['result'] == 'error' :
			result['errors'].append(
			{ 'id' : item['assetid'], 'error' : item['message']})
		elif item['result'] == 'unchanged' :
			result['unchanged'].append(item['assetid'])
	result['success'].extend(http_result['passed'])

def sendAssets(pConf, pAssetTranslation, result) :
	curMultipart = MultipartContent()
	session = requests.Session()
	asset_count = 0
	max_size = pConf[max_chunk_size]
	if not pConf[verifyssl]:
		session.verify = False
		requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
	
	lHttpAuth = base64.b64encode(('%s:%s' % (pConf[http_username], pConf[http_password])).encode('utf-8')).decode('ascii')
	
	lHeaders = {
		'Authorization': 'Basic ' + lHttpAuth,
		'Content-type': 'multipart/form-data; boundary=' + curMultipart.getBoundary()
	}
	lUrl = pConf["directoryurl"] + '/api/assets/push'

	lAssetsBatch = []
	lCurSize = 0
	for line in open(pConf[asset_file], 'r', encoding='utf-8') :
		line = line.strip()
		if line == '':
			continue
		old_asset = json.loads(line)
		if len(old_asset.keys()) == 0 :
			continue
		asset_count += 1
		(new_asset,content) = migrateAsset(old_asset, pConf, pAssetTranslation, result)
		if new_asset is None or content is None:
			continue
		lAssetsBatch.append((new_asset,content))
		# this is a raw estimate
		lCurSize += len(line)
		if lCurSize >= max_size :
			sendRequest(curMultipart, lAssetsBatch, lUrl, lHeaders, session, pConf, result)
			lCurSize = 0
			 
	if lCurSize > 0 :
		sendRequest(curMultipart, lAssetsBatch, lUrl, lHeaders, session, pConf, result)
	 
	if len(result['success']) + len(result['errors']) + len(result['unchanged']) != asset_count :
		print('asset count mismatch')

def populateConf(pConf) :
	if not http_username in pConf :
		pConf[http_username] = "infinite"
	if not verifyssl in pConf:
		pConf[verifyssl] = True
	if not max_chunk_size in pConf:
		pConf[max_chunk_size] = 256
	
	pConf[max_chunk_size] = pConf[max_chunk_size] * 1024 * 1024

if __name__ == '__main__':

	if len(sys.argv) != 2:
		print(usage)
		sys.exit(1)
	
	curDir = os.path.dirname(os.path.realpath( __file__ ))
	sys.path.append(curDir)
	import CustomMigration

	assetTranslation = CustomMigration.CustomMigration()

	jsonFile = sys.argv[1]
	
	if not os.path.exists(jsonFile) :
		print('file %s does not exist' % jsonFile)
		print(usage)
		sys.exit(1)
	
	handle = open(jsonFile, encoding='utf-8')
	conf = json.loads(handle.read())
	handle.close()

	handle = open(os.path.join(curDir, 'conf.schema.json'), encoding='utf-8')
	validation = json.loads(handle.read())
	handle.close()

	handle = open(os.path.join(curDir, 'oldasset.schema.json'), encoding='utf-8')
	oldAssetValidation = json.loads(handle.read())
	handle.close()

	oldAssetValidator = jsonschema.Draft202012Validator(oldAssetValidation)
	
	# handle = open(os.path.join(curDir, 'asset_header_baked.schema.json'), encoding='utf-8')
	# newAssetValidation = json.loads(handle.read())
	# handle.close()
	# newAssetAssetValidator = jsonschema.Draft202012Validator(newAssetValidation)

	jsonschema.validate(instance=conf,schema=validation)

	populateConf(conf)

	if not os.path.exists(conf[asset_file]) :
		print('the asset file %s does not exists' % conf[asset_file])
		sys.exit(1)
	
	lResult = {
		'success' : [],
		'errors' : [],
		'unchanged' : []
	}
	sendAssets(conf, assetTranslation, lResult)

	print("\n\n%s\n\n" % json.dumps(lResult))

	
	