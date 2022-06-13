# Copyright (c) 2018 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank import Hook


class TemplateFields(Hook):
    
    def modifyFields(self, fields):
        """
        :param fields: the dictionary of fields applied to the template.

        returns: the fields dictionary, modified if desired.
        """
        
        #template can be accessed as this Hook's parent
        template=self.parent

        return fields
