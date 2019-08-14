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

#############################################################################
# Warning: Use at your own discretion, this file may be out of date         #
#############################################################################

FROM centos:7

# Set up yum repo:
RUN yum install -y epel-release deltarpm && \
    yum install -y git wget gcc gcc-c++ make autoconf automake \
    libtool yasm nasm bzip2 cmake3 file openssl-devel && \
    yum clean all

# Create the OpenMPF ldconfig file:
# Add /apps/install/lib to the OpenMPF ldconfig file:
# Update the shared library cache:
RUN touch /etc/ld.so.conf.d/mpf-x86_64.conf && \
    sh -c 'echo "/apps/install/lib" >> /etc/ld.so.conf.d/mpf-x86_64.conf' && \
    ldconfig

RUN mkdir -p /apps/source/ffmpeg_sources

# cmake 2.8.12.2:
RUN mkdir -p /apps/source/cmake_sources && \
    wget -nv -O /apps/source/cmake_sources/cmake-2.8.12.2.tar.gz \
    "https://cmake.org/files/v2.8/cmake-2.8.12.2.tar.gz" && \
    cd /apps/source/cmake_sources && tar xzf cmake-2.8.12.2.tar.gz && \
    cd cmake-2.8.12.2 && chmod +x * && ./configure --prefix=/apps/install && make -j && \
    make install && ldconfig && ln -s /apps/install/bin/cmake /usr/local/bin/cmake

#############################################################################
# Build Audio and Video Codecs and FFmpeg                                   #
#############################################################################

 # opencore-amr:	
RUN wget -nv -O /apps/source/ffmpeg_sources/opencore-amr-0.1.4.tar.gz \	
    "https://downloads.sf.net/project/opencore-amr/opencore-amr/opencore-amr-0.1.4.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf opencore-amr-0.1.4.tar.gz && \	
    cd opencore-amr-0.1.4 && autoreconf -fiv && \	
    ./configure --prefix="/apps/install" --enable-shared && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libfdk_aac:	
RUN wget -nv -O /apps/source/ffmpeg_sources/fdk-aac-0.1.5.tar.gz \	
    "https://github.com/mstorsjo/fdk-aac/archive/v0.1.5.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf fdk-aac-0.1.5.tar.gz && \	
    cd fdk-aac-0.1.5 && autoreconf -fiv && ./configure --prefix="/apps/install" --enable-shared && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libmp3lame:	
RUN wget -nv -O /apps/source/ffmpeg_sources/lame-3.99.5.tar.gz \	
    "http://downloads.sourceforge.net/project/lame/lame/3.99/lame-3.99.5.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf lame-3.99.5.tar.gz && cd lame-3.99.5 && \	
    ./configure --prefix="/apps/install" --bindir="/apps/install/bin" --enable-shared --enable-nasm && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libogg:	
RUN wget -nv -O /apps/source/ffmpeg_sources/libogg-1.3.2.tar.gz \	
    "http://downloads.xiph.org/releases/ogg/libogg-1.3.2.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf libogg-1.3.2.tar.gz && \	
    cd libogg-1.3.2 && ./configure --prefix="/apps/install" --enable-shared && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libopus:	
RUN wget -nv -O /apps/source/ffmpeg_sources/libopus-1.2.tar.gz \	
    "https://archive.mozilla.org/pub/opus/opus-1.2.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf libopus-1.2.tar.gz && \	
    cd opus-1.2 && autoreconf -fiv && ./configure --prefix="/apps/install" --enable-shared && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libspeex:	
RUN wget -nv -O /apps/source/ffmpeg_sources/speex-1.2rc2.tar.gz \	
    "http://downloads.xiph.org/releases/speex/speex-1.2rc2.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf speex-1.2rc2.tar.gz && \	
    cd speex-1.2rc2 && LDFLAGS="-L/apps/install/lib" CPPFLAGS="-I/apps/install/include" \	
    ./configure --prefix="/apps/install" --enable-shared && make -j$(nproc) && make install && \	
    make distclean && ldconfig	

 # libvorbis:	
RUN wget -nv -O /apps/source/ffmpeg_sources/libvorbis-1.3.5.tar.gz \	
    "http://downloads.xiph.org/releases/vorbis/libvorbis-1.3.5.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf libvorbis-1.3.5.tar.gz && \	
    cd libvorbis-1.3.5 && LDFLAGS="-L/apps/install/lib" CPPFLAGS="-I/apps/install/include" \	
    ./configure --prefix="/apps/install" --with-ogg="/apps/install" --enable-shared && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libtheora:	
RUN wget -nv -O /apps/source/ffmpeg_sources/libtheora-1.1.1.tar.gz \	
    "http://downloads.xiph.org/releases/theora/libtheora-1.1.1.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf libtheora-1.1.1.tar.gz && \	
    cd libtheora-1.1.1 && ./configure --prefix="/apps/install" \	
    --with-ogg="/apps/install" --enable-shared && make -j$(nproc) && make install && \	
    make  distclean && ldconfig	

 # libvpx:	
RUN wget -nv -O /apps/source/ffmpeg_sources/v1.6.1.tar.gz \	
    "https://codeload.github.com/webmproject/libvpx/tar.gz/v1.6.1" && \	
    cd /apps/source/ffmpeg_sources && tar xzf v1.6.1.tar.gz && cd libvpx-1.6.1 && \	
    ./configure --prefix="/apps/install" --enable-shared --enable-vp8 \	
    --enable-vp9 --enable-pic --disable-debug --disable-examples --disable-docs \	
    --as=yasm && make -j$(nproc) && make install && make distclean && ldconfig	

 # libx264:	
RUN wget -nv -O /apps/source/ffmpeg_sources/x264-snapshot-20170226-2245-stable.tar.bz2 \	
    "http://download.videolan.org/pub/videolan/x264/snapshots/x264-snapshot-20170226-2245-stable.tar.bz2" && \	
    cd /apps/source/ffmpeg_sources && tar xvjf x264-snapshot-20170226-2245-stable.tar.bz2 && \	
    cd x264-snapshot-20170226-2245-stable && PKG_CONFIG_PATH="/apps/install/lib/pkgconfig" \	
    ./configure --prefix="/apps/install" --bindir="/apps/install" --enable-shared --disable-cli && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # libx265:	
RUN wget -nv -O /apps/source/ffmpeg_sources/x265_2.3.tar.gz \	
    "https://download.videolan.org/pub/videolan/x265/x265_2.3.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar xzf x265_2.3.tar.gz && cd x265_2.3/build/linux && \	
    MAKEFLAGS="-j" ./multilib.sh && cd 8bit && cmake ../../../source -DEXTRA_LIB="x265_main10.a;x265_main12.a" \	
    -DEXTRA_LINK_FLAGS=-L. -DLINKED_10BIT=ON -DLINKED_12BIT=ON -DCMAKE_INSTALL_PREFIX="/apps/install" && \	
    make install && make clean && cd ../10bit && make clean && cd ../12bit && make clean && ldconfig	

 # xvidcore:	
RUN wget -nv -O /apps/source/ffmpeg_sources/xvidcore-1.3.4.tar.gz \	
    "http://downloads.xvid.org/downloads/xvidcore-1.3.4.tar.gz" && \	
    cd /apps/source/ffmpeg_sources && tar zxf xvidcore-1.3.4.tar.gz && \	
    cd xvidcore/build/generic && ./configure --prefix="/apps/install" && \	
    make -j$(nproc) && make install && make distclean && ldconfig	

 # FFmpeg 3.3.3:	
RUN cd /apps/source/ffmpeg_sources && git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg && \	
    cd ffmpeg && git checkout release/3.3 && PKG_CONFIG_PATH="/apps/install/lib/pkgconfig" \	
    ./configure --bindir="/apps/install/bin" --disable-libsoxr --enable-avresample \	
    --enable-gpl --enable-libopencore-amrnb --enable-libopencore-amrwb \	
    --enable-libfdk_aac --enable-libmp3lame --enable-libopus --enable-libspeex \	
    --enable-libtheora --enable-libvorbis --enable-libvpx --enable-libx264 \	
    --enable-libx265 --enable-libxvid --enable-nonfree --enable-openssl \	
    --enable-shared --enable-version3 --extra-cflags="-I/apps/install/include" \	
    --extra-ldflags="-L/apps/install/lib" --extra-libs=-ldl --prefix="/apps/install" && \	
    make -j$(nproc) && make install && make distclean && ln -s /apps/install/bin/ffmpeg /usr/bin/ffmpeg && \	
    ldconfig

RUN ln -s /apps/install/bin/ffserver /usr/bin/ffserver && \
    ln -s /apps/install/bin/ffprobe /usr/bin/ffprobe

ENTRYPOINT [ "/bin/bash" ]