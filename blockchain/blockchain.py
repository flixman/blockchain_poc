"""Module for blockchain definition and operations."""

import json
import logging
from dataclasses import dataclass, field
from typing import Self

from blockchain.block import Block

logger = logging.getLogger("blockchain")


@dataclass
class Blockchain:
    """Model a blockchain."""

    _chain: list[Block] = field(default_factory=list[Block])

    def __len__(self) -> int:
        """Return the length of the inner chain."""
        return len(self._chain)

    def add_block(self, block: Block) -> None:
        """Add a block to the chain."""
        self._chain.append(block)

    @property
    def last_block(self) -> Block:
        """Return the reference to the last block of the chain."""
        return self._chain[-1]

    @property
    def chain(self) -> list[Block]:
        """Return a reference to the internal chain."""
        return self._chain

    def set(self, new_chain: Self) -> None:
        """Reset the internal chain to the given."""
        self._chain = new_chain.chain

    def validate(self) -> bool:
        """Validate each block of the chain."""
        # validate the first block
        if not self._chain[0].validate():
            return False

        # validate all the blocks
        return all(
            block.previous_block_hash == last_block.hash and block.validate()
            for block, last_block in zip(self._chain[1:], self._chain[:-1], strict=True)
        )

    def serialize(self) -> bytes:
        """Serialize the chain into bytes."""
        return json.dumps([block.to_dict() for block in self._chain]).encode()

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        """Deserialize the chain from bytes."""
        blocks_data = json.loads(data)
        return cls(_chain=[Block.from_dict(b) for b in blocks_data])

    def __repr__(self) -> str:
        """Return a string with the contents of the chain."""
        return ",".join(str(x) for x in self._chain)
