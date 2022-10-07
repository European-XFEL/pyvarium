FROM ecpe4s/ubuntu20.04:22.08

RUN . /spack/share/spack/setup-env.sh && spack install python && spack install py-pip

RUN apt install python3.8-venv

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install pipx

RUN pipx install pipenv
RUN pipx install poetry

ENV PATH="${PATH}:/root/.local/bin"
