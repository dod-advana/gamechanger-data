FROM paas/minimal:latest

ENV AWS_DEFAULT_REGION=us-gov-west-1

RUN rm -f /etc/yum.repos.d/s3-epel.repo \
    && curl -k -o /tmp/epel.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum install -y /tmp/epel.rpm \
    && rm -f /tmp/epel.rpm

RUN yum update -y \
	&& yum install -y file clamav python3 \
	&& yum clean all

RUN freshclam --update-db=daily

COPY parallel-dlp-scanner.py dirty-words.regex dlp-scanner.sh /srv/dlp-scanner/

ENTRYPOINT ["/srv/dlp-scanner/dlp-scanner.sh"]