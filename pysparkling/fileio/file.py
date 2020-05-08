from __future__ import absolute_import

from io import BytesIO
import logging

from . import codec
from . import fs

log = logging.getLogger(__name__)


class File(object):
    """File object.

    :param file_name: Any file name.
    """

    def __init__(self, file_name):
        self.file_name = file_name
        self.fs = fs.get_fs(file_name)(file_name)
        self.codec = codec.get_codec(file_name)()

    @staticmethod
    def resolve_filenames(all_expr):
        """resolve expression for a filename

        :param all_expr:
            A comma separated list of expressions. The expressions can contain
            the wildcard characters ``*`` and ``?``. It also resolves Spark
            datasets to the paths of the individual partitions
            (i.e. ``my_data`` gets resolved to
            ``[my_data/part-00000, my_data/part-00001]``).

        :returns: A list of file names.
        :rtype: list
        """
        files = []
        for expr in all_expr.split(','):
            expr = expr.strip()
            files += fs.get_fs(expr).resolve_filenames(expr)
        log.debug('Filenames: {0}'.format(files))
        return files

    @classmethod
    def get_content(cls, all_expr):
        """Return all files matching or in folder matching one of the given expression

        :param all_expr:
            A list of expressions.
            The expressions can contain the wildcard characters ``*`` and ``?``.

        :returns: A list of file names.
        :rtype: list
        """
        files = []
        for expr in all_expr:
            expr = expr.strip()
            files += fs.get_fs(expr).resolve_content(expr)
        log.debug('Filenames: {0}'.format(files))
        return files

    def exists(self):
        """Checks both for a file or directory at this location.

        :returns: True or false.
        """
        return self.fs.exists()

    def load(self):
        """Load the data from a file.

        :rtype: io.BytesIO
        """
        stream = self.fs.load()
        stream = self.codec.decompress(stream)
        return stream

    def dump(self, stream=None):
        """Writes a stream to a file.

        :param stream:
            A BytesIO instance. ``bytes`` are also possible and are converted
            to BytesIO.

        :rtype: File
        """
        if stream is None:
            stream = BytesIO()

        if isinstance(stream, bytes):
            stream = BytesIO(stream)

        stream = self.codec.compress(stream)
        self.fs.dump(stream)

        return self

    def make_public(self, recursive=False):
        """Makes the file public. Currently only supported on S3.

        :param recursive: Whether to apply this recursively.
        :rtype: File
        """
        self.fs.make_public(recursive)
        return self
