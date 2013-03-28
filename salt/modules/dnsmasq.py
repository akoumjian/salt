'''
Module for managing dnqmasq
'''

# Import salt libs
import salt.utils

# Import python libs
import os
import logging

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only work on posix-like systems
    '''
    # Disable on these platorms, specific service modules exist:
    disable = [
        'Windows',
        ]
    if __grains__['os'] in disable:
        return False
    return 'dnsmasq'


def version():
    '''
    Shows installed version of dnsmasq

    CLI Example::

        salt '*' dnsmasq.version
    '''
    cmd = 'dnsmasq -v'
    out = __salt__['cmd.run'](cmd).splitlines()
    comps = out[0].split()
    return comps[2]


def fullversion():
    '''
    Shows installed version of dnsmasq, and compile options

    CLI Example::

        salt '*' dnsmasq.version
    '''
    cmd = 'dnsmasq -v'
    out = __salt__['cmd.run'](cmd).splitlines()
    comps = out[0].split()
    version = comps[2]
    comps = out[1].split()
    return {'version': version,
            'compile options': comps[3:]}


def set_config(config_file='/etc/dnsmasq.conf', follow=True, **kwargs):
    '''
    Sets a value or a set of values in the specified file. By default, if
    conf-dir is configured in this file, salt will attempt to set the option
    in any file inside the conf-dir where it has already been enabled. If it
    does not find it inside any files, it will append it to the main config
    file. Setting follow to False will turn off this behavior.

    If a config option currently appears multiple times (such as dhcp-host,
    which is specified at least once per host), the new option will be added
    to the end of the main config file (and not to any includes). If you need
    an option added to a specific include file, specify it as the config_file.

    CLI Examples::

        salt '*' dnsmasq.set_config domain=mydomain.com
        salt '*' dnsmasq.set_config follow=False domain=mydomain.com
        salt '*' dnsmasq.set_config file=/etc/dnsmasq.conf domain=mydomain.com
    '''
    dnsopts = get_config(config_file)
    includes = [config_file]
    if follow is True and 'conf-dir' in dnsopts:
        for filename in os.listdir(dnsopts['conf-dir']):
            if filename.startswith('.'):
                continue
            if filename.endswith('~'):
                continue
            if filename.endswith('bak'):
                continue
            if filename.endswith('#') and filename.endswith('#'):
                continue
            includes.append('{0}/{1}'.format(dnsopts['conf-dir'], filename))
    for key in kwargs.keys():
        if key in dnsopts:
            if type(dnsopts[key]) is str:
                for config in includes:
                    __salt__['file.sed'](path=config,
                                    before='^{0}=.*'.format(key),
                                    after='{0}={1}'.format(key, kwargs[key]))
            else:
                __salt__['file.append'](config_file,
                                    '{0}={1}'.format(key, kwargs[key]))
        else:
            __salt__['file.append'](config_file,
                                    '{0}={1}'.format(key, kwargs[key]))
    return kwargs


def get_config(config_file='/etc/dnsmasq.conf'):
    '''
    Dumps all options from the config file

    CLI Examples::

        salt '*' dnsmasq.get_config
        salt '*' dnsmasq.get_config file=/etc/dnsmasq.conf
    '''
    dnsopts = _parse_file(config_file)
    if 'conf-dir' in dnsopts:
        for filename in os.listdir(dnsopts['conf-dir']):
            if filename.startswith('.'):
                continue
            if filename.endswith('~'):
                continue
            if filename.endswith('#') and filename.endswith('#'):
                continue
            dnsopts.update(_parse_file('{0}/{1}'.format(dnsopts['conf-dir'],
                                                        filename)))
    return dnsopts


def _parse_file(filename):
    '''
    Generic function for parsing dnsmasq files, including includes
    '''
    fileopts = {}
    with salt.utils.fopen(filename, 'r') as fp_:
        for line in fp_:
            if not line.strip():
                continue
            if line.startswith('#'):
                continue
            if '=' in line:
                comps = line.split('=')
                if comps[0] in fileopts:
                    if type(fileopts[comps[0]]) is str:
                        temp = fileopts[comps[0]]
                        fileopts[comps[0]] = [temp]
                    fileopts[comps[0]].append(comps[1].strip())
                else:
                    fileopts[comps[0]] = comps[1].strip()
            else:
                if not 'unparsed' in fileopts:
                    fileopts['unparsed'] = []
                fileopts['unparsed'].append(line)
    return fileopts


