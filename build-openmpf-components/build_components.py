#!/usr/bin/env python

#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2019 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2019 The MITRE Corporation                                      #
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

import abc
import argparse
import contextlib
import glob
import json
import multiprocessing
import multiprocessing.pool
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile


def main():
    cmdline_args = MpfArgumentParser.parse()
    print_argument_warnings(cmdline_args)
    sdks = get_sdks(cmdline_args)
    components = ComponentLocator.locate(cmdline_args)

    if cmdline_args.clean or cmdline_args.clean_only:
        clean(cmdline_args.build_dir, sdks + components)

    if not cmdline_args.clean_only:
        ProjectBuilder.build_projects(sdks, components, cmdline_args)



def print_argument_warnings(cmdline_args):
    if cmdline_args.clean_only:
        return
    if not cmdline_args.cpp_sdk_src:
        print_warning('MPF C++ Component SDK source path was not provided, so it won\'t be built.')
    if not cmdline_args.java_sdk_src:
        print_warning('MPF Java Component SDK source path was not provided, so it won\'t be built.')
    if not cmdline_args.python_sdk_src:
        print_warning('MPF Python Component SDK source path was not provided, so it won\'t be built.')

    if cmdline_args.mpf_package_json and cmdline_args.components:
        print_warning('Both a JSON package file and a component list was specified. Only components from the JSON'
                      ' package file will be built.')
    if not cmdline_args.mpf_package_json and not cmdline_args.components:
        print_warning('No components specified.')



def clean(base_build_dir, projects):
    for base_package in Files.list_component_packages(base_build_dir):
        print 'Deleting', base_package
        os.remove(base_package)

    for build_dir in Files.dir_children(base_build_dir):
        CmakeUtil.clean(build_dir)

    for project in projects:
        MavenUtil.clean(project.src_dir)


def print_warning(msg):
    yellow = '\033[0;33m'
    reset = '\033[0m'
    print yellow + msg + reset


class MpfArgumentParser(argparse.ArgumentParser):

    @staticmethod
    def parse(arg_strings=sys.argv[1:]):
        return MpfArgumentParser().parse_args(arg_strings)

    def __init__(self):
        super(MpfArgumentParser, self).__init__(
            description='Builds the MPF Component SDKs and any specified components.',
            epilog='Arguments can also be read from a file by passing in @<args_file>. '
                   'Each line is a single command line argument.',
            fromfile_prefix_chars='@')


        self.add_argument(
            '-csdk', '--cpp-sdk-src',
            help='Path to directory containing the MPF C++ Component SDK project. '
                 'If not provided the C++ SDK will not be built.',
            metavar='<cpp_sdk_path>')


        self.add_argument(
            '-jsdk', '--java-sdk-src',
            help='Path to directory containing the MPF Java Component SDK project. '
                 'If not provided the Java SDK will not be built.',
            metavar='<java_sdk_path>')


        self.add_argument(
            '-psdk', '--python-sdk-src',
            help='Path to directory containing the MPF Python Component SDK project. '
                 'If not provided the Python SDK will not be built.',
            metavar='<python_sdk_path>')


        self.add_argument(
            '-b', '--build-dir',
            default='mpf-build',
            help='Path to the directory where build will occur. Defaults to the current directory.',
            metavar='<build_dir>')

        self.add_argument(
            '-cp', '--component-search-path',
            default='',
            help='Colon separated list containing directories where components can be found. '
                 'Can also be specified through the '
                 'MPF_COMPONENT_SEARCH_PATH environment variable.',
            metavar='<search_paths>')

        self.add_argument(
            '-c', '--components',
            type=none_when_falsy(),
            help='Colon separated list of components to build. '
                 'May either be full path to component '
                 'or a path relative to a path provided in the component search paths.',
            metavar='<components>')

        self.add_argument(
            '-json', '--mpf-package-json',
            type=none_when_falsy(argparse.FileType()),
            help='Path to MPF Package JSON descriptor.',
            metavar='<package_file_path>')

        self.add_argument(
            '--clean',
            action='store_true',
            help='Cleans each build under the build directory.')

        self.add_argument(
            '--clean-only',
            action='store_true',
            help='Cleans without building anything'
        )


        parallel_arg_def = self.add_argument(
            '-p', '--parallel',
            nargs='?',  # 0 or 1 arguments can be passed to the parallel option.
            default=1,
            const=float('inf'),  # If parallel option is present, but no number follows
            type=int,
            help='Specifies that maximum number of simultaneous builds. '
                 'If option is not provided, defaults to 1. '
                 'If option is provided but no number is specified, '
                 'the number of simultaneous builds is unbounded.',
            metavar='<num_builds>')


        jobs_arg_def = self.add_argument(
            '-j', '--jobs',
            nargs='?',
            default=1,
            const=float('inf'),
            type=int,
            help='Specifies the number of "make" jobs for C++ builds. '
                 'The given value is forwarded to all calls to "make".',
            metavar='<num_make_jobs>')

        # Add as separate argument to prevent parsing second letter as a number.
        self.add_argument(
            '-jp', '-pj',
            nargs='?',
            default=1,
            const=float('inf'),
            type=int,
            action=MapShortOptionsGroup,
            mapped_args=(parallel_arg_def, jobs_arg_def),
            help=argparse.SUPPRESS)


    def parse_args(self, arg_strings=sys.argv[1:], namespace=None):
        arg_strings = MpfArgumentParser._expand_path_tilde(arg_strings)
        args = super(MpfArgumentParser, self).parse_args(arg_strings, namespace)
        if args.cpp_sdk_src or args.java_sdk_src or args.python_sdk_src or args.components or args.mpf_package_json \
                or args.clean or args.clean_only:
            return args
        else:
            self.error(
                'One of the following options must be provided: '
                '-csdk, -jsdk, -psdk, -c, -json, '
                '--clean, --clean-only, or --help')


    @staticmethod
    def _expand_path_tilde(arg_strings):
        new_args = []
        for arg in arg_strings:
            if arg and arg[0] == '@' and '~' in arg:
                path_no_at_sign = arg[1:]
                expanded_path = os.path.expanduser(path_no_at_sign)
                new_args.append('@' + expanded_path)
            else:
                new_args.append(arg)
        return new_args


    def convert_arg_line_to_args(self, arg_line):
        """ Need to override because the super class implementation
        considers blank lines to be arguments """
        if arg_line.strip():
            return [arg_line]
        else:
            return []


def none_when_falsy(func=lambda x: x):
    def apply_func(arg):
        return func(arg) if arg else None
    return apply_func


class MapShortOptionsGroup(argparse.Action):
    def __init__(self, mapped_args, **kwargs):
        super(MapShortOptionsGroup, self).__init__(**kwargs)
        self._mapped_args = mapped_args

    def __call__(self, parser, namespace, values, option_string=None):
        delattr(namespace, self.dest)
        for arg_def in self._mapped_args:
            arg_def(parser, namespace, values)


class ComponentLocator(object):
    LANG_DIRS = ('cpp', 'java', 'python')

    @staticmethod
    def locate(cmdline_args):
        return ComponentLocator(cmdline_args).locate_components()

    def __init__(self, cmdline_args):
        self._cmdline_args = cmdline_args
        if cmdline_args.mpf_package_json:
            self._components \
                = ComponentLocator._get_components_listed_in_json(cmdline_args.mpf_package_json)
            self._component_search_paths = ()
        elif cmdline_args.components:
            self._components = ComponentLocator._split_path_list(cmdline_args.components)
            self._component_search_paths \
                = self._get_search_paths(cmdline_args.component_search_path)
        else:
            self._components = ()
            self._component_search_paths = ()


    @staticmethod
    def _get_search_paths(cmdline_paths):
        joined_search_paths = cmdline_paths + ':' + os.environ.get('MPF_COMPONENT_SEARCH_PATH', '')
        specified_search_paths = ComponentLocator._split_path_list(joined_search_paths)
        search_paths = []
        for path in specified_search_paths:
            search_paths.append(path)
            for lang_dir in ComponentLocator.LANG_DIRS:
                search_paths.append(os.path.join(path, lang_dir))
        return search_paths


    def locate_components(self):
        located_components = []
        missing_components = []
        for component_path in self._components:
            components = self._locate_component(component_path)
            if components:
                located_components.extend(components)
            else:
                missing_components.append(component_path)

        if missing_components:
            sys.exit('Error: The following components were not found: '
                     + ', '.join(missing_components))

        duplicate_components = ComponentLocator._get_duplicate_components(located_components)
        if duplicate_components:
            sys.exit('Error: The following components were listed more than once: '
                     + ', '.join(c.src_dir for c in duplicate_components))

        return located_components


    def _locate_component(self, component_path):
        component = self._check_search_paths(component_path)
        if component:
            return [component]
        else:
            return self._check_lang_dirs(component_path)


    def _check_search_paths(self, component_path):
        component = MpfComponent.create(component_path, self._cmdline_args)
        if component:
            return component
        for search_path in self._component_search_paths:
            full_component_path = os.path.join(search_path, component_path)
            component = MpfComponent.create(full_component_path, self._cmdline_args)
            if component:
                return component

    def _check_lang_dirs(self, component_path):
        """
        If the top level directory of a component repo is given as a component,
        a separate project needs to be created for each component language
        """
        components_in_lang_dir = []
        for lang_dir in ComponentLocator.LANG_DIRS:
            component = self._check_search_paths(os.path.join(component_path, lang_dir))
            if component:
                components_in_lang_dir.append(component)
        return components_in_lang_dir

    @staticmethod
    def _get_duplicate_components(components):
        src_dirs = set()
        duplicate_components = []
        for component in components:
            if component.src_dir in src_dirs:
                duplicate_components.append(component)
            else:
                src_dirs.add(component.src_dir)
        return duplicate_components


    @staticmethod
    def _split_path_list(paths_str):
        paths = []
        path_segments = paths_str.split(':')
        for segment in path_segments:
            if segment == '':
                continue
            if segment != '/':
                segment = segment.rstrip('/')
            if '~' in segment:
                segment = os.path.expanduser(segment)
            paths.append(segment)
        return paths


    @staticmethod
    def _get_components_listed_in_json(json_file):
        try:
            mpf_package_json = json.load(json_file)
        except ValueError as err:
            sys.exit('Error: Failed to parse JSON file: %s' % err)

        components = mpf_package_json.get('MPF_Components')
        if components is None:
            sys.exit('Error: JSON file does not contain a mapping for the key named: '
                     '"MPF_Components"')

        component_paths = []
        for component in components:
            path = component.get('path')
            if path is None:
                sys.exit('Error: A component listed in the JSON file does not contain '
                         'a key named "path"')
            component_paths.append(path)

        return component_paths



class ProjectBuilder(object):
    def __init__(self, pool_size):
        if pool_size > 1:
            self._pool = multiprocessing.pool.ThreadPool(processes=pool_size)
        else:
            self._pool = None

    def build(self, projects):
        if self._pool:
            self._build_parallel(projects)
        else:
            ProjectBuilder._build_sequential(projects)


    def _build_parallel(self, projects):
        build_results = []
        for project in projects:
            async_result = self._pool.apply_async(project.build)
            build_results.append((project, async_result))

        for p, r in build_results:
            r.wait()
        ProjectBuilder._report_build_errors(build_results)


    @staticmethod
    def _build_sequential(projects):
        for project in projects:
            try:
                project.build()
            except Exception as err:
                sys.exit('An error occurred while trying to build %s: %s.' % (project.src_dir, err))


    @staticmethod
    def _report_build_errors(build_results):
        error_msgs = []
        for project, result in build_results:
            try:
                result.get()
            except Exception as err:
                error_msgs.append(
                    'An error occurred while trying to build %s: %s.' % (project.src_dir, err))
        if error_msgs:
            sys.exit('\n'.join(error_msgs))


    @staticmethod
    def build_projects(sdks, components, cmdline_args):
        if not sdks and not components:
            return
        max_possible_simultaneous_builds = max(len(sdks), len(components))
        pool_size = min(max_possible_simultaneous_builds, cmdline_args.parallel)
        builder = ProjectBuilder(pool_size)
        builder.build(sdks)
        if components:
            plugin_output_dir = get_plugin_output_dir(cmdline_args)
            Files.make_dir(plugin_output_dir)
            builder.build(components)
            print 'Component packages written to:', plugin_output_dir



class CmakeUtil(object):
    @staticmethod
    def is_project(src_dir):
        return Files.path_exists(src_dir, 'CMakeLists.txt')

    @staticmethod
    def build(build_dir, src_dir, num_jobs):
        Files.make_dir(build_dir)
        subprocess.check_call(('cmake3', '-DCMAKE_RULE_MESSAGES=OFF', src_dir), cwd=build_dir)
        if num_jobs == 1:
            subprocess.check_call(('make', 'install'), cwd=build_dir)
        elif num_jobs == float('inf'):
            subprocess.check_call(('make', 'install', '--jobs'), cwd=build_dir)
        else:
            subprocess.check_call(('make', 'install', '--jobs', str(num_jobs)), cwd=build_dir)

    @staticmethod
    def clean(build_dir):
        if Files.path_exists(build_dir, 'makefile') or Files.path_exists(build_dir, 'Makefile'):
            print 'Cleaning', build_dir
            subprocess.check_call(('make', 'clean'), cwd=build_dir)
            for package in Files.list_component_packages(build_dir):
                print 'Deleting', package
                os.remove(package)

    @staticmethod
    def generate_build_path(base_build_dir, src_dir):
        path_no_leading_slash = src_dir[1:]
        build_dir_name = path_no_leading_slash.replace('/', '-') + '-build'
        return os.path.join(base_build_dir, build_dir_name)



class MavenUtil(object):
    @staticmethod
    def is_project(src_dir):
        return Files.path_exists(src_dir, 'pom.xml')

    _SKIP_INTEGRATION_TESTS_ARGS = ('-Dit.test=none', '-DfailIfNoTests=false', '-DskipITs')

    @staticmethod
    def _run_maven_phase(phase, src_dir):
        subprocess.check_call(('mvn', phase) + MavenUtil._SKIP_INTEGRATION_TESTS_ARGS, cwd=src_dir)

    @staticmethod
    def package(src_dir):
        MavenUtil._run_maven_phase('package', src_dir)

    @staticmethod
    def install(src_dir):
        MavenUtil._run_maven_phase('install', src_dir)

    @staticmethod
    def clean(src_dir):
        if MavenUtil.is_project(src_dir):
            print 'Cleaning ', src_dir
            subprocess.check_call(('mvn', 'clean'), cwd=src_dir)



class PipUtil(object):
    _VERSION_VERIFIED = False

    @staticmethod
    def verify_version():
        if PipUtil._VERSION_VERIFIED:
            return
        # Example: pip 8.1.2 from /usr/lib/python2.7/site-packages (python 2.7)
        version_output = subprocess.check_output(['pip', '--version'])
        version_string = version_output.split()[1]
        major_version = int(version_string.split('.')[0])
        if major_version < 9:
            raise Exception('pip version 9 or greater is required, but found version: %s' % version_output)
        PipUtil._VERSION_VERIFIED = True


    @staticmethod
    def has_setup_py_file(src_dir):
        return Files.path_exists(src_dir, 'setup.py')

    @staticmethod
    def is_component(src_dir):
        return PipUtil.has_setup_py_file(src_dir) or PipUtil._descriptor_lang_matches(src_dir)

    @staticmethod
    def _descriptor_lang_matches(src_dir):
        try:
            with open(os.path.join(src_dir, 'descriptor', 'descriptor.json')) as f:
                descriptor_json = json.load(f)
                return descriptor_json.get('sourceLanguage', '').lower() == 'python'
        except IOError:
            return False

    @staticmethod
    def clean(src_dir):
        if PipUtil.has_setup_py_file(src_dir):
            print 'Cleaning ', src_dir
            subprocess.check_call(('python', 'setup.py', 'clean'), cwd=src_dir)

    @staticmethod
    def _get_sdk_install_root():
        return os.path.join(Files.get_sdk_install_path(), 'python')

    @staticmethod
    def get_sdk_wheelhouse():
        return os.path.join(PipUtil._get_sdk_install_root(), 'wheelhouse')

    @staticmethod
    def get_sdk_installed_packages():
        return os.path.join(PipUtil._get_sdk_install_root(), 'site-packages')




class MpfProject(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, src_dir):
        self.src_dir = os.path.abspath(Files.expand_path(src_dir))

    @abc.abstractmethod
    def build(self):
        raise NotImplementedError()



def get_sdks(cmdline_args):
    sdks = []
    try:
        if cmdline_args.cpp_sdk_src:
            sdks.append(CppSdk(cmdline_args))
        if cmdline_args.java_sdk_src:
            sdks.append(JavaSdk(cmdline_args))
        if cmdline_args.python_sdk_src:
            sdks.append(PythonSdk(cmdline_args))
    except Exception as err:
        sys.exit('Error: ' + err.message)
    return sdks



class CppSdk(MpfProject):
    def __init__(self, cmdline_args):
        super(CppSdk, self).__init__(cmdline_args.cpp_sdk_src)
        self._sdk_build_dir = CmakeUtil.generate_build_path(cmdline_args.build_dir, self.src_dir)
        self._num_make_jobs = cmdline_args.jobs
        if not CmakeUtil.is_project(self.src_dir):
            raise Exception(
                'Unable to build C++ SDK because %s does not appear to be a CMake project.'
                % self.src_dir)

    def build(self):
        CmakeUtil.build(self._sdk_build_dir, self.src_dir, self._num_make_jobs)


class JavaSdk(MpfProject):
    def __init__(self, cmdline_args):
        super(JavaSdk, self).__init__(cmdline_args.java_sdk_src)
        if not MavenUtil.is_project(self.src_dir):
            raise Exception(
                'Unable to build Java SDK because %s does not appear to be a Maven project.'
                % self.src_dir)

    def build(self):
        MavenUtil.install(self.src_dir)


class PythonSdk(MpfProject):
    def __init__(self, cmdline_args):
        super(PythonSdk, self).__init__(
            os.path.join(cmdline_args.python_sdk_src, 'detection')
        )
        PipUtil.verify_version()
        self.packages = [os.path.join(self.src_dir, d) for d in ('api', 'component_util')]
        for package in self.packages:
            if not PipUtil.has_setup_py_file(package):
                raise Exception(
                    'Unable to build Python SDK because %s does not contain a setup.py file.'
                    % package)

    def build(self):
        for package in self.packages:
            subprocess.check_call(('pip', 'wheel', '--wheel-dir', PipUtil.get_sdk_wheelhouse(),
                                   '--find-links', PipUtil.get_sdk_wheelhouse(), package))

            subprocess.check_call(('pip', 'install', '--upgrade', '--target', PipUtil.get_sdk_installed_packages(),
                                   '--find-links', PipUtil.get_sdk_wheelhouse(), package))



class MpfComponent(MpfProject):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def create(src_dir, cmdline_args):
        if CmakeUtil.is_project(src_dir):
            return CppComponent(src_dir, cmdline_args)
        elif MavenUtil.is_project(src_dir):
            return JavaComponent(src_dir, cmdline_args)
        elif PipUtil.is_component(src_dir):
            return PythonComponent(src_dir, cmdline_args)
        else:
            return None

    def __init__(self, src_dir, cmdline_args):
        super(MpfComponent, self).__init__(src_dir)
        self.base_plugin_output_dir = get_plugin_output_dir(cmdline_args)

    @abc.abstractmethod
    def build_package(self):
        raise NotImplementedError()

    def build(self):
        packages = self.build_package()
        for package in packages:
            shutil.copy(package, self.base_plugin_output_dir)



class CppComponent(MpfComponent):
    def __init__(self, component_src_dir, cmdline_args):
        super(CppComponent, self).__init__(component_src_dir, cmdline_args)
        self._component_build_dir = CmakeUtil.generate_build_path(cmdline_args.build_dir, self.src_dir)
        self._num_make_jobs = cmdline_args.jobs


    def build_package(self):
        CmakeUtil.build(self._component_build_dir, self.src_dir, self._num_make_jobs)
        return Files.list_component_packages(self._component_build_dir)


class JavaComponent(MpfComponent):
    def __init__(self, component_src_dir, cmdline_args):
        super(JavaComponent, self).__init__(component_src_dir, cmdline_args)

    def build_package(self):
        MavenUtil.package(self.src_dir)
        return self._find_plugin_packages()


    def _find_plugin_packages(self):
        """
        For each Maven module in a Maven project,
        Maven creates a target directory within the module's directory.
        This method recursively searches self.src_dir for target directories containing
        a plugin-packages directory.
        :return: List of paths to created plugin packages.
        """
        def should_explore(dir_name):
            return dir_name[0] != '.' and dir_name not in ('plugin-files', 'src')

        packages = []
        for root, dirs, files in os.walk(self.src_dir):
            if os.path.basename(root) == 'target':
                dirs[:] = []  # No need to further explore this directory
                packages.extend(Files.list_component_packages(root))
            else:
                dirs[:] = [d for d in dirs if should_explore(d)]
        return packages



class PythonComponent(MpfComponent):
    def __init__(self, component_src_dir, cmdline_args):
        super(PythonComponent, self).__init__(component_src_dir, cmdline_args)
        PipUtil.verify_version()

    def build_package(self):
        if PipUtil.has_setup_py_file(self.src_dir):
            return self._build_setuptools_component()
        else:
            Files.tar_directory(self.src_dir, self.base_plugin_output_dir)
            return ()  # Builds package in place, no need to copy

    def _build_setuptools_component(self):
        leaf_dir = Files.get_leaf(self.src_dir)
        with Files.create_temp_dir() as temp_path:
            download_target_wheelhouse = os.path.join(temp_path, 'wheelhouse')

            pip_args = ['pip', 'wheel', self.src_dir,
                        '--wheel-dir', download_target_wheelhouse,
                        '--find-links', PipUtil.get_sdk_wheelhouse()]

            plugin_provided_wheelhouse = os.path.join(self.src_dir, 'plugin-files', 'wheelhouse')
            if os.path.exists(plugin_provided_wheelhouse):
                pip_args += ('--find-links', plugin_provided_wheelhouse)

            subprocess.check_call(pip_args)

            with tarfile.open(os.path.join(self.base_plugin_output_dir, leaf_dir + '.tar.gz'), 'w:gz') as tar:
                dup_filter = create_tar_duplicate_filter()
                tar.add(os.path.join(self.src_dir, 'plugin-files'), arcname=leaf_dir, filter=dup_filter)

                for whl_file_name in os.listdir(download_target_wheelhouse):
                    tar.add(os.path.join(download_target_wheelhouse, whl_file_name),
                            arcname=os.path.join(leaf_dir, 'wheelhouse', whl_file_name),
                            filter=dup_filter)

            return ()  # Builds package in place, no need to copy



def create_tar_duplicate_filter():
    files_seen = set()

    def do_filter(tar_info):
        if tar_info.name in files_seen:
            return None
        files_seen.add(tar_info.name)
        return tar_info
    return do_filter


def get_plugin_output_dir(cmdline_args):
    return os.path.join(cmdline_args.build_dir, 'plugin-packages')


class Files(object):
    @staticmethod
    def dir_children(directory):
        if os.path.exists(directory):
            return [os.path.join(directory, f) for f in os.listdir(directory)]
        return ()

    @staticmethod
    def path_exists(path, *paths):
        return os.path.exists(os.path.join(path, *paths))

    @staticmethod
    def make_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def list_component_packages(path, *paths):
        directory = os.path.join(path, *paths)
        return glob.glob(os.path.join(directory, 'plugin-packages', '*.tar.gz'))

    @staticmethod
    def expand_path(path):
        return os.path.expanduser(os.path.expandvars(path))

    @staticmethod
    def tar_directory(input_dir, output_dir):
        leaf_dir = Files.get_leaf(input_dir)
        tar_full_path = os.path.join(output_dir, leaf_dir + '.tar.gz')
        with tarfile.open(tar_full_path, 'w:gz') as tar:
            tar.add(input_dir, arcname=leaf_dir)

    @staticmethod
    def get_sdk_install_path():
        return Files.expand_path(os.getenv('MPF_SDK_INSTALL_PATH', '~/mpf-sdk-install'))

    @staticmethod
    def get_leaf(path):
        path.rstrip('/')
        return os.path.basename(path)

    @staticmethod
    @contextlib.contextmanager
    def create_temp_dir():
        name = tempfile.mkdtemp()  # Create the temp directory when entering "with" block
        try:
            yield name  # Make path to temp dir available through "with" statement's "as" variable
        finally:
            shutil.rmtree(name)  # Delete the temp directory when exiting "with" block



if __name__ == '__main__':
    main()
