// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ERC20Invoice {
    constructor(address _token, address _to) {
        (bool success, bytes memory balance) = _token.staticcall(abi.encodeWithSelector(bytes4(0x70a08231), address(this)));
        _token.call(abi.encodeWithSelector(bytes4(0xa9059cbb), _to, abi.decode(balance, (uint256))));
    }
}
