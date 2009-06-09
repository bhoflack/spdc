import ldap
from ldap.dn import str2dn, dn2str
import sys

def domainnames(l):
  """ get a mapping of dn and domain name, sid """
  mapping = {}
  # locate all the samba domains in the ldap
  r = l.search_s('dc=elex', ldap.SCOPE_SUBTREE, '(objectClass=sambaDomain)', ['sambaDomainName','sambaSID'])
  for dn, entry in r:
    mapping[dn] = (entry['sambaDomainName'][0], entry['sambaSID'][0])
  return mapping

def domainroot(d):
  """ get the domain ldap root for the given dn 

      >>> dn = "sambaDomainName=IEPER-TEST,dc=Ieper,dc=elex"
      >>> domainroot(dn)
      'dc=Ieper,dc=elex'
  """
  dn = str2dn(d)
  dn.pop(0)
  return dn2str(dn)

def sambaaccountsindomainroot(domainroot, l):
  """ get a list of dn's of all the sambaaccounts for a given domainroot """
  dns = {}
  r = l.search_s(domainroot, ldap.SCOPE_SUBTREE, '(objectClass=sambaSamAccount)', ['uidNumber'])
  for dn, entry in r:
    try:
      dns[dn] = entry['uidNumber'][0]
    except KeyError:
      sys.stderr.write("dn %s has no uidNumber!\n" % dn)
  return dns

def updatesid(dn, sid, l):
  """ update an account with a new sid number """
  mod_attrs = [(ldap.MOD_REPLACE, 'sambaSID', sid )]
  l.modify_s(dn, mod_attrs)

def main(ldapserver, user_dn, user_pw):
  try:
    l = ldap.initialize(ldapserver)
    l.bind_s(user_dn, user_pw)
    for dn, d in domainnames(l).iteritems():
      domain, sid = d
      print "Found domain %s in dn %s with sid %s" % (domain, dn, sid)
      # locate all the samba accounts in the given domainroot
      for dn, uid in sambaaccountsindomainroot(domainroot(dn), l).iteritems():
        print "dn %s uid %s" % (dn, uid)
        updatesid(dn, "%s-%s" % (sid, uid), l)
  except ldap.INVALID_CREDENTIALS:
    sys.stderr.write("Your username or password is incorrent.")
    sys.exit()

def _test():
  import doctest
  doctest.testmod()

if __name__ == '__main__':
  if len(sys.argv) == 1:
    _test()
  else:
    main(sys.argv[1], sys.argv[2], sys.argv[3])

