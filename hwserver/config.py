import ConfigParser

CONFIG_FILE = "/etc/homeauto/homeauto.conf"

glob = {}

def _confRead():
    glob["confParser"] = ConfigParser.RawConfigParser()
    glob["confParser"].read(CONFIG_FILE)

def _conf(method, section, option, default=None):
    if "cmdlineOptions" not in glob:
        _confRead()
    try:
        return getattr(glob["confParser"], method)(section, option)
    except ConfigParser.NoSectionError:
        return default
    except ConfigParser.NoOptionError:
        return default

def conf(*args, **kwargs):
    return _conf("get", *args, **kwargs)

def confInt(*args, **kwargs):
    return _conf("getint", *args, **kwargs)

