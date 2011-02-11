import re
from copy import copy
from datetime import timedelta
from PyQt4 import QtGui

_ctag_begin = re.compile(r'(?i)<c=(.*?)>')
_ctag_rgb = re.compile(r'\d+,\d+,\d+')
_urlre = re.compile(r"(?i)(http://[^\s<[]+)")
_memore = re.compile(r" (#[A-Za-z0-9_]+)")

def lexer(string, objlist):
    """objlist is a list: [(objecttype, re),...] list is in order of preference"""
    stringlist = [string]
    for (oType, regexp) in objlist:
        newstringlist = copy(stringlist)
        for (stri, s) in enumerate(stringlist):
            tmp = []
            lasti = 0
            for m in regexp.finditer(string):
                start = m.start()
                end = m.end()
                tag = oType(group(0), *groups())
                tmp.append(string[lasti:start])
                tmp.append(tag)
            if lasti < len(string):
                tmp.append(string[lasti:])
            stringlist = stringlist[0:stri]+tmp+stringlist[stri+1:]
        stringlist = copy(newstringlist)
    return stringlist

def convertTags(string, format="html"):
    if format not in ["html", "bbcode", "ctag"]:
        raise ValueError("Color format not recognized")
    def colorrepfunc(matchobj):
        color = matchobj.group(1)
        if _ctag_rgb.match(color) is not None:
            if format=='ctag':
                return "<c=%s>" % (color)
            try:
                qc = QtGui.QColor(*[int(c) for c in color.split(",")])
            except ValueError:
                qc = QtGui.QColor("black")
        else:
            qc = QtGui.QColor(color)
        if not qc.isValid():
            qc = QtGui.QColor("black")
        if format == "html":
            return '<span style="color:%s">' % (qc.name())
        elif format == "bbcode":
            return '[color=%s]' % (qc.name())
        elif format == "ctag":
            (r,g,b,a) = qc.getRgb()
            return '<c=%s,%s,%s>' % (r,g,b)
    string = _ctag_begin.sub(colorrepfunc, string)
    endtag = {"html": "</span>", "bbcode": "[/color]", "ctag": "</c>"}
    string = string.replace("</c>", endtag[format])
    def urlrep(matchobj):
        if format=="html":
            return "<a href='%s'>%s</a>" % (matchobj.group(1).replace("&amp;", "&"), matchobj.group(1))
        elif format=="bbcode":
            return "[url]%s[/url]" % (matchobj.group(1).replace("&amp;", "&"))
        elif format=="ctag":
            return matchobj.group(1)
    string = _urlre.sub(urlrep, string)
    if format == "html":
        string = _memore.sub(r" <a href='\1'>\1</a>", string)
        for (code, f) in smiledict.iteritems():
            string = string.replace(" %s" % (code), " <img src='smilies/%s' />" % (f))
    return string

def escapeBrackets(string):
    class beginTag(object):
        def __init__(self, tag):
            self.tag = tag
    class endTag(object):
        pass
    newlist = []
    begintagpos = [(m.start(), m.end()) for m in _ctag_begin.finditer(string)]
    lasti = 0
    for (s, e) in begintagpos:
        newlist.append(string[lasti:s])
        newlist.append(beginTag(string[s:e]))
        lasti = e
    if lasti < len(string):
        newlist.append(string[lasti:])
    tmp = []
    for o in newlist:
        if type(o) is not beginTag:
            l = o.split("</c>")
            tmp.append(l[0])
            l = l[1:]
            for item in l:
                tmp.append(endTag())
                tmp.append(item)
        else:
            tmp.append(o)
    btlen = 0
    etlen = 0
    retval = ""
    newlist = tmp
    for o in newlist:
        if type(o) is beginTag:
            retval += o.tag.replace("&", "&amp;")
            btlen +=1
        elif type(o) is endTag:
            if etlen >= btlen:
                continue
            else:
                retval += "</c>"
                etlen += 1
        else:
            retval += o.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if btlen > etlen:
        for i in range(0, btlen-etlen):
            retval += "</c>"
    return retval

def addTimeInitial(string, grammar):
    endofi = string.find(":")
    endoftag = string.find(">")
    if endoftag < 0 or endoftag > 16 or endofi > 17:
        return string
    return string[0:endoftag+1]+grammar.pcf+string[endoftag+1:endofi]+grammar.number+string[endofi:]

def timeProtocol(cmd):
    dir = cmd[0]
    cmd = cmd[1:]
    cmd = re.sub("[^0-9:]", "", cmd)
    try:
        l = [int(x) for x in cmd.split(":")]
    except ValueError:
        l = [0,0]
    timed = timedelta(0, l[0]*3600+l[1]*60)
    if dir == "P":
        timed = timed*-1
    return timed

def timeDifference(td):
    if td < timedelta(0):
        when = "AGO"
    else:
        when = "FROM NOW"
    atd = abs(td)
    minutes = (atd.days*86400 + atd.seconds) // 60
    hours = minutes // 60
    leftoverminutes = minutes % 60
    if atd == timedelta(0):
        timetext = "RIGHT NOW"
    elif atd < timedelta(0,3600):
        if minutes == 1:
            timetext = "%d MINUTE %s" % (minutes, when)
        else: 
            timetext = "%d MINUTES %s" % (minutes, when)
    elif atd < timedelta(0,3600*100):
        if hours == 1 and leftoverminutes == 0:
            timetext = "%d:%02d HOUR %s" % (hours, leftoverminutes, when)
        else:
            timetext = "%d:%02d HOURS %s" % (hours, leftoverminutes, when)
    else:
        timetext = "%d HOURS %s" % (hours, when)
    return timetext


smiledict = {
    ":rancorous:": "pc_rancorous.gif",  
    ":apple:": "apple.gif",
    ":bathearst:" "bathearst.gif"
    ":pleasant:": "pc_pleasant.gif",
    ":blueghost:": "blueslimer.gif",
    ":candycorn:": "candycorn.gif",
    ":cheer:": "cheer.gif", 
    ":duhjohn:": "confusedjohn.gif",
    ":datrump:": "datrump.gif",
    ":facepalm:": "facepalm.gif",
    ":bonk:": "headbonk.gif",
    ":mspa:": "mspa_face.gif",
    ":gun:": "mspa_reader.gif",
    ":cal:": "lilcal.png",
    ":amazedfirman:": "pc_amazedfirman.gif",
    ":amazed:": "pc_amazed.gif",
    ":chummy:": "pc_chummy.gif",
    ":cool:": "pccool.gif",
    ":smooth:": "pccool.gif",
    ":distraughtfirman": "pc_distraughtfirman.gif",
    ":distraught:": "pc_distraught.gif",
    ":insolent:": "pc_insolent.gif",
    ":3:": "pckitty.gif",
    ":mystified:": "pc_mystified.gif",
    ":pranky:": "pc_pranky.gif",
    ":tense:": "pc_tense.gif",
    ":record:": "record.gif",
    ":squiddle:": "squiddle.gif",
    ":tab:": "tab.gif",
    ":beetip:": "theprofessor.gif",
    ":flipout:": "weasel.gif",
    ":befuddled:": "what.gif",
    ":pumpkin:": "whatpumpkin.gif",
    ":trollcool:": "trollcool.gif"}