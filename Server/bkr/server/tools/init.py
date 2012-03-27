#!/usr/bin/env python
# Beaker - 
#
# Copyright (C) 2008 bpeck@redhat.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# -*- coding: utf-8 -*-

import sys
from bkr.server.model import *
from bkr.server.commands import ConfigurationError
from bkr.server.util import load_config, log_to_stream
from turbogears.database import session
from os.path import dirname, exists, join
from os import getcwd
import turbogears
from turbogears.database import metadata, get_engine

from optparse import OptionParser

__version__ = '0.1'
__description__ = 'Command line tool for initializing Beaker DB'

def dummy():
    pass

def init_db(user_name=None, password=None, user_display_name=None, user_email_address=None):
    get_engine()
    metadata.create_all()
    session.begin()

    try:
        admin = Group.by_name(u'admin')
    except InvalidRequestError:
        admin     = Group(group_name=u'admin',display_name=u'Admin')

    try:
        lab_controller = Group.by_name(u'lab_controller')
    except InvalidRequestError:
        lab_controller = Group(group_name=u'lab_controller',
                               display_name=u'Lab Controller')
    
    #Setup User account
    if user_name:
        if password:
            user = User(user_name=user_name, password=password)
            if user_display_name:
                user.display_name = user_display_name
            if user_email_address:
                user.email_address = user_email_address
            admin.users.append(user)
        else:
            print "Password must be provided with username"

    if Permission.query.count() == 0:
        Permission(u'proxy_auth')
        admin.permissions.append(Permission(u'tag_distro'))

    #Setup Hypervisors Table
    if Hypervisor.query.count() == 0:
        kvm       = Hypervisor(hypervisor=u'KVM')
        xen       = Hypervisor(hypervisor=u'Xen')
        hyperv    = Hypervisor(hypervisor=u'HyperV')
        vmware    = Hypervisor(hypervisor=u'VMWare')

    #Setup base Architectures
    if Arch.query.count() == 0:
        i386   = Arch(u'i386')
        x86_64 = Arch(u'x86_64')
        ia64   = Arch(u'ia64')
        ppc    = Arch(u'ppc')
        ppc64  = Arch(u'ppc64')
        s390   = Arch(u's390')
        s390x  = Arch(u's390x')

    #Setup base power types
    if PowerType.query.count() == 0:
        apc_snmp    = PowerType(u'apc_snmp')
        bladecenter = PowerType(u'bladecenter')
        bullpap     = PowerType(u'bladepap')
        drac        = PowerType(u'drac')
        ether_wake  = PowerType(u'ether_wake')
        ilo         = PowerType(u'ilo')
        integrity   = PowerType(u'integrity')
        ipmilan     = PowerType(u'ipmilan')
        ipmitool    = PowerType(u'ipmitool')
        lpar        = PowerType(u'lpar')
        rsa         = PowerType(u'rsa')
        virsh       = PowerType(u'virsh')
        wti         = PowerType(u'wti')

    #Setup key types
    if Key.query.count() == 0:
        DISKSPACE       = Key('DISKSPACE',True)
        COMMENT         = Key('COMMENT')
        CPUFAMILY	= Key('CPUFAMILY',True)
        CPUFLAGS	= Key('CPUFLAGS')
        CPUMODEL	= Key('CPUMODEL')
        CPUMODELNUMBER 	= Key('CPUMODELNUMBER', True)
        CPUSPEED	= Key('CPUSPEED',True)
        CPUVENDOR	= Key('CPUVENDOR')
        DISK		= Key('DISK',True)
        FORMFACTOR 	= Key('FORMFACTOR')
        HVM		= Key('HVM')
        MEMORY		= Key('MEMORY',True)
        MODEL		= Key('MODEL')
        MODULE		= Key('MODULE')
        NETWORK		= Key('NETWORK')
        NR_DISKS	= Key('NR_DISKS',True)
        NR_ETH		= Key('NR_ETH',True)
        NR_IB		= Key('NR_IB',True)
        PCIID		= Key('PCIID')
        PROCESSORS	= Key('PROCESSORS',True)
        RTCERT		= Key('RTCERT')
        SCRATCH		= Key('SCRATCH')
        STORAGE		= Key('STORAGE')
        USBID		= Key('USBID')
        VENDOR		= Key('VENDOR')
        XENCERT		= Key('XENCERT')

    #Setup ack/nak reposnses
    if Response.query.count() == 0:
        ACK      = Response(response=u'ack')
        NAK      = Response(response=u'nak')

    if RetentionTag.query.count() == 0:
        SCRATCH         = RetentionTag(tag=u'scratch', is_default=1, expire_in_days=30)
        SIXTYDAYS       = RetentionTag(tag=u'60days', needs_product=False, expire_in_days=60)
        ONETWENTYDAYS   = RetentionTag(tag=u'120days', needs_product=False, expire_in_days=120)
        ACTIVE          = RetentionTag(tag=u'active', needs_product=True)
        AUDIT           = RetentionTag(tag=u'audit', needs_product=True)

    try:
        ConfigItem.by_name('root_password')
    except NoResultFound:
        rootpw_clear    = ConfigItem(name='root_password',
                                     description=u'Plaintext root password for provisioned systems')
    try:
        ConfigItem.by_name('root_password_hash')
    except NoResultFound:
        rootpw_hash     = ConfigItem(name='root_password_hash',
                                     description=u'Root password hash for provisioned systems',
                                     readonly=True)
    try:
        ConfigItem.by_name('root_password_validity')
    except NoResultFound:
        rootpw_validity = ConfigItem(name='root_password_validity',
                                     description=u"Maximum number of days a user's root password is valid for",
                                     numeric=True)

    session.commit()
    session.close()

def get_parser():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage, description=__description__,
                          version=__version__)

    ## Actions
    parser.add_option("-c", "--config", action="store", type="string",
                      dest="configfile", help="location of config file.")
    parser.add_option("-u", "--user", action="store", type="string",
                      dest="user_name", help="username of Admin account")
    parser.add_option("-p", "--password", action="store", type="string",
                      dest="password", help="password of Admin account")
    parser.add_option("-e", "--email", action="store", type="string",
                      dest="email_address", 
                      help="email address of Admin account")
    parser.add_option("-n", "--fullname", action="store", type="string",
                      dest="display_name", help="Full name of Admin account")

    return parser

def main():
    parser = get_parser()
    opts, args = parser.parse_args()
    load_config(opts.configfile)
    log_to_stream(sys.stderr)
    init_db(user_name=opts.user_name, password=opts.password,
            user_display_name=opts.display_name,
            user_email_address=opts.email_address)

if __name__ == "__main__":
    main()
