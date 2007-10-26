#!/usr/bin/python
# vim:fileencoding=UTF-8
# $Revision$, $Date$

import BaseHTTPServer, cgi, datetime, locale, os, poldek, re, rpm, sys, urllib

TYP_RPM = 0
TYP_POLDEK = 1
grupy = {}
pakiety = []
index_html = '''<html><head><title>RPM View</title></head><frameset cols="20%,80%"><frameset rows="30%,70%">
<frame src="/grupy" name="a" /><frame src="/gr?n=A" name="b" /></frameset><frame src="about:blank" name="c" /></frameset></html>'''

rpm_pattern = re.compile('^(.*)-(.*)-(.*)\.(.*)$')
poldek_pattern = re.compile('(.*);')

def compare(a, b):
	"Compare two packages by name."
	global TYP_RPM
	(pak1, napis1, typ1) = a
	(pak2, napis2, typ2) = b
	w = cmp(napis1, napis2)
	if w == 0:
		if typ1 == TYP_RPM:
			return 1
		else:
			return -1
	return w

def sort_and_uniq():
	"Sorts packages and remove duplicates."
	global pakiety
	pakiety.sort(compare)
	liczba = len(pakiety)
	lista = []
	for i in xrange(liczba - 2):
		(pkg, napis, typ) = pakiety[i]
		(pkg_next, napis_next, typ_next) = pakiety[i + 1]
		if (napis != napis_next):
			lista.append((pkg, napis, typ))
	pakiety = lista

def show_groups():
	"Show groups."
	global grupy
	html = '<a href="reload">Reload database</a><hr/>\nGroups<br/>\n<pre>\n<a href="gr?n=A" target="b">All</a>\n'
	nazwy = grupy.keys()
	nazwy.sort()
	for gr in nazwy:
		html += '<a href="gr?n=' + gr + '" target="b">' + gr + '</a>\n'
	return html

def show_packages(lista):
	"Show packages from given list."
	html = '<pre>\n'
	for (gr, napis, typ) in lista:
		html += '<a href="pkgs?n=' + urllib.quote(napis) + '" target="c">' + napis + '</a>\n'
	html += '</pre>\n'
	return html

def show_packages_from_group(name="A"):
	"Show packages from given group. A means all packages."
	global pakiety
	if name == "A":
		html = '<br/>All packages:<br/>\n'
		html += show_packages(pakiety)
	else:
		html = '<br/>Packages from group(' + name + '):<br/>\n'
		lista = [(gr, napis, typ) for (gr, napis, typ) in pakiety if gr == name]
		html += show_packages(lista)
	return html

def load_packages():
	"Load installed packages and from poldek's database."
	global grupy, pakiety, pak, pyl
	grupy = {}
	pakiety = []
	pak.load_packages()
	pyl.load_packages()
	sort_and_uniq()

class RPM_package:
	"Contains methods related to installed packages."
	def load_packages(self):
		"Load info about installed packages."
		global TYP_RPM, grupy, pakiety
		ts = rpm.TransactionSet()
		ts.openDB()
		for h in ts.dbMatch():
			gr = h[rpm.RPMTAG_GROUP]
			napis = "%s-%s-%s.%s" % (h[rpm.RPMTAG_NAME], h[rpm.RPMTAG_VERSION], h[rpm.RPMTAG_RELEASE], h[rpm.RPMTAG_ARCH])
			if grupy.has_key(gr):
				grupy[gr] += 1
			else:
				grupy[gr] = 1
			pakiety.append((gr, napis, TYP_RPM))
		ts.closeDB()

	def optional_tags(self, h, name, flags, version):
		"Helper function."
		html = ''
		ile = len(h[name])
		for i in xrange(ile):
			html += h[name][i] + ' '
			f = h[flags][i]
			if f & rpm.RPMSENSE_LESS:
				html += '<'
			if f & rpm.RPMSENSE_GREATER:
				html += '>'
			if f & rpm.RPMSENSE_EQUAL:
				html += '='
			html += ' ' + h[version][i] + '\n'
		return html

	def package_info(self, name):
		"Show info about an installed package with given name-version-release.arch ."
		global pakiety, rpm_pattern
		html = '<hr/>'
		m = rpm_pattern.search(name)
		if not m:
			return False
		n = m.group(1)
		ver = m.group(2)
		rel = m.group(3)
		arch = m.group(4)
		ts = rpm.TransactionSet()
		mi = ts.dbMatch('name', n)
		mi.pattern('version', rpm.RPMMIRE_DEFAULT, ver)
		mi.pattern('release', rpm.RPMMIRE_DEFAULT, rel)
		mi.pattern('arch', rpm.RPMMIRE_DEFAULT, arch)
		found = False
		for h in mi:
			found = True
			html += 'Package: ' + '%s-%s-%s.%s<br/>\n' % (h[rpm.RPMTAG_NAME], h[rpm.RPMTAG_VERSION], h[rpm.RPMTAG_RELEASE], h[rpm.RPMTAG_ARCH])
			if h[rpm.RPMTAG_EPOCH]:
				html += 'Epoch: %d<br/>\n' % (h[rpm.RPMTAG_EPOCH])
			html += 'Group: ' + h[rpm.RPMTAG_GROUP] + '<br/>\n'
			html += 'Size: %d<br/>\n' % h[rpm.RPMTAG_SIZE]
			if h[rpm.RPMTAG_URL]:
				html += 'URL: <a href="' + h[rpm.RPMTAG_URL] + '">' + h[rpm.RPMTAG_URL] + '</a><br/>\n'
			build_date = datetime.datetime.fromtimestamp(h[rpm.RPMTAG_BUILDTIME])
			html += 'Build time: ' + str(build_date) + '<br/>\n'
			if h[rpm.RPMTAG_INSTALLTIME]:
				install_date = datetime.datetime.fromtimestamp(h[rpm.RPMTAG_INSTALLTIME])
				html += 'Install time: ' + str(install_date) + '<br/>\n'
			html += 'Build host: ' + h[rpm.RPMTAG_BUILDHOST] + '<br/>\n'
			if h[rpm.RPMTAG_SOURCERPM]:
				html += "Source rpm: " + h[rpm.RPMTAG_SOURCERPM] + '<br/>\n'
			html += 'Summary: ' + h[rpm.RPMTAG_SUMMARY] + '<br/>\n'
			html += 'Description: <pre>' + h[rpm.RPMTAG_DESCRIPTION] + '</pre><hr/>\nProvides: <pre>'

			html += self.optional_tags(h, rpm.RPMTAG_PROVIDENAME, rpm.RPMTAG_PROVIDEFLAGS, rpm.RPMTAG_PROVIDEVERSION)

			html += '</pre><hr/>Requires: <pre>'
			html += self.optional_tags(h, rpm.RPMTAG_REQUIRENAME, rpm.RPMTAG_REQUIREFLAGS, rpm.RPMTAG_REQUIREVERSION)

			html += '</pre><hr/>Suggests: <pre>'
			html += self.optional_tags(h, rpm.RPMTAG_SUGGESTSNAME, rpm.RPMTAG_SUGGESTSFLAGS, rpm.RPMTAG_SUGGESTSVERSION)
			html += '</pre><hr/>Files: <pre>'
			for plik in h[rpm.RPMTAG_OLDFILENAMES]:
				html += plik + '\n'
			html += '</pre><hr/>Changelog:<br/><pre>\n'
			try:
				html += h[rpm.RPMTAG_CHANGELOGTEXT][0]
			except TypeError:
				pass
			html += '</pre><hr/>\n'
		if found:
			return html
		return False

class Pyldek:
	"Contains methods related to poldek's packages."
	def __init__(self):
		ctx = poldek.poldek_ctx()
		ctx.load_config()

		if not ctx.setup():
			raise RuntimeError, "poldek setup failed"

		self.ctx = ctx
		self.cctx = poldek.poclidek_ctx(ctx)

	def return_packages(self):
		cmd = self.cctx.rcmd()
		if cmd.execute("ls"):
			return cmd.packages

	def load_packages(self):
		"Load information about packages from poldek's database."
		global TYP_POLDEK, grupy, pakiety
		self.cctx.load_packages(self.cctx.LOAD_ALL)
		packages = self.return_packages()
		for pkg in packages:
			gr = pkg.group
			napis = "%s-%s-%s.%s" % (pkg.name, pkg.ver, pkg.rel, pkg.arch())
			if grupy.has_key(gr):
				grupy[gr] += 1
			else:
				grupy[gr] = 1
			pakiety.append((gr, napis, TYP_POLDEK))

	def package_info(self, name):
		"Show info about package given as name-version-release.arch ."
		html = '<hr/>'
		cmd = self.cctx.rcmd()
		command = "ls %s" % name
		if not cmd.execute(command):
			return html
		packages = cmd.packages
		for pkg in packages:
			inf = pkg.uinf()
			if not inf:
				continue
			html += 'Package: ' + '%s-%s-%s.%s<br/>\n' % (pkg.name, pkg.ver, pkg.rel, pkg.arch())
			if pkg.epoch:
				html += 'Epoch: %d<br/>\n' % (pkg.epoch)
			html += 'Group: ' + pkg.group + '<br/>\n'
			html += 'Size: %d<br/>\n' % pkg.size
			if inf.url:
				html += 'URL: <a href="' + inf.url + '">' + inf.url + '</a><br/>\n'
			build_date = datetime.datetime.fromtimestamp(pkg.btime)
			html += 'Build time: ' + str(build_date) + '<br/>\n'
			if pkg.itime:
				install_date = datetime.datetime.fromtimestamp(pkg.itime)
				html += 'Install time: ' + str(install_date) + '<br/>\n'
			html += 'Build host: ' + inf.buildhost + '<br/>\n'
#			if h[rpm.RPMTAG_SOURCERPM]:
#				html += "Source rpm: " + h[rpm.RPMTAG_SOURCERPM] + '<br/>\n'
			html += 'Summary: ' + inf.summary + '<br/>\n'
			html += 'Description: <pre>' + inf.description + '</pre><hr/>\nProvides: <pre>'

			for prov in pkg.provides:
				html += str(prov) + '\n'
			html += '</pre><hr/>Requires: <pre>'

			for req in pkg.requires:
				html += str(req) + '\n'

			html += '</pre><hr/>Suggests: <pre>'
			for sug in pkg.suggests:
				html += str(sug) + '\n'
			html += '</pre><hr/>Files: <pre>'
			if pkg.files:
				for (filename, filesize, filemode) in pkg.files:
					html += filename + '\n'
#			html += '</pre><hr/>Changelog:<br/><pre>\n'
#			try:
#				html += h[rpm.RPMTAG_CHANGELOGTEXT][0]
#			except TypeError:
#				pass
			html += '</pre><hr/>\n'
		return html



class Serwer(BaseHTTPServer.BaseHTTPRequestHandler):
	"Server WWW."
	def send_html(self, html):
		"Sends response."
		global content_type
		self.send_response(200)
		self.send_header('Content-Type', content_type)
		self.end_headers()
		self.wfile.write(html)

	def do_GET(self):
		"GET method handler."
		global pak, pyl, pakiety, grupy
		if self.path == '/':
			global index_html
			self.send_html(index_html)
		elif self.path == '/reload':
			load_packages()
			html = show_groups()
			self.send_html(html)
		elif self.path == '/grupy':
			html = show_groups()
			self.send_html(html)
		else:
			lista = cgi.parse_qsl(self.path)
			if len(lista) >= 1:
				(prefix, name) = lista[0]
				if prefix == '/gr?n':
					html = show_packages_from_group(name)	
					self.send_html(html)
				elif prefix == '/pkgs?n':
					global poldek_pattern
					html = pak.package_info(name)
					if not html:
						m = poldek_pattern.search(name)
						if m:
							html = pyl.package_info(m.group(1))
						else:
							html = pyl.package_info(name)
					self.send_html(html)
			else:
				self.send_error(404)

def run(server_class = BaseHTTPServer.HTTPServer, handler_class = Serwer, port = 9999):
	"Starts a http server."
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()


if __name__ == '__main__':
	locale.setlocale(locale.LC_ALL, '')
	content_type = 'text/html; charset=%s' % locale.nl_langinfo(locale.CODESET)
	pak = RPM_package()
	poldek.lib_init()
	pyl = Pyldek()
	load_packages()

	if len(sys.argv) > 1:
		p = int(sys.argv[1])
	else:
		p = 9999
	sys.stderr.write('Started on port %d\n' % p)
	run(port=p)
