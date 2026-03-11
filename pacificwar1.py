import random
import math

# --- HISTORICAL REGISTRY & LOGISTICS ---
NAMES_USA = {
    "Carrier": ["USS Enterprise", "USS Yorktown", "USS Hornet"],
    "Battleship": ["USS Iowa", "USS Missouri", "USS Arizona"],
    "Cruiser": ["USS Indianapolis", "USS San Francisco", "USS New Orleans"],
    "Destroyer": ["USS Fletcher", "USS Laffey", "USS Johnston"],
    "Submarine": ["USS Gato", "USS Tang", "USS Wahoo"]
}

NAMES_IJN = {
    "Carrier": ["IJN Akagi", "IJN Kaga", "IJN Shokaku"],
    "Battleship": ["IJN Yamato", "IJN Musashi", "IJN Nagato"],
    "Cruiser": ["IJN Mogami", "IJN Takao", "IJN Myoko"],
    "Destroyer": ["IJN Yukikaze", "IJN Shimakaze", "IJN Fubuki"],
    "Submarine": ["IJN I-19", "IJN I-400", "IJN I-58"]
}

SHIP_STATS = {
    "Carrier": {"hp": 100, "range": 15, "ammo": 20, "symbol": "C", "ability": "Air Recon", "move_speed": 1},
    "Battleship": {"hp": 150, "range": 10, "ammo": 40, "symbol": "B", "ability": "Heavy Salvo", "move_speed": 1},
    "Cruiser": {"hp": 80, "range": 8, "ammo": 50, "symbol": "R", "ability": "None", "move_speed": 2},
    "Destroyer": {"hp": 50, "range": 6, "ammo": 60, "symbol": "D", "ability": "Sonar Ping", "move_speed": 3},
    "Submarine": {"hp": 40, "range": 5, "ammo": 12, "symbol": "S", "ability": "Torpedo Launch", "move_speed": 1} # Submarine ability changed to Torpedo
}

WEATHER_CONDITIONS = {
    "CLEAR": {"penalty": 0, "desc": "Optimal visibility."},
    "OVERCAST": {"penalty": 1, "desc": "Slight radar degradation."},
    "FOG": {"penalty": 2, "desc": "Visual ID limited."},
    "TYPHOON": {"penalty": 4, "desc": "Instruments blind."}
}

class Ship:
    def __init__(self, faction, ship_type, x, y):
        self.name = random.choice(NAMES_USA[ship_type] if faction == "USA" else NAMES_IJN[ship_type])
        self.type = ship_type
        self.max_hp = SHIP_STATS[ship_type]["hp"]
        self.hp = self.max_hp
        self.max_range = SHIP_STATS[ship_type]["range"]
        self.ammo = SHIP_STATS[ship_type]["ammo"]
        self.symbol = SHIP_STATS[ship_type]["symbol"]
        self.ability_name = SHIP_STATS[ship_type]["ability"]
        self.move_speed = SHIP_STATS[ship_type]["move_speed"]
        self.x, self.y = x, y
        self.alive = True
        self.spotted = False 
        self.identified = False 
        self.ability_cooldown = 0
        self.stationary_turns = 0
        self.repair_stage = 0
        self.can_repair = False
        self.suppressed = 0 # Turns suppressed

    def check_repair_status(self):
        req = [3, 2, 2]
        if self.repair_stage < len(req) and self.stationary_turns >= req[self.repair_stage]:
            self.can_repair = True
        else:
            self.can_repair = False

class NavalWarfare:
    def __init__(self):
        self.grid_size = 20
        self.islands = self._generate_islands()
        self.player_fleet = self._build_fleet("USA", 0)
        self.ai_fleet = self._build_fleet("IJN", 19)
        self.turn = 1
        self.weather = "CLEAR"
        self.radar_history = []
        self.recon_pings = []
        self.torpedo_tracks = [] # list of {'x': int, 'y': int, 'dx': int, 'dy': int, 'age': int, 'origin_faction': str}

    def _generate_islands(self):
        islands = set()
        num_islands = random.randint(3, 7)
        for _ in range(num_islands):
            # Ensure islands are not near starting zones (rows 0, 1, 18, 19)
            ix = random.randint(2, self.grid_size - 3) 
            iy = random.randint(0, self.grid_size - 1)
            islands.add((ix, iy))
            # Make some islands 2x2 or 1x2 for variety
            if random.random() < 0.5: 
                if ix + 1 < self.grid_size - 2: islands.add((ix + 1, iy))
            if random.random() < 0.5: 
                if iy + 1 < self.grid_size: islands.add((ix, iy + 1))
        return islands

    def _build_fleet(self, faction, row):
        fleet = []
        # Ensure ships don't start on islands
        occupied_coords = set()
        for i, t in enumerate(SHIP_STATS.keys()):
            y_offset = i * (self.grid_size // len(SHIP_STATS))
            
            # Find a non-island spot
            while (row, y_offset) in self.islands or (row, y_offset) in occupied_coords:
                y_offset = (y_offset + 1) % self.grid_size
            
            fleet.append(Ship(faction, t, row, y_offset))
            occupied_coords.add((row, y_offset))
        return fleet

    def get_dist(self, s1, s2):
        return math.sqrt((s1.x - s2.x)**2 + (s1.y - s2.y)**2)

    def is_line_of_sight_clear(self, x1, y1, x2, y2):
        # Basic Bresenham's line algorithm to check for islands in between
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while x != x2 or y != y2:
            if (x, y) in self.islands and (x, y) != (x1,y1) and (x,y) != (x2,y2): # Ignore start/end points
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        return True

    def update_intel(self):
        # Update radar history
        for contact in self.radar_history: contact['age'] += 1
        self.radar_history = [c for c in self.radar_history if c['age'] <= 3]
        
        penalty = WEATHER_CONDITIONS[self.weather]["penalty"]
        
        for enemy in self.ai_fleet:
            if not enemy.alive: continue
            
            min_dist = 99
            for p in self.player_fleet:
                if p.alive and self.is_line_of_sight_clear(enemy.x, enemy.y, p.x, p.y):
                    min_dist = min(min_dist, self.get_dist(enemy, p))
            
            sonar = any([p.ability_name == "Sonar Ping" and p.ability_cooldown > 0 and 
                         self.get_dist(enemy, p) <= 10 and self.is_line_of_sight_clear(enemy.x, enemy.y, p.x, p.y) 
                         for p in self.player_fleet if p.alive])
            recon = any([abs(enemy.x - rx) <= 2 and abs(enemy.y - ry) <= 2 for rx, ry in self.recon_pings])

            spot_range, id_range = max(1, 5 - penalty), max(1, 2 - penalty)
            enemy.spotted = (min_dist <= spot_range) or sonar or recon
            enemy.identified = (min_dist <= id_range) or recon

            if enemy.spotted:
                self.radar_history = [c for c in self.radar_history if c['ship'] != enemy]
                self.radar_history.append({'ship': enemy, 'x': enemy.x, 'y': enemy.y, 'age': 0})

    def display_status(self):
        print("\n" + "="*70)
        print(f" PACIFIC WAR 1 - TURN {self.turn} | WEATHER: {self.weather} ".center(70, "="))
        print("="*70)
        print("\n[ FRIENDLY FORCES ]")
        for i, s in enumerate(self.player_fleet):
            if s.alive:
                rep_str = "READY" if s.can_repair else f"{s.stationary_turns}nd Wait"
                sup_str = f" SUPPRESSED ({s.suppressed}T)" if s.suppressed > 0 else ""
                print(f"[{i}] {s.name:<18} | Pos:({s.x:02},{s.y:02}) | HP:{s.hp:3}/{s.max_hp} | Ammo:{s.ammo:2} | Repair: {rep_str}{sup_str}")
            else:
                print(f"[{i}] {s.name:<18} | ** SUNK **")

    def display_radar(self):
        grid = [["." for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Draw islands
        for ix, iy in self.islands:
            grid[ix][iy] = "#"

        # Draw torpedo tracks
        for t in self.torpedo_tracks:
            if 0 <= t['x'] < self.grid_size and 0 <= t['y'] < self.grid_size and grid[t['x']][t['y']] == ".":
                grid[t['x']][t['y']] = "T" # Torpedo icon

        # Draw radar history
        for c in sorted(self.radar_history, key=lambda x: x['age'], reverse=True):
            if grid[c['x']][c['y']] == ".": # Only draw if not island or torpedo
                grid[c['x']][c['y']] = {0: "X", 1: "x", 2: "+", 3: "?"}[c['age']]
        
        # Draw allied ships (always on top)
        for s in self.player_fleet:
            if s.alive: grid[s.x][s.y] = s.symbol

        print("\nTACTICAL RADAR GRID")
        header = "   " + "".join([f"{i:02} " for i in range(self.grid_size)])
        print(header)
        for x in range(self.grid_size):
            print(f"{x:02}  " + "  ".join(grid[x]))

    def resolve_shot(self, attacker, tx, ty, silent=False):
        if attacker.ammo <= 0:
            if not silent: print(f">> {attacker.name}: MAGAZINES DEPLETED.")
            return False
        
        if not self.is_line_of_sight_clear(attacker.x, attacker.y, tx, ty):
            if not silent: print(f">> {attacker.name}: LINE OF SIGHT BLOCKED BY TERRAIN.")
            return False

        attacker.ammo -= 1
        dist = math.sqrt((attacker.x - tx)**2 + (attacker.y - ty)**2)
        
        effective_range = attacker.max_range
        if attacker.suppressed > 0:
            effective_range *= 0.75 # 25% range reduction
            if not silent: print(f">> {attacker.name} is SUPPRESSED. Effective Range: {effective_range:.1f}")

        if dist > effective_range:
            if not silent: print(f">> {attacker.name}: TARGET BEYOND EFFECTIVE RANGE. SHOT WASTED.")
            return False

        if random.random() < (1 - (dist / effective_range)): # Hit probability
            for s in self.player_fleet + self.ai_fleet:
                if s.x == tx and s.y == ty and s.alive:
                    roll = random.random()
                    base_dmg = random.randint(20, 45)
                    
                    if roll < 0.05: # Ammo Detonation
                        s.hp = 0
                        if not silent: print(f">> !!! DETONATION !!! {s.name} AMMO STORAGE HIT.")
                    elif roll < 0.15: # Citadel Hit
                        dmg = base_dmg * 4
                        s.hp = max(0, s.hp - dmg)
                        if not silent: print(f">> !! CITADEL HIT !! {s.name} took {dmg} damage.")
                    else: # Standard Hit
                        dmg = base_dmg
                        s.hp = max(0, s.hp - dmg)
                        if not silent: print(f">> IMPACT: {s.name} damaged for {dmg}.")
                    
                    if dmg > 30 and s.alive: # Apply suppression
                        s.suppressed = 1
                        if not silent: print(f">> {s.name} is now SUPPRESSED!")

                    if s.hp <= 0: s.alive = False
                    return True
        if not silent: print(">> SHOT MISSED.")
        return False
    
    def handle_torpedo_launch(self, ship):
        if ship.ammo <= 0:
            print(">> NO TORPEDOES LEFT.")
            return

        direction_input = input("Launch direction (N/S/E/W): ").upper()
        dx, dy = 0, 0
        if direction_input == 'N': dx = -1
        elif direction_input == 'S': dx = 1
        elif direction_input == 'E': dy = 1
        elif direction_input == 'W': dy = -1
        else: print(">> INVALID DIRECTION."); return

        ship.ammo -= 1
        self.torpedo_tracks.append({
            'x': ship.x + dx, 'y': ship.y + dy, 'dx': dx, 'dy': dy, 'age': 0, 
            'origin_faction': ship.faction
        })
        print(f">> {ship.name} launched torpedo. ({ship.ammo} left)")

    def update_torpedo_tracks(self):
        new_torpedo_tracks = []
        for t in self.torpedo_tracks:
            target_ships = []
            if t['origin_faction'] == "USA":
                target_ships = [s for s in self.ai_fleet if s.alive and s.x == t['x'] and s.y == t['y']]
            else: # AI torpedoes target player ships
                target_ships = [s for s in self.player_fleet if s.alive and s.x == t['x'] and s.y == t['y']]

            if target_ships: # Torpedo hit
                target = target_ships[0]
                roll = random.random()
                base_dmg = random.randint(40, 80) # Torpedoes hit harder
                
                if roll < 0.10: # Higher chance for critical with torpedoes
                    target.hp = 0
                    if t['origin_faction'] == "USA":
                        print(f">> !!! TORPEDO DETONATION !!! {target.name} AMMO STORAGE HIT.")
                elif roll < 0.30:
                    dmg = base_dmg * 2 # Torpedo citadels
                    target.hp = max(0, target.hp - dmg)
                    if t['origin_faction'] == "USA":
                        print(f">> !! TORPEDO HIT !! {target.name} took {dmg} critical damage.")
                else:
                    dmg = base_dmg
                    target.hp = max(0, target.hp - dmg)
                    if t['origin_faction'] == "USA":
                        print(f">> TORPEDO IMPACT: {target.name} damaged for {dmg}.")
                
                if target.hp <= 0: target.alive = False
                continue # Torpedo detonated

            # Move torpedo
            t['x'] += t['dx'] * 1 # Torpedo travels 1 tile per age increment, not 4
            t['y'] += t['dy'] * 1
            t['age'] += 1
            
            # Check for range and collision with islands
            if t['age'] <= 3 and 0 <= t['x'] < self.grid_size and 0 <= t['y'] < self.grid_size and (t['x'], t['y']) not in self.islands:
                new_torpedo_tracks.append(t)
            else:
                if t['origin_faction'] == "USA": # Only report for player's torpedoes
                    print(f">> TORPEDO FAILED (Age: {t['age']}) or hit land.")
        self.torpedo_tracks = new_torpedo_tracks

    def play(self):
        while any(s.alive for s in self.player_fleet) and any(s.alive for s in self.ai_fleet):
            # Environment and Intel Update
            if random.random() < 0.2: self.weather = random.choice(list(WEATHER_CONDITIONS.keys()))
            self.recon_pings = []
            self.update_torpedo_tracks() # Update torpedo positions before intel and actions
            self.update_intel()
            for s in self.player_fleet: s.check_repair_status()
            
            # Display
            self.display_status()
            self.display_radar()
            
            # Player Action Phase
            for idx, ship in enumerate(self.player_fleet):
                if not ship.alive: continue
                
                print(f"\n--- {ship.name} ACTIONS ---")
                current_x, current_y = ship.x, ship.y
                try:
                    cmd = input(f"ACTION for {ship.name} (M:{ship.move_speed} moves, F:Fire, A:Ability, R:Repair, S:Skip): ").upper()
                    
                    if cmd == "M":
                        moves_left = ship.move_speed
                        while moves_left > 0:
                            print(f"  {moves_left} moves remaining for {ship.name}")
                            dx = int(input("  dX (-1 to 1): "))
                            dy = int(input("  dY (-1 to 1): "))
                            new_x, new_y = ship.x + dx, ship.y + dy
                            
                            if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size and (new_x, new_y) not in self.islands:
                                ship.x, ship.y = new_x, new_y
                                moves_left -= 1
                            else:
                                print("  >> INVALID MOVE: Grid boundary or island.")
                                break # End movement for this ship if invalid move
                        
                        if (current_x, current_y) != (ship.x, ship.y): # If moved at all
                            ship.stationary_turns = 0
                            ship.repair_stage = 0
                        else: # Didn't move or only invalid moves
                            ship.stationary_turns += 1

                    elif cmd == "F":
                        self.resolve_shot(ship, int(input("  TX: ")), int(input("  TY: ")))
                        ship.stationary_turns += 1
                    elif cmd == "A":
                        if ship.ability_name == "Air Recon" and ship.type == "Carrier":
                            if ship.ability_cooldown == 0:
                                self.recon_pings.append((int(input("  RX: ")), int(input("  RY: "))))
                                ship.ability_cooldown = 3
                                print(f">> {ship.name} launched recon. Cooldown: {ship.ability_cooldown}")
                            else: print(f">> ABILITY ON COOLDOWN. {ship.ability_cooldown} turns left.")
                        elif ship.ability_name == "Sonar Ping" and ship.type == "Destroyer":
                            if ship.ability_cooldown == 0:
                                ship.ability_cooldown = 4 # Becomes active for 1 turn (current) then 3 turns cooldown
                                print(f">> {ship.name} activated SONAR. Cooldown: {ship.ability_cooldown}")
                            else: print(f">> ABILITY ON COOLDOWN. {ship.ability_cooldown} turns left.")
                        elif ship.ability_name == "Torpedo Launch" and ship.type == "Submarine":
                             self.handle_torpedo_launch(ship)
                        else:
                            print(">> NO ACTIVE ABILITY FOR THIS CLASS.")
                        ship.stationary_turns += 1
                    elif cmd == "R" and ship.can_repair:
                        heal_cap = int(ship.max_hp * 0.75)
                        if ship.hp < heal_cap:
                            ship.hp = min(heal_cap, ship.hp + 20)
                            print(f">> DAMAGE CONTROL SUCCESSFUL. {ship.name} HP: {ship.hp}")
                        else:
                            print(">> REPAIR LIMIT REACHED (75% MAX).")
                        
                        ship.repair_stage = (ship.repair_stage + 1) % 3 # Cycle through 0,1,2
                        ship.stationary_turns = 0 # Reset for next tier
                    elif cmd == "S":
                        ship.stationary_turns += 1 # Still contributes to stationary count
                    else:
                        print(">> ACTION NOT POSSIBLE OR INVALID.")
                        ship.stationary_turns += 1

                except ValueError: print(">> INVALID INPUT.")
                except IndexError: print(">> UNIT INDEX OUT OF BOUNDS.")

            # AI Logic Phase
            for s in [ship for ship in self.ai_fleet if ship.alive]:
                # AI Torpedo Launch logic (Submarines/Destroyers)
                if s.type in ["Submarine", "Destroyer"] and s.ammo > 0 and s.ability_cooldown == 0:
                    targets = [p for p in self.player_fleet if p.alive and self.get_dist(s, p) <= 5 and self.is_line_of_sight_clear(s.x, s.y, p.x, p.y)]
                    if targets:
                        target = random.choice(targets)
                        # Aim in direction of target
                        dx = 0
                        if target.x < s.x: dx = -1
                        elif target.x > s.x: dx = 1
                        dy = 0
                        if target.y < s.y: dy = -1
                        elif target.y > s.y: dy = 1
                        
                        if dx != 0 or dy != 0: # Only launch if clear direction
                            s.ammo -= 1
                            self.torpedo_tracks.append({
                                'x': s.x + dx, 'y': s.y + dy, 'dx': dx, 'dy': dy, 'age': 0, 
                                'origin_faction': s.faction
                            })
                            s.ability_cooldown = 3 # Cooldown for torpedo ability

                # AI Movement & Firing Logic
                targets = [p for p in self.player_fleet if p.alive]
                if targets:
                    target = min(targets, key=lambda p: self.get_dist(s, p))
                    
                    if self.get_dist(s, target) <= s.max_range and self.is_line_of_sight_clear(s.x, s.y, target.x, target.y):
                        self.resolve_shot(s, target.x, target.y, silent=True)
                    else:
                        # Move towards target, respecting islands and move speed
                        moves_made = 0
                        while moves_made < s.move_speed:
                            prev_x, prev_y = s.x, s.y
                            
                            next_x, next_y = s.x, s.y
                            if target.x < s.x: next_x -= 1
                            elif target.x > s.x: next_x += 1
                            
                            if target.y < s.y: next_y -= 1
                            elif target.y > s.y: next_y += 1

                            if (next_x, next_y) not in self.islands and 0 <= next_x < self.grid_size and 0 <= next_y < self.grid_size:
                                s.x, s.y = next_x, next_y
                                moves_made += 1
                            elif (s.x, s.y) == (next_x, next_y): # Stuck, cant move towards target.
                                break 
                            else: # Attempt to move around island by changing one axis
                                if random.random() < 0.5: # Try X axis first
                                    if target.x < s.x and (s.x - 1, s.y) not in self.islands: s.x -= 1
                                    elif target.x > s.x and (s.x + 1, s.y) not in self.islands: s.x += 1
                                else: # Else try Y axis
                                    if target.y < s.y and (s.x, s.y - 1) not in self.islands: s.y -= 1
                                    elif target.y > s.y and (s.x, s.y + 1) not in self.islands: s.y += 1
                                
                                if (s.x, s.y) != (prev_x, prev_y): # If moved, even if sidestepping
                                    moves_made += 1
                                else:
                                    break # Stuck

            self.turn += 1
            for s in self.player_fleet: 
                if s.ability_cooldown > 0: s.ability_cooldown -= 1
            for s in self.ai_fleet:
                if s.ability_cooldown > 0: s.ability_cooldown -= 1
                if s.suppressed > 0: s.suppressed -= 1

        print("\n" + "="*70)
        if any(s.alive for s in self.player_fleet):
            print(">> ALLIED VICTORY! ENEMY FLEET DESTROYED.")
        else:
            print(">> DEFEAT! ALLIED FLEET SUNK.")
        print("="*70)

if __name__ == "__main__":
    game = NavalWarfare()
    game.play()