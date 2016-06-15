# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import urlparse


class LocalFileStorageManager(object):
    """
    Class that encapsulates logic for resolving local storage paths.

    Toolkit needs to store cache data, logs and other items at runtime.
    Some of this data is global, other is per site or per configuraiton.

    This class provides a consistent and centralized interface for resolving
    such paths and also handles compatibility across generations of path
    standards if and when these change between releases.

    .. note:: All paths returned by this class are local to the currently running
              user and typically private or with limited access settings for other users.

    :constant CORE_V17: Indicates compatibility with Core 0.17 or earlier
    :constant CORE_V18: Indicates compatibility with Core 0.18 or later

    :constant LOGGING: Indicates a path suitable for storing logs, useful for debugging
    :constant CACHE: Indicates a path suitable for storing cache data that can be deleted without
                       any loss of functionality or state.
    :constant PERSISTENT: Indicates a path suitable for storing settings and other data that is needs
                          to be retained between sessions.
    """
    # generation of path structures
    (CORE_V17, CORE_V18) = range(2)

    # supported types of paths
    (LOGGING, CACHE, PERSISTENT) = range(3)

    @classmethod
    def get_global_root(cls, path_type, generation=CORE_V18):
        """
        Returns a generic Shotgun storage root.

        The following paths will be used:

            - On the mac, paths will point into ``~/Library/PATH_TYPE/Shotgun``, where PATH_TYPE
              is controlled by the path_type property.
            - On Windows, paths will created below a ``%APPDATA%/Shotgun`` root point.
            - On Linux, paths will be created below a ``~/.shotgun`` root point.

        .. note:: This method does not ensure that the folder exists.

        :param path_type: Type of path to return. One of ``LocalFileStorageManager.LOGGING``,
                          ``LocalFileStorageManager.CACHE``, ``LocalFileStorageManager.PERSISTENT``, where
                          logging is a path where log- and debug related data should be stored,
                          cache is a location intended for cache data, e.g. data that can be deleted
                          without affecting the state of execution, and persistent is a location intended
                          for data that is meant to be persist. This includes things like settings and
                          preferences.
        :param generation: Path standard generation to use. Defaults to ``LocalFileStorageManager.CORE_V18``,
                           which is the current generation of paths.
        :return: Path as string
        """
        if generation == cls.CORE_V18:

            # current generation of paths
            if sys.platform == "darwin":
                if path_type == cls.CACHE:
                    return os.path.expanduser("~/Library/Caches/Shotgun")
                elif path_type == cls.PERSISTENT:
                    return os.path.expanduser("~/Library/Application Support/Shotgun")
                elif path_type == cls.LOGGING:
                    return os.path.expanduser("~/Library/Logs/Shotgun")
                else:
                    raise ValueError("Unsupported path type!")

            elif sys.platform == "win32":
                if path_type == cls.CACHE:
                    return os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun")
                elif path_type == cls.PERSISTENT:
                    return os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun", "Data")
                elif path_type == cls.LOGGING:
                    return os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun", "Logs")
                else:
                    raise ValueError("Unsupported path type!")

            elif sys.platform.startswith("linux"):
                if path_type == cls.CACHE:
                    return os.path.expanduser("~/.shotgun")
                elif path_type == cls.PERSISTENT:
                    return os.path.expanduser("~/.shotgun/data")
                elif path_type == cls.LOGGING:
                    return os.path.expanduser("~/.shotgun/logs")
                else:
                    raise ValueError("Unsupported path type!")

            else:
                raise ValueError("Unknown platform: %s" % sys.platform)

        if generation == cls.CORE_V17:

            # previous generation of paths
            if sys.platform == "darwin":
                if path_type == cls.CACHE:
                    return os.path.expanduser("~/Library/Caches/Shotgun")
                elif path_type == cls.PERSISTENT:
                    return os.path.expanduser("~/Library/Application Support/Shotgun")
                elif path_type == cls.LOGGING:
                    return os.path.expanduser("~/Library/Logs/Shotgun")
                else:
                    raise ValueError("Unsupported path type!")

            elif sys.platform == "win32":
                if path_type == cls.CACHE:
                    return os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun")
                elif path_type == cls.PERSISTENT:
                    return os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun")
                elif path_type == cls.LOGGING:
                    return os.path.join(os.environ.get("APPDATA", "APPDATA_NOT_SET"), "Shotgun")
                else:
                    raise ValueError("Unsupported path type!")

            elif sys.platform.startswith("linux"):
                if path_type == cls.CACHE:
                    return os.path.expanduser("~/.shotgun")
                elif path_type == cls.PERSISTENT:
                    return os.path.expanduser("~/.shotgun")
                elif path_type == cls.LOGGING:
                    return os.path.expanduser("~/.shotgun")
                else:
                    raise ValueError("Unsupported path type!")

            else:
                raise ValueError("Unknown platform: %s" % sys.platform)

    @classmethod
    def get_site_root(cls, hostname, path_type, generation=CORE_V18):
        """
        Returns a cache root where items can be stored on a per site basis.

        For more details, see :meth:`LocalFileStorageManager.get_global_root`.

        .. note:: This method does not ensure that the folder exists.

        :param hostname: Shotgun hostname as string, e.g. 'https://foo.shotgunstudio.com'
        :param path_type: Type of path to return. One of ``LocalFileStorageManager.LOGGING``,
                          ``LocalFileStorageManager.CACHE``, ``LocalFileStorageManager.PERSISTENT``, where
                          logging is a path where log- and debug related data should be stored,
                          cache is a location intended for cache data, e.g. data that can be deleted
                          without affecting the state of execution, and persistent is a location intended
                          for data that is meant to be persist. This includes things like settings and
                          preferences.
        :param generation: Path standard generation to use. Defaults to ``LocalFileStorageManager.CORE_V18``,
                           which is the current generation of paths.
        :return: Path as string
        """
        # get site only; https://www.FOO.com:8080 -> www.foo.com
        base_url = urlparse.urlparse(hostname).netloc.split(":")[0].lower()

        if generation > cls.CORE_V17:
            # for 0.18, in order to apply further shortcuts to avoid hitting
            # MAX_PATH on windows, strip shotgunstudio.com from all
            # hosted sites
            #
            # mysite.shotgunstudio.com -> mysite
            # shotgun.internal.int     -> shotgun.internal.int
            #
            base_url = base_url.replace(".shotgunstudio.com", "")

        return os.path.join(
            cls.get_global_root(path_type, generation),
            base_url
        )

    @classmethod
    def get_configuration_root(cls, hostname, project_id, pipeline_config_id, path_type, generation=CORE_V18):
        """
        Returns the storage root for any data that is project and config specific.

        For more details, see :meth:`LocalFileStorageManager.get_global_root`.

        .. note:: This method does not ensure that the folder exists.

        :param hostname: Shotgun hostname as string, e.g. 'https://foo.shotgunstudio.com'
        :param project_id: Shotgun project id as integer. For the site config, this should be None.
        :param pipeline_config_id: Shotgun pipeline config id. None for bootstraped configs.
        :param path_type: Type of path to return. One of ``LocalFileStorageManager.LOGGING``,
                          ``LocalFileStorageManager.CACHE``, ``LocalFileStorageManager.PERSISTENT``, where
                          logging is a path where log- and debug related data should be stored,
                          cache is a location intended for cache data, e.g. data that can be deleted
                          without affecting the state of execution, and persistent is a location intended
                          for data that is meant to be persist. This includes things like settings and
                          preferences.
        :param generation: Path standard generation to use. Defaults to ``LocalFileStorageManager.CORE_V18``,
                           which is the current generation of paths.
        :return: Path as string
        """
        if generation == cls.CORE_V17:

            # older paths are on the form root/mysite.shotgunstudio.com/project_123/config_123
            return os.path.join(
                cls.get_site_root(hostname, path_type, generation),
                "project_%s" % project_id,
                "config_%s" % pipeline_config_id
            )

        else:

            # new paths are on the form
            # project 123, config 33:     root/mysite/p123c33
            # project 123 without config: root/mysite/p123
            # site project:               root/mysite/site
            if pipeline_config_id is None:
                # unmanaged config
                pc_suffix = ""
            else:
                pc_suffix = "c%d" % pipeline_config_id

            if project_id is None:
                # site configuration
                project_config_folder = "site%s" % pc_suffix
            else:
                project_config_folder = "p%d%s" % (project_id, pc_suffix)

            return os.path.join(
                cls.get_site_root(hostname, path_type, generation),
                project_config_folder
            )