# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Methods for loading and managing plugins, e.g. Apps, Engines, Hooks etc.

"""

import sys, os
import imp, importlib
import traceback
import inspect
from hashlib import md5
from pprint import pprint
from traceback import format_exc

from ..errors import TankError
from .. import LogManager

log = LogManager.get_logger(__name__)

python3=False
try:
    from cPickle import loads
except:
    python3=True


class TankLoadPluginError(TankError):
    """
    Errors related to git communication
    """

    pass


def load_plugin(plugin_file, valid_base_class, alternate_base_classes=None):
    """
    Load a plugin into memory and extract its single interface class.

    :param plugin_file:             The file to use when looking for the plug-in class to load
    :param valid_base_class:        A type to use when searching for a derived class.
    :param alternate_base_classes:  A list of alternate base classes to be searched for if a class deriving
                                    from valid_base_class can't be found
    :returns:                       A class derived from the base class if found
    :raises:                        Raises a TankError if it fails to load the file or doesn't find exactly
                                    one matching class.
    """
    log.debug('load_plugin called for '+os.path.basename(plugin_file))
    # build a single list of valid base classes including any alternate base classes
    alternate_base_classes = alternate_base_classes or []
    valid_base_classes = [valid_base_class] + alternate_base_classes
    
    #log.debug("loading "+str(plugin_file)+" with valid base classes: "+str(valid_base_classes))

    # construct a uuid and use this as the module name to ensure
    # that each import is unique


    if python3:
        module_uid = md5(plugin_file.encode()).hexdigest()
    else:
        module_uid = md5(plugin_file).hexdigest()

    module = None
    try:
        if not python3:
            imp.acquire_lock()
            module = imp.load_source(module_uid, plugin_file)
        else:
            loader=importlib.machinery.SourceFileLoader(module_uid, plugin_file)
            spec =importlib.util.spec_from_loader(loader.name, loader)
            module=importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            sys.modules[module_uid]=module
    except:
        # dump out the callstack for this one -- to help people get good messages when there is a plugin error
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        
        log.debug(exc_traceback)
        # log the full callstack to make sure that whatever the
        # calling code is doing, this error is logged to help
        # with troubleshooting and support
        log.exception("Cannot load plugin file '%s'" % plugin_file)


        message = ""
        message += (
            "Failed to load plugin %s. The following error was reported:\n"
            % plugin_file
        )
        message += "Exception: %s - %s\n" % (exc_type, exc_value)
        message += "Traceback (most recent call last):\n"
        message += "\n".join(traceback.format_tb(exc_traceback))
        raise TankLoadPluginError(message)
    finally:
        if not python3:
            imp.release_lock()
        
    log.debug(os.path.basename(plugin_file)+': plugin loaded as '+str(module))


    # cool, now validate the module
    found_classes = list()
    try:
        # first, find all classes in the module, being careful to only find classes that
        # are actually from this module and not from any other imports!
        search_predicate = (
            lambda member: inspect.isclass(member)
            and member.__module__ == module.__name__
        )
        all_classes = [cls for _, cls in inspect.getmembers(module, search_predicate)]
        
        #log.debug("checking in all base classes: "+str(all_classes))

        # Now look for classes in the module that are derived from the specified base
        # class.  Note that 'inspect.getmembers' returns the contents of the module
        # in alphabetical order so no assumptions should be made based on the order!
        #
        # Enumerate the valid_base_classes in order so that we find the highest derived
        # class we can.
        for base_cls in valid_base_classes:
            #log.debug(os.path.basename(plugin_file)+": checking classes under "+str(base_cls)+str((base_cls.__module__, inspect.getfile(sys.modules[base_cls.__module__]))))
            found_classes = []
            for cls in all_classes:
                #issubclass and importing with the imp modules dont mesh well
                #if a class is imported more than once with the imp commands, issubclass will report FALSE
                #even if the class is correctly subclassed from the file
                base=str(base_cls).split("'")[1]
                #log.debug(os.path.basename(plugin_file)+": checking for "+base+" in "+str([str(classer).split("'")[1] for classer in cls.__bases__]))
                if issubclass(cls, base_cls):
                    #log.debug("allowing "+str(cls)+" ("+str(type(cls))+") because it correctly inherits "+str({classer:(classer.__module__, inspect.getfile(sys.modules[classer.__module__])) for classer in cls.__bases__}))
                    found_classes.append(cls)
                elif base in [str(classer).split("'")[1] for classer in cls.__bases__]:
                    #log.debug("allowing "+str(cls)+" ("+str(type(cls))+") through text verification ")
                    found_classes.append(cls)
                else:
                    pass#log.debug("skipping "+str(cls)+" ("+str(type(cls))+") because it inherits "+str({classer:(classer.__module__, inspect.getfile(sys.modules[classer.__module__])) for classer in cls.__bases__})+" (issubclass of "+str(base_cls)+": "+str(issubclass(cls, base_cls))+")")

            #log.debug(os.path.basename(plugin_file)+":  found :"+str(found_classes))

            if len(found_classes) > 1:
                # it's possible that this file contains multiple levels of derivation - if this
                # is the case then we should try to remove any intermediate classes from the list
                # of found classes so that we are left with only leaf classes:
                filtered_classes = list(found_classes)
                for cls in found_classes:
                    #log.debug("class "+str(cls)+" has bases: "+str(cls.__bases__))
                    for base in cls.__bases__:
                        if base in filtered_classes:
                            # this is an intermediate class so remove it from the list:
                            #log.debug("removing "+str(base)+' from the list because it is in intermediate base class')
                            filtered_classes.remove(base)
                found_classes = filtered_classes
            if found_classes:
                # we found at least one class so assume this is a match!
                break
    except Exception as e:
        log.debug(traceback.format_exc())


        # log the full callstack to make sure that whatever the
        # calling code is doing, this error is logged to help
        # with troubleshooting and support
        log.exception("Failed to introspect hook structure for '%s'" % plugin_file)

        # re-raise as a TankError
        raise TankError(
            "Introspection error while trying to load and introspect file %s. "
            "Error Reported: %s" % (plugin_file, e)
        )

    if len(found_classes) != 1:
        # didn't find exactly one matching class!
        msg = (
            "Error loading the file '%s'. Couldn't find a single class deriving from '%s'. "
            "You need to have exactly one class defined in the file deriving from that base class. "
            "If your file looks fine, it is possible that the cached .pyc file that python "
            "generates is invalid and this is causing the error. In that case, please delete "
            "the .pyc file and try again." % (plugin_file, valid_base_class.__name__)
        )


        log.debug(msg)
        raise TankLoadPluginError(msg)


    #log.debug(os.path.basename(plugin_file)+': returning '+str(found_classes[0])+' for hook '+os.path.basename(plugin_file))
    # return the class that was found.
    return found_classes[0]
