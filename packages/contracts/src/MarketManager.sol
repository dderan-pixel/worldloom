// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title MarketManager
 * @notice Manages prediction market lifecycle: creation, states, resolution
 */
contract MarketManager is AccessControl, Pausable {
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    enum MarketState { OPEN, FROZEN, RESOLVED }
    enum Outcome { INVALID, YES, NO }

    struct Market {
        uint256 id;
        string question;
        uint256 endTime;
        MarketState state;
        Outcome resolvedOutcome;
        address oracle;
        uint256 disputeWindow; // seconds
        uint256 disputeEndsAt;
        uint256 createdAt;
    }

    uint256 public marketCounter;
    mapping(uint256 => Market) public markets;

    event MarketCreated(
        uint256 indexed marketId,
        string question,
        uint256 endTime,
        address oracle,
        uint256 disputeWindow
    );
    event MarketStateChanged(uint256 indexed marketId, MarketState newState);
    event MarketResolved(uint256 indexed marketId, Outcome outcome);
    event DisputeStarted(uint256 indexed marketId, uint256 disputeEndsAt);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
        _grantRole(ORACLE_ROLE, admin);
    }

    /**
     * @notice Create a new prediction market
     */
    function createMarket(
        string calldata question,
        uint256 endTime,
        address oracle,
        uint256 disputeWindow
    ) external onlyRole(OPERATOR_ROLE) whenNotPaused returns (uint256) {
        require(endTime > block.timestamp, "End time must be in future");
        require(oracle != address(0), "Invalid oracle address");

        uint256 marketId = ++marketCounter;
        
        markets[marketId] = Market({
            id: marketId,
            question: question,
            endTime: endTime,
            state: MarketState.OPEN,
            resolvedOutcome: Outcome.INVALID,
            oracle: oracle,
            disputeWindow: disputeWindow,
            disputeEndsAt: 0,
            createdAt: block.timestamp
        });

        emit MarketCreated(marketId, question, endTime, oracle, disputeWindow);
        
        return marketId;
    }

    /**
     * @notice Freeze market (stop trading)
     */
    function freezeMarket(uint256 marketId) external onlyRole(OPERATOR_ROLE) {
        Market storage market = markets[marketId];
        require(market.id != 0, "Market does not exist");
        require(market.state == MarketState.OPEN, "Market not open");

        market.state = MarketState.FROZEN;
        emit MarketStateChanged(marketId, MarketState.FROZEN);
    }

    /**
     * @notice Reopen frozen market
     */
    function reopenMarket(uint256 marketId) external onlyRole(OPERATOR_ROLE) {
        Market storage market = markets[marketId];
        require(market.id != 0, "Market does not exist");
        require(market.state == MarketState.FROZEN, "Market not frozen");
        require(block.timestamp < market.endTime, "Market ended");

        market.state = MarketState.OPEN;
        emit MarketStateChanged(marketId, MarketState.OPEN);
    }

    /**
     * @notice Resolve market (oracle only)
     */
    function resolveMarket(uint256 marketId, Outcome outcome) external {
        Market storage market = markets[marketId];
        require(market.id != 0, "Market does not exist");
        require(msg.sender == market.oracle || hasRole(ORACLE_ROLE, msg.sender), "Not authorized");
        require(market.state != MarketState.RESOLVED, "Already resolved");
        require(block.timestamp >= market.endTime, "Market not ended");
        require(outcome != Outcome.INVALID, "Must specify YES or NO");

        market.state = MarketState.RESOLVED;
        market.resolvedOutcome = outcome;
        
        if (market.disputeWindow > 0) {
            market.disputeEndsAt = block.timestamp + market.disputeWindow;
            emit DisputeStarted(marketId, market.disputeEndsAt);
        }

        emit MarketResolved(marketId, outcome);
        emit MarketStateChanged(marketId, MarketState.RESOLVED);
    }

    /**
     * @notice Change resolution during dispute window
     */
    function updateResolution(uint256 marketId, Outcome outcome) external onlyRole(OPERATOR_ROLE) {
        Market storage market = markets[marketId];
        require(market.id != 0, "Market does not exist");
        require(market.state == MarketState.RESOLVED, "Market not resolved");
        require(market.disputeEndsAt > 0, "No dispute window");
        require(block.timestamp <= market.disputeEndsAt, "Dispute window ended");
        require(outcome != Outcome.INVALID, "Must specify YES or NO");

        market.resolvedOutcome = outcome;
        emit MarketResolved(marketId, outcome);
    }

    /**
     * @notice Get market details
     */
    function getMarket(uint256 marketId) external view returns (Market memory) {
        require(markets[marketId].id != 0, "Market does not exist");
        return markets[marketId];
    }

    /**
     * @notice Check if market is open for trading
     */
    function isMarketOpen(uint256 marketId) external view returns (bool) {
        Market memory market = markets[marketId];
        return market.state == MarketState.OPEN && block.timestamp < market.endTime;
    }

    /**
     * @notice Check if market can be redeemed
     */
    function canRedeem(uint256 marketId) external view returns (bool) {
        Market memory market = markets[marketId];
        if (market.state != MarketState.RESOLVED) return false;
        if (market.disputeEndsAt > 0 && block.timestamp <= market.disputeEndsAt) return false;
        return true;
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
