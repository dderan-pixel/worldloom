// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./Vault.sol";
import "./OutcomeToken.sol";
import "./MarketManager.sol";
import "./FeeCollector.sol";

/**
 * @title Settlement
 * @notice Processes batch settlements from off-chain matching engine
 * @dev MVP: Backend is authorized operator. Future: Verify EIP-712 signatures
 */
contract Settlement is AccessControl, ReentrancyGuard, Pausable {
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    Vault public vault;
    OutcomeToken public outcomeToken;
    MarketManager public marketManager;
    FeeCollector public feeCollector;

    uint256 public feeRate; // in basis points (100 = 1%)
    uint256 public constant MAX_FEE_RATE = 500; // 5%

    struct Trade {
        uint256 marketId;
        address maker;
        address taker;
        bool isBuyYes; // true if buying YES, false if buying NO
        uint256 price; // price in collateral (scaled by 1e18)
        uint256 size; // number of shares
    }

    event TradeSettled(
        uint256 indexed marketId,
        address indexed maker,
        address indexed taker,
        bool isBuyYes,
        uint256 price,
        uint256 size,
        uint256 fee
    );
    event BatchSettled(uint256 indexed batchId, uint256 tradeCount);
    event FeeRateUpdated(uint256 newFeeRate);

    constructor(
        address admin,
        address _vault,
        address _outcomeToken,
        address _marketManager,
        address _feeCollector,
        uint256 _feeRate
    ) {
        require(_vault != address(0), "Invalid vault");
        require(_outcomeToken != address(0), "Invalid outcome token");
        require(_marketManager != address(0), "Invalid market manager");
        require(_feeCollector != address(0), "Invalid fee collector");
        require(_feeRate <= MAX_FEE_RATE, "Fee rate too high");

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);

        vault = Vault(_vault);
        outcomeToken = OutcomeToken(_outcomeToken);
        marketManager = MarketManager(_marketManager);
        feeCollector = FeeCollector(_feeCollector);
        feeRate = _feeRate;
    }

    /**
     * @notice Settle a batch of matched trades
     */
    function settleBatch(
        uint256 batchId,
        Trade[] calldata trades,
        address collateralAsset
    ) external onlyRole(OPERATOR_ROLE) nonReentrant whenNotPaused {
        require(trades.length > 0, "Empty batch");

        for (uint256 i = 0; i < trades.length; i++) {
            _settleTrade(trades[i], collateralAsset);
        }

        emit BatchSettled(batchId, trades.length);
    }

    /**
     * @notice Settle a single trade
     */
    function _settleTrade(Trade calldata trade, address collateralAsset) internal {
        // Verify market is open
        require(marketManager.isMarketOpen(trade.marketId), "Market not open");
        
        // Validate trade parameters
        require(trade.price > 0 && trade.price <= 1e18, "Invalid price");
        require(trade.size > 0, "Invalid size");

        // Calculate amounts
        uint256 collateralAmount = (trade.size * trade.price) / 1e18;
        uint256 fee = (collateralAmount * feeRate) / 10000;
        uint256 collateralAmountAfterFee = collateralAmount - fee;

        // Determine who is buyer and seller
        address buyer;
        address seller;
        bool buyingYes;

        if (trade.isBuyYes) {
            buyer = trade.taker;
            seller = trade.maker;
            buyingYes = true;
        } else {
            buyer = trade.maker;
            seller = trade.taker;
            buyingYes = false;
        }

        // Transfer collateral from buyer to seller (minus fee)
        vault.transferBalance(buyer, seller, collateralAsset, collateralAmountAfterFee);
        
        // Transfer fee to fee collector
        if (fee > 0) {
            vault.transferBalance(buyer, address(feeCollector), collateralAsset, fee);
        }

        // Mint outcome shares to buyer
        outcomeToken.mint(buyer, trade.marketId, buyingYes, trade.size);

        emit TradeSettled(
            trade.marketId,
            trade.maker,
            trade.taker,
            trade.isBuyYes,
            trade.price,
            trade.size,
            fee
        );
    }

    /**
     * @notice Redeem winning shares after market resolution
     */
    function redeemShares(
        uint256 marketId,
        address collateralAsset
    ) external nonReentrant whenNotPaused {
        require(marketManager.canRedeem(marketId), "Cannot redeem yet");

        MarketManager.Market memory market = marketManager.getMarket(marketId);
        require(market.resolvedOutcome != MarketManager.Outcome.INVALID, "Invalid outcome");

        bool isYesWinner = market.resolvedOutcome == MarketManager.Outcome.YES;
        
        uint256 shares;
        if (isYesWinner) {
            shares = outcomeToken.getYesShares(msg.sender, marketId);
        } else {
            shares = outcomeToken.getNoShares(msg.sender, marketId);
        }

        require(shares > 0, "No winning shares");

        // Burn the winning shares
        outcomeToken.burn(msg.sender, marketId, isYesWinner, shares);

        // Transfer collateral (1:1 ratio, shares worth 1 unit each)
        vault.transferBalance(address(this), msg.sender, collateralAsset, shares);
    }

    /**
     * @notice Update fee rate
     */
    function setFeeRate(uint256 newFeeRate) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newFeeRate <= MAX_FEE_RATE, "Fee rate too high");
        feeRate = newFeeRate;
        emit FeeRateUpdated(newFeeRate);
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
