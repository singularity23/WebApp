import json
import re

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import HttpResponse
from django.shortcuts import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from urllib.parse import unquote, urlsplit, quote

from filemanager.core import Filemanager
from filemanager.forms import DirectoryCreateForm, RenameForm


class FilemanagerMixin(object):
    def __init__(self):
        self.fm = Filemanager()

    def dispatch(self, request, *args, **kwargs):
        params = dict(request.GET)
        params.update(dict(request.POST))
        print("params: " + str(params))

        if 'directory' in params:
            print("direct_params: " + str(params['directory'][0]))
            self.fm.get_root(params['directory'][0])

        if 'path' in params and len(params['path'][0]) > 0:
            self.fm.update_path(params['path'][0])
        if 'popup' in params:
            self.popup = params['popup']

        return super(FilemanagerMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        # noinspection PyUnresolvedReferences
        context = super(FilemanagerMixin, self).get_context_data(*args, **kwargs)
        print("context: " + str(context))
        self.fm.patch_context_data(context)

        if hasattr(self, 'popup'):
            context['popup'] = self.popup

        if hasattr(self, 'extra_breadcrumbs') and isinstance(self.extra_breadcrumbs, list):
            context['breadcrumbs'] += self.extra_breadcrumbs

        return context


class JSONResponseMixin:
    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        response_kwargs['content_type'] = 'application/javascript; charset=utf8'
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
            )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or queryset
        # -- can be serialized as JSON.
        return context


class BrowserView(FilemanagerMixin, TemplateView):
    template_name = 'filemanager/browser/filemanager_list.html'

    def dispatch(self, request, *args, **kwargs):
        self.popup = self.request.GET.get('popup', 0) == '1'
        print("request: " + str(request.GET))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print("kwargs: " + str(kwargs))
        context = super().get_context_data(**kwargs)
        print("context：" + str(context))
        context['popup'] = self.popup
        query = self.request.GET.get('q')
        print("query: " + str(query))
        search_params = self.request.GET.get('search_param')
        print("search_params: " + str(search_params))
        if query:
            if re.match('here', search_params, re.I):
                files = self.fm.directory_list()
                print("files: " + str(files))
                q = []
                for file in files:
                    if re.search(query, file['filename'], re.I):
                        q.append(file)
                    try:
                        if file['filetype'] == 'File':
                            with open('media/uploads/' + file['filepath']) as f:
                                content = f.read()
                                if query in content:
                                    q.append(file)
                    except:
                        pass

                context['files'] = q
                context['empty'] = 'No item found'

            else:
                context['files'] = self.fm.search(query)
                context['empty'] = 'No item found'

        else:
            print("else")
            context['files'] = self.fm.directory_list()

            context['empty'] = 'Folder is empty'

            context['clean_directory'] = unquote(context.get('directory'))
        print(context)
        return context


class DetailView(FilemanagerMixin, JSONResponseMixin, TemplateView, SingleObjectTemplateResponseMixin):
    template_name = 'filemanager/browser/filemanager_detail.html'

    def get_context_data(self, **kwargs):
        print("kw: " + str(kwargs))
        context = super(DetailView, self).get_context_data(**kwargs)

        context['file'] = self.fm.file_details()

        return context

    def render_to_response(self, context, **response_kwargs):
        context['file'] = self.fm.file_details()
        if self.request.GET.get('format') == 'json':
            return self.render_to_json_response(context['file'])
        else:
            return super().render_to_response(context)

    # def get(self, request, *args, **kwargs):
    #
    #     return JsonResponse({'data':'james'})


class UploadView(TemplateView, FilemanagerMixin):
    template_name = 'filemanager/filemanager_upload.html'
    extra_breadcrumbs = [{
        'path' : '#',
        'label': 'Upload'
        }]


class UploadFileView(FilemanagerMixin, View):
    def post(self, request, *args, **kwargs):
        if len(request.FILES) != 1:
            return HttpResponseBadRequest("Just a single file please.")

        # TODO: get filepath and validate characters in name, validate mime type and extension
        filename = self.fm.upload_file(filedata=request.FILES['files[]'])

        return HttpResponse(json.dumps({
            'files': [{'name': filename}],
            }))


class DirectoryCreateView(FilemanagerMixin, FormView):
    template_name = 'filemanager/filemanager_create_directory.html'
    form_class = DirectoryCreateForm
    extra_breadcrumbs = [{
        'path' : '#',
        'label': 'Create directory'
        }]

    def get_success_url(self):
        url = '%s?path=%s' % (reverse('filemanager:browser'), self.fm.path)
        if hasattr(self, 'popup') and self.popup:
            url += '&popup=1'
        return url

    def form_valid(self, form):
        self.fm.create_directory(form.cleaned_data.get('directory_name'))
        return super(DirectoryCreateView, self).form_valid(form)


class RenameView(FilemanagerMixin, FormView):
    template_name = 'filemanager/rename_modal.html'
    form_class = RenameForm
    extra_breadcrumbs = [{
        'path' : '#',
        'label': 'Rename'
        }]

    def get_success_url(self):
        url = '%s?path=%s' % (reverse('filemanager:browser'), self.fm.path)
        if hasattr(self, 'popup') and self.popup:
            url += '&popup=1'
        return url

    def form_valid(self, form):
        self.fm.rename(form.cleaned_data.get('old_name'), form.cleaned_data.get('input_name'))

        return super(RenameView, self).form_valid(form)


class DeleteView(FilemanagerMixin, View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        json_data = json.loads(request.body)
        try:
            for files in json_data['files']:
                self.fm.remove(files)

        except Exception as e:
            print(e)
        return HttpResponse('success')
