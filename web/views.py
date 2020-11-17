import logging

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
import pygments.formatters

from .models import KleberInput, Voucher
from .forms import CreatePasteForm, UploadFileForm
from rest_framework.authtoken.models import Token

LOGGER = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')


def get_uploads(request, shortcut=None):
    if shortcut:
        doc = get_object_or_404(KleberInput, shortcut=shortcut)
        doc = doc.cast()
        if doc.burn_after_reading:
            _doc = doc
            doc.delete()
            doc = _doc
        elif doc.lifetime_expired():
            doc.delete()
            raise Http404()
        password = request.GET.get('password')
        if doc.password and not doc.check_password(password):
            return render(request, 'pastes/password.html', {'paste': doc})
        highlightcss = pygments.formatters.HtmlFormatter(
            style=pygments.styles.get_style_by_name('colorful')).get_style_defs('.highlight')
        return render(request, 'pastes/view.html', {'paste': doc,
                                                    'highlightcss': highlightcss,
                                                    'password': password})
    else:
        if request.user.is_authenticated:
            uploads_db = KleberInput.objects.filter(owner=request.user).order_by('-created')
            uploads = []
            for u in uploads_db:
                if u.lifetime_expired():
                    u.delete()
                    continue
                uploads.append(u.cast())
            limit = request.GET.get('limit')
            try:
                limit = int(limit)
            except (ValueError, TypeError):
                limit = 10
            paginator = Paginator(uploads, limit)
            page = request.GET.get('page')
            try:
                show_lines = paginator.page(page)
            except PageNotAnInteger:
                show_lines = paginator.page(1)
            except EmptyPage:
                show_lines = paginator.page(paginator.num_pages)#
            quota = KleberInput.objects.filter(owner=request.user) \
                               .aggregate(models.Sum('size'))
            return render(request, 'pastes/history.html', {'pastes': uploads,
                                                           'lines': show_lines,
                                                           'quota': quota.get('size__sum')})
        else:
            return redirect('account_login')


def uploads_plain(request, shortcut):
    doc = get_object_or_404(KleberInput, shortcut=shortcut)
    doc = doc.cast()
    if doc.burn_after_reading:
        _doc = doc
        doc.delete()
        doc = _doc
    elif doc.lifetime_expired():
        doc.delete()
        raise Http404()
    password = request.GET.get('password')
    if doc.password and not doc.check_password(password):
        return render(request, 'pastes/password.html', {'paste': doc})
    if doc.is_file:
        if doc.mimetype and (doc.mimetype.startswith('image')
                or doc.mimetype.startswith('video')
                or doc.mimetype.startswith('audio')):
            mimetype = doc.mimetype
        elif doc.mimetype and doc.mimetype.startswith('text'):
            mimetype = 'text/plain'
        elif doc.mimetype and doc.mimetype == 'application/pdf':
            response = HttpResponse(doc.uploaded_file.file.read(),
                                    content_type=doc.mimetype)
            response['Content-Disposition'] = 'inline; filename= "{}"'.format(doc.name)
            return response
        else:
            mimetype = 'application/octet-stream'
            response = HttpResponse(doc.uploaded_file.file.read(),
                                    content_type=mimetype)
            response['Content-Disposition'] = 'attachment; filename= "{}"'.format(doc.name)
            return response
        resp = HttpResponse(doc.uploaded_file.file.read(),
                            content_type=mimetype)
        return resp
    else:
        return HttpResponse(doc.content,
                            content_type='text/plain')


def upload(request, shortcut=None):
    doc = KleberInput.objects.filter(shortcut=shortcut).first()
    if doc and not doc.is_file:
        doc = doc.cast()
        paste_form = CreatePasteForm(initial={'content': doc.content,
                                              'name': doc.name})
    else:
        paste_form = CreatePasteForm()
    upload_form = UploadFileForm()
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.is_authenticated and request.FILES:
            if not request.user.has_perm('web.add_file'):
                return HttpResponse(status=403)
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                file = upload_form.save(request=request)
                if upload_form.has_error('uploaded_file'):
                    return render(request, 'pastes/create.html', {'form': paste_form,
                                                                  'upload_form': upload_form})
                response = redirect('uploads_short',
                                    shortcut=file.shortcut)
                if password:
                    response['Location'] += '?password=' + password
                return response
        else:
            paste_form = CreatePasteForm(request.POST)
            if paste_form.is_valid():
                paste = paste_form.save(request=request)
                if paste_form.has_error('content'):
                    return render(request, 'pastes/create.html', {'form': paste_form,
                                                                  'upload_form': upload_form})
                response = redirect('uploads_short',
                                    shortcut=paste.shortcut)
                if password:
                    response['Location'] += '?password=' + password
                return response
    return render(request, 'pastes/create.html', {'form': paste_form,
                                                  'upload_form': upload_form})


def delete(request, shortcut):
    if request.user.is_authenticated:
        doc = get_object_or_404(KleberInput, shortcut=shortcut)
        if request.user == doc.owner:
            doc.delete()
        return redirect('upload_history')
    else:
        return redirect('index')


def user_account(request):
    tokens = Token.objects.filter(user=request.user)
    vouchers = Voucher.objects.filter(owner=request.user)
    return render(request, 'users/profile.html', {'tokens': tokens,
                                                  'vouchers': vouchers})


def user_token_create(request):
    if request.user.is_authenticated:
        token = Token(user=request.user)
        token.save()
        return redirect('users_account')
    else:
        return redirect('account_login')

def user_token_delete(request, token):
    if request.user.is_authenticated:
        token = get_object_or_404(Token, user=request.user, key=token)
        token.delete()
        return redirect('users_account')
    else:
        return redirect('account_login')


def user_voucher_create(request):
    if request.user.is_authenticated:
        if not request.user.has_perm('web.add_voucher'):
            return HttpResponse(status=403)
        voucher = Voucher()
        voucher.owner = request.user
        voucher.save()
        return redirect('users_account')
    else:
        return redirect('account_login')


def user_voucher_delete(request, code):
    if request.user.is_authenticated:
        if not request.user.has_perm('web.delete_voucher'):
            return HttpResponse(status=403)
        voucher = get_object_or_404(Voucher, code=code)
        voucher.delete()
        return redirect('users_account')
    else:
        return redirect('account_login')


def about(request):
    return render(request, 'about.html')


def cli(request):
    return  render(request, 'cli.html')