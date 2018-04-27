#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

import config
from handle_updates import *

def main():
    hu = HandleUpdates
    last_update_id = None

    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            hu.handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
