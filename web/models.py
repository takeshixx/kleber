import datetime
import hashlib
import random
import secrets
import magic
import logging
import mimetypes
import pygments
import pygments.lexers
import pygments.formatters
import pygments.styles

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_migrate, pre_save
from django.dispatch import receiver
from django.conf import settings
from rest_framework.authtoken.models import Token

LOGGER = logging.getLogger(__name__)


class KleberInput(models.Model):
    owner = models.ForeignKey(User,
                              null=True)
    name = models.CharField(max_length=100,
                            blank=True,
                            null=True)
    shortcut = models.CharField(max_length=60,
                                unique=True)
    size = models.IntegerField()
    mimetype = models.TextField()
    mimetype_long = models.TextField()
    created = models.DateTimeField(auto_now_add=True,
                                   blank=True)
    lifetime = models.DateTimeField(blank=True,
                                    null=True)
    burn_after_reading = models.BooleanField(default=False)
    hits = models.IntegerField(default=0)
    is_encrypted = models.BooleanField(default=False)
    is_file = models.BooleanField(default=False)
    secure_shortcut = models.BooleanField(default=False)
    lexer = models.TextField()
    password = models.CharField(max_length=100,
                                null=True,
                                blank=True)

    def __unicode__(self):
        return self.shortcut

    def __str__(self):
        return self.shortcut

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_mimetype()
        self.set_lexer()
        self.set_size()
        self.set_shortcut()
        super(KleberInput, self).save(force_insert=force_insert,
                                      force_update=force_update,
                                      using=using,
                                      update_fields=update_fields)

    def check_quota(self):
        current_quota = KleberInput.objects.filter(owner=self.owner)\
                                           .aggregate(models.Sum('size'))
        if current_quota.get('size__sum') is not None:
            total_quota = current_quota.get('size__sum') + self.size
        else:
            total_quota = self.size
        if self.owner.has_perm('web.quota_unlimited_file'):
            return True
        elif self.owner.has_perm('web.quota_4g_file'):
            if total_quota >= 4294967296:
                return False
        elif self.owner.has_perm('web.quota_1g_file'):
            if total_quota >= 1073741824:
                return False
        else:
            if total_quota >= 536870912:
                return
        return True

    def set_lifetime(self, lifetime):
        try:
            lifetime = int(lifetime)
        except (ValueError, TypeError):
            return
        if lifetime == 1:
            self.burn_after_reading = True
        elif lifetime > 1:
            self.lifetime = datetime.datetime.now() + \
                            datetime.timedelta(0, int(lifetime))

    def lifetime_expired(self):
        if not self.lifetime:
            return False
        if self.lifetime <= timezone.now():
            return True
        else:
            return False

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return True if password == self.password else False

    def set_shortcut(self, shortcut=None):
        # TODO: do we still need these? maybe they need to be updated
        KLEBER_SHORTURL_BAD_WORDS = [
            'history',
            'new',
            'users',
            'register',
            'login',
            'logout',
            'about',
            'faq',
            'cli',
            'pastes',
            'paste']
        if shortcut:
            self.shortcut = shortcut
        elif self.shortcut:
            print('shortcut already set')
            return
        else:
            print('setting shortcut')
            if self.secure_shortcut:
                min = 25
                max = 40
            else:
                min = 3
                max = 9
            while True:
                url = secrets.token_urlsafe(random.randrange(min, max))
                if not Paste.objects.filter(shortcut=url).first() and \
                        not url in KLEBER_SHORTURL_BAD_WORDS:
                    self.shortcut = url
                    break

    def set_lexer(self, lexer='auto'):
        if not lexer or lexer == 'auto' and self.mimetype.startswith('text'):
            _lexer = None
            if self.name:
                try:
                    _lexer = pygments.lexers.get_lexer_for_filename(self.name)
                except pygments.util.ClassNotFound:
                    pass
            if not _lexer:
                try:
                    _lexer = pygments.lexers.get_lexer_for_mimetype(self.mimetype)
                except pygments.util.ClassNotFound:
                    pass
            if not _lexer:
                content = self.get_content()
                if isinstance(content, bytes):
                    content = content.decode()
                try:
                    _lexer = pygments.lexers.guess_lexer(content)
                except pygments.util.ClassNotFound:
                    pass
            if _lexer.name == 'Text only':
                self.lexer = 'text'
            else:
                self.lexer = _lexer.name
        else:
            for _lexer in pygments.lexers.get_all_lexers():
                if lexer == _lexer[0]:
                    self.lexer = lexer
                    return

    @property
    def content_lexed(self):
        _content = self.get_content()
        if not self.lexer:
            return _content
        lexer = None
        try:
            lexer = pygments.lexers.get_lexer_by_name(self.lexer)
        except pygments.util.ClassNotFound as e:
            pass
        if not lexer:
            lexer = pygments.lexers.get_lexer_by_name('text')
        _content = pygments.highlight(
            _content,
            lexer,
            pygments.formatters.HtmlFormatter(
                linenos='table'))
        return _content

    def cast(self):
        for name in dir(self):
            try:
                attr = getattr(self, name)
                if isinstance(attr, self.__class__):
                    return attr
            except:
                pass
        return self


class Paste(KleberInput):
    content = models.TextField()

    def __repr__(self):
        return '<Paste Shortcut: {} Name: {} '.format(self.shortcut, self.name.encode('utf-8'))

    def set_size(self):
        self.size = len(self.get_content())

    def get_content(self):
        return self.content

    def set_mimetype(self, content=None):
        # First, try do determine the mimetype based on the file extension
        mime = mimetypes.guess_type(self.name)
        if mime[0]:
            self.mimetype = mime[0]
            return
        content = content or self.content
        # Second, try to guess the mimetype from the content
        try:
            mimetype = magic.from_buffer(content)
            if mimetype == 'data':
                raise TypeError
            else:
                self.mimetype = mimetype
        except TypeError:
            # If the magic module fails, try it with pygments
            mimetype = pygments.lexers.guess_lexer(content)
            if not mimetype:
                self.mimetype = 'text/plain'
            else:
                if mimetype.mimetypes:
                    self.mimetype = mimetype.mimetypes[0]
                else:
                    self.mimetype = 'text/plain'
        except Exception as e:
            LOGGER.exception(e)
            self.mimetype = 'text/plain'


class File(KleberInput):
    uploaded_file = models.FileField(upload_to=settings.UPLOAD_PATH,
                                     default=None)
    remove_meta = models.BooleanField(default=False)
    remove_meta_message = models.TextField()
    metadata = models.TextField()
    checksum = models.TextField()
    clean_checksum = models.TextField()

    def __repr__(self):
        return '<File Shortcut: {} Name: {} '.format(self.shortcut,
                                                     self.name.encode('utf-8'))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.is_file = True
        if not self.name:
            self.name = self.uploaded_file.name
        super(File, self).save(force_insert=force_insert,
                               force_update=force_update,
                               using=using,
                               update_fields=update_fields)

    def calc_checksum_from_file(self, filename=None, blocksize=65536):
        filename = filename or self.uploaded_file.url
        hasher = hashlib.sha256()
        with open(filename, 'rb') as f:
            b = f.read(blocksize)
            while len(b) > 0:
                hasher.update(b)
                b = f.read(blocksize)
        return hasher.hexdigest()

    def store_metadata_dict(self, metadata):
        if not metadata:
            return
        _metadata = ''
        for item in metadata.items():
            _metadata += str(item[0]) + ':\t' + str(item[1]) + '\n'
        self.metadata = _metadata

    @property
    def content(self):
        return self.get_content()

    def get_content(self):
        return self.uploaded_file.file.read()

    def set_size(self):
        self.size = self.uploaded_file.size

    def set_mimetype(self, file=None):
        if not file:
            file = self.uploaded_file.url
        try:
            self.mimetype = magic.from_file(file, mime=True)
            self.mimetype_long = magic.from_file(file)
        except Exception:
            return 'data'


class Voucher(models.Model):
    code = models.TextField()
    owner = models.ForeignKey(User,
                              null=True,
                              related_name='owner_user')
    receiver = models.ForeignKey(User,
                                 null=True,
                                 related_name='receiver_user')
    created = models.DateTimeField(auto_now_add=True,
                                   blank=True)
    lifetime = models.DateTimeField(blank=True,
                                    null=True)
    used = models.BooleanField(default=False)

    def __unicode__(self):
        return self.code

    def __str__(self):
        return self.code

    def save(self, force_insert=False, force_update=False,
             using=None, update_fields=None):
        self.generate_code()
        super(Voucher, self).save(force_insert=force_insert,
                                  force_update=force_update,
                                  using=using,
                                  update_fields=update_fields)

    def generate_code(self):
        self.code = secrets.token_hex(16)


@receiver(post_delete, sender=File)
def file_post_delete_handler(sender, **kwargs):
    """Make sure files will be deleted from the file system."""
    file = kwargs['instance']
    storage, path = file.uploaded_file.storage, file.uploaded_file.path
    storage.delete(path)


@receiver(post_migrate)
def init_groups(sender, **kwargs):
    file_uploads_group, created = Group.objects.get_or_create(
        name='Can upload files')
    file_ct = ContentType.objects.get_for_model(File)
    file_add_perm, created = Permission.objects.get_or_create(
        codename='add_file',
        name='Can add file',
        content_type=file_ct)
    file_change_perm, created = Permission.objects.get_or_create(
        codename='change_file',
        name='Can change file',
        content_type=file_ct)
    file_delete_perm, created = Permission.objects.get_or_create(
        codename='delete_file',
        name='Can delete file',
        content_type=file_ct)
    file_uploads_group.permissions.add(file_add_perm)
    file_uploads_group.permissions.add(file_change_perm)
    file_uploads_group.permissions.add(file_delete_perm)

    voucher_group, created = Group.objects.get_or_create(
        name='Can use vouchers')
    voucher_ct = ContentType.objects.get_for_model(Voucher)
    voucher_add_perm, created = Permission.objects.get_or_create(
        codename='add_voucher',
        name='Can add voucher',
        content_type=voucher_ct)
    voucher_change_perm, created = Permission.objects.get_or_create(
        codename='change_voucher',
        name='Can change voucher',
        content_type=voucher_ct)
    voucher_delete_perm, created = Permission.objects.get_or_create(
        codename='delete_voucher',
        name='Can delete voucher',
        content_type=voucher_ct)
    voucher_group.permissions.add(voucher_add_perm)
    voucher_group.permissions.add(voucher_change_perm)
    voucher_group.permissions.add(voucher_delete_perm)

    quota_1g_group, created = Group.objects.get_or_create(
        name='Can upload 1G')
    file_ct = ContentType.objects.get_for_model(KleberInput)
    quota_1g_perm, created = Permission.objects.get_or_create(
        codename='quota_1g_file',
        name='Can upload 1G',
        content_type=file_ct)
    quota_1g_group.permissions.add(quota_1g_perm)

    quota_4g_group, created = Group.objects.get_or_create(
        name='Can upload 4G')
    file_ct = ContentType.objects.get_for_model(KleberInput)
    quota_4g_perm, created = Permission.objects.get_or_create(
        codename='quota_4g_file',
        name='Can upload 4G',
        content_type=file_ct)
    quota_4g_group.permissions.add(quota_4g_perm)

    quota_unlimited_group, created = Group.objects.get_or_create(
        name='Can upload unlimited')
    file_ct = ContentType.objects.get_for_model(KleberInput)
    quota_unlimited_perm, created = Permission.objects.get_or_create(
        codename='quota_unlimited_file',
        name='Can upload unlimited',
        content_type=file_ct)
    quota_unlimited_group.permissions.add(quota_unlimited_perm)
