import os
from django.conf import settings
from translate.convert import json2po, po2json
from shutil import copyfile

def initialize(projectdir, languagecode):
	print "*************** initialize: %s, %s" % (projectdir, languagecode)
	pass

def precommit(commitfile, author, message):
	print "*************** precommit %s, %s, %s" % (commitfile, author, message)
	if not 'countries.json' in commitfile:
		print 'commit to %s' % commitfile
		return [commitfile]
	elif 'countries.pot' in commitfile:
		print 'ignore file'
		return []
	elif 'en_US' in commitfile:
		print 'ignore file'
		return []
	else:
		originalFile = os.path.splitext(os.path.basename(commitfile))[0]
		pofile = os.path.join(settings.PODIRECTORY, commitfile)
		try:
			os.makedirs(os.path.join(settings.VCS_DIRECTORY, os.path.dirname(commitfile)))
		except os.error:
			pass
		copyfile(pofile, os.path.join(settings.VCS_DIRECTORY, commitfile))
		jsonfile = os.path.join(settings.PODIRECTORY, os.path.dirname(commitfile), 'LC_MESSAGES', originalFile)
		template = os.path.join(settings.VCS_DIRECTORY, commitfile.split('/')[0], 'en_US', 'LC_MESSAGES', originalFile)
		print 'Converting po to json: %s to %s' % (pofile, jsonfile)
		with open(pofile, 'r') as po, open(jsonfile, 'w') as json, open(template, 'r') as templ:
			po2json.convertjson(po, json, templ)
		print 'commit to %s' % jsonfile
		return [jsonfile]

def postcommit(updatedfile, success):
	print "*************** postcommit %s, %s" % (updatedfile, success)

def preupdate(updatedfile):
	print "*************** preupdate %s" % updatedfile
	originalFile = os.path.splitext(os.path.basename(updatedfile))[0]
	if '.json.pot' in updatedfile:
		jsonfile = os.path.join(updatedfile.split('/')[0], 'en_US', 'LC_MESSAGES', originalFile)
		print 'rewrite to %s' % jsonfile
		return jsonfile
	else:
		return updatedfile

def postupdate(updatedfile):
        print "*************** postupdate %s" % updatedfile
	originalFile = os.path.splitext(os.path.basename(updatedfile))[0]
	if '.json.pot' in updatedfile:
		potfile = os.path.join(settings.PODIRECTORY, updatedfile)
		jsonfile = os.path.join(settings.VCS_DIRECTORY, updatedfile.split('/')[0], 'en_US', 'LC_MESSAGES', originalFile)
		print 'Converting en_US json to pot: %s to %s' % (jsonfile, potfile)
		with open(jsonfile, 'r') as json, open(potfile, 'w') as pot:
			json2po.convertjson(json, pot, None, pot=True, filter='name')
		copyfile(potfile, os.path.join(settings.VCS_DIRECTORY, updatedfile))

def pretemplateupdate(updatedfile):
	print "*************** pretemplateupdate %s" % updatedfile
	if 'en_US' in updatedfile and 'countries.json' in updatedfile:
		return False
	return True
