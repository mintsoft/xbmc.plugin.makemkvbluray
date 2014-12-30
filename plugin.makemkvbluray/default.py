import xbmc, xbmcgui, subprocess, os, time, sys, urllib, re
import xbmcplugin, xbmcaddon

# Shared resources
BASE_RESOURCE_PATH = os.path.join( os.getcwd(), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

  
__scriptname__ = "MakeMKV BluRay Watch Plugin"
__scriptID__      = "plugin.makemkvbluray"
__author__ = "Magnetism"
__url__ = "http://bultsblog.com/arne"
__credits__ = ""
__version__ = "0.1"
__addon__ = xbmcaddon.Addon(__scriptID__)

__language__ = __addon__.getLocalizedString
_ = sys.modules[ "__main__" ].__language__

import settings, file, mkvparser, brlog

_log = brlog.BrLog()

_log.info('Starting the BluRay script') #@UndefinedVariable

class BluRayStarter:
  def __init__(self):
    _log.info('Staring') #@UndefinedVariable
    self.settings = settings.BluRaySettings()

  def killAndStart(self, mkvStart):
    if self.settings.local:
      _log.info('Running makemkvcon locally') #@UndefinedVariable
      self.killMkv()
      # Determine if we're doing the disc or if we're browsing..
      _log.info(mkvStart) #@UndefinedVariable
      return subprocess.Popen(mkvStart, shell=True)
    else:
      _log.info('connecting to remote stream, returning fake file browse class..') #@UndefinedVariable
      return file.FakeFile()

  def killMkv(self):
    # Linux
    try :
      _log.info('attempting linux kill of makemkvcon') #@UndefinedVariable
      subprocess.call('killall -9 makemkvcon', shell=True)
      _log.info('Linux call successful') #@UndefinedVariable
    except:
      pass

    #Windows.
    try :
      _log.info('attempting windows kill of makemkvcon') #@UndefinedVariable
      subprocess.call('taskkill /F /IM makemkvcon.exe', shell=True)
      _log.info('Windows call successful') #@UndefinedVariable
    except:
      pass

  def browse(self, url) :
    _log.info('starting browser handler') #@UndefinedVariable
    h = mkvparser.BrowseHandler()
    h.start(url)
    for k,v in h.titleMap.iteritems() : #@UnusedVariable
      self.addLink("%s %s, %s %s" %(_(50005), v['duration'], _(50006), v['chaptercount']),v['file'])


  def getMainFeatureTitle(self, url):
    h = mkvparser.BrowseHandler()
    h.start(url)
    # Play the longest feature on the disc:
    largest = 0
    largestTitle = ''
    for k,v in h.titleMap.iteritems() : #@UnusedVariable
      m = re.search('(\d+):(\d+):(\d+)', v['duration'])
      length = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
      if length > largest :
        largest = length
        largestTitle = v['file']
    _log.info('largest: %d, %s' %(largest,largestTitle))
    return largestTitle

  def handleListing(self):
    mode = self.settings.paramMode
    _log.info( 'mode: ' + str(mode))
    if mode ==None:
      _log.info('Showing categories')
      self.CATEGORIES()
      _log.info('Showing categories done')
#      _log.info(__addon__.)
      xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
    if mode == 1 :
        _log.info( 'Entering Disc mode')
        mystarter = BluRayStarter()
        mkvStart = '"%s" stream disc:0' %(mystarter.settings.mkvLocation)
        mystarter.process(mkvStart)
    elif mode == 3 :
        _log.info( 'Entering Remote mode')
        mystarter = BluRayStarter()
        mystarter.process('')
    elif mode == 2:
      _log.info( 'Entering Browse mode')
      d = xbmcgui.Dialog() #@UndefinedVariable
      choice = d.browse(1, 'Select folder', 'video', 'index.bdmv|.iso|.isoRenamedMeansSkip!|.MDS|.CUE|.CDI|.CCD', False, False, '')
      if choice <> '':
        mystarter = BluRayStarter()
        mkvStart = "jjrkr3i3oqwjelrkjewlwrj"
        type = ''
        if re.search("BDMV.index.bdmv", choice) :
          # Treat as file
          type = 'file'
          choice = choice[:-15]
        elif re.search("BDMV.MovieObject.bdmv", choice) :
          # Treat as file
          type = 'file'
          choice = choice[:-21]
        else:
          # Treat as iso
          type = 'iso'
        
        # Check if the file is reachable through the filesystem, to prevent errors with smb:// shares etc.
        if not os.path.exists(choice) :
          self.message(_(50073))
        mkvStart = '"%s" stream %s:%s' %(mystarter.settings.mkvLocation, type, choice)
        
        mystarter.process(mkvStart)
    
    if mode == 20:
      self.settings.showSettings()

  def process(self, mkvLocation):
    _log.info(mkvLocation)
    timeSlept = 0
    self.pDialog = xbmcgui.DialogProgress() #@UndefinedVariable
    self.pDialog.create('XBMC', _(50050), _(50051))
    try :
      tst = self.killAndStart(mkvLocation)
      self.pDialog.update(2, 'XBMC', _(50052), _(50056))
      ready = False
      while True:   
        try:
          urllib.urlretrieve(self.settings.rootURL)
          ready = True
          break;
        except IOError:
          pass
        if self.pDialog.iscanceled():
          break
        if tst.poll() :
          if tst.returncode != 0 :
            self.message(_(50070))
            break
        time.sleep(1)
        timeSlept = timeSlept + 1
        perc = (timeSlept * 100) / self.settings.waitTimeOut
        self.pDialog.update(perc)
        if timeSlept > self.settings.waitTimeOut :
          break
        
      if ready:
        _log.info( 'Stream ready. ')
        # the Stream has started, start auto playback?
        if self.settings.autoPlay:
          _log.info( 'Autoplay selected')
          title = self.getMainFeatureTitle(self.settings.rootURL)
          _log.info( 'Main feature determined to be : ' + title)
          opener = urllib.URLopener()
          testfile = ''
          try:
            testfile = title
            opener.open(testfile)
          except IOError:
            testfile = ''

          del opener

          if testfile<>'':
              _log.info( 'Playing file ' + testfile)
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = testfile)) #@UndefinedVariable
          else:
            self.message(_(50071))
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem()) #@UndefinedVariable

        else:
          # Add the selections as selectable files.
          self.browse(self.settings.rootURL)
          xbmcplugin.endOfDirectory(int(sys.argv[1])) #@UndefinedVariable


    except :
        self.message(_(50072))
        self.pDialog.close()
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem()) #@UndefinedVariable
        raise
    else :
        self.pDialog.close()


  def CATEGORIES(self):
    # Disc
    if self.settings.enableDisc:
      self.addDir(_(50061),1, True)
      self.addDir(_(50062),1, False)
    # Filelocation
    if self.settings.enableFile:
      self.addDir(_(50063),2, True)
      self.addDir(_(50064),2, False)
    # Remote
    if self.settings.enableRemote:
      self.addDir(_(50065),3, True)
      self.addDir(_(50066),3, False)
    self.addDir(_(50060),20, True, False)                     
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


  def addDir(self, name,mode, autoplay, isPlayable = True):
    u=sys.argv[0]+"?mode="+str(mode)+"&autoplay="+urllib.quote_plus(str(autoplay))
    _log.info(u)
    icon = "DefaultVideoPlaylists.png"
    if autoplay:
      icon= "DefaultVideo.png"
    liz=xbmcgui.ListItem(name, iconImage=icon, thumbnailImage='')
    if autoplay and isPlayable:
      liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    _log.info(name)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz, isFolder= not autoplay)
    
  
  def addLink(self, name,url):
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage='') #@UndefinedVariable
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty("IsPlayable" , "true")
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz) #@UndefinedVariable

  def message(self, messageText):
    dialog = xbmcgui.Dialog() #@UndefinedVariable
    dialog.ok("Info", messageText)


mydisplay = BluRayStarter()
mydisplay.handleListing()
