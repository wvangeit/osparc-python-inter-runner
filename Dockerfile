FROM ubuntu:22.04 as base

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS="yes"

RUN apt-get update --yes && apt-get upgrade --yes 
RUN apt-get install -y --no-install-recommends apt-utils
RUN apt-get install --yes --no-install-recommends python3 python-is-python3 python3-venv

########
# Only necessary for Dakota
########
RUN apt install --yes --no-install-recommends gfortran liblapack-dev libboost-dev libboost-filesystem-dev libboost-program-options-dev \
    libboost-regex-dev libboost-serialization-dev libblas-dev 
RUN apt install --yes --no-install-recommends wget cmake make gcc g++ python3-dev python3-numpy git

ENV DAKOTA_VERSION 6.18.0

USER $NB_UID   

RUN wget -q https://github.com/snl-dakota/dakota/releases/download/v${DAKOTA_VERSION}/dakota-${DAKOTA_VERSION}-public-src-cli.tar.gz && \
  tar -xzf dakota-${DAKOTA_VERSION}-public-src-cli.tar.gz && \
  rm -rf dakota-${DAKOTA_VERSION}-public-src-cli.tar.gz

ENV DAKOTA_INSTALL_DIR /usr/local

RUN cd dakota-${DAKOTA_VERSION}-public-src-cli && \
  mkdir build && \
  cd build && \
  cmake .. \
  -Wno-dev \
  -D CMAKE_INSTALL_PREFIX=${DAKOTA_INSTALL_DIR} \
  -D CMAKE_C_FLAGS="-O2 -w" \
  -D CMAKE_CXX_FLAGS="-O2 -w" \
  -D CMAKE_Fortran_FLAGS="-O2 -w" \
  -D DAKOTA_PYTHON_WRAPPER=ON \
  -D DAKOTA_PYTHON_DIRECT_INTERFACE=ON \
  -D DAKOTA_PYTHON_SURROGATES=ON \
  -D PYBIND11_INSTALL=ON \
  -D DAKOTA_PYBIND11=ON && \ 
  make -j && \
  ctest -L Accept && \
  make install

RUN dakota -v  
#########
# End Dakota block
########

# Copying boot scripts                                                                                                                                                                                                                                                                                                   
COPY docker_scripts /docker

ENTRYPOINT [ "/bin/bash", "/docker/entrypoint.bash" ]
CMD [ "/bin/sh", "-c", "docker/runner.bash "]
