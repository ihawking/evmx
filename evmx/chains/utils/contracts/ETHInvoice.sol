// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ETHInvoice {
    constructor(address _to) {
        selfdestruct(payable(_to));
    }
}
