# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

"""This package contains the implemenatation of the BalancerPoolBehaviour class."""

from abc import ABC
from typing import Any, Dict, Generator, List, Optional, Tuple

from packages.valory.contracts.balancer_vault.contract import VaultContract
from packages.valory.contracts.balancer_weighted_pool.contract import (
    WeightedPoolContract,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.liquidity_trader_abci.pool_behaviour import PoolBehaviour


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class BalancerPoolBehaviour(PoolBehaviour, ABC):
    """BalancerPoolBehaviour"""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the balancer pool behaviour."""
        super().__init__(**kwargs)
        # https://docs.balancer.fi/reference/joins-and-exits/pool-exits.html#userdata
        self.exit_kind: int = 1  # EXACT_BPT_IN_FOR_TOKENS_OUT
        # https://docs.balancer.fi/reference/joins-and-exits/pool-joins.html#userdata
        self.join_kind: int = 1  # EXACT_TOKENS_IN_FOR_BPT_OUT

    def enter(self, **kwargs: Any) -> Generator[None, None, Optional[Tuple[str, str]]]:
        """Enter a Balancer pool."""
        pool_address = kwargs.get("pool_address")
        safe_address = kwargs.get("safe_address")
        assets = kwargs.get("assets")
        chain = kwargs.get("chain")
        max_amounts_in = kwargs.get("max_amounts_in")

        if not all([pool_address, safe_address, assets, chain, max_amounts_in]):
            self.context.logger.error(
                f"Missing required parameters for entering the pool. Here are the kwargs: {kwargs}"
            )
            return None, None

        # Get vault contract address from balancer weighted pool contract
        vault_address = self.params.balancer_vault_contract_addresses.get(chain, "")
        if not vault_address:
            self.context.logger.error(f"No vault address found for chain {chain}")
            return None, None

        # Fetch the pool id
        pool_id = yield from self._get_pool_id(pool_address, chain)  # getPoolId()
        if pool_id is None:
            return None, None

        # TO-DO: calculate minimum_bpt
        minimum_bpt = 0

        # fromInternalBalance - True if sending from internal token balances. False if sending ERC20.
        from_internal_balance = ZERO_ADDRESS in assets

        tx_hash = yield from self.contract_interact(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_address=vault_address,
            contract_public_id=VaultContract.contract_id,
            contract_callable="join_pool",
            data_key="tx_hash",
            pool_id=pool_id,
            sender=safe_address,
            recipient=safe_address,
            assets=assets,
            max_amounts_in=max_amounts_in,
            join_kind=self.join_kind,
            minimum_bpt=minimum_bpt,
            from_internal_balance=from_internal_balance,
            chain_id=chain,
        )

        return tx_hash, vault_address

    def exit(self, **kwargs: Any) -> Generator[None, None, Optional[Tuple[str,str,bool]]]:
        """Exit pool"""
        pool_address = kwargs.get("pool_address")
        safe_address = kwargs.get("safe_address")
        assets = kwargs.get("assets")
        chain = kwargs.get("chain")

        if not all([pool_address, safe_address, assets, chain]):
            self.context.logger.error(
                f"Missing required parameters for exiting the pool. Here are the kwargs: {kwargs}"
            )
            return None, None, None

        # Get vault contract address from balancer weighted pool contract
        vault_address = self.params.balancer_vault_contract_addresses.get(chain, "")
        if not vault_address:
            self.context.logger.error(f"No vault address found for chain {chain}")
            return None, None, None

        # Fetch the pool id
        pool_id = yield from self._get_pool_id(pool_address, chain)  # getPoolId()
        if pool_id is None:
            return None, None, None

        # TO-DO: queryExit in BalancerQueries to find the current amounts of tokens we would get for our BPT, and then account for some possible slippage.
        min_amounts_out = [0, 0]

        # fetch the amount of LP tokens
        bpt_amount_in = yield from self.contract_interact(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_address=pool_address,
            contract_public_id=str(WeightedPoolContract.contract_id),
            contract_callable="get_balance",
            data_key="balance",
            account=safe_address,
            chain_id=chain,
        )
        if bpt_amount_in is None:
            self.context.logger.error(
                f"Error fetching BPT Amount for safe {safe_address} for pool {pool_address}"
            )
            return None, None, None

        # toInternalBalance - True if receiving internal token balances. False if receiving ERC20.
        to_internal_balance = ZERO_ADDRESS in assets

        tx_hash = yield from self.contract_interact(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_address=vault_address,
            contract_public_id=VaultContract.contract_id,
            contract_callable="exit_pool",
            data_key="tx_hash",
            pool_id=pool_id,
            sender=safe_address,
            recipient=safe_address,
            assets=assets,
            min_amounts_out=min_amounts_out,
            exit_kind=self.exit_kind,
            bpt_amount_in=bpt_amount_in,
            to_internal_balance=to_internal_balance,
            chain_id=chain,
        )

        return tx_hash, vault_address, False

    def _get_tokens(
        self, pool_address: str, chain: str
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Get balancer pool tokens"""
        """Return a dict of tokens {"token0": 0x00, "token1": 0x00}"""

        # Get vault contract address from balancer weighted pool contract
        vault_address = self.params.balancer_vault_contract_addresses.get(chain, "")
        if not vault_address:
            self.context.logger.error(f"No vault address found for chain {chain}")
            return []

        # Fetch the pool id
        pool_id = yield from self._get_pool_id(pool_address, chain)  # getPoolId()
        if pool_id is None:
            return []

        pool_tokens = yield from self.contract_interact(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_address=vault_address,
            contract_public_id=VaultContract.contract_id,
            contract_callable="get_pool_tokens",
            data_key="tokens",
            pool_id=pool_id,
            chain_id=chain,
        )

        if not pool_tokens:
            self.context.logger.error(
                f"Could not fetch tokens for balancer pool id {pool_id}"
            )
            return None
        
        tokens = {
            "token0" : pool_tokens[0][0],
            "token1" : pool_tokens[0][1]
        }
        self.context.logger.info(
            f"Tokens for balancer poolId {pool_id} : {pool_tokens}"
        )
        return tokens

    def _get_pool_id(
        self, pool_address: str, chain: str
    ) -> Generator[None, None, Optional[str]]:
        """Get pool id"""

        pool_id = yield from self.contract_interact(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_address=pool_address,
            contract_public_id=WeightedPoolContract.contract_id,
            contract_callable="get_pool_id",
            data_key="pool_id",
            chain_id=chain,
        )

        if not pool_id:
            self.context.logger.error(
                f"Could not fetch the Pool ID for pool {pool_address}"
            )
            return None

        self.context.logger.info(f"PoolId for balancer pool {pool_address}: {pool_id}")
        return pool_id
