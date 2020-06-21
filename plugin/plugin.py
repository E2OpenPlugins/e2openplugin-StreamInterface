from __future__ import print_function
from . import _
from Plugins.Plugin import PluginDescriptor
from twisted.internet import reactor
from twisted.web import resource, server 
from Screens.Screen import Screen
from Components.Sources.ServiceList import ServiceList
from Components.ConfigList import ConfigListScreen
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSubsection, ConfigSelection, getConfigListEntry, ConfigYesNo
from enigma import eServiceReference

config.plugins.streaminterface = ConfigSubsection()
config.plugins.streaminterface.enabled = ConfigYesNo(True)
config.plugins.streaminterface.port = ConfigInteger(default = 40080, limits=(1, 65535))
config.plugins.streaminterface.services = ConfigSelection([("0", _("both")), ("1", _("bouquets/services lists")), ("2", _("current service"))], default="0")

class StreamSetupScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="StreamSetupScreen" position="center,center" size="500,235" title="Setup StreamInterface">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="160,0" size="140,40" alphatest="on" />
			<widget name="red" position="10,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;17" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
			<widget name="green" position="160,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;17" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
			<widget name="config" position="10,50" size="480,80" scrollbarMode="showOnDemand"/>
			<widget name="help" position="10,130" size="480,105" zPosition="4" valign="center" halign="center" foregroundColor="yellow" font="Regular;18" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
		</screen>
		""" 
	def __init__(self, session):
		self.skin = StreamSetupScreen.skin
		self.setup_title = _("Setup StreamInterface")
		Screen.__init__(self, session)
		self["red"] = Button(_("Cancel"))
		self["green"] = Button(_("Save/OK"))
		self["help"] = Label("")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"], 
		{
			"ok": self.keyOk,
			"save": self.keyGreen,
			"cancel": self.keyRed,
		}, -2)
		
		ConfigListScreen.__init__(self, [])
		self.initConfig()
		self.newConfig()
		self.onClose.append(self.__closed)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __closed(self):
		pass

	def __layoutFinished(self):
		self.setTitle(self.setup_title)

	def initConfig(self):
		def getPrevValues(section):
			res = { }
			for (key, val) in section.content.items.items():
				if isinstance(val, ConfigSubsection):
					res[key] = getPrevValues(val)
				else:
					res[key] = val.value
			return res
		self.STR = config.plugins.streaminterface
		self.prev_values = getPrevValues(self.STR)
		self.cfg_enabled = getConfigListEntry(_("StreamInterface enabled"), self.STR.enabled)
		self.cfg_port = getConfigListEntry(_("Http port"), self.STR.port)
		self.cfg_services = getConfigListEntry(_("Type stream for services"), self.STR.services)

	def createSetup(self):
		list = [self.cfg_enabled]
		if self.STR.enabled.value:
			list.append(self.cfg_port)
			list.append(self.cfg_services)
		self["config"].list = list
		self["config"].l.setList(list)

	def newConfig(self):
		text = ""
		if self.STR.enabled.value:
			first_text = _("Open browser --> set url 'http://your-ip-box:port'")
			two_text = _("Create file any name.m3u --> write text 'http://your-ip-box:port/<current> or standby <current?tv|current?radio>'")
			if self.STR.services.value == "0":
				text = first_text + '\n' + two_text
			elif self.STR.services.value == "1":
				text = first_text
			elif self.STR.services.value == "2":
				text = two_text
		self["help"].setText(text)
		self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def keyOk(self):
		self.keyGreen()

	def keyRed(self):
		def setPrevValues(section, values):
			for (key, val) in section.content.items.items():
				value = values.get(key, None)
				if value is not None:
					if isinstance(val, ConfigSubsection):
						setPrevValues(val, value)
					else:
						val.value = value
		setPrevValues(self.STR, self.prev_values)
		self.keyGreen()

	def keyGreen(self):
		self.STR.save()
		self.close()

class BouquetList(resource.Resource):
	addSlash = True
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		s = '<br/>'
		if config.usage.multibouquet.value:
			bouquet_rootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
		else:
			from Screens.ChannelSelection import service_types_tv
			bouquet_rootstr = '%s FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'%(service_types_tv)
		fav = eServiceReference(bouquet_rootstr)
		services = ServiceList(fav, command_func = None, validate_commands = False)
		sub = services.getServicesAsList()
		if len(sub) > 0:
			self.putChild('channel', ChannelList())
			for (ref, name) in sub:
				s = s + '<p>'
				ref = ref.replace(' ', '%20').replace(':', '%3A').replace('"', '%22')
				s = s + '<a href="/channel?ref=' + ref + '">' + name + '</a>'
			req.setResponseCode(200)
			req.setHeader('Content-type', 'text/html');
			return s;
	def locateChild(self, request, segments):
		return resource.Resource.locateChild(self, request, segments)

class ChannelList(resource.Resource):
	addSlash = True
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		try:
			w1 = req.uri.split("?")[1]
			w2 = w1.split("&")
			parts = {}
			for i in w2:
					w3 = i.split("=")
					parts[w3[0]] = w3[1]
		except:
			req.setResponseCode(200);
			return "no ref given with ref=???"

		if "ref" in parts:
			s = '<br/>'
			ref = parts['ref'].replace('%20', ' ').replace('%3A', ':').replace('%22', '"')
			print(ref)
			fav = eServiceReference(ref)
			services = ServiceList(fav, command_func = None, validate_commands = False)
			sub = services.getServicesAsList()
			if len(sub) > 0:
				for (ref, name) in sub:
					s = s + '<p>'
					s = s + '<a href="http://%s:8001/%s" vod>%s</a>'%(req.host.host, ref, name)
				req.setResponseCode(200);
				req.setHeader('Content-type', 'text/html');
				return s;
		else:
			req.setResponseCode(200);
			return "no ref";

class CurrentService(resource.Resource):
	addSlash = True
	def __init__(self, session):
		resource.Resource.__init__(self)
		self.session = session

	def render(self, req):
		currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentService is not None:
			sref = currentService.toString()
		else:
			mode = "?radio" in req.uri.lower() and 'radio' or 'tv'
			sref = eval('config.%s.lastservice'%mode).value or "N/A"
		req.redirect("http://%s:8001/%s" % (req.getHost().host, sref))
		req.finish()
		return server.NOT_DONE_YET

def startServer(session):
	setup = config.plugins.streaminterface
	if setup.enabled.value:
		if setup.services.value == "0":
			list = BouquetList()
			channels = ChannelList()
			current = CurrentService(session)
			res = resource.Resource()
			res.putChild("", list)
			res.putChild("channel", channels) 
			res.putChild("current", current) 
		elif setup.services.value == "1":
			list = BouquetList()
			channels = ChannelList()
			res = resource.Resource()
			res.putChild("", list)
			res.putChild("channel", channels) 
		elif setup.services.value == "2":
			current = CurrentService(session)
			res = resource.Resource()
			res.putChild("current", current) 
		reactor.listenTCP(setup.port.value, server.Site(res))

def main(session, **kwargs):
	session.open(StreamSetupScreen)

def autostart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		try:
			startServer(kwargs["session"])
		except ImportError as e:
			print("[WebIf] twisted not available, not starting web services", e)

def Plugins(**kwargs):
 	return [
		PluginDescriptor(
			name=_("Setup StreamInterface"),
			description=_("Set port and type streaming"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon="stream.png",
			fnc=main),
		PluginDescriptor(
			where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART],
			fnc = autostart)]
