#!/usr/bin/env python3
# example script to change setting and update timestamp to  sync with device

import cmd
import json
import time
import random

DEVICE_ID = '<your device serial>'

def deep_merge(d1, d2):
    for k, v in d2.items():
        if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
            deep_merge(d1[k], v)
        else:
            d1[k] = v
    return d1


def edit_config(setting, value):
    with open(f'./settings/version.json') as f:
        ver = json.load(f)
    with open(f'./settings/{setting}.json') as f:
        oldconfig = json.load(f)

    deep_merge(oldconfig, value)

    with open(f'./settings/{setting}.json', 'w') as f:
        json.dump(oldconfig, f, indent=4)

    new = {
        setting: {
            DEVICE_ID: {
                "$version": random.randint(1000, 9000),
                "$timestamp": int(time.time()*1000)
            }
        }
    }
    ver.update(new)
    with open(f'./settings/version.json', 'w') as f:
        json.dump(ver, f, indent=4)




class MyCLI(cmd.Cmd):
    prompt = '> '

    def do_temp(self, arg):
        """temp <int>"""
        try:
            edit_config('shared', {'target_temperature': int(arg)} )
        except ValueError:
            print('invalid int')

    def do_name(self, arg):
        """name <string>"""
        edit_config('shared', {'name': arg} )

    def do_exit(self, arg):
        """exit"""
        return True  # ends loop

if __name__ == '__main__':
    MyCLI().cmdloop()


