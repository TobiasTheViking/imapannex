#!/usr/bin/env python2
import os
import re
import sys
import json
import time
import imaplib
#import email
from email import message_from_string
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import Encoders

conf = False
version = "0.1.0"
plugin = "imapannex-" + version

pwd = os.path.dirname(__file__)
if not pwd:
    pwd = os.getcwd()
sys.path.append(pwd + '/lib')

if "--dbglevel" in sys.argv:
    dbglevel = int(sys.argv[sys.argv.index("--dbglevel") + 1])
else:
    dbglevel = 0

import CommonFunctions as common

imap = False

def login():
    common.log("")
    global imap
    if conf["imap-ssl"].find("SSL/TLS") > -1:
        common.log("Connecting to %s with SSL" % conf["imap-host"])
        imap = imaplib.IMAP4_SSL(conf["imap-host"], int(conf["imap-port"]))
    else:
        common.log("Connecting to %s without SSL" % conf["imap-host"])
        imap = imaplib.IMAP4(conf["imap-host"], int(conf["imap-port"]))

    imap.login(conf["imap-username"], conf["imap-password"])

    common.log("res: " + repr(imap), 2)
    if imap:
        common.log("Done")
    else:
        common.log("Failure")
        sys.exit(1)

def postFile(subject, filename, folder):
    common.log("%s to %s - %s" % ( filename, folder[0], subject))
    
    msg_id = findInFolder(subject, folder)
    if msg_id:
        common.log("File already exists: " + repr(msg_id))
        return True

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = folder
    #msg.attach(MIMEText("body", 'plain'))

    part = MIMEBase('application', "octet-stream")
    part.set_payload( readFile(filename, "rb") )
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filename))
    msg.attach(part)

    res = imap.append(conf["folder"], "", time.time(), msg.as_string())

    if res:
        common.log("Done: " + repr(res))
    else:
        sys.exit(1)

def findFolder(subject):
    common.log(repr(subject), 0)

    typ, data = imap.list()
    common.log("List: " + repr(data),3 )
    typ, bla = imap.select()
    common.log("Select: " + repr(bla), 3)

    for item in data: # Search for folders
        if not item:
            continue
        item = item.split('"')
        if len(item) > 1 and item[0] != "0":
            item = item[3].decode("ascii").strip()
            common.log("name: " + repr(item) + " - " + repr(subject), 3)
            if item.find("/") > -1:
                item = item[item.rfind("/") + 1:]

            if item == subject:
                common.log("Done, found folder: " + repr(item))
                return item
    common.log("Failure")
    return False

def findInFolder(subject, sender):
    common.log("%s - %s" % (repr(subject), type(subject), ), 0)

    typ, data = imap.list(conf["folder"])
    common.log("List: " + repr(data), 2)
    typ, bla = imap.select(conf["folder"])
    common.log("Select: " + repr(bla), 2)

    typ, bla = imap.search(None, '(FROM "' + sender + '")')
    common.log("Search: " + repr(bla), 1)
    if bla != ['']:
        try:
            resp, data = imap.fetch(bla[0].replace(" ", ","), '(BODY[HEADER.FIELDS (SUBJECT)])')
            common.log("Fetch: " + repr(resp) + " - " + repr(data), 1)
        except Exception as e:
            common.log("Exception: " + repr(e))
            data = []
                
        for item in data: # Searches for messages
            if len(item) > 1 and item[0] != "0":
                tsub = re.compile("Subject: (.*?)\r\n\r\n").findall(item[1])
                common.log("name2: " + repr(tsub) + " - " + repr(subject), 2)
                if len(tsub) and tsub[0].strip() == subject:
                    msgid = item[0]
                    msgid = msgid[:msgid.find(" ")]
                    common.log("Done, found message: " + repr(msgid))
                    return msgid

    common.log("Failure")
    return False

def checkFile(subject, folder):
    common.log(subject)
    global m

    msg_id = findInFolder(subject, folder)
    if msg_id:
        common.log("Found: " + repr(msg_id))
        print(subject)
    else:
        common.log("Failure")

def getFile(subject, filename, folder):
    common.log(subject)

    msg_id = findInFolder(subject, folder)
    if msg_id:
        common.log("msg_id: " + repr(msg_id))
        resp, content = imap.fetch(msg_id, "(RFC822)")
        mail = message_from_string(content[0][1])

        for part in mail.walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue

            saveFile(filename, part.get_payload(decode=True), "wb")
            common.log("Done")
            return True
    common.log("Failure")

def deleteFile(subject, folder):
    common.log(subject)
    global m

    msg_id = findInFolder(subject, folder)

    #typ, data = imap.search(None, 'ALL')
    #for num in data[0].split():
    common.log("msg_id: " + repr(msg_id))
    if msg_id:
        res = imap.store(msg_id[0], '+FLAGS', '\\Deleted')
        imap.expunge()
        common.log("Done")
        return True
    common.log("Failure")

def readFile(fname, flags="r"):
    common.log(repr(fname) + " - " + repr(flags))

    if not os.path.exists(fname):
        common.log("File doesn't exist")
        return False
    d = ""
    try:
        t = open(fname, flags)
        d = t.read()
        t.close()
    except Exception as e:
        common.log("Exception: " + repr(e), -1)

    common.log("Done")
    return d

def saveFile(fname, content, flags="w"):
    common.log(fname + " - " + str(len(content)) + " - " + repr(flags))
    t = open(fname, flags)
    t.write(content)
    t.close()
    common.log("Done")

def createFolder(path="", folder=""):
    common.log(repr(path) + " - " + repr(folder))
    if len(path):
        res = imap.create(path + "/" + folder)
        common.log("Done: "+ repr(res))
        return path + "/" + folder
    else:
        res = imap.create(folder)
        common.log("Done: "+ repr(res))
        return folder

def main():
    global conf
    args = sys.argv

    ANNEX_ACTION = os.getenv("ANNEX_ACTION")
    ANNEX_KEY = os.getenv("ANNEX_KEY")
    ANNEX_HASH_1 = os.getenv("ANNEX_HASH_1")
    ANNEX_HASH_2 = os.getenv("ANNEX_HASH_2")
    ANNEX_FILE = os.getenv("ANNEX_FILE")
    envargs = []
    if ANNEX_ACTION:
        envargs += ["ANNEX_ACTION=" + ANNEX_ACTION]
    if ANNEX_KEY:
        envargs += ["ANNEX_KEY=" + ANNEX_KEY]
    if ANNEX_HASH_1:
        envargs += ["ANNEX_HASH_1=" + ANNEX_HASH_1]
    if ANNEX_HASH_2:
        envargs += ["ANNEX_HASH_2=" + ANNEX_HASH_2]
    if ANNEX_FILE:
        envargs += ["ANNEX_FILE=" + ANNEX_FILE]
    common.log("ARGS: " + repr(" ".join(envargs + args)))

    conf = readFile(pwd + "/imapannex.conf")
    try:
        conf = json.loads(conf)
    except Exception as e:
        common.log("Traceback EXCEPTION: " + repr(e))
        common.log("Couldn't parse conf: " + repr(conf))
        conf = {"folder": "gitannex"}

    if "imap-username" not in conf:
        conf["imap-username"] = raw_input("Please enter your imap username: ")
        common.log("e-mail set to: " + conf["imap-username"])
        changed = True

    if "imap-password" not in conf:
        conf["imap-password"] = raw_input("Please enter your imap password: ")
        common.log("password set to: " + conf["imap-password"], 3)
        changed = True

    if "imap-method" not in conf:
        conf["imap-method"] = raw_input("Please enter your imap authentication method: ")
        common.log("method set to: " + conf["imap-method"], 3)
        changed = True

    if "imap-host" not in conf:
        conf["imap-host"] = raw_input("Please enter your imap host: ")
        common.log("host set to: " + conf["imap-host"], 3)
        changed = True

    if "imap-port" not in conf:
        conf["imap-port"] = raw_input("Please enter your imap port: ")
        common.log("port set to: " + conf["imap-port"], 3)
        changed = True

    if "imap-ssl" not in conf:
        conf["imap-ssl"] = raw_input("Please enter your imap ssl: ")
        common.log("ssl set to: " + conf["imap-ssl"], 3)
        changed = True

    common.log("Conf: " + repr(conf), 2)

    login()
    
    folder = findFolder(conf["folder"])
    if folder:
        common.log("Using folder: " + repr(folder))
        ANNEX_FOLDER = folder
    else:
        folder = createFolder(folder=conf["folder"])
        common.log("created folder0: " + repr(folder))
        ANNEX_FOLDER = folder

    if ANNEX_HASH_1:
        ANNEX_FOLDER += "/" + ANNEX_HASH_1

    if ANNEX_HASH_2:
        ANNEX_FOLDER += "/" + ANNEX_HASH_2

    if "store" == ANNEX_ACTION:
        postFile(ANNEX_KEY, ANNEX_FILE, ANNEX_FOLDER)
    elif "checkpresent" == ANNEX_ACTION:
        checkFile(ANNEX_KEY, ANNEX_FOLDER)
    elif "retrieve" == ANNEX_ACTION:
        getFile(ANNEX_KEY, ANNEX_FILE, ANNEX_FOLDER)
    elif "remove" == ANNEX_ACTION:
        deleteFile(ANNEX_KEY, ANNEX_FOLDER)
    else:
        setup = '''
Please run the following commands in your annex directory:

git config annex.imap-hook '/usr/bin/python2 %s/imapannex.py'
git annex initremote imap type=hook hooktype=imap encryption=%s
git annex describe imap "the imap library"
git annex content imap exclude=largerthan=30mb
''' % (os.getcwd(), "shared")
        print setup

        saveFile(pwd + "/imapannex.conf", json.dumps(conf))
        sys.exit(1)

t = time.time()
common.log("START")
if __name__ == '__main__':
    main()
common.log("STOP: %ss" % int(time.time() - t))
