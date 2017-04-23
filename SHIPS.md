What properties, abilities, and upgrades are available for ships?

# Ships

 * capacity - used for cargo, fuel, and passengers
 * electronics - used for all navigation, AI, radars, etc

Every upgrade costs some amount of capacity or electronics, or both.

Ships can upgrade and expand their capacity and electronics.

## Attributes of a ship
 
 * Capacity
  * base capacity
  * max capacity
  * current capacity
 * Electronics
  * base electronics
  * max electronics
  * current electronics
 * Cargo space
  * max
  * current
 * fuel
  * max
  * current
 * passenger space
  * max
  * current
  * grade 
 
## Upgrades

Current ship upgrades:

 - Expanded Cargo (ShipUpgrade::target == "cargo")
 - Expanded Range (ShipUpgrade::target == "range")

The factors that go into determining available upgrades and their cost and
impact:

 * *Upgrade Quality* - the quality of an upgrade effects two things; the size of the upgrade,
and the cost of the upgrade.
 * *Upgrade Size* - what additional size/change does this upgrade offer
 * *Base Cost* - what is the base cost for this upgrade?
 * *Rarity* - how often does this upgrade occur?
 
### Base Cost

*Expanded Cargo*:

 - +10 *size*, -10 *upgrade capacity*, ¥5,000 *base cost*
 - +25 *size*, -25 *upgrade capacity*, ¥12,000 *base cost*
 - +50 *size*, -50 *upgrade capacity*, ¥22,000 *base cost*
 - +100 *size*, -100 *upgrade capacity*, ¥40,000 *base cost*

### Rarity

Rarity is a factor up *upgrade quality*, and is expressed as a percentage
chance that the part of such quality is available at a shipyard.

 - Basic, 100% *availability*
 - Alpha, 75% *availability*
 - Beta, 50% *availability*
 - Delta, 10% *availability*
 - Omega, 3% *availability*
 - Ancient, 1% *availability*
 - Grorian, 0.1% *availability*

### Upgrade Quality

The general trend through the upgrades is that every step up the chain multiples
the effected size by an increment of 1, and the price by 10:

 - Basic, 1x *size*, 1x *base cost*
 - Alpha, 2x *size*, 10x *base cost*
 - Beta, 4x *size*, 100x *base cost*
 - Delta, 8x *size*, 1,000x *base cost*
 - Omega, 16x *size*, 10,000x *base cost*
 - Ancient, 64x *size*, 100,000x *base cost*
 - Grorian, 256x *size*, 1,000,000x *base cost*
 

### Expanded Cargo

Modify Ship::cargo_capacity up to Ship::cargo_capacity_max.

### Expanded Range

Modify Ship::max_range up to Ship::cargo_capacity_max.
 
 
 
 
Possible future upgrades:

Base ship upgrades

 * Extended capacity
 * Extended electronics

 * Engines (costs capacity and electronics)
 * passenger space
  * based on passenger grade
  * takes capacity
 * cargo space
 * specialized cargo space
  
## Ship model

ShipUpgrade:
  - target: what does this effect on the ship
  - size: how much does if effect the ship
  - ship: which ship does it effect
  - cost: how much does this upgrade cost?
  - name: what is this upgrade called?
  - quality: what is the quality of this upgrade (see upgrade_quality.json)
  - space: how much upgrade space does this consume?

Ship
  - cargo_capacity
  - upgrade_capacity: how much of the ships upgrade capacity has been used?
  - upgrade_capacity_max: what is the total upgrade capacity of this ship?

# Shipyards

Ship yards have bare ships and available upgrades.

