import datetime
import hashlib
import random
import magic
import mimetypes
import string
import pygments
import pygments.lexers
import pygments.formatters
import pygments.styles

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group, Permission


# TODO: properly link to user objects
class UserConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.TextField(default='default')


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

    def __unicode__(self):
        return self.shortcut

    def __str__(self):
        return self.shortcut

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_shortcut()
        self.set_mimetype()
        self.set_lexer()
        self.set_size()
        super(KleberInput, self).save(force_insert=force_insert,
                                      force_update=force_update,
                                      using=using,
                                      update_fields=update_fields)

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
        else:
            if self.secure_shortcut:
                min = 25
                max = 40
            else:
                min = 3
                max = 9
            while True:
                url = ''.join(random.choice(
                    string.ascii_letters + string.digits) for _ in range(random.randrange(min, max)))
                if not Paste.objects.filter(shortcut=url).first() and not url in KLEBER_SHORTURL_BAD_WORDS:
                    self.shortcut = url
                    break

    def set_lexer(self, lexer='auto'):
        if not lexer or lexer == 'auto' and self.mimetype.startswith('text'):
            _lexer = None
            try:
                _lexer = pygments.lexers.get_lexer_for_mimetype(self.mimetype)
            except pygments.util.ClassNotFound:
                pass
            if not _lexer:
                try:
                    _lexer = pygments.lexers.get_lexer_for_filename(self.name)
                except pygments.util.ClassNotFound:
                    pass
            if not _lexer:
                try:
                    _lexer = pygments.lexers.guess_lexer(self.get_content())
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
            self.mimetype = magic.from_buffer(content)
            if self.mimetype == 'data':
                raise TypeError
            self.mimetype_long = magic.from_buffer(content)
        except Exception:
            self.mimetype = 'text/plain'
            self.mimetype_long = 'text/plain'


class File(KleberInput):
    uploaded_file = models.FileField(upload_to='uploads/',
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
        print(filename)
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
            file = self.uploaded_file.name
        try:
            self.mimetype = magic.from_file(file, mime=True)
            self.mimetype_long = magic.from_file(file)
        except Exception:
            return 'data'

