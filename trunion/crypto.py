# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Trunion
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Ryan Tilder (rtilder@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****


#
# Wrapper for crypto functions
#

from pyramid.threadlocal import get_current_registry

import jwt
import logging
import M2Crypto
import time

class KeyStore(object):

    def __init__(self, key=None, cert=None, interval=60):
        from pprint import pprint
        pprint(get_current_registry())

        if key is None:
            self.key_file = get_current_registry()['trunion']['keyfile']
        else:
            self.key_file = key

        if cert is None:
            self.cert_file = get_current_registry()['trunion']['certfile']
        else:
            self.cert_file = cert
        self.setKey(self.key_file)
        # FIXME Verify that it's actually a paired set of keys
        self.load_cert(self.cert_file)
        self.kid = json.loads(jwt.decode(self.certificate, verify=False))['key'][0]['kid']
        self.last_stat = time.time()
        self.poll_interval = interval

    def sign(self, data, hash):
        self.key.reset_context(hash)
        self.key.sign_init()
        self.key.sign_update(data)
        return self.key.sign_final()

    def verify(self, digest, signature, alg):
        self.key.verify_init()
        self.key.verify_update(digest)
        return self.key.verify_final(signature)

    def encode_jwt(self, payload):
        return jwt.encode(payload, self, u'RS256')

    def decode_jwt(self, payload):
        return jwt.decode(payload, self)

    def setKey(self, name):
        self.key = M2Crypto.EVP.load_key(name)
        self.load_cert(name)

    def load_cert(self, name):
        # FIXME  Need to verify that the pubkey in the cert does match the
        # signing key by doing a quick signature check
        try:
            self.certificate = open(name, "r").read()
            try:
                self.kid = json.loads(jwt.decode(self.certificate,
                                                 verify=False))['key'][0]['kid']
            except jwt.DecodeError:
                # This may raise an exception but that's ok
                self.kid = json.loads(self.certificate)['jwk'][0]['kid']
        except Exception, e:
            logging.error("Unable to load certificate for key '%s': cannot find '%s.crt' file in working directory" % (name, name))
            raise IOError("Unable to load certificate for key '%s'" % name)


KEYSTORE = None

def init(*args, **kwargs):
    global KEYSTORE
    if KEYSTORE is None:
        KEYSTORE = KeyStore(*args, **kwargs)

def sign(input_data):
	return KEYSTORE.sign(input_data, "sha256")

def sign_jwt(input_data):
	return KEYSTORE.encode_jwt(input_data)

def verify_jwt(input_data):
	return KEYSTORE.decode_jwt(input_data)

def get_certificate():
	return KEYSTORE.certificate
