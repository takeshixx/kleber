from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
import pygments.formatters

from .models import KleberInput
from .forms import RegisterUser, CreatePasteForm, UploadFileForm, ChangeUserForm
from mal.shortcuts import remove_metadata, retrieve_metadata


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
        highlightcss = pygments.formatters.HtmlFormatter(
            style=pygments.styles.get_style_by_name('colorful')).get_style_defs('.highlight')
        return render(request, 'pastes/view.html', {'paste': doc,
                                                    'highlightcss': highlightcss})
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
                show_lines = paginator.page(paginator.num_pages)
            return render(request, 'pastes/history.html', {'pastes': uploads,
                                                           'lines': show_lines})
        else:
            return redirect('users_login')


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
    if doc.is_file:
        mimetype = doc.mimetype or 'application/octet-stream'
        return HttpResponse(doc.uploaded_file.file.read(),
                            content_type=mimetype)
    else:
        return HttpResponse(doc.content)


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
        if request.user.is_authenticated and request.FILES:
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                file = upload_form.save()
                file.set_lifetime(request.POST.get('lifetime'))
                if request.POST.get('secure_url') == 'on':
                    file.secure_shortcut = True
                file.owner = request.user
                file.checksum = file.calc_checksum_from_file()
                remove_meta = request.POST.get('remove_meta')
                try:
                    remove_meta = int(remove_meta)
                except ValueError:
                    remove_meta = 0
                if remove_meta and remove_meta > 1:
                    meta_status, meta_message = remove_metadata(file.uploaded_file.url)
                    file.remove_meta = meta_status
                    file.remove_meta_message = meta_message
                    if meta_status:
                        file.clean_checksum = file.calc_checksum_from_file()
                elif remove_meta == 1:
                    file.store_metadata_dict(
                        retrieve_metadata(file.uploaded_file.url))
                    file.remove_meta = False
                    file.remove_meta_message = 'Metadata stored, but not removed'
                file.save()
                return redirect('uploads_short', shortcut=file.shortcut)
        else:
            paste_form = CreatePasteForm(request.POST)
            if paste_form.is_valid():
                paste = paste_form.save()
                paste.set_lifetime(request.POST.get('lifetime'))
                if request.POST.get('secure_url') == 'on':
                    paste.secure_shortcut = True
                if request.user.is_authenticated:
                    paste.owner = request.user
                paste.save()
                return redirect('uploads_short', shortcut=paste.shortcut)
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


def user_register(request):
    if request.method == 'POST':
        form = RegisterUser(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users_login')
    else:
        form = RegisterUser()
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('/')


def users_pwreset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users_login')
    else:
        form = PasswordResetForm()
    return render(request, 'users/pwreset.html', {'form': form})


def users_pwchange(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('users_account')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/pwchange.html', {'form': form})


def users_userchange(request):
    if request.method == 'POST':
        form = ChangeUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('users_account')
    else:
        form = ChangeUserForm(instance=request.user)
    return render(request, 'users/userchange.html', {'form': form})


def user_account(request):
    return render(request, 'users/profile.html')


def about(request):
    return render(request, 'about.html')


def cli(request):
    return  render(request, 'cli.html')
