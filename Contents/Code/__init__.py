import re

###################################################################################################

PLUGIN_TITLE               = 'AVForums'
PLUGIN_PREFIX              = '/video/avforums'

YT_USER                    = 'AVForumsTV'
YT_API_UPLOADS             = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?orderby=published&start-index=%%d&max-results=%%d&v=2'
YT_API_PLAYLISTS           = 'http://gdata.youtube.com/feeds/api/users/%s/playlists?start-index=%d&max-results=%d&v=2'
YT_API_PLAYLIST            = 'http://gdata.youtube.com/feeds/api/playlists/%s?start-index=%%d&max-results=%%d&v=2'
YT_API_SEARCH              = 'http://gdata.youtube.com/feeds/api/videos?q=%s&author=%s&orderby=relevance&start-index%%d&max-results=%%d&v=2'

YT_VIDEO_PAGE              = 'http://www.youtube.com/watch?v=%s'
YT_GET_VIDEO_URL           = 'http://www.youtube.com/get_video?video_id=%s&t=%s&fmt=%d&asv=3'

# Namespaces
YT_NS                      = {'atom':'http://www.w3.org/2005/Atom','app':'http://www.w3.org/2007/app', 'openSearch':'http://a9.com/-/spec/opensearch/1.1/', 'gd':'http://schemas.google.com/g/2005', 'yt':'http://gdata.youtube.com/schemas/2007', 'media':'http://search.yahoo.com/mrss/'}

YT_VIDEO_FORMATS           = [L('STANDARD'), L('MEDIUM'), L('HIGH'), L('HD720P'), L('HD1080P')]
YT_FMT                     = [34, 18, 35, 22, 37]

# Default artwork and icon(s)
PLUGIN_ARTWORK             = 'art-default.png'
PLUGIN_ICON_DEFAULT        = 'icon-default.png'
PLUGIN_ICON_SEARCH         = 'icon-search.png'
PLUGIN_ICON_PREFS          = 'icon-prefs.png'

###################################################################################################

def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)

  Plugin.AddViewGroup('_List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('_InfoList', viewMode='InfoList', mediaType='items')

  # Set the default MediaContainer attributes
  MediaContainer.title1    = PLUGIN_TITLE
  MediaContainer.viewGroup = '_InfoList'
  MediaContainer.art       = R(PLUGIN_ARTWORK)
  MediaContainer.userAgent = ''

  # Set the default cache time
  HTTP.SetCacheTime(CACHE_1HOUR)
  HTTP.SetHeader('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6')

###################################################################################################

def CreatePrefs():
  Prefs.Add(id='ytfmt', type='enum', default=YT_VIDEO_FORMATS[-1], label=L('YTMAXQUALITY'), values=YT_VIDEO_FORMATS)

###################################################################################################

def MainMenu():
  dir = MediaContainer(viewGroup='_List')
  dir.Append(Function(DirectoryItem(YtUploads, title=L('UPLOADS'), thumb=R(PLUGIN_ICON_DEFAULT))))
  dir.Append(Function(DirectoryItem(YtPlaylists, title=L('PLAYLISTS'), thumb=R(PLUGIN_ICON_DEFAULT))))
  dir.Append(Function(InputDirectoryItem(YtVideoSearch, title=L('SEARCH'), prompt=L('SEARCH'), thumb=R(PLUGIN_ICON_SEARCH))))
  dir.Append(PrefsItem(L('PREFERENCES'), thumb=R(PLUGIN_ICON_PREFS)))
  return dir

###################################################################################################

def YtUploads(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  videos = GetYtVideos(YT_API_UPLOADS % (YT_USER), loopNext=False)

  for v in videos:
    title, summary, thumb, duration, date, videoId, rating, views = v
    dir.Append(Function(VideoItem(YtPlayVideo, title=title, subtitle=date + ' - ' + views + ' ' + L('VIEWS'), summary=summary, rating=rating, duration=int(duration)*1000, thumb=Function(GetThumb, url=thumb)), videoId=videoId))

  return dir

###################################################################################################

def YtPlaylists(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  playlists = GetYtPlaylists(YT_USER)

  for p in playlists:
    title, summary, count, playlistId = p
    dir.Append(Function(DirectoryItem(YtPlaylist, title=title, summary=summary, infoLabel=str(count) + ' ' + L('VIDEOS'), thumb=R(PLUGIN_ICON_DEFAULT)), playlistId=playlistId))

  return dir

###################################################################################################

def GetYtPlaylists(ytUser, startIndex=1, maxResults=50):
  playlists = []
  feed = XML.ElementFromURL(YT_API_PLAYLISTS % (ytUser, startIndex, maxResults), errors='ignore')
  ytPlaylists = feed.xpath('/atom:feed/atom:entry', namespaces=YT_NS)

  for p in ytPlaylists:
    title = p.xpath('./atom:title', namespaces=YT_NS)[0].text.strip()
    try:
      summary = p.xpath('./atom:summary', namespaces=YT_NS)[0].text.strip()
    except:
      summary = ''
    count = p.xpath('./yt:countHint', namespaces=YT_NS)[0].text
    playlistId = p.xpath('./yt:playlistId', namespaces=YT_NS)[0].text
    playlists.append([title, summary, count, playlistId])

  if len(feed.xpath('./atom:link[@rel="next"]', namespaces=YT_NS)) > 0:
    playlists.extend( GetYtPlaylists(ytUser, startIndex=startIndex+maxResults) )

  return playlists

###################################################################################################

def YtPlaylist(sender, playlistId):
  dir = MediaContainer(title2=sender.itemTitle)
  videos = GetYtVideos(YT_API_PLAYLIST % playlistId)

  for v in videos:
    title, summary, thumb, duration, date, videoId, rating, views = v
    dir.Append(Function(VideoItem(YtPlayVideo, title=title, subtitle=date + ' - ' + views + ' ' + L('VIEWS'), summary=summary, rating=rating, duration=int(duration)*1000, thumb=Function(GetThumb, url=thumb)), videoId=videoId))

  return dir

###################################################################################################

def YtVideoSearch(sender, query):
  dir = MediaContainer(title2=sender.itemTitle)
  videos = GetYtVideos( YT_API_SEARCH % (String.Quote(query, usePlus=True), YT_USER), loopNext=False, maxResults=20 )

  for v in videos:
    title, summary, thumb, duration, date, videoId, rating, views = v
    dir.Append(Function(VideoItem(YtPlayVideo, title=title, subtitle=date + ' - ' + views + ' ' + L('VIEWS'), summary=summary, rating=rating, duration=int(duration)*1000, thumb=Function(GetThumb, url=thumb)), videoId=videoId))

  return dir

###################################################################################################

def GetYtVideos(feedUrl, loopNext=True, startIndex=1, maxResults=50):
  videos = []
  feed = XML.ElementFromURL(feedUrl % (startIndex, maxResults), errors='ignore')
  ytVideos = feed.xpath('/atom:feed/atom:entry', namespaces=YT_NS)

  for v in ytVideos:
    appControlState = ''

    if len( v.xpath('./app:control/yt:state', namespaces=YT_NS) ) > 0:
      appControlState = v.xpath('./app:control/yt:state', namespaces=YT_NS)[0].get('name')

    if appControlState != 'restricted':
      title = v.xpath('./atom:title', namespaces=YT_NS)[0].text.strip()

      if len( v.xpath('./media:group/media:description', namespaces=YT_NS) ) > 0 and v.xpath('./media:group/media:description', namespaces=YT_NS)[0].text != None:
        summary = v.xpath('./media:group/media:description', namespaces=YT_NS)[0].text.strip()
      else:
        summary = ''

      thumb = v.xpath('./media:group/media:thumbnail[contains(@url, "hqdefault")]', namespaces=YT_NS)[0].get('url')
      duration = v.xpath('./media:group/yt:duration', namespaces=YT_NS)[0].get('seconds')
      datetime = v.xpath('./media:group/yt:uploaded', namespaces=YT_NS)[0].text
      date = Datetime.ParseDate(datetime).strftime('%d-%m-%Y')
      videoId = v.xpath('./media:group/yt:videoid', namespaces=YT_NS)[0].text

      if len( v.xpath('./gd:rating', namespaces=YT_NS) ) > 0:
        ratingAverage = v.xpath('./gd:rating', namespaces=YT_NS)[0].get('average')
        ratingMax = v.xpath('./gd:rating', namespaces=YT_NS)[0].get('max')
        rating = (10 / float(ratingMax)) * float(ratingAverage) # Convert YouTube rating (0-5) to Plex rating (0-10)
      else:
        rating = None

      views = v.xpath('./yt:statistics', namespaces=YT_NS)[0].get('viewCount')
      videos.append([title, summary, thumb, duration, date, videoId, rating, views])

  if len(feed.xpath('./atom:link[@rel="next"]', namespaces=YT_NS)) > 0 and loopNext == True:
    videos.extend( GetYtVideos(feedUrl, startIndex=startIndex+maxResults) )

  return videos

###################################################################################################

def YtPlayVideo(sender, videoId):
  ytPage = HTTP.Request(YT_VIDEO_PAGE % videoId, cacheTime=1)
  
  ytPage = str(ytPage)
  t = re.findall('&t=([^&]+)', ytPage)[0]
  fmt_list = re.findall('&fmt_list=([^&]+)', ytPage)[0]
  fmt_list = String.Unquote(fmt_list, usePlus=False)
  fmts = re.findall('([0-9]+)[^,]*', fmt_list)

  index = YT_VIDEO_FORMATS.index( Prefs.Get('ytfmt') )
  if YT_FMT[index] in fmts:
    fmt = YT_FMT[index]
  else:
    for i in range(index, -1, -1):
      if str(YT_FMT[i]) in fmts:
        fmt = YT_FMT[i]
        break
      else:
        fmt = 5

  url = YT_GET_VIDEO_URL % (videoId, t, fmt)
#  Log(url)
  return Redirect(url)

###################################################################################################

def GetThumb(url):
  data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
  if data:
    return DataObject(data, 'image/jpeg')
  else:
    return Redirect(R(PLUGIN_ICON_DEFAULT))
