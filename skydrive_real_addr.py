#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
#------------------------------------------------------------------------------

Version : v2012-01-19
Author  : crifan
Mail    : green-waste (at) 163.com

[Function]
extrat the real addr for files in skydrive [and download them]
you can find output info in outputed extractedSkydriveInfo_${time}.txt, 
which contains the extracted file's detailed info.

[Usage]
1.Install Python 2.7.2
http://www.python.org/ftp/python/2.7.2/python-2.7.2.msi
download and install it.

2. Install BeautifulSoup
http://www.crummy.com/software/BeautifulSoup/download/3.x/BeautifulSoup-3.0.6.py
download it then rename to BeautifulSoup.py, copy it to folder, where this script located.

3. Run this python script
(1) skydrive_real_addr.py -s your_skydrive_main_entry_url
eg:
skydrive_real_addr.py -s https://skydrive.live.com/?cid=9a8b8bf501a38a36

(2) if you want also download these files, add -d yes:
skydrive_real_addr.py -s https://skydrive.live.com/?cid=9a8b8bf501a38a36 -d yes

(3)if you want to only check sub folders, then do like this:
skydrive_real_addr.py -s entryUrl.txt
in which, the content of entryUrl.txt is:
https://skydrive.live.com/?cid=9A8B8BF501A38A36&id=9A8B8BF501A38A36%21538
and this link is entry url for folder 'wordpress' under 'pic/tect' in https://skydrive.live.com/?cid=9a8b8bf501a38a36

[other notes]
1.javascript formatter:
http://www.gosu.pl/decoder/
2. Q: how can I find the link url for any file and folder ?
A: Example:
for folder 'wordpress' under 'pic/tect' in https://skydrive.live.com/?cid=9a8b8bf501a38a36
you can right click the folder 'wordpress' -> share ->get a link ->make it public,
then got the share link:
https://skydrive.live.com/redir.aspx?cid=9a8b8bf501a38a36&resid=9A8B8BF501A38A36!538&parid=9A8B8BF501A38A36!535
in which you can find the resid=9A8B8BF501A38A36!538
then the entry url for folder pic/tech/wordprss is:
https://skydrive.live.com/?cid=9A8B8BF501A38A36&id=9A8B8BF501A38A36%21538
in which:
https://skydrive.live.com/?cid=9A8B8BF501A38A36 is main entry url
9A8B8BF501A38A36%21538 is resid=9A8B8BF501A38A36!538=9A8B8BF501A38A36%21538

#------------------------------------------------------------------------------
"""

#---------------------------------import---------------------------------------
import os
import re
import sys
import time
import random
import codecs
import logging
import urllib
import urllib2
#import cookielib
from BeautifulSoup import BeautifulSoup,Tag,CData
from datetime import datetime,timedelta
from optparse import OptionParser
#from string import Template,replace
#import httplib
#import httplib2


consEqualLine = '='*80
constDelimiter = "-"*80
constHalfDelimiter = "-"*40
__VERSION__ = 'v2012-01-19'

gConst = {
    'rootId'    : 'root',
}

gVal = {
    'selfScriptName'    : "",
    'exportFileName'    : "",
    'processedFolder'   : {},
    'info'              : { 'dirName' : '', 'fileName' : '', },
}

gCfg = {
    'needOutputInfo'    : "",
    'needDownload'      : "",
}

#------------------------------------------------------------------------------
# validate the original url:
# 1. replace \/ to /
# ...
def validateUrl(originUrl) :
     #filteredUrl = re.compile('\/').sub('/', originUrl) # this line not work ???
     filteredUrl = originUrl.replace('\\/', '/')
     return filteredUrl

#------------------------------------------------------------------------------
# download from fileUrl then save to fileToSave
# with exception support
# note: the caller should make sure the fileUrl is a valid internet resource/file
def downloadFile(fileUrl, fileToSave, needReport) :
    isDownOK = False
    downloadingFile = ''

    #---------------------------------------------------------------------------
    # note: totalFileSize -> may be -1 on older FTP servers which do not return a file size in response to a retrieval request
    def reportHook(copiedBlocks, blockSize, totalFileSize) :
        #global downloadingFile
        if copiedBlocks == 0 : # 1st call : once on establishment of the network connection
            logging.debug('Begin to download %s, total size=%d', downloadingFile, totalFileSize)
        else : # rest call : once after each block read thereafter
            logging.debug('Downloaded bytes: %d', blockSize * copiedBlocks)
        return
    #---------------------------------------------------------------------------

    try :
        if fileUrl :
            downloadingFile = fileUrl

            logging.info("  Downloading %s", downloadingFile)
            if needReport :
                urllib.urlretrieve(fileUrl, fileToSave, reportHook)
            else :
                urllib.urlretrieve(fileUrl, fileToSave)
            logging.debug("Saved %s to %s", fileUrl, fileToSave)
            isDownOK = True
        else :
            logging.warning("Input download file url is NULL")
    except urllib.ContentTooShortError(msg) :
        isDownOK = False
        logging.warning("ContentTooShortError while downloading %s, msg=%s", fileUrl, msg)
    except :
        isDownOK = False
        logging.warning("Error while downloading %s", fileUrl)

    return isDownOK


#------------------------------------------------------------------------------
# output info
def outputLogAndInfo(infoLines) :
    global gVal
    global gCfg
    
    if gCfg['needOutputInfo'] == 'yes' :
        infoFile = codecs.open(gVal['info']['fileName'], 'a+', 'utf-8')
        
    for info in infoLines :
        logging.info("%s", info)
        if gCfg['needOutputInfo'] == 'yes' :
            infoFile.write(info + '\r\n')

    if gCfg['needOutputInfo'] == 'yes' :
        infoFile.flush()
        infoFile.close()
    return

#------------------------------------------------------------------------------
# create output info dir and file
def createOutInfoDirAndFile() :
    global gVal

    # create dir
    gVal['info']['dirName'] = 'skydrive'
    if (os.path.isdir(gVal['info']['dirName']) == False) :
        os.makedirs(gVal['info']['dirName']) # create dir recursively
        logging.info("Create dir [%s] for save output info file", gVal['info']['dirName'])

    # create file
    gVal['info']['fileName'] = gVal['info']['dirName'] + "/" + 'extractedSkydriveInfo' + datetime.now().strftime('_%Y%m%d_%H%M') + '.txt'
    infoFile = codecs.open(gVal['info']['fileName'], 'w', 'utf-8')
    if infoFile:
        logging.info('Created file %s for store extracted info', gVal['info']['fileName'])
        infoFile.close()
    else:
        logging.error("Can not create output info file: %s", gVal['info']['fileName'])
        sys.exit(2)
    return

#------------------------------------------------------------------------------
# generate the child url from parent url
# id is 9A8B8BF501A38A36%21504 or 9A8B8BF501A38A36!504
# child url should like this:
# https://skydrive.live.com/?cid=9a8b8bf501a38a36&id=9A8B8BF501A38A36%21504
# note: main entry url like this:
# https://skydrive.live.com/?cid=9a8b8bf501a38a36
def genChildUrl(id) :
    childUrl = ''
    if ('!' in id) or ('%' in id):
        if '!' in id :
            cidPos = id.find('!')
        if '%' in id :
            cidPos = id.find('%')
        cid = id[0 : cidPos]
        EntryUrl = "https://skydrive.live.com/?cid=" + str(cid)
        childUrl = EntryUrl
        quotedId = urllib.quote(id)
        childUrl += '&' + 'id=' + quotedId
        logging.debug("Generated child url %s from id=%s", childUrl, id)
    else :
        logging.debug("Can not extract cid from id=%s", id)

    return childUrl

#------------------------------------------------------------------------------
# check the input icontype is foler or not,
# if it is, return ture if folder is not empty
def parseFolderInfo(iconType) :
    isFolder = False
    notEmpty = False

    def toNonEmpty(emptyFolder) :
        return 'Non' + emptyFolder

    emptyList = ['EmptyDocumentFolder', 'EmptyAlbum', 'EmptyFavoriteFolder']
    nonEmptyList = map(toNonEmpty, emptyList)
    
    if (iconType in emptyList) or (iconType in nonEmptyList) :
        isFolder = True
        if iconType in nonEmptyList :
            notEmpty = True
    else :
        isFolder = False
        notEmpty = False

    return (isFolder, notEmpty)
    
#------------------------------------------------------------------------------
# for current skydrive folder entry link url,
# extract its files info and found its sub dirs and recursively process them
def processCurrentDir(curEntryUrl) :
    curId = '' # example: 9A8B8BF501A38A36!504
    if curEntryUrl.find('&') > 0 :
        # is sub folder
        # https://skydrive.live.com/?cid=9a8b8bf501a38a36&id=9A8B8BF501A38A36%21504
        idStr = curEntryUrl.split('&')[-1]
        curId = idStr.split('=')[1]
        curId = curId.replace('%21', '!')
        logging.debug("Extract the id=[%s] from input entry url [%s]", curId, curEntryUrl)
    else :
        # is main url
        # https://skydrive.live.com/?cid=9a8b8bf501a38a36
        curId = gConst['rootId']
        logging.debug("Input entry url [%s] not contain '&', is main url", curEntryUrl)

    if curId in gVal['processedFolder'] :
        logging.debug("Not processed the overlapped folder: id=%s, name=%s", curId, gVal['processedFolder'][curId]['name'])
        logging.debug("and current the processed list is:\n%s", gVal['processedFolder'])
        return

    # need later fill fields info
    gVal['processedFolder'][curId] = {}

    logging.info("%s", consEqualLine)
    logging.info("Begin to open current entry url %s", curEntryUrl)
    openedUrl = urllib2.urlopen(curEntryUrl)
    soup = BeautifulSoup(openedUrl, fromEncoding="utf-8")
    #logging.debug("------prettified page for: %s\n%s", curEntryUrl, soup.prettify())

    # 1. prase retured response to find items string
    soupStr = str(soup)
    #logging.debug("------after convert to string, soup is\n-----%s", soupStr)
    itemsP = re.compile(r'var\s+primedResponse=\{"items"\:\[\{(.*)}\]\};\s+\$Do\.register\("primedResponse"\);')
    items = itemsP.search(soupStr)
    itemsStr = items.group(1)
    logging.debug("------found items reponse string for [%s]-----\n%s", curEntryUrl, itemsStr)
    
    # "group":0,"iconType":"EmptyDocumentFolder","id":"9A8B8BF501A38A36!524","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634614241208800000,"name":"domestic","ownerCid"
    # "group":0,"iconType":"EmptyFavoriteFolder","id":"9A8B8BF501A38A36!468","isSpecialFolder":1,"lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":633643215224330000,"name":"Shared favorites","ownerCid":"9A8B8BF501A38A36","ownerDCid"
    # "group":0,"iconType":"NonEmptyDocumentFolder","id":"9A8B8BF501A38A36!523","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634614257856830000,"name":"foreign","ownerCid"
    # "group":0,"iconType":"EmptyDocumentFolder","id":"9A8B8BF501A38A36!525","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634614241548600000,"name":"pureMusic","ownerCid"
    # "group":0,"iconType":"Audio","id":"9A8B8BF501A38A36!505","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634079507897400000,"name":"预感时枯萎 なアーティスト","ownerCid"
    # "group":0,"iconType":"NonEmptyDocumentFolder","id":"9A8B8BF501A38A36!504","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634614257856870000,"name":"music","ownerCid"
    
    # "group":0,"iconType":"NonEmptyAlbum","id":"45C0783A59320656!278","lastModifierCid":"45C0783A59320656","lastModifierName":"亮 陈","modifiedDate":634220317830670000,"name":"blogpic","ownerCid"
    # "group":0,"iconType":"NonEmptyDocumentFolder","id":"45C0783A59320656!698","lastModifierCid":"45C0783A59320656","lastModifierName":"亮 陈","modifiedDate":634220319631400000,"name":"itlobo","ownerCid"
    # "group":0,"iconType":"NonEmptyDocumentFolder","id":"45C0783A59320656!648","lastModifierCid":"45C0783A59320656","lastModifierName":"亮 陈","modifiedDate":634315576610770000,"name":"itlobo-publish-file","ownerCid"
    
    # first extract the folder relation
    # "group":0,"iconType":"NonEmptyDocumentFolder","id":"9A8B8BF501A38A36!538","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634625385140870000,"name":"wordpress","ownerCid":"9A8B8BF501A38A36","ownerDCid":"-7310595685695124938","ownerName":"tian wang","parentId":"9A8B8BF501A38A36!535","sharingLevel":"Everyone (public)","sharingLevelValue":0,"size":"2934239","urls":{"viewInBrowser":"https:\/\/skydrive.live.com\/redir.aspx?cid=9a8b8bf501a38a36&page=view&resid=9A8B8BF501A38A36!538&parid=9A8B8BF501A38A36!535"},"userRole":2},{"commands":"defc,1,dl,1,pm,1","commentCount":0,"creationDate":634624541062800000,"creatorCid":"9A8B8BF501A38A36","creatorName":"tian wang","displayCreationDate":"1\/18\/2012","displayModifiedDate":"1\/19\/2012","displaySize":"2,866 KB","folder":{"hasSubfolders":1,"totalCount":1},
    foldersP = re.compile('"group":\d+,"iconType":"\w+","id":"[\w!]+","lastModifierCid":"\w+","lastModifierName":"[^\"]*","modifiedDate":\d+,"name":"[^\"]*","ownerCid":"\w+","ownerDCid":"[\d-]+","ownerName":"[^\"]*","parentId":"[\w!]+","sharingLevel".*?"folder":{.*?"hasSubfolders":\d+');
    #foldersP = re.compile(r'"group":\d+,"iconType":"\w+","id":"[\w!]+".*?"name":".*?".*?"parentId":"[\w!]+","sharingLevel".*?"folder":{.*?"hasSubfolders":\d+')
    folersList = foldersP.findall(itemsStr)
    foldersListLen = len(folersList)
    logging.debug("For extract folder relation, found [%d] folders:", foldersListLen)
    for folerStr in folersList :
        logging.debug("%s", folerStr)

    folderRelation = {}
    firstFound = ''
    for folerStr in folersList :
        #                                1=id                2=name              3=cid                  4=parentId  
        foldersInfoP = re.compile('"id":"([\w!]+)".*?"name":"([^\"]*)","ownerCid":"(\w+)".*?"parentId":"([\w!]+)"')
        searched = foldersInfoP.search(folerStr)
        folderInfo = {}
        folderInfo['id']        = searched.group(1)
        folderInfo['name']      = searched.group(2)
        folderInfo['ownerCid']  = searched.group(3)
        folderInfo['parentId']  = searched.group(4)
        folderRelation[folderInfo['id']] = folderInfo
        if not firstFound : # record first, it is the current folder
            firstFound = folderInfo

    curDirNameUni = ''
    fullFolderPathUni = ''
    
    if firstFound :
        if firstFound['parentId'] == 'root' :
            # it is main Url
            curDirNameUni = unicode('skydrive')
            fullFolderPathUni = curDirNameUni
        else :
            curDirNameUni = firstFound['name'].decode("utf-8")
            # extract the folder relation
            fullFolderPathUni = curDirNameUni
            folderId = firstFound['parentId']
            while (folderId in folderRelation) :
                if (folderRelation[folderId]['parentId'] == 'root') :
                    fullFolderPathUni = unicode('skydrive') + unicode('/') + folderRelation[folderId]['name'].decode('utf-8') + unicode('/') + fullFolderPathUni
                    break
                else :
                    fullFolderPathUni = folderRelation[folderId]['name'].decode('utf-8') + unicode('/') + fullFolderPathUni
                    folderId = folderRelation[folderId]['parentId']

    if curId in folderRelation :
        curFolderInfo = folderRelation.pop(curId)
        gVal['processedFolder'][curId] = curFolderInfo
        logging.debug("Current folder id=%s, name=%s", curId, curFolderInfo['name'])
        # now only left parent folder info

    # here can not add the parent folders into processed list,
    # for the result we got is messy, contains both the main folder under root and some other subfolders
    # if do following, then will omit processing these folders
    #if curId != gConst['rootId'] :
    #    for folderId in folderRelation.keys() :
    #        gVal['processedFolder'][folderId] = folderRelation[folderId]
    #        logging.debug("Omit process parent folder: id=%s, name=%s", folderId, folderRelation[folderId]['name'])

    #found fields (iconType, id, name)
    #fieldsP = re.compile(r'"group":\d+,"iconType":"\w+","id":"[\w!]+",.*?"lastModifierCid":"\w+","lastModifierName":"[\w\s]+","modifiedDate":\d+,"name":".*?","ownerCid"')
    fieldsP = re.compile(r'"group":\d+,"iconType":"\w+","id":"[\w!]+","lastModifierCid":"\w+","lastModifierName":".*?","modifiedDate":\d+,"name":".*?","ownerCid"')
    fieldsList = fieldsP.findall(itemsStr)
    fieldListLen = len(fieldsList)
    logging.debug("Found [%d] fields:", fieldListLen)
    for fieldStr in fieldsList :
        logging.debug("%s", fieldStr)

    urlTodoList = {}

    for fieldStr in fieldsList :
        #                                  1=group          2=iconType     3=id                4=lastModifierCid           5=lastModifierName        6=modifiedDate         7=name
        eachFieldP = re.compile(r'"group":(\d+),"iconType":"(\w+)","id":"([\w!]+)","lastModifierCid":"(\w+)","lastModifierName":"(.*?)","modifiedDate":(\d+),"name":"(.*?)","ownerCid"')
        # note: .* -> max greedy match; .*? -> non-greedy or minimal match
        foundField = eachFieldP.search(fieldStr)

        allField         = foundField.group(0)
        group            = foundField.group(1)
        iconType         = foundField.group(2)
        id               = foundField.group(3)
        lastModifierCid  = foundField.group(4)
        lastModifierName = foundField.group(5)
        modifiedDate     = foundField.group(6)
        name             = foundField.group(7)
        
        nameUni = name.decode("utf-8")
        
        (isFolder, notEmpty) = parseFolderInfo(iconType)
        logging.debug("For [%s], parsed info from [%s] : isFolder=%s, notEmpty=%s", name, iconType, isFolder, notEmpty)
        if isFolder :
            if notEmpty :
                # is folder, recursively process it
                if id not in gVal['processedFolder'] :
                    childUrl = genChildUrl(id)
                    # not process, then add to later process
                    urlTodoList[nameUni] = childUrl
                    logging.debug("Added %s for later process", childUrl)
        #else :
            # is file, add to name list
            #namesList.append(nameUni)
            #logging.debug("Found file [%s]", nameUni)

    logging.debug("For current level, found urls to process:")
    for url in urlTodoList.values() : logging.debug("  %s", url)
    #logging.debug("For current level, found names:",)
    #for name in namesList : logging.debug("  %s", name)
    

    # process all remaining files
    # refind all names and download address
    # [ example 1 ]
    # "extension":".mp3","group":0,"iconType":"Audio","id":"9A8B8BF501A38A36!505","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":634079507897400000,"name":"预感时枯萎 なアーティスト","ownerCid":"9A8B8BF501A38A36","ownerDCid":"-7310595685695124938","ownerName":"tian wang","parentId":"9A8B8BF501A38A36!504","sharingLevel":"Everyone (public)","sharingLevelValue":0,"size":"2891855","urls":{"download":"https:\/\/zxhpmw.bay.livefilestore.com\/y1pPJvYiEgB-tnkrvqziGbn2IkDWpeN9RYmvrzzC4KetLPVrsBh1DDzwbVXWGEyTPCZsHwbAPptOlSWEOagCTjunQ\/%E9%A2%84%E6%84%9F%E6%97%B6%E6%9E%AF%E8%90%8E%20%E3%81%AA%E3%82%A2%E3%83%BC%E3%83%86%E3%82%A3%E3%82%B9%E3%83%88.mp3?download&psid=1","viewInBrowser":
    
    # [ example 2 ]
    # "extension":".jpg","group":0,"iconType":"Photo","id":"9A8B8BF501A38A36!379","lastModifierCid":"9A8B8BF501A38A36","lastModifierName":"tian wang","modifiedDate":632932774479730000,"name":"特等奖：","ownerCid":"9A8B8BF501A38A36","ownerDCid":"-7310595685695124938","ownerName":"tian wang","parentId":"9A8B8BF501A38A36!368","photo":{"height":450,"width":600},"sharingLevel":"Everyone (public)","sharingLevelValue":0,"size":"46546","thumbnailSet":{"baseUrl":"https:\/\/by","id":"9A8B8BF501A38A36!379","thumbnails":[{"height":450,"name":"scaledLargest","url":"files.storage.live.com\/y1pADxvJVSoAsgjIZ1Kow7AmR6qnN3GgHRthmSDe507peKzQqYzD3OnhZPOti-tS5dlNWRsxKgXOWc\/%E7%89%B9%E7%AD%89%E5%A5%96%EF%BC%9A.jpg?psid=1","width":600},{"height":128,"name":"height128","url":"files.storage.live.com\/y1pSUUluVoJg6mzrkFDqIZC5V7ZFkXNBFVoZwGoSWQO5mQAL-CXDwDsxie6D1bCBBQFsmi8Cfdu4vY\/%E7%89%B9%E7%AD%89%E5%A5%96%EF%BC%9A.jpg?psid=1","width":170},{"height":171,"name":"width228","url":"2.storage.live.com\/items\/9A8B8BF501A38A36!379:ConstantWidth228\/%E7%89%B9%E7%AD%89%E5%A5%96%EF%BC%9A.jpg?psid=1&ck=0&ex=720","width":228},{"height":450,"name":"scaled1024","url":"2.storage.live.com\/items\/9A8B8BF501A38A36!379:Scaled1024\/%E7%89%B9%E7%AD%89%E5%A5%96%EF%BC%9A.jpg?psid=1&ck=0&ex=720","width":600}]},"urls":{"download":"https:\/\/byfiles.storage.live.com\/y1pADxvJVSoAsgjIZ1Kow7AmR6qnN3GgHRthmSDe507peKzQqYzD3OnhZPOti-tS5dlNWRsxKgXOWc\/%E7%89%B9%E7%AD%89%E5%A5%96%EF%BC%9A.jpg?download&psid=1","open":"https:\/\/byfiles.storage.live.com\/y1pADxvJVSoAsgjIZ1Kow7AmR6qnN3GgHRthmSDe507peKzQqYzD3OnhZPOti-tS5dlNWRsxKgXOWc\/%E7%89%B9%E7%AD%89%E5%A5%96%EF%BC%9A.jpg?psid=1","viewInBrowser":
    
    filesP = re.compile(r'"extension":".+?".+?"id":".+?".+?"name":".+?","ownerCid".+?"ownerName":".+?",.+?"urls":{"download":"https:.+?".*?"viewInBrowser":"https:.+?\},"userRole":')
    filesList = filesP.findall(itemsStr)
    filesListLen = len(filesList)
    logging.debug("------filesList: total [%d] files string ------", filesListLen)
    for filesStr in filesList : logging.debug("%s", filesStr)

    if gCfg['needDownload'] == 'yes' :
        # create main dir to store download files
        if (os.path.isdir(fullFolderPathUni) == False) :
            os.makedirs(fullFolderPathUni) # create dir recursively
            logging.info("Create dir [%s] for save downloaded files", fullFolderPathUni)

    fileInfoList = []
    for singleFile in filesList :
        #                                  1=extension       2=id            3=name                         4=ownerName                       5=tmpLink
        fileInfoP = re.compile(r'"extension":"(.+?)".+?"id":"(.+?)".+?"name":"(.+?)","ownerCid".+?"ownerName":"(.+?)",.+?"urls":{"download":"(https:.+?)".*?"viewInBrowser":"https:.+?\},"userRole":')
        foundInfo = fileInfoP.search(singleFile)
        if foundInfo :
            infoDict = {
                'extension' : '',
                'id'        : '',
                'name'      : '',
                'ownerName' : '',
                'tmpLink'   : '',
                
                'nameUni'   : '',
                'permLink'  : '',
            }

            infoDict['extension']= foundInfo.group(1)
            infoDict['id']      = foundInfo.group(2)
            
            infoDict['name']    = foundInfo.group(3)
            infoDict['nameUni'] = infoDict['name'].decode("utf-8")

            tmpLink = foundInfo.group(4)
            
            tmpLink = foundInfo.group(5)
            questionPos = tmpLink.find('?')
            tmpLink = tmpLink[0 : questionPos]
            logging.debug("After remove question mark : %s", tmpLink)
            tmpLink = validateUrl(tmpLink)
            logging.debug("After valite url : %s", tmpLink)
            infoDict['tmpLink'] = tmpLink

            # %E7%AC%AC%E5%85%AD%E5%90%8D%EF%BC%9A%E5%8D%87%E9%99%8D%E5%B7%A5.jpg
            quotedFullName = infoDict['tmpLink'].split('/')[-1]
            # http://storage.live.com/items/9A8B8BF501A38A36!359?filename=%E7%AC%AC%E5%85%AD%E5%90%8D%EF%BC%9A%E5%8D%87%E9%99%8D%E5%B7%A5.jpg
            infoDict['permLink'] = "http://storage.live.com/items/" + infoDict['id'] + "?filename=" + quotedFullName

            fileInfoList.append(infoDict)

    infoLines = []
    infoLines.append(consEqualLine)
    infoLines.append("For Current Folder:")
    infoLines.append("Full Path   : %s" % fullFolderPathUni)
    infoLines.append("Folder Name : %s" % curDirNameUni)
    infoLines.append("Folder Link : %s" % curEntryUrl)
    infoLines.append("Found  Files: %s" % filesListLen)

    outputLogAndInfo(infoLines)
    for i in range(filesListLen) :
        infoDict = fileInfoList[i]

        infoLines = []
        infoLines.append(constHalfDelimiter)
        infoLines.append("[%d]" % (i+1))
        infoLines.append("File Name     : %s" % infoDict['nameUni'])
        infoLines.append("File ID       : %s" % infoDict['id'])
        infoLines.append("File Extension: %s" % infoDict['extension'])
        infoLines.append("Permanent Link: %s" % infoDict['permLink'])
        infoLines.append("Temorary  Link: %s" % infoDict['tmpLink'])
        outputLogAndInfo(infoLines)
            
        if gCfg['needDownload'] == 'yes' :
            sufPos = infoDict['tmpLink'].rfind('.')
            pointSuf = infoDict['tmpLink'][sufPos:]
            fileToSave = fullFolderPathUni + '/' + infoDict['nameUni'] + pointSuf
            downloadFile(infoDict['tmpLink'], fileToSave, True)

    # process each pending url
    for nameUni in urlTodoList.keys() :
        processCurrentDir(urlTodoList[nameUni])

    logging.debug("Done for process %s", curEntryUrl)
    return

#------------------------------------------------------------------------------
def main():
    global gVal
    global gCfg

    # 0. main procedure begin
    parser = OptionParser()
    parser.add_option("-s","--srcMainUrl",action="store", type="string",dest="srcMainUrl",help="open the skydrive dir to extract files real address. Should like this: https://skydrive.live.com/?cid=9a8b8bf501a38a36, if you want to input such address like https://skydrive.live.com/?cid=9A8B8BF501A38A36&id=9A8B8BF501A38A36%21538, then you should use config file, such as entryUrl.txt, which contains https://skydrive.live.com/?cid=9A8B8BF501A38A36&id=9A8B8BF501A38A36%21538 ")
    parser.add_option("-d","--needDownload",action="store", type="string",dest="needDownload",default='no',help="'yes' or 'no'. Download the extracted files or not.")
    parser.add_option("-o","--needOutputInfo",action="store", type="string",dest="needOutputInfo",default='yes',help="'yes' or 'no'. Output the extracted files info to file or not.")

    (options, args) = parser.parse_args()
    # 1. export all options variables
    for i in dir(options):
        exec(i + " = options." + i)

    gCfg['needOutputInfo'] = needOutputInfo
    gCfg['needDownload'] = needDownload
    logging.info("Script : %s", gVal['selfScriptName'])
    logging.info("Version: %s", __VERSION__)

    # Note: 
    # (1) input [main] url should be like this:
    # https://skydrive.live.com/?cid=9a8b8bf501a38a36
    # (2) input url can not include '&', otherwise will be parsed by python to be another seperate command !
    # that is, input url should not like this:
    # https://skydrive.live.com/?cid=9a8b8bf501a38a36#cid=9A8B8BF501A38A36&id=9A8B8BF501A38A36%21504
    # (3) only open this kind of address:
    # https://skydrive.live.com/?cid=9a8b8bf501a38a36&id=9A8B8BF501A38A36%21504
    # can get the files info
    # (4) here, the method 1: use the generated request url + open it + get return content
    # does not take effect, so use following method 2: open main url and child url to get content, then extract it
    # for method 1: just for record, there two kind of request url:
    # [ request url kind 1 ]
    # https://skydrive.live.com/API/2/GetItems?id=9a8b8bf501a38a36%21504&cid=9a8b8bf501a38a36&group=0&qt=&ft=&sb=1&sr=0&d=1&lid=9A8B8BF501A38A36!504&caller=&path=0
    # &si=0
    # &ps=100&pi=5&m=zh-CN&rset=web&lct=1
    # &v=0.8950186939910054
    # [ request url kind 2 ]
    # https://skydrive.live.com/API/2/GetItems?id=9a8b8bf501a38a36%21504&cid=9a8b8bf501a38a36&group=0&qt=&ft=&sb=1&sr=0&d=1&lid=9A8B8BF501A38A36!504&caller=&path=0
    # &sid=9A8B8BF501A38A36!522
    # &ps=100&pi=5&m=zh-CN&rset=web&lct=1
    # &v=634613457185730000

    if gCfg['needOutputInfo'] == 'yes' :
        # create dir and file
        createOutInfoDirAndFile()

    # for folder /pic/tech/wordpress, its address is:
    # https://skydrive.live.com/?cid=9A8B8BF501A38A36&id=9A8B8BF501A38A36%21538
    if os.path.isfile(srcMainUrl) :
        # open config file, extract configure parameter
        logging.debug("Input config file is %s", srcMainUrl)
        cfgFile = os.open(srcMainUrl, os.O_RDONLY)
        cfgEntryUrl = os.read(cfgFile, os.path.getsize(srcMainUrl))
        logging.debug("Extracted config info is %s", cfgEntryUrl)
        srcMainUrl = cfgEntryUrl

    # recursively process each url
    processCurrentDir(srcMainUrl)

    logging.info("Complete of processing all files for %s", srcMainUrl)
    return    

#------------------------------------------------------------------------------
# got python script file name itsself
def getScriptSelfFilename() :
    # got script self's name
    # for : python xxx.py -s yyy    # -> sys.argv[0]=xxx.py
    # for : xxx.py -s yyy           # -> sys.argv[0]=D:\yyy\zzz\xxx.py
    argv0List = sys.argv[0].split("\\")
    scriptName = argv0List[len(argv0List) - 1] # get script file name self
    possibleSuf = scriptName[-3:]
    if possibleSuf == ".py" :
        scriptName = scriptName[0:-3] # remove ".py"
    return scriptName

###############################################################################
if __name__=="__main__":
    gVal['selfScriptName'] = getScriptSelfFilename()

    logging.basicConfig(
                    level    =logging.DEBUG,
                    format   = 'LINE %(lineno)-4d  %(levelname)-8s %(message)s',
                    datefmt  = '%m-%d %H:%M',
                    filename = gVal['selfScriptName'] + '.log',
                    filemode = 'w');
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('LINE %(lineno)-4d : %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    try:
        main()
    except:
        logging.exception("Unknown Error !")
        raise
