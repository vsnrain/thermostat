#!/usr/bin/env python3

import json
import time
import random
import inspect
import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response, RedirectResponse, HTMLResponse, JSONResponse

DEVICE_ID = '<put your device serial here>'

app = FastAPI()

# /entry
# ========================================

@app.post('/entry')
async def entry(request: Request):
    auth = request.headers['authorization']

    form = await request.form()
    mac = form['mac']

    log(f'mac :{mac}')
    #log(f'authorization :{auth}')

    res = {
        "server_version":       "9.44.0.63156-20251002-3e07db2",
        "tier_name":            "production",

        "czfe_url":             "http://192.168.1.100:8000/czfe/",
        "passphrase_url":       "http://192.168.1.100:8000/passphrase/",
        "transport_url":        "http://192.168.1.100:8000/transport/",
        "direct_transport_url": "http://192.168.1.100:8000/direct/",
        "upload_url":           "http://192.168.1.100:8000/upload/",
    }

    return JSONResponse(status_code=200, content=res)

# /transport/
# ========================================

@app.get('/ping')
async def transport_ping(request: Request, dev_id):
    return HTMLResponse(status_code=200, content='ok')

@app.get('/transport/v3/device/{dev_id}')
async def transport_v3_device(request: Request, dev_id):
    log(f'[server_squeakydoor][/tran/v3/device/] {dev_id}')

    with open(f'./settings/version.json') as f:
        ver = json.load(f)

    return JSONResponse(status_code=200, content=ver)

@app.post('/transport/v3/put')
async def transport_v3_put(request: Request):
    log(f'start')

    contents = await request.json()

    try:
        #cur = contents['shared'][DEVICE_ID]['current_temperature']
        tgt = contents['shared'][DEVICE_ID]['target_temperature']
        log(f'target temp {tgt}')
    except Exception as e:
        log(e)
        log(contents)

    response = {}
    with open(f'./settings/version.json') as f:
        ver = json.load(f)

    for setting in ['shared', 'schedule', 'device']:
        got_setting = contents.get(setting, {})
        if not got_setting:
            continue

        got_value = got_setting.get(DEVICE_ID, {})
        if not got_value:
            continue

        with open(f'./settings/{setting}.json') as f:
            oldconfig = json.load(f)

        deep_merge(oldconfig, got_value)

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

        response.update(new)
        ver.update(new)

        log(f'updated ver {setting} {new}')

    with open(f'./settings/version.json', 'w') as f:
        json.dump(ver, f, indent=4)

    return JSONResponse(status_code=200, content=response)

@app.post('/transport/v3/subscribe')
async def transport_v3_subscribe(request: Request):
    contents = await request.json()

    #time.sleep(3)
    #log(json.dumps(contents))
    #log('start')

    with open(f'./settings/version.json') as f:
        ver = json.load(f)

    _ts = int(time.time()*1000)

    for dd in contents.get('keys', []):
        dk = dd.get('key')
        dkk, dkd = dk.split('.')
        dv = dd.get('version', None)
        dt = dd.get('timestamp', None)

        if not (dv or dt):
            continue

        if (dv == ver[dkk][dkd]['$version']) and (dt == ver[dkk][dkd]['$timestamp']):
            continue

        try:
            with open(f'./settings/{dkk}.json', 'r') as f:
                res_content = json.load(f)
        except FileNotFoundError:
            log(f'send empty: no file {dkk}')
            res_content = {}

        log(f'subscribe: send version update {dk} -> {ver[dkk][dkd]}')
        _res = JSONResponse(status_code=200, content=res_content)
        _res.raw_headers = [
            (b'X-nl-defer-device-window', b'120'                                          ),
            (b'X-nl-skv-key',             f'{dkk}.{dkd}'.encode('ascii')                  ),
            (b'X-nl-skv-version',         f'{ver[dkk][dkd]['$version']}'.encode('ascii')  ),
            (b'X-nl-skv-timestamp',       f'{ver[dkk][dkd]['$timestamp']}'.encode('ascii')),
            (b'X-nl-service-timestamp',   f'{_ts}'.encode('ascii')                        ),
        ]
        return _res

    #log(f'send empty')
    _res = JSONResponse(status_code=200, content={})
    _res.raw_headers = [
        (b'X-nl-defer-device-window', b'120'),
        (b'X-nl-skv-key',             f'demand_response.{DEVICE_ID}'.encode('ascii')                      ),
        (b'X-nl-skv-version',         f'{ver['demand_response'][DEVICE_ID]['$version']}'.encode('ascii')  ),
        (b'X-nl-skv-timestamp',       f'{ver['demand_response'][DEVICE_ID]['$timestamp']}'.encode('ascii')),
        (b'X-nl-service-timestamp',   f'{ver['demand_response'][DEVICE_ID]['$timestamp']}'.encode('ascii')),
    ]
    return _res

# /passphrase/pass
# ========================================

@app.get('/passphrase/pass')
async def _pass(request: Request):
    log('pass called')
    res = {
        "value": "1234567",
        "expires": time.time() + 5*60
    }
    return JSONResponse(status_code=200, content=res)

# /upload/upload
# ========================================

@app.post('/upload')
async def upload(request: Request):
    log(f'start')
    #auth = request.headers['authorization']

    #contents = await request.body()
    #with open('./files/upload', "wb") as f:
    #    f.write(contents)

    res = {
        "authorized": True,
        "numBytes": 594,
        "md5": "8f0d5b61d225425b754790981e901475"
    }

    return JSONResponse(status_code=200, content=res)

# main
# ========================================

@app.exception_handler(404)
async def catch_all_404(request: Request, full_path: str):
    headers = dict(request.headers)
    host = request.headers['host']

    log(f'[404]: {request.method} {host}{request.url.path}')
    return Response(status_code=404)

def deep_merge(d1, d2):
    for k, v in d2.items():
        if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
            deep_merge(d1[k], v)
        else:
            d1[k] = v
    return d1

def log(msg):
    fname = inspect.stack()[1].function
    mname = inspect.stack()[1].frame.f_globals['__name__']
    print(f'[{datetime.datetime.now()}][{mname}][{fname}] {msg}')


if __name__=="__main__":
    uvicorn.run(
        'main:app', host='0.0.0.0', port=8000,
        reload=True, workers=3, log_level="critical"
    )
