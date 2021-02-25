import os, shutil

import re
from django.conf import settings
from django.core.files.base import ContentFile
from urllib.parse import unquote, urlsplit, quote

from filemanager import signals
from filemanager.settings import STORAGE#, #DIRECTORY
from filemanager.utils import sizeof_fmt
from django.core.files.storage import FileSystemStorage

DIRECTORY = r'C:\Documents\media'
STORAGE = FileSystemStorage(location=DIRECTORY, base_url="")

class Filemanager(object):

    def __init__(self):

        self._directory = DIRECTORY
        if not os.path.exists(self._directory):
            os.makedirs(self._directory)
        self._path = ""
        self._storage = FileSystemStorage(location=self._directory, base_url="")
        self._abspath = os.path.join(self._directory, self._path)
        self._url = os.path.join(self._path)
        self._location = self._abspath


    def get_root(self, directory):
        if directory is not None:
            assert isinstance(directory, str)
            self._directory = self.validate_path(directory)


        self._storage = FileSystemStorage(location=self._directory, base_url="")
        self.update_path("")

    def update_path(self, path):
        if path is not None:
            self._path = self.validate_path(path)

        self._abspath = self.validate_path(os.path.join(self._directory, self._path))
        self._url = os.path.join(self._path)
        self._location = self._abspath


    def validate_path(self, path):
        # replace backslash with slash
        format_path = str(path).replace('\\', '/')
        # remove leading and trailing slashes
        validated_path = '/'.join([i for i in format_path.split('/') if i])

        return validated_path

    def get_breadcrumbs(self):
        breadcrumbs = [{
            'label': 'ROOT',
            'path': '',
        }]
        print("self.path: " + str(self._path))
        parts = [e for e in self._path.split('/') if e]
        print("parts: "+str(parts))
        path = ''
        for part in parts:
            path = self.validate_path(os.path.join(path, part))
            breadcrumbs.append({
                'label': part,
                'path': path,
            })

        return breadcrumbs

    def patch_context_data(self, context):
        context.update({
            'directory': quote(self._directory),
            'path': quote(self._path),
            'breadcrumbs': self.get_breadcrumbs(),
            })

    def file_details(self):
        print("self.path: " + str(self._path))
        filename = self._path.rsplit('/', 1)[-1]
        print("filename"+str(filename))
        print(self._storage.size(self._location))
        return {
            'filetype': os.path.dirname(self._path),
            'filepath': self.validate_path(self._path),
            'filename': filename,
            'filesize': sizeof_fmt(self._storage.size(self._location)),
            'filedate': self._storage.get_modified_time(self._location),
            'fileurl': self.validate_path(self._url),
        }

    def directory_list(self):
        print("directory_list")
        listing = []
        print("self.storage: " + str(self._storage.base_location))
        print("self.path: "+str(self._path))
        print("self.location: "+str(self._location))
        print("self.directory: "+str(self._directory))

        directories, files = self._storage.listdir(self._location)
        print("directories: "+str(directories))
        def _helper(name, filetype):
            filepath = os.path.join(self._path, name)
            return {
                'filepath': quote(os.path.join(self._path, name)),
                'filetype': filetype,
                'filename': name,
                'filedate': self._storage.get_modified_time(filepath),
                'filesize': sizeof_fmt(self._storage.size(filepath)),
                'fileurl' : self._abspath,
                }

        for directoryname in directories:
            listing.append(_helper(directoryname, 'Directory'))

        for filename in files:
            listing.append(_helper(filename, 'File'))

        return listing

    def upload_file(self, filedata):
        filename = self._storage.get_valid_name(filedata.name)
        filepath = os.path.join(self._path, filename)
        signals.filemanager_pre_upload.send(sender=self.__class__, filename=filename, path=self._path, filepath=filepath)
        self._storage.save(filepath, filedata)
        signals.filemanager_post_upload.send(sender=self.__class__, filename=filename, path=self._path, filepath=filepath)
        return filename

    def create_directory(self, name):
        print("create")
        name = self._storage.get_valid_name(name)
        tmpfile = os.path.join(name, '.tmp')

        path = os.path.join(self._path, tmpfile)
        print(path)
        self._storage.save(path, ContentFile(''))
        self._storage.delete(path)

    def rename(self, src, dst):
        os.rename(os.path.join(self._location, src), os.path.join(self._location, dst))

    def remove(self, name):
        if os.path.isdir(os.path.join(self._location, name)):
            shutil.rmtree(os.path.join(self._location, name))
        else:
            os.remove(os.path.join(self._location, name))

    def search(self, name):
        startpath = os.path.join(settings.MEDIA_ROOT, self._abspath)
        q = []
        for root, dirs, files in os.walk(startpath):
            self.update_path(root.replace(startpath, ''))

            for file in self.directory_list():
                if re.search(name, file['filename'], re.I):
                    q.append(file)
                try:
                    if file['filetype'] == 'File':
                        with open(self._directory + file['filepath']) as f:
                            content = f.read()
                            if name in content:
                                q.append(file)
                except:
                    pass

        return q
