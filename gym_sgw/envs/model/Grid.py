import random
import json
import xlrd
from typing import List
import numpy as np
import pygame as pg
from gym_sgw.envs.model.Cell import Cell
from gym_sgw.envs.enums.Enums import MapObjects, Terrains, Actions, Orientations, MapProfiles, MapColors
import copy



class Grid:

    def __init__(self, map_file: str = None, rows=10, cols=10, random_profile: MapProfiles = MapProfiles.uniform):
        self.map_file = map_file
        self.rows = rows
        self.cols = cols
        self.random_profile = random_profile
        self.player_orientation = None
        self.player_location = None
        self.grid = self.random_grid()
        self.map_max_energy = None
        self.turns = 0
        self.zombies_squished = 0
        self.zombie_count = 0
        self.pedestrians_squished = 0
        self.pedestrian_count = 0
        self.pedestrian_count = 0
        self.victims_squished = 0
        self.victim_count = 0

        # Shown squares
        self.visible_range = []

        # Setup of last_seen
        self.last_seen = []
        for a in self.grid:
            self.last_seen.append([])
            for cell in a:
                self.last_seen[-1].append(Cell(cell.terrain))
                if MapObjects.injured in cell.objects:
                    self.last_seen[-1][-1].add_map_object(MapObjects.injured)

    def read_in_map(self):

        # Hard-coded Constants
        SYMBOL_PLAYER_LIST = ['^', '>', 'v', '<']
        SYMBOL_INJURED = '*'
        SYMBOL_ZOMBIE = 'Z'
        SYMBOL_BATTERY = '#'
        SYMBOL_PEDESTRIAN = '@'
        SHEET_INDEX = 0

        # Open Excel file
        book = xlrd.open_workbook(self.map_file, formatting_info=True)

        # Each sheet (tabs at the bottom) contains 1 map
        sheet = book.sheet_by_index(SHEET_INDEX)
        print('Loading Map: {}'.format(sheet.name))

        # Get constants defined in spreadsheet -- cells are 0 indexed (hardcoded references for now)
        max_width = int(sheet.cell(19, 3).value)
        max_height = int(sheet.cell(20, 3).value)
        start_row = int(sheet.cell(21, 3).value) - 1
        start_col = int(sheet.cell(22, 3).value) - 1
        self.map_max_energy = int(sheet.cell(25, 3).value)

        color_indexes = {}
        # Get color constants for terrain, found in the legend
        for i in range(7):
            xfx = sheet.cell_xf_index(2 + i, 1)
            xf = book.xf_list[xfx]
            bgx = xf.background.pattern_colour_index
            color_indexes[bgx] = i  # i = enum value, where 0 = none, etc.

        # Get end rows and cols of map
        max_rows = min(sheet.nrows, start_row + max_height)
        max_cols = min(sheet.ncols, start_col + max_width)
        end_row = start_row
        end_col = start_col

        # Get the bounds of the map
        for row_ in range(start_row, max_rows):
            for col_ in range(start_col, max_cols):
                cell = sheet.cell(row_, col_)
                xfx = sheet.cell_xf_index(row_, col_)
                xf = book.xf_list[xfx]
                bgx = xf.background.pattern_colour_index
                # Check if cell is empty
                if not cell.value and color_indexes[bgx] == 0:
                    continue
                # otherwise update the end_row and end_col
                else:
                    end_row = max(end_row, row_)
                    end_col = max(end_col, col_)

        # Set the bounds of the map
        num_rows = end_row - start_row + 1
        num_cols = end_col - start_col + 1

        # Update important things based on the read in map
        self.rows = num_rows
        self.cols = num_cols

        grid = []
        for r_ in range(num_rows):
            grid_row = []
            for c_ in range(num_cols):
                row_, col_ = r_ + start_row, c_ + start_col
                sheet_cell = sheet.cell(row_, col_)
                xfx = sheet.cell_xf_index(row_, col_)
                xf = book.xf_list[xfx]
                bgx = xf.background.pattern_colour_index
                # Terrain
                if bgx in color_indexes:
                    grid_cell = Cell(Terrains(color_indexes[bgx]))
                else:
                    grid_cell = Cell()
                # Objects
                if sheet_cell.value in SYMBOL_PLAYER_LIST:
                    grid_cell.add_map_object(MapObjects.player)
                    self.player_location = [r_, c_]
                    if sheet_cell.value == '^':
                        self.player_orientation = Orientations.up
                    elif sheet_cell.value == '>':
                        self.player_orientation = Orientations.right
                    elif sheet_cell.value == 'v':
                        self.player_orientation = Orientations.down
                    elif sheet_cell.value == '<':
                        self.player_orientation = Orientations.left
                    else:
                        raise ValueError('Invalid player icon')
                elif sheet_cell.value == SYMBOL_INJURED:
                    grid_cell.add_map_object(MapObjects(1))
                elif sheet_cell.value == SYMBOL_ZOMBIE:
                    grid_cell.add_map_object(MapObjects(3))
                elif sheet_cell.value == SYMBOL_BATTERY:
                    grid_cell.add_map_object(MapObjects(4))
                elif sheet_cell.value == SYMBOL_PEDESTRIAN:
                    grid_cell.add_map_object(MapObjects(2))

                # Add cell to grid[][]
                grid_row.append(grid_cell)

            grid.append(grid_row)

        return grid

    def random_grid(self):
        empty_grid = self._get_empty_grid_with_boarders()
        random_grid = self._random_fill_setup(empty_grid)
        return random_grid

    def _get_empty_grid_with_boarders(self) -> List:
        grid = list()
        for r_ in range(self.rows):
            row_data = []
            for c_ in range(self.cols):
                # Put edges to the top and bottom
                if r_ == 0 or r_ == self.rows - 1:
                    cell_data = Cell(Terrains.out_of_bounds)
                # Put edges to the left and right
                elif c_ == 0 or c_ == self.cols - 1:
                    cell_data = Cell(Terrains.out_of_bounds)
                # Set normal defaults then
                else:
                    cell_data = Cell(Terrains.floor)
                row_data.append(cell_data)
            grid.append(row_data)
        return grid

    def _random_fill_setup(self, grid):
        # This replicates the excel workbook that generates random maps. Directly implemented for ease of use.
        # The only difference is that this implementation also adds the player with a valid orientation.

        p_wall = 16
        p_floor = 82
        p_hospital = 84
        p_fire = 88
        p_injured = 90
        p_pedestrian = 95
        p_zombie = 100

        # for each cell in the grid
        for r_ in range(len(grid)):
            for c_ in range(len(grid[r_])):
                # Start the player in the middle of the grid facing right
                if r_ == int(self.rows // 2) and c_ == int(self.cols // 2):
                    grid[r_][c_].add_map_object(MapObjects.player)
                    self.player_location = [r_, c_]
                    self.player_orientation = Orientations.right
                    continue
                curr_cell = grid[r_][c_]

                # Leave in place any boarder walls that we may have set already in the grid when we initialized it.
                if curr_cell.terrain is Terrains.out_of_bounds:
                    continue

                # Get a random int between 1 and 100, note these bounds are both inclusive
                cell_roll = random.randint(1, 100)  # We could use a random continuous value if we wanted too!
                if cell_roll < p_wall:
                    grid[r_][c_].terrain = Terrains.wall
                elif cell_roll < p_floor:
                    grid[r_][c_].terrain = Terrains.floor
                elif cell_roll < p_hospital:
                    grid[r_][c_].terrain = Terrains.hospital
                elif cell_roll < p_fire:
                    grid[r_][c_].terrain = Terrains.fire
                elif cell_roll < p_injured:
                    grid[r_][c_].add_map_object(MapObjects.injured)
                elif cell_roll < p_pedestrian:
                    grid[r_][c_].add_map_object(MapObjects.pedestrian)
                    orientation = random.choice([0, 1, 2, 3])
                    grid[r_][c_].zombie_pedestrian_orientation = orientation

                elif cell_roll <= p_zombie:
                    grid[r_][c_].add_map_object(MapObjects.zombie)
                    orientation = random.choice([0, 1, 2, 3])
                    grid[r_][c_].zombie_pedestrian_orientation = orientation

                else:
                    raise RuntimeError('Random cell value out of range?')

        return grid

    def do_turn(self, action: Actions):
        self.turn_score = 0
        # Update turn count
        self.turns +=1
        # Update where objects are
        self.new_grid = copy.deepcopy(self.grid)
        for a in range(10):
            for b in range(10):
                coords = [a,b]
                if self.grid[a][b].terrain == Terrains.fire: # Updates fire
                    self._execute_fire_spread(coords)
                    if MapObjects.pedestrian in self.grid[a][b].objects:
                        self.new_grid[a][b].remove_map_object(MapObjects.pedestrian)
                        self.turn_score -= 10
                    if MapObjects.zombie in self.grid[a][b].objects:
                        self.new_grid[a][b].remove_map_object(MapObjects.zombie)
                    if MapObjects.zombing in self.grid[a][b].objects and MapObjects.player not in self.grid[a][b].objects:
                        self.new_grid[a][b].remove_map_object(MapObjects.zombing)
                    if MapObjects.injured in self.grid[a][b].objects and MapObjects.player not in self.grid[a][b].objects:
                        self.new_grid[a][b].remove_map_object(MapObjects.injured)

                elif self.grid[a][b].terrain == Terrains.wall: # Updates walls
                    self._execute_wall_fall(coords)

                elif self.grid[a][b].terrain == Terrains.floor:
                    if self.grid[a][b].objects == [MapObjects.zombie]: # Move zombies around
                        self._execute_zombies_move(coords)

                    elif self.grid[a][b].objects == [MapObjects.pedestrian]: # Move pedestrians around
                        self._execute_pedestrian_move(coords)

                    elif self.grid[a][b].objects == [MapObjects.zombing]:
                        self.new_grid[a][b].zombing_turns_left -= 1
                        if self.new_grid[a][b].zombing_turns_left == 0:
                            self.turn_score -= 7
                            self.new_grid[a][b].remove_map_object(MapObjects.zombing)
                            self.new_grid[a][b].add_map_object(MapObjects.zombie)
                            self.new_grid[a][b].zombing_turns_left = None
                            self.new_grid[a][b].zombie_pedestrian_orientation = Orientations.down

        # Stop conflicts

        self.grid = copy.deepcopy(self.new_grid)


        # Update player position based on current location and orientation
        if action == Actions.step_forward:
            self._execute_step_forward()
        # Update player orientation
        elif action == Actions.turn_left:
            self._execute_turn_left()
        elif action == Actions.turn_right:
            self._execute_turn_right()
        # Didn't find a valid action so defaulting to none
        elif action == Actions.none:
            pass
        else:
            raise ValueError('Invalid action found while attempting to do turn on the Grid.')

        # Process penalties and rewards
        # Baseline score, energy numbers for each move, modify these based on the cell we end up at
        self.turn_score += self._get_score_of_action()  # Total score is captured in the env
        energy_action = -1
        done = False  # always false, the game object will keep track of total energy and total score


        return self.turn_score, energy_action, done

    def _execute_step_forward(self):

        # Get the next position based on orientation
        curr_pos = self.player_location
        if self.player_orientation == Orientations.right:
            next_pos = [curr_pos[0], curr_pos[1] + 1]
        elif self.player_orientation == Orientations.left:
            next_pos = [curr_pos[0], curr_pos[1] - 1]
        elif self.player_orientation == Orientations.up:
            next_pos = [curr_pos[0] - 1, curr_pos[1]]
        elif self.player_orientation == Orientations.down:
            next_pos = [curr_pos[0] + 1, curr_pos[1]]
        else:
            raise RuntimeError('Invalid orientation when trying to move forward')

        # Check validity of move
        if not self._is_valid_move(next_pos):
            next_pos = curr_pos

        # Update the player's position
        self.player_location = next_pos

        # Grab the current and next cell
        curr_cell = self.grid[curr_pos[0]][curr_pos[1]]
        next_cell = self.grid[next_pos[0]][next_pos[1]]

        # Update the player's position in the cells
        curr_cell.remove_map_object(MapObjects.player)
        next_cell.add_map_object(MapObjects.player)

        # Update the map objects in cells so they move with the player (update injured, passengers)
        if MapObjects.injured in curr_cell.objects:
            curr_cell.remove_map_object(MapObjects.injured)
            next_cell.add_map_object(MapObjects.injured)
        elif MapObjects.zombing in curr_cell.objects:
            curr_cell.remove_map_object(MapObjects.zombing)
            next_cell.add_map_object(MapObjects.zombing)

    def _execute_turn_left(self):
        if self.player_orientation == Orientations.right:
            self.player_orientation = Orientations.up
        elif self.player_orientation == Orientations.left:
            self.player_orientation = Orientations.down
        elif self.player_orientation == Orientations.up:
            self.player_orientation = Orientations.left
        elif self.player_orientation == Orientations.down:
            self.player_orientation = Orientations.right
        else:
            raise RuntimeError('Invalid orientation when trying to change orientation left')

    def _execute_turn_right(self):
        if self.player_orientation == Orientations.right:
            self.player_orientation = Orientations.down
        elif self.player_orientation == Orientations.left:
            self.player_orientation = Orientations.up
        elif self.player_orientation == Orientations.up:
            self.player_orientation = Orientations.right
        elif self.player_orientation == Orientations.down:
            self.player_orientation = Orientations.left
        else:
            raise RuntimeError('Invalid orientation when trying to change orientation right')

    def _get_score_of_action(self):
        # Default Reward Scheme
        RESCUE_REWARD = 9  # +9 per rescued victim (picked up one by one and delivered to hospital)
        PED_PENALTY = -10  # -10 per squished pedestrian (or mobile pedestrian)
        VIC_PENALTY = -5  # -1 per squished victim (if you already have one onboard and enter it’s space, SQUISH)
        FIRE_PENALTY = -5  # -5 per entry into fire (each entry; but otherwise it doesn’t actually hurt you)

        t_score = 0

        # Grab the cell where the player is (after the move)
        end_cell: Cell = self.grid[self.player_location[0]][self.player_location[1]]

        # Add a reward if they rescued a victim
        if end_cell.terrain == Terrains.hospital:
            if MapObjects.injured in end_cell.objects:
                t_score += RESCUE_REWARD  # Deliver the injured
                end_cell.remove_map_object(MapObjects.injured)  # Remove them from the board
            if MapObjects.zombing in end_cell.objects:
                t_score += RESCUE_REWARD
                end_cell.remove_map_object(MapObjects.zombing)

        # Add a penalty if you squished a pedestrian
        if MapObjects.pedestrian in end_cell.objects:
            t_score += PED_PENALTY  # Oh no, watch out!
            end_cell.remove_map_object(MapObjects.pedestrian)
            end_cell.zombie_pedestrian_orientation = None

        if MapObjects.zombie in end_cell.objects:
            end_cell.remove_map_object(MapObjects.zombie)
            end_cell.zombie_pedestrian_orientation = None

        # Add a penalty if you squish an injured person
        if end_cell.objects.count(MapObjects.injured) > 1:
            t_score += VIC_PENALTY  # Can only carry one so if there's more than one, squish
            end_cell.remove_map_object(MapObjects.injured)
        elif end_cell.objects.count(MapObjects.zombing) > 1:
            t_score += VIC_PENALTY  # Can only carry one so if there's more than one, squish
            end_cell.remove_map_object(MapObjects.zombing)

        elif end_cell.objects.count(MapObjects.injured) + end_cell.objects.count(MapObjects.zombing) > 1:
            t_score += VIC_PENALTY  # Can only carry one so if there's more than one, squish
            end_cell.remove_map_object(MapObjects.zombing)

        # Add a penalty for going into fire
        if end_cell.terrain == Terrains.fire:
            t_score += FIRE_PENALTY  # ouch


        return t_score

    def _is_valid_move(self, pos) -> bool:
        # Don't let the player move out of bounds or through walls
        curr_cell = self.grid[pos[0]][pos[1]]
        return curr_cell.terrain not in [Terrains.none, Terrains.out_of_bounds, Terrains.wall]

    def get_human_cell_value(self, row, col, fogofwar):
        if fogofwar == True:
            cell = self.visible_grid[row][col]
        else:
            cell = self.grid[row][col]
        cell_val = ''
        if MapObjects.none in cell.objects:
            cell_val += '?'
        if MapObjects.player in cell.objects:
            if self.player_orientation == Orientations.up:
                p_icon = '^'
            elif self.player_orientation == Orientations.down:
                p_icon = 'v'
            elif self.player_orientation == Orientations.left:
                p_icon = '<'
            elif self.player_orientation == Orientations.right:
                p_icon = '>'
            else:
                raise ValueError('Invalid player orientation while retrieving cell value for encoding/decoding')
            cell_val += p_icon
        if MapObjects.injured in cell.objects:
            cell_val += 'I'
        if MapObjects.pedestrian in cell.objects:
            cell_val += 'P'
        if MapObjects.zombie in cell.objects:
            cell_val += 'Z'
        if MapObjects.zombing in cell.objects:
            cell_val += 'N'

        return cell_val

    def _get_machine_cell_value(self, row, col):

        # Encode each cell value with an integer between 0 and 70
        # The ten's place is a map of the terrains as follows:
        #     none = 00's
        #     out_of_bounds = 10's
        #     wall = 20's
        #     floor = 30's
        #     fire = 50's
        #     hospital = 60's
        # The one's place is a map of the map object as follows:
        #     none = 0
        #     injured = 1
        #     pedestrian = 2
        #     zombie = 3
        #     player_up = 4
        #     player_down = 5
        #     player_left = 6
        #     player_right = 7

        cell = self.grid[row][col]
        cell_val = 0

        # Get the ten's place based on the terrain, only ever one kind of terrain
        if cell.terrain == Terrains.none:
            cell_val += 0
        elif cell.terrain == Terrains.out_of_bounds:
            cell_val += 10
        elif cell.terrain == Terrains.wall:
            cell_val += 20
        elif cell.terrain == Terrains.floor:
            cell_val += 30
        elif cell.terrain == Terrains.fire:
            cell_val += 40
        elif cell.terrain == Terrains.hospital:
            cell_val += 50
        else:
            raise ValueError('Invalid cell terrain while retrieving cell value for encoding/decoding.')

        # Technically supports more than one object so order here matters
        if MapObjects.player in cell.objects:
            if self.player_orientation == Orientations.up:
                cell_val += 4
            elif self.player_orientation == Orientations.down:
                cell_val += 5
            elif self.player_orientation == Orientations.left:
                cell_val += 6
            elif self.player_orientation == Orientations.right:
                cell_val += 7
            else:
                raise ValueError('Invalid player orientation while retrieving cell value for encoding/decoding')
        elif MapObjects.injured in cell.objects:
            cell_val += 1
        elif MapObjects.pedestrian in cell.objects:
            cell_val += 2
        elif MapObjects.zombie in cell.objects:
            cell_val += 3
        elif MapObjects.none in cell.objects:
            cell_val += 0
        else:
            # No objects assigned to cell
            cell_val += 0  # Mark it the same as none for the machine

        return cell_val

    def human_encode(self, turns_executed, action_taken, energy_remaining, game_score):
        # Package up "Grid" object in a way that is viewable to humans (multi-line string)
        grid_data = dict()
        for r_ in range(self.rows):
            for c_ in range(self.cols):
                grid_data[f'{r_}, {c_}'] = self.grid[r_][c_].get_data()
        grid_data['status'] = {
            'turns_executed': turns_executed,
            'action_taken': action_taken,
            'energy_remaining': energy_remaining,
            'game_score': game_score
        }
        return json.dumps(grid_data)

    def machine_encode(self, turns_executed, action_taken, energy_remaining, game_score):
        # Package up the "grid" object to be compatible with state space
        # self.observation_space = spaces.Box(low=0, high=60, shape=(self.num_rows, self.num_cols), dtype='uint8')
        # Create a numpy array with the right dtype filled with zeros and then add in the state values for each cell
        machine_state = np.zeros((self.rows + 1, self.cols), dtype='uint8')
        for r_ in range(self.rows):
            for c_ in range(self.cols):
                cell_val = self._get_machine_cell_value(r_, c_)
                machine_state[r_, c_] = cell_val

        # Add some status fields to the state in the last row
        machine_state[self.rows, 0] = int(turns_executed)
        machine_state[self.rows, 1] = int(action_taken[1])
        machine_state[self.rows, 2] = int(energy_remaining)
        machine_state[self.rows, 3] = int(game_score)

        return machine_state

    def machine_render(self, turns_executed, action_taken, energy_remaining, game_score):
        # Render briefly for the machine (not likely to be seen, mainly for debugging)
        # Print the raw machine encoding for debugging only

        print('Turns Executed: {0} | Action: {1} | Energy Remaining: {2} | '
              'Score: {3} | Full State: {4}'.format(turns_executed, action_taken,
                                                    energy_remaining, game_score,
                                                    self.machine_encode(turns_executed, action_taken,
                                                                        energy_remaining, game_score)))

    def observation_space(self):
        '''Takes in the current grid and returns a version where only a radius of 4 is shown'''
        # Clear the shown list from previous turn
        self.shown = [[self.player_location[0],self.player_location[1]]]

        a , b = self.player_location
        print('player location is: ' + str([a,b]))
        self.visible_range = [[0,0], [0,1], [1,1],[1,0],[1,-1], [0,-1], [-1,-1], [-1,0], [-1,1],[0,2],[2,0],[0,-2], [-2,0]]


        self.visible_grid = []
        for m in range(10):
            self.visible_grid.append([])
            if m == 0 or m == 9:
                for n in range(10):
                    self.visible_grid[m].append(Cell(Terrains.out_of_bounds))
            else:
                for _ in range(10):
                    if _ == 0 or _ == 9:
                        self.visible_grid[m].append(Cell(Terrains.out_of_bounds))
                    else:
                        self.visible_grid[m].append([])

        #Corners
        if a == 1 and b == 1:
            print('a=b=1')
            self.visible_range = [[0, 0], [0,1], [1,1],[1,0],[1,-1], [0,-1], [-1,-1], [-1,0], [-1,1],[0,2],[2,0]]

        elif a == 1 and b == 8:
            print('a=1,b=8')
            self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1],
                                  [0, -2],[2, 0]]
        elif a == 8 and b == 1:
            print('a=8, b=1')
            self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1],
                                  [0, 2], [-2, 0]]
        elif a == 8 and b == 8:
            print('a=b=8')
            self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1],
                                  [0, -2], [-2, 0]]
        elif a == 1 or a == 8: # Side Columns
            if a == 1:
                print('a=1')
                self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 2],
                                      [0, -2], [2, 0]]
            elif a == 8:
                print('a=8')
                self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, -2],
                                      [-2, 0], [0, 2]]
            else:
                print('else a')
        elif b == 1 or b == 8: # Side Rows
            if b == 1:
                print('b=1')
                self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1], [2, 0],
                                      [0, 2], [-2, 0]]
            elif b == 8:
                print('b=8')
                self.visible_range = [[0, 0], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1], [-2, 0],
                                      [2, 0], [0, -2]]
            else:
                print('else b')

        if [2,0] in self.visible_range: # East Wall
            if self.grid[a+1][b].terrain == Terrains.wall:
                self.visible_range.remove([2,0])
        #    elif self.grid[a+1][b].terrain == Terrains.out_of_bounds:
        #        raise ValueError("This cell should not be out of bounds [2,0]")
        if [-2,0] in self.visible_range: # West Wall
            if self.grid[a-1][b].terrain == Terrains.wall:
                self.visible_range.remove([-2,0])
        #     elif self.grid[a-1][b].terrain == Terrains.out_of_bounds:
        #        raise ValueError("This cell should not be out of bounds [-2,0]")
        if [0,2] in self.visible_range: # South Wall
            if self.grid[a][b+1].terrain == Terrains.wall:
                self.visible_range.remove([0,2])
        #    elif self.grid[a][b+1].terrain == Terrains.out_of_bounds:
        #        raise ValueError("This cell should not be out of bounds [-2,0]")
        if [0,-2] in self.visible_range: # North Wall
            if self.grid[a][b-1].terrain == Terrains.wall:
                self.visible_range.remove([0,-2])
        #    elif self.grid[a][b-1].terrain == Terrains.out_of_bounds:
        #       raise ValueError("This cell should not be out of bounds [-2,0]")

        #Update self.shown
        print(self.visible_range)
        for u,v in self.visible_range:
            self.shown.append([a+u,v+b])

        for h,i in self.visible_range:
            self.visible_grid[a+h][b+i] = self.grid[a+h][b+i]
            self.last_seen[a+h][b+i] = Cell(self.grid[a+h][b+i].terrain)
            if MapObjects.injured in self.grid[a+h][b+i].objects:
                self.last_seen[a + h][b + i].add_map_object(MapObjects.injured)
            if MapObjects.zombing in self.grid[a+h][b+i].objects:
                self.last_seen[a + h][b + i].add_map_object(MapObjects.zombing)

        for x in range(10):
            for y in range(10):
                if self.visible_grid[x][y] == []:
                    self.visible_grid[x][y] = self.last_seen[x][y]

    def _execute_fire_spread(self, coords):
        '''Spreads fire out over a small region'''
        areas_around = [[0,1], [1,1], [1,0], [1,-1], [0,-1], [-1,-1], [-1,0], [-1,1]]
        if self.grid[coords[0]][coords[1]].terrain == Terrains.fire:
            for h,i in areas_around:
                try:
                    if self.grid[coords[0]+h][coords[1]+i].terrain == Terrains.floor:
                        a = random.random()
                        if self.grid[coords[0]+h][coords[1]+i].terrain == Terrains.floor and a < .01:
                            self.new_grid[coords[0]+h][coords[1]+i].terrain = Terrains.fire
                except:
                    pass

    def _execute_wall_fall(self, coords):
        '''Small chance of walls falling'''
        a = random.random()
        if a < .01:
            self.new_grid[coords[0]][coords[1]].terrain = Terrains.floor

    def _execute_zombies_move(self, zomb_coords):
        '''Moves randomly unless there's a nearby pedestrian; then the zombie loads a neural net to chase the pedestrian'''
        human_in_radius , human_coords = self._human_in_radius(zomb_coords)
        print(human_in_radius, human_coords)
        if not human_in_radius: # No human -> random move out of viable moves
            if self.turns % 2 == 0:
                print('zombie move')
                if self.grid[zomb_coords[0]][zomb_coords[1]].next_move != None: # Continue previous moves
                    if self.grid[zomb_coords[0]][zomb_coords[1]].next_move == 'turn_left':
                        self._execute_zombie_pedestrian_turn_left(zomb_coords)
                        self.new_grid[zomb_coords[0]][zomb_coords[1]].next_move = None # Reset next move

                    elif self.grid[zomb_coords[0]][zomb_coords[1]].next_move == 'turn_right':
                        self._execute_zombie_pedestrian_turn_right(zomb_coords)
                        self.new_grid[zomb_coords[0]][zomb_coords[1]].next_move = None

                    elif self.grid[zomb_coords[0]][zomb_coords[1]].next_move == 'forward':
                        self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                        self.new_grid[zomb_coords[0]][zomb_coords[1]].next_move = None

                elif self.grid[zomb_coords[0]][zomb_coords[1]].next_next_move != None: # Continue the last-last turn's move
                    if self.grid[zomb_coords[0]][zomb_coords[1]].next_next_move == 'forward':
                        self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                        self.new_grid[zomb_coords[0]][zomb_coords[1]].next_next_move = None # Reset next move
                    else:
                        raise ValueError("Next next move isn't working")

                else: # Decide new action
                    possible_place = []
                    if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        move_pos_dict = {(1,0):'180Turn', (-1,0):'forward',(0,1):'right',(0,-1):'left'}
                    elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        move_pos_dict = {(1,0):'right', (-1,0):'left',(0,1):'forward',(0,-1):'180Turn'}
                    elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        move_pos_dict = {(1,0):'forward', (-1,0):'180Turn',(0,1):'left',(0,-1):'right'}
                    elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        move_pos_dict = {(1,0):'left', (-1,0):'right',(0,1):'180Turn',(0,-1):'forward'}
                    else:
                        raise ValueError("Missing zombie orientation")


                    for places in [(1,0),(-1,0),(0,1),(0,-1)]:
                        if self._is_valid_move([zomb_coords[0]+places[0], zomb_coords[1]+places[1]]) and \
                            self.grid[zomb_coords[0]+places[0]][zomb_coords[1]+places[1]].terrain != Terrains.hospital and \
                            self.grid[zomb_coords[0]+places[0]][zomb_coords[1]+places[1]].terrain != Terrains.fire and \
                            MapObjects.injured not in self.grid[zomb_coords[0]+places[0]][zomb_coords[1]+places[1]].objects and \
                            MapObjects.player not in self.grid[zomb_coords[0] + places[0]][zomb_coords[1] + places[1]].objects and \
                            MapObjects.zombie not in self.grid[zomb_coords[0] + places[0]][zomb_coords[1] + places[1]].objects and \
                            MapObjects.zombing not in self.grid[zomb_coords[0] + places[0]][zomb_coords[1] + places[1]].objects and \
                            MapObjects.zombie not in self.new_grid[zomb_coords[0] + places[0]][zomb_coords[1] + places[1]].objects:

                            possible_place.append(move_pos_dict[places])

                    try:
                        place = random.choice(possible_place)
                    except:
                        place = None
                        print('trapped zombie rip')

                    if place == 'right':
                        self._execute_zombie_pedestrian_turn_right(zomb_coords)
                        self.grid[zomb_coords[0]][zomb_coords[1]].next_move = 'forward'
                    elif place == 'left':
                        self._execute_zombie_pedestrian_turn_left(zomb_coords)
                        self.grid[zomb_coords[0]][zomb_coords[1]].next_move = 'forward'
                    elif place == 'forward':
                        self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                    elif place == '180Turn':
                        self._execute_zombie_pedestrian_turn_right(zomb_coords)
                        self.grid[zomb_coords[0]][zomb_coords[1]].next_move = 'turn_right'
                        self.grid[zomb_coords[0]][zomb_coords[1]].next_next_move = 'forward'

        else: # THERES A HUMAN GOTTA GO EAT IT
            print("no longer afk ")
            self._chase_pedestrian(zomb_coords, human_coords[0])

    def _execute_zombie_pedestrian_turn_left(self, coords):
        if self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.up:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.left
        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.left:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.down
        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.down:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.right
        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.right:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.up
        else:
            raise RuntimeError('Can not turn zombie/pedestrian left')

    def _execute_zombie_pedestrian_turn_right(self, coords):
        if self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.up:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.right
        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.right:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.down
        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.down:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.left
        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.left:
            self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = Orientations.up
        else:
            raise RuntimeError('Can not turn zombie/pedestrian left')

    def _execute_zombie_pedestrian_forward(self, coords, zombie_pedestrian):

        if self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.up:
            next_pos = [coords[0]-1, coords[1]]
            if self._is_valid_move(next_pos):
                if zombie_pedestrian == 'zombie':
                    # Remove zombie
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.zombie)
                    # Add zombie to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.zombie)
                else:
                    # Remove pedestrian
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.pedestrian)
                    # Add pedestrian to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.pedestrian)
                # Reset old zombie/pedestrian orientation
                self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = None
                # Add new zombie/pedestrian orientation
                self.new_grid[next_pos[0]][next_pos[1]].zombie_pedestrian_orientation = Orientations.up

        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.right:
            next_pos = [coords[0], coords[1]+1]
            if self._is_valid_move(next_pos):
                if zombie_pedestrian == 'zombie':
                    # Remove zombie
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.zombie)
                    # Add zombie to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.zombie)
                else:
                    if MapObjects.pedestrian in self.new_grid[coords[0]][coords[1]].objects:
                        # Remove pedestrian
                        self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.pedestrian)
                        # Add pedestrian to new coords
                        self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.pedestrian)
                # Reset old zombie/pedestrian orientation
                self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = None
                # Add new zombie/pedestrian orientation
                self.new_grid[next_pos[0]][next_pos[1]].zombie_pedestrian_orientation = Orientations.right

        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.down:
            next_pos = [coords[0]+1, coords[1]]
            if self._is_valid_move(next_pos):
                if zombie_pedestrian == 'zombie':
                    # Remove zombie
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.zombie)
                    # Add zombie to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.zombie)
                else:
                    # Remove pedestrian
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.pedestrian)
                    # Add pedestrian to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.pedestrian)
                # Reset old zombie/pedestrian orientation
                self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = None
                # Add new zombie/pedestrian orientation
                self.new_grid[next_pos[0]][next_pos[1]].zombie_pedestrian_orientation = Orientations.down

        elif self.grid[coords[0]][coords[1]].zombie_pedestrian_orientation == Orientations.left:
            next_pos = [coords[0], coords[1]-1]
            if self._is_valid_move(next_pos):
                if zombie_pedestrian == 'zombie':
                    # Remove zombie
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.zombie)
                    # Add zombie to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.zombie)
                else:
                    # Remove pedestrian
                    self.new_grid[coords[0]][coords[1]].remove_map_object(MapObjects.pedestrian)
                    # Add pedestrian to new coords
                    self.new_grid[next_pos[0]][next_pos[1]].add_map_object(MapObjects.pedestrian)
                # Reset old zombie/pedestrian orientation
                self.new_grid[coords[0]][coords[1]].zombie_pedestrian_orientation = None
                # Add new zombie/pedestrian orientation
                self.new_grid[next_pos[0]][next_pos[1]].zombie_pedestrian_orientation = Orientations.left

        else:
            raise RuntimeError('Can not move zombie/pedestrian forward?')

    def _execute_pedestrian_move(self, pedestrian_coords): # Same as execute zombie move
        '''Moves randomly unless there's a nearby zombie; then the pedestrian loads a neural net to run away from the zombie'''
        zombie_in_radius, zomb_coords = self._zombie_in_radius(pedestrian_coords)
        print(zombie_in_radius, zomb_coords)
        if not zombie_in_radius:  # No human -> random move out of viable moves
            if self.turns % 2 == 0:
                print('pedestrian move')
                if self.grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move != None:  # Continue previous moves
                    if self.grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move == 'turn_left':
                        self._execute_zombie_pedestrian_turn_left(pedestrian_coords)
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = None  # Reset next move

                    elif self.grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move == 'turn_right':
                        self._execute_zombie_pedestrian_turn_right(pedestrian_coords)
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = None

                    elif self.grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move == 'forward':
                        self._execute_zombie_pedestrian_forward(pedestrian_coords, 'pedestrian')
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = None

                elif self.grid[pedestrian_coords[0]][pedestrian_coords[1]].next_next_move != None:  # Continue the last-last turn's move
                    if self.grid[pedestrian_coords[0]][pedestrian_coords[1]].next_next_move == 'forward':
                        self._execute_zombie_pedestrian_forward(pedestrian_coords, 'pedestrian')
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_next_move = None  # Reset next move
                    else:
                        raise ValueError("Next next move isn't working")

                else:  # Decide new action

                    possible_place = []
                    if self.grid[pedestrian_coords[0]][pedestrian_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        move_pos_dict = {(1, 0): '180Turn', (-1, 0): 'forward', (0, 1): 'right', (0, -1): 'left'}
                    elif self.grid[pedestrian_coords[0]][pedestrian_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        move_pos_dict = {(1, 0): 'right', (-1, 0): 'left', (0, 1): 'forward', (0, -1): '180Turn'}
                    elif self.grid[pedestrian_coords[0]][pedestrian_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        move_pos_dict = {(1, 0): 'forward', (-1, 0): '180Turn', (0, 1): 'left', (0, -1): 'right'}
                    elif self.grid[pedestrian_coords[0]][pedestrian_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        move_pos_dict = {(1, 0): 'left', (-1, 0): 'right', (0, 1): '180Turn', (0, -1): 'forward'}
                    else:
                        print(self.grid[pedestrian_coords[0]][pedestrian_coords[1]].zombie_pedestrian_orientation)
                        raise ValueError("Missing pedestrian orientation")

                    for places in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        if self._is_valid_move([pedestrian_coords[0] + places[0], pedestrian_coords[1] + places[1]]) and \
                            self.grid[pedestrian_coords[0]+places[0]][pedestrian_coords[1]+places[1]].terrain != Terrains.hospital and \
                            self.grid[pedestrian_coords[0]+places[0]][pedestrian_coords[1]+places[1]].terrain != Terrains.fire and \
                            MapObjects.injured not in self.grid[pedestrian_coords[0]+places[0]][pedestrian_coords[1]+places[1]].objects and \
                            MapObjects.pedestrian not in self.grid[pedestrian_coords[0] + places[0]][pedestrian_coords[1] + places[1]].objects and \
                            MapObjects.player not in self.grid[pedestrian_coords[0]+places[0]][pedestrian_coords[1]+places[1]].objects and \
                            MapObjects.zombing not in self.grid[pedestrian_coords[0]+places[0]][pedestrian_coords[1]+places[1]].objects and \
                            MapObjects.pedestrian not in self.new_grid[pedestrian_coords[0] + places[0]][pedestrian_coords[1] + places[1]].objects:

                            possible_place.append(move_pos_dict[places])
                    try:
                        place = random.choice(possible_place)
                    except:
                        place = None
                        print('trapped pedestrian rip')
                    if place == 'right':
                        self._execute_zombie_pedestrian_turn_right(pedestrian_coords)
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = 'forward'
                    elif place == 'left':
                        self._execute_zombie_pedestrian_turn_left(pedestrian_coords)
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = 'forward'
                    elif place == 'forward':
                        self._execute_zombie_pedestrian_forward(pedestrian_coords, 'pedestrian')
                    elif place == '180Turn':
                        self._execute_zombie_pedestrian_turn_right(pedestrian_coords)
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = 'turn_right'
                        self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_next_move = 'forward'

        else:  # THERES A ZOMBIE GOTTA RUN
            print("pedestrian, " + str(pedestrian_coords) + ", is running from zombies: " + str(zomb_coords))
            self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_move = None
            self.new_grid[pedestrian_coords[0]][pedestrian_coords[1]].next_next_move = None
            self._run_from_zombie(zomb_coords[0], pedestrian_coords)

    def _zombie_in_radius(self, human_coords):
        zombie_list = []
        zombies = False
        for a,b in [[0,1], [1,1],[1,0],[1,-1], [0,-1], [-1,-1], [-1,0], [-1,1],[0,2],[2,0],[0,-2], [-2,0]]:
            try:
                if MapObjects.zombie in self.grid[human_coords[0]+a][human_coords[1]+b].objects:
                    print('zombie in radius of pedestrian: ' + str(human_coords))
                    zombie_list.append([human_coords[0]+a,human_coords[1]+b])
                    zombies = True
            except:
                pass
        return zombies, zombie_list

    def _human_in_radius(self, zombie_coords):
        human_list = []
        humans = False
        for a, b in [[0,1], [1,1],[1,0],[1,-1], [0,-1], [-1,-1], [-1,0], [-1,1],[0,2],[2,0],[0,-2], [-2,0]]:
            try:
                if MapObjects.pedestrian in self.grid[zombie_coords[0] + a][zombie_coords[1] + b].objects and \
                    MapObjects.zombing not in self.new_grid[zombie_coords[0] + a][zombie_coords[1] + b].objects:
                    print('Human in radius of zombie: ' + str(zombie_coords))
                    human_list.append([zombie_coords[0] + a,zombie_coords[1] + b])
                    humans = True
            except:
                pass
        return humans, human_list


    def _chase_pedestrian(self, zomb_coords, human_coords):
        print('chasing pedestrian')
        if zomb_coords[0] == human_coords[0]:
            print('branch 1 0=0')
            if zomb_coords[1] - human_coords[1] < 0:
                # Move right
                print('going right')
                if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                    print('zombie: ' + str(zomb_coords) + ' turning right to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_right(zomb_coords)
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                    print('zombie: ' + str(zomb_coords) + ' going forward to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                    print('zombie: ' + str(zomb_coords) + ' turning left to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_left(zomb_coords)
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                    print('zombie: ' + str(zomb_coords) + ' turning 180 to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_right(zomb_coords)
                else:
                    print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                    raise ValueError("Missing pedestrian orientation")
            elif zomb_coords[1] - human_coords[1] > 0:
                    # Move left
                    print('going left')
                    if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        print('zombie: ' + str(zomb_coords) + ' turning left to get ' + str(human_coords))
                        self._execute_zombie_pedestrian_turn_left(zomb_coords)
                    elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        print('zombie: ' + str(zomb_coords) + ' turning 180 to get ' + str(human_coords))
                        self._execute_zombie_pedestrian_turn_right(zomb_coords)
                    elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        print('zombie: ' + str(zomb_coords) + ' turning right to get ' + str(human_coords))
                        self._execute_zombie_pedestrian_turn_right(zomb_coords)
                    elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        print('zombie: ' + str(zomb_coords) + ' going forward to get ' + str(human_coords))
                        self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                    else:
                        print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                        raise ValueError("Missing pedestrian orientation")
        elif zomb_coords[1] == human_coords[1]:
            print('branch 2 1=1')
            if zomb_coords[0] - human_coords[0] < 0:
                # Move down
                print('moving down')
                if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                    print('zombie: ' + str(zomb_coords) + ' turning 180 degrees to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_right(zomb_coords)
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                    print('zombie: ' + str(zomb_coords) + ' turning right to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_right(zomb_coords)
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                    print('zombie: ' + str(zomb_coords) + ' going forward to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                    print('zombie: ' + str(zomb_coords) + ' turning left to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_left(zomb_coords)
                else:
                    print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                    raise ValueError("Missing pedestrian orientation")
            elif zomb_coords[0] - human_coords[0] > 0:
                # Move up
                print('going up')
                if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                    print('zombie: ' + str(zomb_coords) + ' going forward to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                    print('zombie: ' + str(zomb_coords) + ' turning left to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_left(zomb_coords)
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                    print('zombie: ' + str(zomb_coords) + ' turning 180 to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_right(zomb_coords)
                elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                    print('zombie: ' + str(zomb_coords) + ' turning right to get ' + str(human_coords))
                    self._execute_zombie_pedestrian_turn_right(zomb_coords)
                else:
                    print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                    raise ValueError("Missing pedestrian orientation")
        elif zomb_coords[1] - human_coords[1] < 0:
            print('branch 3')
            # Move right
            print('going right')
            if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                print('zombie: ' + str(zomb_coords) + ' turning right to get ' + str(human_coords))
                self._execute_zombie_pedestrian_turn_right(zomb_coords)
            elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                print('zombie: ' + str(zomb_coords) + ' going forward to get ' + str(human_coords))
                self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
            elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                print('zombie: ' + str(zomb_coords) + ' turning left to get ' + str(human_coords))
                self._execute_zombie_pedestrian_turn_left(zomb_coords)
            elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                print('zombie: ' + str(zomb_coords) + ' turning 180 to get ' + str(human_coords))
                self._execute_zombie_pedestrian_turn_right(zomb_coords)
            else:
                print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                raise ValueError("Missing pedestrian orientation")
        elif zomb_coords[1] - human_coords[1] > 0:
            print('branch 4')
            # Move left
            print('going left')
            if self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                print('zombie: ' + str(zomb_coords) + ' turning left to get ' + str(human_coords))
                self._execute_zombie_pedestrian_turn_left(zomb_coords)
            elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                print('zombie: ' + str(zomb_coords) + ' turning 180 to get ' + str(human_coords))
                self._execute_zombie_pedestrian_turn_right(zomb_coords)
            elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                print('zombie: ' + str(zomb_coords) + ' turning right to get ' + str(human_coords))
                self._execute_zombie_pedestrian_turn_right(zomb_coords)
            elif self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                print('zombie: ' + str(zomb_coords) + ' going forward to get ' + str(human_coords))
                self._execute_zombie_pedestrian_forward(zomb_coords, 'zombie')
            else:
                print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                raise ValueError("Missing pedestrian orientation")
        else:
            print('broken pedestrian')
        print('DID THEY WALK INTO THE SAME SQUARE????')
        print(self.new_grid[zomb_coords[0]][zomb_coords[1]].objects)
        print(self.new_grid[human_coords[0]][human_coords[1]].objects)
        if MapObjects.pedestrian in self.new_grid[human_coords[0]][human_coords[1]].objects and \
            MapObjects.zombie in self.new_grid[human_coords[0]][human_coords[1]].objects:
            print('zombie walks into pedestrian')
            self.turn_score -= 3
            self.new_grid[human_coords[0]][human_coords[1]].remove_map_object(MapObjects.pedestrian)
            self.new_grid[human_coords[0]][human_coords[1]].remove_map_object(MapObjects.zombie)
            print(self.new_grid[human_coords[0]][human_coords[1]].objects)
            self.new_grid[human_coords[0]][human_coords[1]].add_map_object(MapObjects.zombing)
            self.new_grid[human_coords[0]][human_coords[1]].zombing_turns_left = 10

            self.new_grid[zomb_coords[0]][zomb_coords[1]].add_map_object(MapObjects.zombie)
            self.new_grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation = Orientations.down


    def _run_from_zombie(self, zomb_coords, human_coords):
        if self.turns % 2 ==0:
            print('pedestrian can move')
            if zomb_coords[0] == human_coords[0]:
                if human_coords[1] - zomb_coords[1] > 0:
                    # Move right
                    print('moving right')
                    if self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        self._execute_zombie_pedestrian_forward(human_coords, "pedestrian")
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        self._execute_zombie_pedestrian_turn_left(human_coords)
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    else:
                        print(self.grid[zomb_coords[0]][zomb_coords[1]].zombie_pedestrian_orientation)
                        raise ValueError("Missing pedestrian orientation")

                elif zomb_coords[1] - human_coords[1] > 0:
                    # Move down
                    print('moving down')
                    if self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    elif self.grid[human_coords[0]][
                        human_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        self._execute_zombie_pedestrian_forward(human_coords, 'pedestrian')
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        self._execute_zombie_pedestrian_turn_left(human_coords)
                    else:
                        print(self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation)
                        raise ValueError("Missing pedestrian orientation")

            elif zomb_coords[1] == human_coords[1]:
                if zomb_coords[0] - human_coords[0] > 0:
                    # Move left
                    print('moving left')
                    if self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        self._execute_zombie_pedestrian_turn_left(human_coords)
                    elif self.grid[human_coords[0]][
                        human_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        self._execute_zombie_pedestrian_forward(human_coords, 'pedestrian')
                    else:
                        print(self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation)
                        raise ValueError("Missing pedestrian orientation")
                elif zomb_coords[0] - human_coords[0] < 0:
                    # Move right
                    print('moving right')
                    if self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    elif self.grid[human_coords[0]][
                        human_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                        self._execute_zombie_pedestrian_forward(human_coords, 'pedestrian')
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                        self._execute_zombie_pedestrian_turn_left(human_coords)
                    elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                        self._execute_zombie_pedestrian_turn_right(human_coords)
                    else:
                        print(self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation)
                        raise ValueError("Missing pedestrian orientation")

            elif zomb_coords[0] - human_coords[0] > 0:
                # Move left
                print('moving left')
                if self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                    self._execute_zombie_pedestrian_turn_left(human_coords)
                elif self.grid[human_coords[0]][
                    human_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                    self._execute_zombie_pedestrian_turn_right(human_coords)
                elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                    self._execute_zombie_pedestrian_turn_right(human_coords)
                elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                    self._execute_zombie_pedestrian_forward(human_coords, 'pedestrian')
                else:
                    print(self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation)
            elif zomb_coords[0] - human_coords[0] < 0:
                # Move right
                print('moving right')
                if self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.up:
                    self._execute_zombie_pedestrian_turn_right(human_coords)
                elif self.grid[human_coords[0]][
                    human_coords[1]].zombie_pedestrian_orientation == Orientations.right:
                    self._execute_zombie_pedestrian_forward(human_coords, 'pedestrian')
                elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.down:
                    self._execute_zombie_pedestrian_turn_left(human_coords)
                elif self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation == Orientations.left:
                    self._execute_zombie_pedestrian_turn_right(human_coords)
                else:
                    print(self.grid[human_coords[0]][human_coords[1]].zombie_pedestrian_orientation)
                    raise ValueError("Missing pedestrian orientation")
        else:
            print("pedestrian can not move cuz it's the wrong turn")


    @staticmethod
    def pp_info(turns_executed, action_taken, energy_remaining, game_score):
        print('Turns Executed: {0} | Action: {1} | Energy Remaining: {2} | '
              'Score: {3}'.format(turns_executed, action_taken, energy_remaining, game_score))



if __name__ == '__main__':
    my_grid = Grid()
    score, energy, is_done = my_grid.do_turn(Actions.step_forward)
    my_grid.human_render(0, 'test', 50, 0)
    new_location = my_grid.player_location
    new_cell = my_grid.grid[new_location[0]][new_location[1]]
    print(str(new_cell.get_data()) + '  @ loc: {}'.format(new_location))
