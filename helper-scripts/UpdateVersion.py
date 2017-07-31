#!/usr/bin/env python

#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2016 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2016 The MITRE Corporation                                      #
#                                                                           #
# Licensed under the Apache License, Version 2.0 (the "License");           #
# you may not use this file except in compliance with the License.          #
# You may obtain a copy of the License at                                   #
#                                                                           #
#    http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                           #
# Unless required by applicable law or agreed to in writing, software       #
# distributed under the License is distributed on an "AS IS" BASIS,         #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
# See the License for the specific language governing permissions and       #
# limitations under the License.                                            #
#############################################################################

import sys
import os


# Run this script within the "openmpf" directory.

old_version = None
new_version = None
updated_files = []


def main():
    global old_version
    global new_version

    if (len(sys.argv) != 3):
        print "Usage: " + sys.argv[0] + " <old_version_str> <new_version_str>"
        return -1

    old_version = sys.argv[1]
    new_version = sys.argv[2]


    ############################################################
    # Add new files here
    ############################################################

    replace_version("echo \\\"                           Installing OpenMPF ", "trunk/ansible/install-mpf.sh")
    replace_version("my \$mpfVersion = \\\"", "trunk/jenkins/scripts/CreateCustomPackage.pl")
    replace_version("mpf.version.semantic=", "trunk/workflow-manager/src/main/resources/properties/mpf.properties")


    if not updated_files:
        print "No files were updated."
    else:
        print "Updated files:"
        print "\n".join(updated_files)


def replace_version(line_starts_with, file_path):
    search_str = line_starts_with + old_version
    search_command = "grep -q \"" + search_str + "\" " + file_path
    # print search_command # DEBUG
    if (os.system(search_command) != 0):
        print "Could not find search string in " + file_path + ":"
        os.system("echo \"" + search_str + "\"")
        print
        return

    replace_command = "sed -i '/^" + line_starts_with + "/s/" + old_version + "/" + new_version + "/' " + file_path
    # print replace_command # DEBUG
    exit_code = os.system(replace_command)
    if (exit_code != 0):
        print "Could not replace search string in " + file_path + ":"
        os.system("echo \"" + search_str + "\"")
        # print "Command returned exit code " + str(exit_code) # DEBUG
        print
        return

    updated_files.append(file_path)


if __name__ == '__main__':
    main()