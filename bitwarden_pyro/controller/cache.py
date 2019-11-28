import os
import json
import stat
import time

from bitwarden_pyro.util.logger import ProjectLogger
from bitwarden_pyro.settings import NAME


class CacheMetadata:
    """Model class containing cache metadata"""

    def __init__(self, time_created=None, count=None):
        self.time_created = time_created
        self.count = count

    def to_dict(self):
        """Convert the instance to a dict ready to be serialised"""

        return {
            'time': self.time_created,
            'count': self.count
        }

    @staticmethod
    def create(dictionary):
        """Create an instance of CacheMetadata from a dict"""

        return CacheMetadata(
            dictionary['time'],
            dictionary['count']
        )


class Cache:
    """Read and write item data to cache files"""

    _cache_dir = f'~/.cache/{NAME}/'
    _items_file = 'items.json'
    _meta_file = 'items.metadata'

    def __init__(self, expiry):
        self._path = None
        self._meta = None

        self._logger = ProjectLogger().get_logger()
        self._expiry = expiry  # Negative values disable cache

        self.__items_path = lambda: os.path.join(self._path, self._items_file)
        self.__meta_path = lambda: os.path.join(self._path, self._meta_file)

        self.__init_meta()

    def __init_meta(self):
        if not self.should_cache():
            self._logger.info("Disabling caching of items")
            return

        try:
            self._path = os.path.expanduser(self._cache_dir)

            if not os.path.isdir(self._path):
                os.makedirs(self._path)
            else:
                mpath = self.__meta_path()
                ipath = self.__items_path()

                # Both items and metadata file need to be present,
                # however, their validity is not checked
                if os.path.isfile(ipath) and os.path.isfile(mpath):
                    with open(mpath, 'r') as file:
                        meta_json = json.load(file)

                    self._meta = CacheMetadata.create(meta_json)
                    self._logger.debug("Initialised meta data from %s", mpath)

        except IOError:
            raise CacheException("Failed to initialise cache metadata")

    def should_cache(self):
        """ Returns true if expiry is a positive number """
        return self._expiry > 0

    def __cache_age(self):
        """Returns the age in days of the saved cache"""
        if self._meta is None:
            raise CacheException("Cache metadata has not been initialised")

        seconds = (time.time() - self._meta.time_created)
        days = seconds / 86_400
        return days

    def get(self):
        """Return a collection of cached items"""

        try:
            ipath = self.__items_path()
            self._logger.debug("Reading cached items from %s", ipath)

            with open(ipath, 'r') as file:
                items = json.load(file)

            return items
        except IOError:
            raise CacheException(f"Failed to write cache data to {self._path}")

    def save(self, items):
        """Sanitise and save a collection of items to a cache files"""

        try:
            self._logger.debug("Writing cache to %s", self._path)
            self._meta = CacheMetadata(time.time(), len(items))

            meta_path = os.path.join(self._path, self._meta_file)
            with open(meta_path, 'w') as file:
                json.dump(self._meta.to_dict(), file)

            # Chmod to 600
            os.chmod(meta_path, stat.S_IWRITE | stat.S_IREAD)

            # Sanitize cache by removing sensitive data
            for item in items:
                if item.get('login'):
                    if item.get('login').get('password') is not None:
                        item['login']['password'] = None
                    if item.get('login').get('totp') is not None:
                        item['login']['totp'] = None

            item_path = os.path.join(self._path, self._items_file)
            with open(item_path, 'w') as file:
                json.dump(items, file)

            # Chmod to 600
            os.chmod(item_path, stat.S_IWRITE | stat.S_IREAD)
        except IOError:
            raise CacheException(f"Failed to write cache data to {self._path}")

    def has_items(self):
        """Returns true if cache is enabled, not expired and contains items"""

        return self._expiry > 0 \
            and self._meta is not None \
            and self._meta.count > 0 \
            and self.__cache_age() < self._expiry


class CacheException(Exception):
    """Base exception raised by Cache objects"""
