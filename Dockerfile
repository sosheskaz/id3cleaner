ARG vPYTHON=3.8
ARG vALPINE=3.12

FROM python:${vPYTHON}-alpine${vALPINE} AS builder

COPY ./ /builder/

RUN cd /builder && python setup.py install

FROM python:${vPYTHON}-alpine${vALPINE}

ARG vPYTHON
COPY --from=builder /usr/local/lib/python${vPYTHON}/site-packages/ /usr/local/lib/python${vPYTHON}/site-packages/

ENTRYPOINT ["python", "-m", "id3cleaner"]
