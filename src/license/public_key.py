# Den offentlige Ed25519-nøgle - trygt at committe til git.
#
# Den kan kun VERIFICERE licensnøgler, aldrig generere/signere nye. Den
# tilhørende private nøgle (som rent faktisk kan generere gyldige nøgler)
# ligger ALDRIG i repoet - kun lokalt på udstederens maskine, i
# src/private_key.pem (git-ignoreret). Se license/keygen.py.

PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAP1LQIDZHZ6Tcbn75NPev0rmCtETwYixkLgyfrag13aA=
-----END PUBLIC KEY-----
"""
