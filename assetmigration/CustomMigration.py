#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) CustomMigration.py 2026 AKKODIS INGENIERIE PRODUIT SAS (support@3djuump.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

class CustomMigration :
    def __init__(self):
        # insert here any relevant code to store your translation maps or any other relevant functionalities
        pass

    def translateProject(self, project_name) :
        # insert here code to translate the old 3.3 project_name onto the new 4.0 project name 
        return project_name
    
    def translateUser(self, user) :
        # insert here code to translate the old 3.3 user onto the new 4.0 user
        return user

    def translateTeam(self, team) :
        # insert here code to translate the old 3.3 team onto the new 4.0 team
        return team

    def getApplicationName(self) :
        # gets here the app name for the infinite native client
        # this should be the given string
        # look at https://<my_directory>/directory/frontend/#/applications
        return '3D Juump Infinite Native Client'
