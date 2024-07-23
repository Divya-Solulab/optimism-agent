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


"""Updates fetched agent with correct config"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def main() -> None:
    """Main"""
    load_dotenv()

    with open(Path("optimism_agent", "aea-config.yaml"), "r", encoding="utf-8") as file:
        config = list(yaml.safe_load_all(file))

        # Ledger RPCs
        if os.getenv("ETHEREUM_LEDGER_RPC"):
            config[2]["config"]["ledger_apis"]["ethereum"][
                "address"
            ] = f"${{str:{os.getenv('ETHEREUM_LEDGER_RPC')}}}"

        if os.getenv("ARBITRUM_LEDGER_RPC"):
            config[2]["config"]["ledger_apis"]["arbitrum"][
                "address"
            ] = f"${{str:{os.getenv('ARBITRUM_LEDGER_RPC')}}}"

        if os.getenv("BNB_LEDGER_RPC"):
            config[2]["config"]["ledger_apis"]["bnb"][
                "address"
            ] = f"${{str:{os.getenv('BNB_LEDGER_RPC')}}}"

        # Params
        config[5]["models"]["params"]["args"]["setup"][
            "all_participants"
        ] = f"${{list:{os.getenv('ALL_PARTICIPANTS')}}}"

        config[5]["models"]["params"]["args"][
            "safe_contract_addresses"
        ] = f"${{str:{os.getenv('SAFE_CONTRACT_ADDRESSES')}}}"

        config[5]["models"]["params"]["args"][
            "pool_data_api_url"
        ] = f"${{str:{os.getenv('POOL_DATA_API_URL')}}}"

        config[5]["models"]["params"]["args"][
            "slippage_for_swap"
        ] = f"${{float:{os.getenv('SLIPPAGE_FOR_SWAP')}}}"

    with open(Path("optimism_agent", "aea-config.yaml"), "w", encoding="utf-8") as file:
        yaml.dump_all(config, file, sort_keys=False)


if __name__ == "__main__":
    main()
