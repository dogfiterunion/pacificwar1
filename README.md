# pacificwar1
🌊 Pacific War 1: Tactical Command
Pacific War 1 is a terminal-based, turn-of-the-century naval warfare simulator. Command a fleet of five distinct ship classes through an island-strewn archipelago, utilizing radar ghosts, torpedo spreads, and specialized abilities to outmaneuver the enemy under varying weather conditions. Use a python running software to run the game. An example on Browser is online-python.com

🕹️ How to Play
1. The Fleet
You command a task force of 5 ships, each with unique roles:

[C] Carrier: Long-range recon and high HP.

[B] Battleship: The heavy hitter with massive range and hull points.

[R] Cruiser: A versatile mid-range ship with balanced speed.

[D] Destroyer: High-speed scout and sonar specialist.

[S] Submarine: Stealthy attacker capable of launching devastating torpedoes.

2. Tactical Movement
Unlike basic sims, speed is class-dependent:

Destroyers: 3 moves per turn.

Cruisers: 2 moves per turn.

Others: 1 move per turn.

Note: Moving into an Island [#] is prohibited. Movement resets your repair cycle.

3. Combat & Ballistics
Firing a salvo [F] consumes 1 Ammo. Accuracy is calculated based on distance:

P(hit)=1− 
Max Range
Distance
​
 
Citadel Hit (10%): Deals 4x damage.

Magazine Explosion (5%): Instantly sinks the vessel.

Suppression: Taking >30 damage in one hit "Suppresses" your crew, reducing your range by 25% for one turn.

4. Specialized Abilities [A]
Air Recon (Carrier): Reveals a 5×5 area anywhere on the map.

Sonar Ping (Destroyer): Detects all ships within a 10-tile radius, ignoring most weather penalties.

Torpedo Launch (Submarine): Fires a projectile that travels 1 tile per turn. It deals massive damage if it intersects an enemy ship.

5. Damage Control [R]
If a ship remains stationary (doesn't move) for several turns, it unlocks Repair:

Tier 1: Available after 3 stationary turns.

Tier 2/3: Available every 2 stationary turns thereafter.

Limit: You can only field-repair up to 75% of your max HP.

📡 The Radar System
Information is your greatest weapon. The map displays different "blips" based on how recently an enemy was seen:

[X]: Current active contact.

[x]: Last known position (1 Turn ago).

[+]: Old position (2 Turns ago).

[?]: Ghost contact (3 Turns ago).

🛠️ Technical Logic
Line of Sight: Projectiles and sensors cannot penetrate Islands [#].

Weather Engine: CLEAR, OVERCAST, FOG, and TYPHOON dynamically affect your spotting and identification ranges.

Delayed Gratification: Torpedoes are not instant; they require you to predict where the enemy will be in 1–3 turns.
