FROM gcc:latest

RUN mkdir /usr/src/bf_jit
COPY . /usr/src/bf_jit

WORKDIR /usr/src/bf_jit
RUN gcc -o bf bf_jit.c