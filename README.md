# OpenMPF Build Tools

Welcome to the Open Media Processing Framework (OpenMPF) Build Tools Project!

## What is the OpenMPF?

OpenMPF provides a platform to perform content detection and extraction on bulk multimedia, enabling users to analyze, search, and share information through the extraction of objects, keywords, thumbnails, and other contextual data.

OpenMPF enables users to build configurable media processing pipelines, enabling the rapid development and deployment of analytic algorithms and large-scale media processing applications.

### Search and Share

Simplify large-scale media processing and enable the extraction of meaningful content

### Open API

Apply cutting-edge algorithms such as face detection and object classification

### Flexible Architecture

Integrate into your existing environment or use OpenMPF as a standalone application

## Overview

This repository contains code for the OpenMPF build tools and related files.

## Where Am I?

- [Parent OpenMPF Project](https://github.com/openmpf/openmpf-projects)
- [OpenMPF Core](https://github.com/openmpf/openmpf)
- Components
    * [OpenMPF Standard Components](https://github.com/openmpf/openmpf-components)
    * [OpenMPF Contributed Components](https://github.com/openmpf/openmpf-contrib-components)
- Component APIs:
    * [OpenMPF C++ Component SDK](https://github.com/openmpf/openmpf-cpp-component-sdk)
    * [OpenMPF Java Component SDK](https://github.com/openmpf/openmpf-java-component-sdk)
    * [OpenMPF Python Component SDK](https://github.com/openmpf/openmpf-python-component-sdk)
- [OpenMPF Build Tools](https://github.com/openmpf/openmpf-build-tools) ( **You are here** )
- [OpenMPF Web Site Source](https://github.com/openmpf/openmpf.github.io)
- [OpenMPF Docker](https://github.com/openmpf/openmpf-docker)

## Getting Started

The `build_components.py` script is used to build the components and component SDKs all in one command.
The source code the for the C++ Component SDK, the Java Components SDK, and the components can be located
anywhere on a system, so a script is required to build them all in one command.

### Quick Start
* To build the C++ Component SDK, the Java Component SDK, and all components you can run:
```
python3 build_components.py \
    -b ~/mpf-component-build \
    -p 2 \
    -j 4 \
    -csdk ~/openmpf-projects/openmpf-cpp-component-sdk \
    -jsdk ~/openmpf-projects/openmpf-java-component-sdk \
    -cp ~/openmpf-projects \
    -c openmpf-components:openmpf-contrib-components
```
* The plugin packages will be placed in `~/mpf-component-build/plugin-packages`
* Documentation for the command line arguments can be shown by passing in the `--help` argument

### Specifying Build Directory
* The C++ SDK and components use an out of source build. If the `-b` argument is provided then the build
  will take place in that directory. If `-b` is not provided a new directory named `mpf-build` will be created within
  the current working directory. Once the build completes, a directory named `plugin-packages` containing the built
  plugin packages will be created at the top level of the build directory.


### Building C++ and Java Component SDKs with `build_components.py`
* To build the C++ SDK, set `-csdk` to the path to the C++ Component SDK source code.
* To build the Java SDK, Set `-jsdk` to the path to the Java Component SDK source code.
* Example: `python3 build_components.py -csdk ~/openmpf-projects/openmpf-cpp-component-sdk -jsdk ~/openmpf-projects/openmpf-java-component-sdk`


### Building Components with `build_components.py`
* In order to build a component, the respective SDK must be installed.
  If you are only interested in building components and already have the SDK installed,
  you do not need to include the `-csdk` or `-jsdk` arguments.


* The simplest way to build a component is to set the `-c` argument to the path to a component's source code.


* For convenience components in the [openmpf-components repo](https://github.com/openmpf/openmpf-components) and the
  [openmpf-contrib-components repo](https://github.com/openmpf/openmpf-contrib-components) can be built at multiple
  levels.
   * To build all the components in openmpf-components you can run:  
      * `python3 build_components.py -c ~/openmpf-projects/openmpf-components`
   * To only build the C++ components in openmpf-components you can run:
      * `python3 build_components.py -c ~/openmpf-projects/openmpf-components/cpp`
   * To only build the OcvFaceDetection component you can run:
      * `python3 build_components.py -c ~/openmpf-projects/openmpf-components/cpp/OcvFaceDetection`


* Multiple components can be passed to the `-c` argument by separating them with colons.
   * To build OcvFaceDetection and DlibFaceDetection you can run:
      * `python3 build_components.py -c ~/openmpf-projects/openmpf-components/cpp/OcvFaceDetection:~/openmpf-projects/openmpf-components/cpp/DlibFaceDetection`
   * To build all the components in open-components and openmpf-contrib-components you can run:
      * `python3 build_components.py -c ~/openmpf-projects/openmpf-components:~/openmpf-projects/openmpf-contrib-components`



* To shorten the command you can set the `-cp` argument. The `-cp` argument specifies directories where components
  may be found. If a relative path is passed to the `-c` argument, first the path relative to the current working
  directory is checked for a component. If there isn't a component there, each path given in `-cp` will be checked.
  Multiple paths can be passed to `-cp` by separating them with a colon.
   * To build all the components in open-components and openmpf-contrib-components you can run:
      * `python3 build_components.py -cp ~/openmpf-projects -c openmpf-components:openmpf-contrib-components`
   * To build OcvFaceDetection, DlibFaceDetection, and MogMotionDetection you can run:
      * `python3 build_components.py -cp ~/openmpf-projects/openmpf-components:~/openmpf-projects/openmpf-contrib-components -c OcvFaceDetection:DlibFaceDetection:motion/MogMotionDetection`

### Parallelism
* The `-p` argument specifies the maximum number of components that will be built in parallel.
* The `-j` argument specifies the number of parallel make jobs for C++ components.
  The argument is forwarded to each call to `make`.

## Project Website

For more information about OpenMPF, including documentation, guides, and other material, visit our  [website](https://openmpf.github.io/)

## Project Workboard

For a latest snapshot of what tasks are being worked on, what's available to pick up, and where the project stands as a whole, check out our [workboard](https://github.com/orgs/openmpf/projects/3).

