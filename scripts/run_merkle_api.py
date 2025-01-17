#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
"""Testing merkle API"""

import json
import os

from flask import Flask, jsonify


app = Flask(__name__)

script_path = os.path.dirname(os.path.realpath(__file__))

with open(f"{script_path}//api_data.json", "r", encoding="utf-8") as data_file:
    api_data = json.load(data_file)


@app.route("/merkle", methods=["GET"])
def merkle():
    """Merkle"""
    return jsonify(api_data)


if __name__ == "__main__":
    app.run(debug=False)
