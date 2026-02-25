from __future__ import annotations
import random
from collections import deque
from typing import Optional
import pygame
from main.room import Room, RoomType, Direction

"""
* Every dungeon has exactly one START room, one BOSS room, one MINI_GAME room,
  and a configurable number of NORMAL rooms.
* The BOSS room has exactly ONE door (entrance only).
* START and BOSS rooms are placed as far apart as possible on the grid.
* Only one room is ever active / displayed at a time.
* Rooms connect through doors which is loading zone triggered by player walking through.

To use:
    gen   = DungeonGenerator(seed=12345, num_normal_rooms=8)
    dungeon = gen.generate()            # returns a Dungeon instance

    # In game loop:
    dungeon.draw(screen, debug=False)
    dungeon.update(player)             
"""

#  Tunables                                                                    

GRID_COLS        = 8
GRID_ROWS        = 8
DEFAULT_NORMALS  = 8     # normal rooms in addition to start / boss / mini-game
MAX_GEN_ATTEMPTS = 200   # retry limit for generation



class Dungeon:
    """
    Holds all rooms and tracks which room the player is currently in.

    Parameters
    ----------
    rooms       : dict mapping room_id → Room
    start_id    : id of the starting room
    screen_size : (width, height) in pixels
    """

    def __init__(
        self,
        rooms:       dict[int, Room],
        start_id:    int,
        screen_size: tuple[int, int] = (960, 540),
    ) -> None:
        self.rooms        = rooms
        self.current_id   = start_id
        self.screen_w, self.screen_h = screen_size

    @property
    def current_room(self) -> Room:
        return self.rooms[self.current_id]
    
    # --- Update ---
    def update(self, player) -> bool:
        result = self.current_room.check_transition(player.rect)
        if result is None:
            return False

        direction, target_id = result
        self.current_id = target_id

        # Place the player just inside the door on the OTHER side
        # TODO maybe add a short timer so the player cant go back and forth so fast

        player.pos = self._entry_position(direction.opposite())
        player.rect.center = (round(player.pos.x), round(player.pos.y))
        return True

    def _entry_position(self, entry_dir: Direction) -> pygame.Vector2:
        cx  = self.screen_w  // 2
        cy  = self.screen_h  // 2
        pad = 80   # pixels from the wall edge

        return {
            Direction.NORTH: pygame.Vector2(cx, pad),
            Direction.SOUTH: pygame.Vector2(cx, self.screen_h - pad),
            Direction.WEST:  pygame.Vector2(pad, cy),
            Direction.EAST:  pygame.Vector2(self.screen_w - pad, cy),
        }[entry_dir]

    # --- Draw ---

    def draw(self, surface: pygame.Surface, debug: bool = False) -> None:
        self.current_room.draw(surface, debug=debug)


    def __repr__(self) -> str:
        lines = ["Dungeon:"]
        for room in self.rooms.values():
            lines.append(f"  {room}")
        return "\n".join(lines)



class DungeonGenerator:
    """
    Parameters
    ----------
    seed             : RNG seed (int or None for random)
    num_normal_rooms : how many NORMAL rooms to include (default 8)
    screen_size      : pixel dimensions of the screen / room
    grid_cols        : width of the logical grid
    grid_rows        : height of the logical grid
    """

    def __init__(
        self,
        seed:             Optional[int] = None,
        num_normal_rooms: int           = DEFAULT_NORMALS,
        screen_size:      tuple[int, int] = (960, 540),
        grid_cols:        int           = GRID_COLS,
        grid_rows:        int           = GRID_ROWS,
    ) -> None:
        self.seed             = seed if seed is not None else random.randrange(0, 2**32)
        self.rng              = random.Random(self.seed)
        self.num_normal_rooms = num_normal_rooms
        self.screen_size      = screen_size
        self.grid_cols        = grid_cols
        self.grid_rows        = grid_rows


    def generate(self) -> Dungeon:
       
        #Attempt to generate a valid dungeon up to MAX_GEN_ATTEMPTS times.
        #Raises RuntimeError if generation consistently fails.
        
        for attempt in range(MAX_GEN_ATTEMPTS):
            dungeon = self._try_generate()
            if dungeon is not None:
                return dungeon
        raise RuntimeError(
            f"DungeonGenerator failed after {MAX_GEN_ATTEMPTS} attempts "
            f"(seed={self.seed}, normals={self.num_normal_rooms}, "
            f"grid={self.grid_cols}x{self.grid_rows}). "
            "Try a larger grid or fewer rooms."
        )


    def _try_generate(self) -> Optional[Dungeon]:
        total_special  = 3   # START + BOSS + MINI_GAME
        total_rooms    = total_special + self.num_normal_rooms
        grid_capacity  = self.grid_cols * self.grid_rows

        if total_rooms > grid_capacity:
            raise ValueError(
                f"Too many rooms ({total_rooms}) for grid size "
                f"{self.grid_cols}x{self.grid_rows} (capacity {grid_capacity})."
            )

        
        # grow a random spanning tree of grid cells via random walk 
        
        occupied: dict[tuple[int, int], int] = {}   # grid_pos -> room_id
        adjacency: list[tuple[int, int]] = []        # (room_id_a, room_id_b)
        room_id_counter = 0

        # pick a random starting cell
        start_col = self.rng.randrange(self.grid_cols)
        start_row = self.rng.randrange(self.grid_rows)
        start_pos = (start_col, start_row)

        occupied[start_pos] = room_id_counter
        room_id_counter += 1

        frontier: list[tuple[int, int]] = [start_pos]

        while len(occupied) < total_rooms:
            if not frontier:
                return None    # retry

            cell = self.rng.choice(frontier)
            neighbors = self._empty_neighbors(cell, occupied)

            if not neighbors:
                frontier.remove(cell)
                continue

            new_cell = self.rng.choice(neighbors)
            adjacency.append((occupied[cell], room_id_counter))
            occupied[new_cell] = room_id_counter
            room_id_counter += 1
            frontier.append(new_cell)

        all_ids   = list(range(total_rooms))
        pos_by_id = {v: k for k, v in occupied.items()}

        #map used for adjacency of rooms
        neighbors_of: dict[int, list[int]] = {i: [] for i in all_ids}
        for a, b in adjacency:
            neighbors_of[a].append(b)
            neighbors_of[b].append(a)

        # Find the rooms that are farthest apart (BFS distance) for boss and spawn rooms
        farthest_pair = self._find_farthest_pair(neighbors_of, all_ids)
        if farthest_pair is None:
            return None

        start_candidate, boss_candidate = farthest_pair

        # Boss room must have degree of 1 so it only has one neighbor/one door  
        # If neither end of the farthest pair is a leaf, look for another leaf to be the boss room

        def is_leaf(rid: int) -> bool:
            return len(neighbors_of[rid]) == 1

        if is_leaf(boss_candidate):
            start_id = start_candidate
            boss_id  = boss_candidate
        elif is_leaf(start_candidate):
            start_id = boss_candidate
            boss_id  = start_candidate
        else:
            leaves = [rid for rid in all_ids if is_leaf(rid)]
            if not leaves:
                return None
            boss_id  = self.rng.choice(leaves)
            start_id = start_candidate

        # Mini-game room: not start, not boss, prefer a different leaf or
        # at least a room not adjacent to boss

        remaining = [rid for rid in all_ids if rid not in (start_id, boss_id)]
        mini_candidates = [
            rid for rid in remaining
            if boss_id not in neighbors_of[rid]
        ]
        if not mini_candidates:
            mini_candidates = remaining
        if not mini_candidates:
            return None
        mini_id = self.rng.choice(mini_candidates)

        # Assign room types
        type_map: dict[int, RoomType] = {}
        type_map[start_id] = RoomType.START
        type_map[boss_id]  = RoomType.BOSS
        type_map[mini_id]  = RoomType.MINI_GAME
        for rid in all_ids:
            if rid not in type_map:
                type_map[rid] = RoomType.NORMAL

        sw, sh = self.screen_size
        rooms: dict[int, Room] = {}
        for rid in all_ids:
            rooms[rid] = Room(
                room_id   = rid,
                room_type = type_map[rid],
                grid_pos  = pos_by_id[rid],
                screen_w  = sw,
                screen_h  = sh,
            )

        # Add doors for each adjacency edge
        for a, b in adjacency:
            dir_a_to_b = self._grid_direction(pos_by_id[a], pos_by_id[b])
            dir_b_to_a = dir_a_to_b.opposite()

            if dir_a_to_b is None or dir_b_to_a is None:
                continue  

            rooms[a].add_door(dir_a_to_b, b)
            rooms[b].add_door(dir_b_to_a, a)

        #  boss room can only ahve one door
        if len(rooms[boss_id].doors) != 1:
            return None

        return Dungeon(rooms=rooms, start_id=start_id, screen_size=self.screen_size)


    def _empty_neighbors(
        self,
        pos: tuple[int, int],
        occupied: dict[tuple[int, int], int],
    ) -> list[tuple[int, int]]:
        col, row = pos
        candidates = [
            (col,     row - 1),
            (col,     row + 1),
            (col - 1, row    ),
            (col + 1, row    ),
        ]
        return [
            c for c in candidates
            if 0 <= c[0] < self.grid_cols
            and 0 <= c[1] < self.grid_rows
            and c not in occupied
        ]

    @staticmethod
    def _grid_direction(
        src: tuple[int, int],
        dst: tuple[int, int],
    ) -> Optional[Direction]:
        dc = dst[0] - src[0]
        dr = dst[1] - src[1]
        if   (dc, dr) == ( 0, -1): return Direction.NORTH
        elif (dc, dr) == ( 0,  1): return Direction.SOUTH
        elif (dc, dr) == (-1,  0): return Direction.WEST
        elif (dc, dr) == ( 1,  0): return Direction.EAST
        return None


    @staticmethod
    def _bfs_distances(
        source: int,
        neighbors_of: dict[int, list[int]],
    ) -> dict[int, int]:
        dist   = {source: 0}
        queue  = deque([source])
        while queue:
            node = queue.popleft()
            for nb in neighbors_of[node]:
                if nb not in dist:
                    dist[nb] = dist[node] + 1
                    queue.append(nb)
        return dist

    def _find_farthest_pair(
        self,
        neighbors_of: dict[int, list[int]],
        all_ids:       list[int],
    ) -> Optional[tuple[int, int]]:
       
        #Use double-BFS to find the two rooms with maximum graph distance for spawn and boss room
        #Returns (start_candidate, boss_candidate).
        
        if not all_ids:
            return None

        # First BFS from an arbitrary node
        dist1 = self._bfs_distances(all_ids[0], neighbors_of)
        if len(dist1) != len(all_ids):
            return None    # graph not connected

        far1  = max(dist1, key=dist1.get)

        dist2 = self._bfs_distances(far1, neighbors_of)
        far2  = max(dist2, key=dist2.get)

        return far1, far2