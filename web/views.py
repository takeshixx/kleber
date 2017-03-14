import logging

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.conf import settings
import pygments.formatters

from .models import KleberInput, Voucher
from .forms import CreatePasteForm, UploadFileForm
from rest_framework.authtoken.models import Token
from mal.shortcuts import remove_metadata, retrieve_metadata

LOGGER = logging.getLogger(__name__)


def index(request):
    try:
        return render(request, 'index.html')
    except Exception as e:
        LOGGER.exception(e)
        raise


def get_uploads(request, shortcut=None):
    try:
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
                uploads = KleberInput.objects.filter(owner=request.user).order_by('-created')
                uploads = [u.cast() for u in uploads]
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
                return redirect('users_login')
    except Exception as e:
        LOGGER.exception(e)
        raise


def uploads_plain(request, shortcut):
    try:
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
            mimetype = doc.mimetype or 'application/octet-stream'
            return HttpResponse(doc.uploaded_file.file.read(),
                                content_type=mimetype)
        else:
            return HttpResponse(doc.content)
    except Exception as e:
        LOGGER.exception(e)
        raise


def upload(request, shortcut=None):
    try:
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
                    file = upload_form.save()
                    file.owner = request.user
                    if not file.check_quota():
                        upload_form.add_error('uploaded_file', 'No quota left')
                        return render(request, 'pastes/create.html', {'form': paste_form,
                                                                      'upload_form': upload_form})
                    file.set_lifetime(request.POST.get('lifetime'))
                    if request.POST.get('secure_shortcut') == 'on':
                        file.secure_shortcut = True
                    file.set_shortcut()
                    if password:
                        file.set_password(password)
                    file.checksum = file.calc_checksum_from_file()
                    remove_meta = request.POST.get('remove_meta')
                    try:
                        remove_meta = int(remove_meta)
                    except ValueError:
                        remove_meta = 0
                    if remove_meta and remove_meta > 1:
                        meta_status, meta_message = remove_metadata(settings.MEDIA_ROOT + file.uploaded_file.url)
                        file.remove_meta = meta_status
                        file.remove_meta_message = meta_message
                        if meta_status:
                            file.clean_checksum = file.calc_checksum_from_file()
                    elif remove_meta == 1:
                        file.store_metadata_dict(
                            retrieve_metadata(settings.MEDIA_ROOT + file.uploaded_file.url))
                        file.remove_meta = False
                        file.remove_meta_message = 'Metadata stored, but not removed'
                    file.save()
                    response = redirect('uploads_short',
                                        shortcut=file.shortcut)
                    if password:
                        response['Location'] += '?password=' + password
                    return response
            else:
                paste_form = CreatePasteForm(request.POST)
                if paste_form.is_valid():
                    paste = paste_form.save()
                    paste.set_lifetime(request.POST.get('lifetime'))
                    if request.POST.get('secure_shortcut') == 'on':
                        paste.secure_shortcut = True
                    paste.set_shortcut()
                    if request.user.is_authenticated:
                        paste.owner = request.user
                        if not paste.check_quota():
                            paste_form.add_error('uploaded_file', 'No quota left')
                            return render(request, 'pastes/create.html', {'form': paste_form,
                                                                          'upload_form': upload_form})
                    if password:
                        paste.set_password(password)
                    paste.save()
                    response = redirect('uploads_short',
                                        shortcut=paste.shortcut)
                    if password:
                        response['Location'] += '?password=' + password
                    return response
        return render(request, 'pastes/create.html', {'form': paste_form,
                                                      'upload_form': upload_form})
    except Exception as e:
        LOGGER.exception(e)
        raise


def delete(request, shortcut):
    try:
        if request.user.is_authenticated:
            doc = get_object_or_404(KleberInput, shortcut=shortcut)
            if request.user == doc.owner:
                doc.delete()
            return redirect('upload_history')
        else:
            return redirect('index')
    except Exception as e:
        LOGGER.exception(e)
        raise


def user_account(request):
    try:
        tokens = Token.objects.filter(user=request.user)
        vouchers = Voucher.objects.filter(owner=request.user)
        return render(request, 'users/profile.html', {'tokens': tokens,
                                                      'vouchers': vouchers})
    except Exception as e:
        LOGGER.exception(e)
        raise


def user_token_create(request):
    try:
        if request.user.is_authenticated:
            token = Token(user=request.user)
            token.save()
            return redirect('users_account')
        else:
            return redirect('account_login')
    except Exception as e:
        LOGGER.exception(e)
        raise


def user_token_delete(request, token):
    try:
        if request.user.is_authenticated:
            token = get_object_or_404(Token, user=request.user, key=token)
            token.delete()
            return redirect('users_account')
        else:
            return redirect('account_login')
    except Exception as e:
        LOGGER.exception(e)
        raise


def user_voucher_create(request):
    try:
        if request.user.is_authenticated:
            if not request.user.has_perm('web.add_voucher'):
                return HttpResponse(status=403)
            voucher = Voucher()
            voucher.owner = request.user
            voucher.save()
            return redirect('users_account')
        else:
            return redirect('account_login')
    except Exception as e:
        LOGGER.exception(e)
        raise


def user_voucher_delete(request, code):
    try:
        if request.user.is_authenticated:
            if not request.user.has_perm('web.delete_voucher'):
                return HttpResponse(status=403)
            voucher = get_object_or_404(Voucher, code=code)
            voucher.delete()
            return redirect('users_account')
        else:
            return redirect('account_login')
    except Exception as e:
        LOGGER.exception(e)
        raise


def about(request):
    try:
        return render(request, 'about.html')
    except Exception as e:
        LOGGER.exception(e)
        raise


def cli(request):
    try:
        return  render(request, 'cli.html')
    except Exception as e:
        LOGGER.exception(e)
        raise
