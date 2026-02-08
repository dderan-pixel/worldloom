// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title Vault
 * @notice Holds user deposits (USDC/ETH) and manages internal accounting
 * @dev Only Settlement contract can move balances for trades
 */
contract Vault is ReentrancyGuard, Pausable, AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant SETTLEMENT_ROLE = keccak256("SETTLEMENT_ROLE");

    // user => asset => balance
    mapping(address => mapping(address => uint256)) public balances;
    
    // user => asset => locked balance (in active orders)
    mapping(address => mapping(address => uint256)) public lockedBalances;

    // Supported assets
    mapping(address => bool) public supportedAssets;

    event Deposited(address indexed user, address indexed asset, uint256 amount);
    event Withdrawn(address indexed user, address indexed asset, uint256 amount);
    event BalanceUpdated(address indexed user, address indexed asset, uint256 available, uint256 locked);
    event AssetAdded(address indexed asset);
    event AssetRemoved(address indexed asset);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
    }

    /**
     * @notice Deposit ERC20 tokens
     */
    function deposit(address asset, uint256 amount) external nonReentrant whenNotPaused {
        require(supportedAssets[asset], "Asset not supported");
        require(amount > 0, "Amount must be > 0");

        IERC20(asset).safeTransferFrom(msg.sender, address(this), amount);
        balances[msg.sender][asset] += amount;

        emit Deposited(msg.sender, asset, amount);
        emit BalanceUpdated(msg.sender, asset, balances[msg.sender][asset], lockedBalances[msg.sender][asset]);
    }

    /**
     * @notice Deposit ETH
     */
    function depositETH() external payable nonReentrant whenNotPaused {
        require(supportedAssets[address(0)], "ETH not supported");
        require(msg.value > 0, "Amount must be > 0");

        balances[msg.sender][address(0)] += msg.value;

        emit Deposited(msg.sender, address(0), msg.value);
        emit BalanceUpdated(msg.sender, address(0), balances[msg.sender][address(0)], lockedBalances[msg.sender][address(0)]);
    }

    /**
     * @notice Withdraw available balance
     */
    function withdraw(address asset, uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be > 0");
        require(balances[msg.sender][asset] >= amount, "Insufficient balance");
        require(balances[msg.sender][asset] - lockedBalances[msg.sender][asset] >= amount, "Insufficient available balance");

        balances[msg.sender][asset] -= amount;

        if (asset == address(0)) {
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "ETH transfer failed");
        } else {
            IERC20(asset).safeTransfer(msg.sender, amount);
        }

        emit Withdrawn(msg.sender, asset, amount);
        emit BalanceUpdated(msg.sender, asset, balances[msg.sender][asset], lockedBalances[msg.sender][asset]);
    }

    /**
     * @notice Lock balance for orders (Settlement role only)
     */
    function lockBalance(address user, address asset, uint256 amount) external onlyRole(SETTLEMENT_ROLE) {
        require(balances[user][asset] - lockedBalances[user][asset] >= amount, "Insufficient available balance");
        lockedBalances[user][asset] += amount;
        emit BalanceUpdated(user, asset, balances[user][asset], lockedBalances[user][asset]);
    }

    /**
     * @notice Unlock balance (Settlement role only)
     */
    function unlockBalance(address user, address asset, uint256 amount) external onlyRole(SETTLEMENT_ROLE) {
        require(lockedBalances[user][asset] >= amount, "Insufficient locked balance");
        lockedBalances[user][asset] -= amount;
        emit BalanceUpdated(user, asset, balances[user][asset], lockedBalances[user][asset]);
    }

    /**
     * @notice Transfer balance between users (Settlement role only)
     */
    function transferBalance(address from, address to, address asset, uint256 amount) external onlyRole(SETTLEMENT_ROLE) {
        require(balances[from][asset] >= amount, "Insufficient balance");
        balances[from][asset] -= amount;
        balances[to][asset] += amount;
        
        emit BalanceUpdated(from, asset, balances[from][asset], lockedBalances[from][asset]);
        emit BalanceUpdated(to, asset, balances[to][asset], lockedBalances[to][asset]);
    }

    /**
     * @notice Get available balance (not locked)
     */
    function availableBalance(address user, address asset) external view returns (uint256) {
        return balances[user][asset] - lockedBalances[user][asset];
    }

    /**
     * @notice Add supported asset
     */
    function addAsset(address asset) external onlyRole(OPERATOR_ROLE) {
        supportedAssets[asset] = true;
        emit AssetAdded(asset);
    }

    /**
     * @notice Remove supported asset
     */
    function removeAsset(address asset) external onlyRole(OPERATOR_ROLE) {
        supportedAssets[asset] = false;
        emit AssetRemoved(asset);
    }

    /**
     * @notice Pause contract
     */
    function pause() external onlyRole(OPERATOR_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause contract
     */
    function unpause() external onlyRole(OPERATOR_ROLE) {
        _unpause();
    }
}
