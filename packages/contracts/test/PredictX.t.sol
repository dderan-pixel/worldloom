// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/Vault.sol";
import "../src/MarketManager.sol";
import "../src/OutcomeToken.sol";
import "../src/Settlement.sol";
import "../src/FeeCollector.sol";

contract MockERC20 is Test {
    string public name = "Mock USDC";
    string public symbol = "USDC";
    uint8 public decimals = 6;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract PredictXTest is Test {
    Vault public vault;
    MarketManager public marketManager;
    OutcomeToken public outcomeToken;
    Settlement public settlement;
    FeeCollector public feeCollector;
    MockERC20 public usdc;

    address public admin = address(1);
    address public user1 = address(2);
    address public user2 = address(3);
    address public oracle = address(4);

    function setUp() public {
        // Deploy contracts
        vm.startPrank(admin);
        
        vault = new Vault(admin);
        marketManager = new MarketManager(admin);
        outcomeToken = new OutcomeToken(admin);
        feeCollector = new FeeCollector(admin);
        settlement = new Settlement(
            admin,
            address(vault),
            address(outcomeToken),
            address(marketManager),
            address(feeCollector),
            100 // 1% fee
        );

        // Setup roles
        vault.grantRole(vault.SETTLEMENT_ROLE(), address(settlement));
        outcomeToken.grantRole(outcomeToken.MINTER_ROLE(), address(settlement));

        // Deploy mock USDC
        usdc = new MockERC20();
        vault.addAsset(address(usdc));
        vault.addAsset(address(0)); // ETH

        vm.stopPrank();

        // Fund users
        usdc.mint(user1, 10000e6);
        usdc.mint(user2, 10000e6);
        vm.deal(user1, 100 ether);
        vm.deal(user2, 100 ether);
    }

    function testDepositUSDC() public {
        vm.startPrank(user1);
        usdc.approve(address(vault), 1000e6);
        vault.deposit(address(usdc), 1000e6);
        vm.stopPrank();

        assertEq(vault.balances(user1, address(usdc)), 1000e6);
    }

    function testDepositETH() public {
        vm.prank(user1);
        vault.depositETH{value: 1 ether}();

        assertEq(vault.balances(user1, address(0)), 1 ether);
    }

    function testWithdraw() public {
        vm.startPrank(user1);
        usdc.approve(address(vault), 1000e6);
        vault.deposit(address(usdc), 1000e6);
        vault.withdraw(address(usdc), 500e6);
        vm.stopPrank();

        assertEq(vault.balances(user1, address(usdc)), 500e6);
        assertEq(usdc.balanceOf(user1), 9500e6);
    }

    function testCreateMarket() public {
        vm.prank(admin);
        uint256 marketId = marketManager.createMarket(
            "Will Bitcoin reach $100k by end of 2024?",
            block.timestamp + 365 days,
            oracle,
            7 days
        );

        assertEq(marketId, 1);
        MarketManager.Market memory market = marketManager.getMarket(marketId);
        assertEq(market.question, "Will Bitcoin reach $100k by end of 2024?");
        assertTrue(marketManager.isMarketOpen(marketId));
    }

    function testResolveMarket() public {
        // Create market
        vm.prank(admin);
        uint256 marketId = marketManager.createMarket(
            "Test market",
            block.timestamp + 1 days,
            oracle,
            1 days
        );

        // Fast forward past end time
        vm.warp(block.timestamp + 2 days);

        // Resolve market
        vm.prank(oracle);
        marketManager.resolveMarket(marketId, MarketManager.Outcome.YES);

        MarketManager.Market memory market = marketManager.getMarket(marketId);
        assertEq(uint(market.state), uint(MarketManager.MarketState.RESOLVED));
        assertEq(uint(market.resolvedOutcome), uint(MarketManager.Outcome.YES));
    }

    function testMintOutcomeTokens() public {
        vm.prank(admin);
        outcomeToken.mint(user1, 1, true, 100);

        assertEq(outcomeToken.getYesShares(user1, 1), 100);
    }

    function testSettleTrade() public {
        // Setup: Create market and deposit funds
        vm.prank(admin);
        uint256 marketId = marketManager.createMarket(
            "Test market",
            block.timestamp + 30 days,
            oracle,
            1 days
        );

        // Users deposit
        vm.startPrank(user1);
        usdc.approve(address(vault), 1000e6);
        vault.deposit(address(usdc), 1000e6);
        vm.stopPrank();

        vm.startPrank(user2);
        usdc.approve(address(vault), 1000e6);
        vault.deposit(address(usdc), 1000e6);
        vm.stopPrank();

        // Create trade
        Settlement.Trade[] memory trades = new Settlement.Trade[](1);
        trades[0] = Settlement.Trade({
            marketId: marketId,
            maker: user1,
            taker: user2,
            isBuyYes: true,
            price: 0.5e18, // 50 cents per share
            size: 100
        });

        // Settle
        vm.prank(admin);
        settlement.settleBatch(1, trades, address(usdc));

        // Check outcome tokens minted
        assertEq(outcomeToken.getYesShares(user2, marketId), 100);
    }
}
