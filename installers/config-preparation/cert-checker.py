from __future__ import print_function
import sys
import os
from OpenSSL import crypto


def getCertInfo(certLocation):
    out = {}
    certF=open(certLocation, 'rt').read()
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, certF)
    subject = cert.get_subject()
    out['subject'] = "".join("/{0:s}={1:s}".format(name.decode(), value.decode()) for name, value in subject.get_components())
    out['notAfter'] = cert.get_notAfter()
    out['notBefore'] = cert.get_notBefore()
    out['issuer'] = "".join("/{0:s}={1:s}".format(name.decode(), value.decode()) for name, value in cert.get_issuer().get_components())
    out['fullDN'] = "%s%s" % (out['issuer'], out['subject'])
    print('Cert Info: %s' % out)
    print(('Certificate Subject:     ', out['subject']))
    print(('Certificate Valid From:  ', out['notAfter']))
    print(('Certificate Valid Until: ', out['notBefore']))
    print(('Certificate Issuer:      ', out['issuer']))
    print(('Certificate Full DN:     ', out['fullDN']))
    print('-'*80)
    print('INFO: Please ensure that Certificate full DN is entered in GIT Repo for the Frontend.')
    print('INFO: In case it is custom certificate, you will need to put ca in Fronend to trust local issued certificate')
    print('-'*80)

if __name__ == '__main__':
    print('Argument must be certificate file. Passed arguments %s' % sys.argv)
    getCertInfo(sys.argv[1])
