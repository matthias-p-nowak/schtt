import yaml

defaultCFG = """
---
endpoints:
  - name: rhino
    type: sip
    local: 
        host: localhost
        port: 6060
    remote:
        host: localhost
        port: 5060
    transport: udp
concurrent: 5
debug: 0
"""
Config = yaml.safe_load(defaultCFG)


def get_config(key: str, default):
    global Config
    keys = key.split('.')
    val = Config
    for k in keys:
        if k in val:
            val = val[k]
        else:
            return default
    return val


def update_config(cf):
    cfg2 = yaml.safe_load(cf)
    if cfg2 is not None:
        Config.update(cfg2)
