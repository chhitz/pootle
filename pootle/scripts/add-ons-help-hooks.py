import os
from django.conf import settings
from translate.convert import html2po, po2html
from shutil import copyfile

html_translations = {
	"help.html": "de_DE",
	"hint.html": "de_DE",
	"intro.html": "en_US",
}

def initialize(projectdir, languagecode):
	print "*************** initialize: %s, %s" % (projectdir, languagecode)
	pass

def precommit(commitfile, author, message):
	"""
	Before we commit to VCS we want to convert the .po files back to .html files
	"""
	print "*************** precommit %s, %s, %s" % (commitfile, author, message)
	if not any(map(lambda x: x in commitfile, html_translations.keys())):
		print 'commit to %s' % commitfile
		return [commitfile]

	if '.pot' in commitfile:
		print 'ignore file'
		return []

	if any(map(lambda (f,lang): f in commitfile and lang in commitfile, html_translations.items())):
		print 'ignore file'
		return []
	else:
		originalFile = os.path.splitext(os.path.basename(commitfile))[0]
		sourceLang = html_translations[originalFile]
		pofile = os.path.join(settings.PODIRECTORY, commitfile)
		try:
			os.makedirs(os.path.join(settings.VCS_DIRECTORY, os.path.dirname(commitfile)))
		except os.error:
			pass
		copyfile(pofile, os.path.join(settings.VCS_DIRECTORY, commitfile))
		htmlfile = os.path.join(settings.PODIRECTORY, os.path.dirname(commitfile), originalFile)
		template = os.path.join(settings.VCS_DIRECTORY, commitfile.split('/')[0], sourceLang, originalFile)
		print 'Converting po to html: %s to %s' % (pofile, htmlfile)
		with open(pofile, 'r') as po, open(htmlfile, 'w') as html, open(template, 'r') as templ:
			po2html.converthtml(po, html, templ)
		print 'commit to %s' % htmlfile
		return [htmlfile]

def postcommit(updatedfile, success):
	print "*************** postcommit %s, %s" % (updatedfile, success)

def preupdate(updatedfile):
	print "*************** preupdate %s" % updatedfile
	originalFile = os.path.splitext(os.path.basename(updatedfile))[0]
	if '.html.pot' in updatedfile:
		sourceLang = html_translations[originalFile]
		htmlfile = os.path.join(updatedfile.split('/')[0], sourceLang, originalFile)
		print 'rewrite to %s' % htmlfile
		return htmlfile
	else:
		return updatedfile

def postupdate(updatedfile):
        print "*************** postupdate %s" % updatedfile
	originalFile = os.path.splitext(os.path.basename(updatedfile))[0]
	if '.html.pot' in updatedfile:
		sourceLang = html_translations[originalFile]
		potfile = os.path.join(settings.PODIRECTORY, updatedfile)
		htmlfile = os.path.join(settings.VCS_DIRECTORY, updatedfile.split('/')[0], sourceLang, originalFile)
		print 'Converting %s html to pot: %s to %s' % (sourceLang, htmlfile, potfile)
		with open(htmlfile, 'r') as html, open(potfile, 'w') as pot:
			html2po.converthtml(html, pot, None, pot=True)
		copyfile(potfile, os.path.join(settings.VCS_DIRECTORY, updatedfile))

def pretemplateupdate(updatedfile):
	print "*************** pretemplateupdate %s" % updatedfile
	if any(map(lambda (f,lang): f in updatedfile and lang in updatedfile, html_translations.items())):
		return False
	return True
