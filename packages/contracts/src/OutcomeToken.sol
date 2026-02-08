// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title OutcomeToken
 * @notice ERC1155 tokens representing YES/NO outcome shares
 * @dev Token IDs: marketId * 2 = YES, marketId * 2 + 1 = NO
 */
contract OutcomeToken is ERC1155, AccessControl, Pausable {
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    string public name = "PredictX Outcome Tokens";
    string public symbol = "PXOT";

    // marketId => total YES shares minted
    mapping(uint256 => uint256) public totalYesShares;
    // marketId => total NO shares minted
    mapping(uint256 => uint256) public totalNoShares;

    event OutcomeMinted(address indexed user, uint256 indexed marketId, bool isYes, uint256 amount);
    event OutcomeBurned(address indexed user, uint256 indexed marketId, bool isYes, uint256 amount);

    constructor(address admin) ERC1155("") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
    }

    /**
     * @notice Get token ID for market outcome
     * @param marketId Market identifier
     * @param isYes true for YES token, false for NO token
     */
    function getTokenId(uint256 marketId, bool isYes) public pure returns (uint256) {
        return marketId * 2 + (isYes ? 0 : 1);
    }

    /**
     * @notice Mint outcome tokens (Settlement contract only)
     */
    function mint(
        address to,
        uint256 marketId,
        bool isYes,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(amount > 0, "Amount must be > 0");
        
        uint256 tokenId = getTokenId(marketId, isYes);
        _mint(to, tokenId, amount, "");

        if (isYes) {
            totalYesShares[marketId] += amount;
        } else {
            totalNoShares[marketId] += amount;
        }

        emit OutcomeMinted(to, marketId, isYes, amount);
    }

    /**
     * @notice Burn outcome tokens (Settlement contract only)
     */
    function burn(
        address from,
        uint256 marketId,
        bool isYes,
        uint256 amount
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(amount > 0, "Amount must be > 0");
        
        uint256 tokenId = getTokenId(marketId, isYes);
        _burn(from, tokenId, amount);

        if (isYes) {
            totalYesShares[marketId] -= amount;
        } else {
            totalNoShares[marketId] -= amount;
        }

        emit OutcomeBurned(from, marketId, isYes, amount);
    }

    /**
     * @notice Batch mint outcome tokens
     */
    function mintBatch(
        address to,
        uint256[] calldata marketIds,
        bool[] calldata isYes,
        uint256[] calldata amounts
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(marketIds.length == isYes.length && isYes.length == amounts.length, "Array length mismatch");
        
        uint256[] memory tokenIds = new uint256[](marketIds.length);
        
        for (uint256 i = 0; i < marketIds.length; i++) {
            require(amounts[i] > 0, "Amount must be > 0");
            tokenIds[i] = getTokenId(marketIds[i], isYes[i]);
            
            if (isYes[i]) {
                totalYesShares[marketIds[i]] += amounts[i];
            } else {
                totalNoShares[marketIds[i]] += amounts[i];
            }
            
            emit OutcomeMinted(to, marketIds[i], isYes[i], amounts[i]);
        }
        
        _mintBatch(to, tokenIds, amounts, "");
    }

    /**
     * @notice Get user's YES shares for a market
     */
    function getYesShares(address user, uint256 marketId) external view returns (uint256) {
        return balanceOf(user, getTokenId(marketId, true));
    }

    /**
     * @notice Get user's NO shares for a market
     */
    function getNoShares(address user, uint256 marketId) external view returns (uint256) {
        return balanceOf(user, getTokenId(marketId, false));
    }

    /**
     * @notice Update URI
     */
    function setURI(string memory newuri) external onlyRole(OPERATOR_ROLE) {
        _setURI(newuri);
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

    /**
     * @notice Required override for AccessControl
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    /**
     * @notice Override to add pause check
     */
    function _beforeTokenTransfer(
        address operator,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) internal override whenNotPaused {
        super._beforeTokenTransfer(operator, from, to, ids, amounts, data);
    }
}
