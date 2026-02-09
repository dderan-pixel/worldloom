// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title FeeCollector
 * @notice Collects trading fees and allows owner withdrawal
 */
contract FeeCollector is Ownable {
    using SafeERC20 for IERC20;

    event FeesWithdrawn(address indexed asset, address indexed to, uint256 amount);
    event ETHWithdrawn(address indexed to, uint256 amount);

    constructor(address admin) Ownable(admin) {}

    /**
     * @notice Withdraw ERC20 fees
     */
    function withdrawFees(address asset, address to, uint256 amount) external onlyOwner {
        require(to != address(0), "Invalid recipient");
        require(amount > 0, "Amount must be > 0");
        
        IERC20(asset).safeTransfer(to, amount);
        emit FeesWithdrawn(asset, to, amount);
    }

    /**
     * @notice Withdraw ETH fees
     */
    function withdrawETH(address payable to, uint256 amount) external onlyOwner {
        require(to != address(0), "Invalid recipient");
        require(amount > 0, "Amount must be > 0");
        require(address(this).balance >= amount, "Insufficient balance");
        
        (bool success, ) = to.call{value: amount}("");
        require(success, "ETH transfer failed");
        
        emit ETHWithdrawn(to, amount);
    }

    /**
     * @notice Get ERC20 balance
     */
    function getBalance(address asset) external view returns (uint256) {
        return IERC20(asset).balanceOf(address(this));
    }

    /**
     * @notice Get ETH balance
     */
    function getETHBalance() external view returns (uint256) {
        return address(this).balance;
    }

    /**
     * @notice Receive ETH
     */
    receive() external payable {}
}
