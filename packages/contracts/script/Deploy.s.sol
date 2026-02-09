// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/Vault.sol";
import "../src/MarketManager.sol";
import "../src/OutcomeToken.sol";
import "../src/Settlement.sol";
import "../src/FeeCollector.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        console.log("Deploying contracts with deployer:", deployer);

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Vault
        Vault vault = new Vault(deployer);
        console.log("Vault deployed at:", address(vault));

        // 2. Deploy MarketManager
        MarketManager marketManager = new MarketManager(deployer);
        console.log("MarketManager deployed at:", address(marketManager));

        // 3. Deploy OutcomeToken
        OutcomeToken outcomeToken = new OutcomeToken(deployer);
        console.log("OutcomeToken deployed at:", address(outcomeToken));

        // 4. Deploy FeeCollector
        FeeCollector feeCollector = new FeeCollector(deployer);
        console.log("FeeCollector deployed at:", address(feeCollector));

        // 5. Deploy Settlement with 1% fee (100 basis points)
        Settlement settlement = new Settlement(
            deployer,
            address(vault),
            address(outcomeToken),
            address(marketManager),
            address(feeCollector),
            100 // 1% fee
        );
        console.log("Settlement deployed at:", address(settlement));

        // 6. Grant roles
        vault.grantRole(vault.SETTLEMENT_ROLE(), address(settlement));
        console.log("Granted SETTLEMENT_ROLE to Settlement in Vault");

        outcomeToken.grantRole(outcomeToken.MINTER_ROLE(), address(settlement));
        console.log("Granted MINTER_ROLE to Settlement in OutcomeToken");

        // 7. Add supported assets (configure via env or add your test USDC here)
        // Example: vault.addAsset(0x... your USDC address);
        // For ETH support:
        vault.addAsset(address(0));
        console.log("Added ETH as supported asset");

        vm.stopBroadcast();

        console.log("\n=== Deployment Summary ===");
        console.log("Vault:", address(vault));
        console.log("MarketManager:", address(marketManager));
        console.log("OutcomeToken:", address(outcomeToken));
        console.log("Settlement:", address(settlement));
        console.log("FeeCollector:", address(feeCollector));
        console.log("=========================\n");
    }
}
