// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract WildBitcoinToken is ERC20 {
    uint256 public constant MAX_SUPPLY = 21000000 * 10**18; // 21 million tokens
    uint256 public constant HALVING_INTERVAL = 210000; // Approximately 4 years (210,000 blocks)
    // After 21,000 mints for any new mint it is required to hold at least 1 token
    // this is intended as a way to make it harder for validators to do front running
    uint256 public constant RESTRICTION_MINT_THRESHOLD = 21000;
    uint256 public constant MINT_INTERVAL = 10 minutes;
    
    uint256 public lastMintTime;
    uint256 public currentReward = 50 * 10**18; // Initial reward: 50 tokens
    uint256 public halvingCount = 0;
    uint256 public totalMints = 0;
    
    event Mint(address indexed minter, uint256 amount, uint256 totalMinted);
    event Halving(uint256 newReward, uint256 halvingCount);

    constructor() ERC20("Wild BTC", "WildBTC") {
        lastMintTime = block.timestamp;
    }

    function mint() external {
        require(totalSupply() < MAX_SUPPLY, "Max supply reached");
        require(block.timestamp >= lastMintTime + MINT_INTERVAL, "Not enough time passed");

        // Check minting restrictions
        if (totalMints >= RESTRICTION_MINT_THRESHOLD) {
            require(balanceOf(msg.sender) >= 1 * 10**18, "Must hold at least 1 token to mint");
        }
        if (halvingCount > 0) {
            require(balanceOf(msg.sender) >= halvingCount * 2 * 10**18, "Must hold tokens equal to twice the halving count");
        }
        
        // Update last mint time
        lastMintTime = block.timestamp;
        totalMints++;
        
        // Check for halving event (every 210,000 mints, every ~4 years)
        if (totalMints % HALVING_INTERVAL == 0) {
            currentReward = currentReward / 2;
            halvingCount++;
            emit Halving(currentReward, halvingCount);
        }

        // This is intended to make it possible to reach the max 21 million supply after ~45 halving events, that means ~180 years
        // and this check will pass only after 21 halving events, that means ~90 years
        if (halvingCount > 21) {
            currentReward = 21_000_000_000_000;
        }
        
        // Adjust reward if it would exceed max supply
        uint256 actualReward = currentReward;
        if (totalSupply() + actualReward > MAX_SUPPLY) {
            actualReward = MAX_SUPPLY - totalSupply();
        }
        
        _mint(msg.sender, actualReward);
        emit Mint(msg.sender, actualReward, totalSupply());
    }

    function timeUntilNextMint() external view returns (uint256) {
        if (totalSupply() >= MAX_SUPPLY) {
            return type(uint256).max; // Indicates that minting is finished forever
        }
    
        uint256 nextMintTime = lastMintTime + MINT_INTERVAL;
    
        if (block.timestamp >= nextMintTime) {
            return 0; // Mint is available now
        } else {
            return nextMintTime - block.timestamp;
        }
    }
}
