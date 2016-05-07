#coding=utf8
import sys, hashlib

import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.NoteStore as NoteStore
from Oauth import Oauth
from Storage import Storage
from evernote.api.client import EvernoteClient

# * If you are international user, replace all the yinxiang with evernote

SANDBOX = True
SERVICE_HOST = 'sandbox.evernote.com'
# SANDBOX = False
# SERVICE_HOST = 'app.yinxiang.com' 

# * If you are international user, replace all the yinxiang with evernote

# You can get this from 'https://%s/api/DeveloperToken.action'%SERVICE_HOST >>
SPECIAL_DEV_TOKEN = True
DEV_TOKEN = 'S=s1:U=91eca:E=15be6680420:C=1548eb6d760:P=1cd:****************************************************'
# SPECIAL_DEV_TOKEN = False
# DEV_TOKEN = ''
# In China it's https://app.yinxiang.com/api/DeveloperToken.action <<

LOCAL_STORAGE = False

class EvernoteController:
    def __init__(self):
        if DEV_TOKEN:
            self.token = DEV_TOKEN
        else:
            self.token = Oauth(SANDBOX).oauth()

        sys.stdout.write('Logging\r')
        if SANDBOX:
            self.client = EvernoteClient(token=self.token)
        else:
            self.client = EvernoteClient(token=self.token, service_host=SERVICE_HOST)
        self.userStore = self.client.get_user_store()
        self.noteStore = self.client.get_note_store()
        if LOCAL_STORAGE: self.__set_storage()
        print 'Login Succeed as ' + self.userStore.getUser().username
    def __set_storage(self):
        print 'Loading Storage'
        self.storage = Storage(self.noteStore, self.token)
        print 'Storage loaded'
    def create_notebook(self,title):
        notebook = Types.Notebook()
        notebook.name = title
        notebook = self.noteStore.createNotebook(notebook)
        if LOCAL_STORAGE: self.storage.create_notebook(notebook)
        print_line('Created notebook: %s successfully'%title)
    def create_note(self, title, content, notebook = None, fileDir = None):
        note = Types.Note()
        note.title = title
        note.content = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        note.content += '<en-note>'
        note.content += content
        if notebook: note.notebookGuid = self.myfile(notebook).guid
        if not fileDir is None:
            with open(fileDir, 'rb') as f:
                fileBytes = f.read()
                fileName = f.name
            fileData = Types.Data()
            fileData.bodyHash = self._md5(fileBytes)
            fileData.size = len(fileBytes)
            fileData.body = fileBytes
            fileAttr = Types.ResourceAttributes()
            fileAttr.fileName = fileName
            fileAttr.attachment = True
            fileResource = Types.Resource()
            fileResource.data = fileData
            fileResource.mime = 'application/octet-stream'
            fileResource.attributes = fileAttr
            note.resources = [fileResource]
            note.content += '<en-media type="application/octet-stream" hash="%s"/>'%fileData.bodyHash
        note.content += '</en-note>'
        note = self.noteStore.createNote(note)
        if LOCAL_STORAGE: self.storage.create_note(note, notebook)
        print_line('Created note: %s successfully' %title)
    def get_note(self, note):
        note = self.myfile(note)
        with open(note.resources[0].attributes.fileName, 'wb') as f: f.write(self.noteStore.getResourceData(note.resources[0].guid))
    def move_note(self, note, _to):
        if type(self.myfile(note)) != type(Types.Note()) or type(self.myfile(_to)) != type(Types.Notebook()): raise Exception('Type Error')
        self.noteStore.copyNote(self.token, self.myfile(note).guid, self.myfile(_to).guid)
        if SPECIAL_DEV_TOKEN:
            self.noteStore.expungeNote(self.token, self.myfile(note).guid)
        else:
            self.noteStore.deleteNote(self.token, self.myfile(note).guid)
        if LOCAL_STORAGE: self.storage.move_note(note, _to)
        print_line('Move %s to %s successfully'%(note,_to))
    def delete_note(self, note):
        if type(self.myfile(note)) != type(Types.Note()): raise Exception('Types Error')
        self.noteStore.deleteNote(self.token, self.myfile(note).guid)
        # BUG
        if LOCAL_STORAGE: self.storage.delete_note(note)
        print_line('Deleted %s successfully'%note)
    def delete_notebook(self, notebook):
        if SPECIAL_DEV_TOKEN:
            if type(self.myfile(notebook)) != type(Types.Notebook()): raise Exception('Types Error')
            self.noteStore.expungeNotebook(self.token, self.myfile(notebook).guid)
            # BUG
            if LOCAL_STORAGE: self.storage.delete_notebook(notebook)
            print_line('Deleted %s successfully'%notebook)
    def myfile(self, s):
        if LOCAL_STORAGE: return self.storage.myfile(s)
        f = s.split('/')
        if '/' in s:
            for nb in self.noteStore.listNotebooks():
                if nb.name == f[0]:
                    fi = NoteStore.NoteFilter()
                    fi.notebookGuid = nb.guid
                    for ns in self.noteStore.findNotes(self.token, fi, 0, 999).notes:
                        if ns.title == f[1]: return ns
        else:
            for nb in self.noteStore.listNotebooks():
                if nb.name == f[0]: return nb
        raise Exception('%s not found'%s)
    def show_notebook(self):
        if LOCAL_STORAGE: 
            self.storage.show_notebook()
        else:
            for nb in self.noteStore.listNotebooks(): print_line(nb.name)
    def show_notes(self, notebook=None):
        if LOCAL_STORAGE:
            self.storage.show_notes(notebook)
        else:
            for nb in self.noteStore.listNotebooks():
                if not notebook: print_line(nb.name + ':')
                if not notebook or nb.name == notebook:
                    f = NoteStore.NoteFilter()
                    f.notebookGuid = nb.guid
                    for ns in self.noteStore.findNotes(self.token, f, 0, 999).notes:
                        print_line(('' if notebook else '    ') + ns.title)
    def _md5(self, s):
        m = hashlib.md5()
        m.update(s)
        return m.hexdigest()

def print_line(s):
    t = sys.getfilesystemencoding()
    print s.decode('UTF-8').encode(t)

if __name__ == '__main__':
    e = EvernoteController()
    # e.create_note('Hello', 'Hello, world!', 'Test', 't.md')
    e.get_note('Test/Hello')

if False:
    e.create_notebook('Notebook1')
    e.create_note('Hello', '<en-note>Hello, world!</en-note>', 'Notebook1')
    e.create_notebook('Notebook2')
    e.show_notes()
    e.move_note('Notebook1/Hello', 'Notebook2')
    e.show_notes()
    e.delete_note('Notebook2/Hello')
    # deleting notebook can only be available when you use developer token for you own evernote
    e.delete_notebook('Notebook1')
    e.delete_notebook('Notebook2')
    e.show_notes()
