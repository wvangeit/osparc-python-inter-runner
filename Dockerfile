FROM ubuntu:22.04 as base
RUN apt-get update --yes && apt-get upgrade --yes
RUN apt-get install --yes --no-install-recommends python3 python-is-python3 python3-venv

USER $NB_UID   

# Copying boot scripts                                                                                                                                                                                                                                                                                                   
COPY docker_scripts /docker

ENTRYPOINT [ "/bin/bash", "/docker/entrypoint.bash" ]
CMD [ "/bin/sh", "-c", "docker/runner.bash "]
