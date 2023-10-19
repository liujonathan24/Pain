import json
import uuid
import gym
import gym_sgw  # Required, don't remove!
import sys
import os
import pygame as pg
from gym_sgw.envs.enums.Enums import Actions, Terrains, PlayTypes, MapProfiles, MapColors, MapObjects
from tkinter import messagebox
from tkinter import *
import pandas as pd


class SGW:
    """
    Human play game variant.
    """
    def __init__(self, data_log_file='data_log.json', max_energy=50, map_file=None,
                 rand_prof=None, num_rows=10, num_cols=10, fogofwar = True):
        print('setup SGW')
        self.FOGOFWAR = fogofwar
        self.ENV_NAME = 'SGW-v0'
        self.DATA_LOG_FILE_NAME = data_log_file
        self.GAME_ID = uuid.uuid4()
        self.env = None # Will be set up in the _setup() function
        self.current_action = Actions.none
        self.max_energy = max_energy
        self.map_file = "./gym_sgw/envs/maps/new_map.xls"
        self.rand_prof = rand_prof # generates a map of this type if there isn't a map file given
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.is_game_over = False
        self.turn = 0
        self.max_turn = 300  # to prevent endless loops and games
        self.cell_size = 80 # size of display
        self.game_screen = None
        self.play_area = None

        # Always do these actions upon start
        self._setup()

    def _setup(self): # private function; should only be called from other functions/methods

        # Game parameters inside the env
        self.env = gym.make(self.ENV_NAME)
        self.env.play_type = PlayTypes.human  # We will get human states and observations back
        #self.env.render_mode = PlayTypes.machine  # We'll draw these manually
        self.env.max_energy = self.max_energy
        self.env.map_file = self.map_file
        self.env.rand_profile = self.rand_prof
        self.env.num_rows = self.num_rows
        self.env.num_cols = self.num_cols
        self.env.reset()
        # Report success
        print('Created new environment {0} with GameID: {1}'.format(self.ENV_NAME, self.GAME_ID))

    def done(self):
        print("Episode finished after {} turns.".format(self.turn))
        info = {"zombies squished": self.env.grid.zombies_squished, "zombie count":self.env.grid.zombie_count,
                                "pedestrians squished":self.env.grid.pedestrians_squished, "pedestrian count":self.env.grid.pedestrian_count,
                                "victims squished":self.env.grid.victims_squished, "victim count":self.env.grid.victim_count, "total score":self.env.total_score}


        with open('logs/Human_Play_Zombie_Data.json', 'a') as f_:
            f_.write(json.dumps(info) + '\n')
            f_.close()
        pg.quit()
        self._cleanup()

    def _cleanup(self):
        self.env.close()

    def text_objects(self, text, font):
        textSurface = font.render(text, True, (0,0,0))
        return textSurface, textSurface.get_rect()

    def _draw_screen(self):
        # Update the screen with the new observation, use the grid object directly
        # Populate each cell

        self.env.grid.observation_space()

        computer_path = sys.path[0]

        wall_b_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "WallBright.png")), (80, 80))
        wall_d_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "WallDark.png")), (80, 80))
        hospital_b_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "HospitalBright.png")), (80, 80))
        hospital_d_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "HospitalDark.png")), (80, 80))
        fire_b_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "FireBright.png")), (80, 80))
        fire_d_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "FireDark.png")), (80, 80))
        zombie_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "PVZ.png")), (80, 80))
        zombie_texture_right = pg.transform.smoothscale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "ZombieRight.png")), (50, 80))
        zombie_texture_down = pg.transform.smoothscale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "ZombieDown.png")), (50, 80))
        zombie_texture_up = pg.transform.smoothscale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "ZombieUp.png")), (50, 80))
        zombie_texture_left = pg.transform.smoothscale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "ZombieLeft.png")), (50, 80))
        patient_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path,"assets"), "Patient.png")), (80, 80))
        patient_d_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path,"assets"), "PatientDark.png")), (80, 80))
        ambulance_texture_up = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "AmbulanceUp.png")), (80, 80))
        ambulance_texture_right = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "AmbulanceRight.png")), (80, 80))
        ambulance_texture_down = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "AmbulanceDown.png")), (80, 80))
        ambulance_texture_left = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "AmbulanceLeft.png")), (80, 80))
        pedestrian_texture_right = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "PedestrianRight.png")), (80, 80))
        pedestrian_texture_up = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "PedestrianUp.png")), (80, 80))
        pedestrian_texture_left = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "PedestrianLeft.png")), (80, 80))
        pedestrian_texture_down = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "PedestrianDown.png")), (80, 80))
        ambulance_texture_up_full = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "LightsUp.png")), (80, 80))
        ambulance_texture_right_full = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "LightsRight.png")), (80, 80))
        ambulance_texture_down_full = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "LightsDown.png")), (80, 80))
        ambulance_texture_left_full = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "LightsLeft.png")), (80, 80))
        zombing_texture = pg.transform.scale(
            pg.image.load(os.path.join(os.path.join(computer_path, "assets"), "Zombing.png")), (80, 80))

        """wall_b_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\WallBright.png")),
                                            (80, 80))
        wall_d_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\WallDark.png")),
                                            (80, 80))
        hospital_b_texture = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\HospitalBright.png")),
            (80, 80))
        hospital_d_texture = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\HospitalDark.png")),
            (80, 80))
        fire_b_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\FireBright.png")),
                                            (80, 80))
        fire_d_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\FireDark.png")),
                                            (80, 80))
        zombie_texture = pg.transform.smoothscale(pg.image.load(os.path.join(computer_path, "assets\PVZ.png")),
                                                  (50, 80))
        zombie_texture_right = pg.transform.smoothscale(pg.image.load(os.path.join(computer_path, "assets\ZombieRight.png")), (50, 80))
        zombie_texture_down = pg.transform.smoothscale(
            pg.image.load(os.path.join(computer_path, "assets\ZombieDown.png")),
                                                  (50, 80))
        zombie_texture_up = pg.transform.smoothscale(
            pg.image.load(os.path.join(computer_path, "assets\ZombieUp.png")),
                                                  (50, 80))
        zombie_texture_left = pg.transform.smoothscale(
            pg.image.load(os.path.join(computer_path, "assets\ZombieLeft.png")),
                                                  (50, 80))
        ambulance_texture_up = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\AmbulanceUp.png")),
            (80, 80))
        ambulance_texture_right = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\AmbulanceRight.png")), (80, 80))
        ambulance_texture_down = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\AmbulanceDown.png")), (80, 80))
        ambulance_texture_left = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\AmbulanceLeft.png")), (80, 80))
        pedestrian_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\Pedestrian.png")),
                                                (80, 80))
        pedestrian_texture_right =pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\PedestrianRight.png")),
                                                (80, 80))
        pedestrian_texture_up = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\PedestrianUp.png")),
            (80, 80))
        pedestrian_texture_left = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\PedestrianLeft.png")),
            (80, 80))
        pedestrian_texture_down = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\PedestrianDown.png")),
            (80, 80))
        patient_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\Patient.png")),
                                                (80, 80))
        patient_d_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\PatientDark.png")),
                                             (80, 80))
        ambulance_texture_up_full = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\LightsUp.png")), (80, 80))
        ambulance_texture_right_full = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\LightsRight.png")), (80, 80))
        ambulance_texture_down_full = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\LightsDown.png")), (80, 80))
        ambulance_texture_left_full = pg.transform.scale(
            pg.image.load(os.path.join(computer_path, "assets\LightsLeft.png")), (80, 80))
        zombing_texture = pg.transform.scale(pg.image.load(os.path.join(computer_path, "assets\Zombing.png")),
                                             (80, 80))"""

        for r_ in range(self.env.grid.rows):
            for c_ in range(self.env.grid.cols):
                if self.FOGOFWAR:
                    cell = self.env.grid.visible_grid[r_][c_]
                    # Set the right background color
                    if [r_, c_] not in self.env.grid.shown:
                        if cell.terrain == Terrains.none:
                            cell_color = pg.color.Color(MapColors.black_tile.value)
                        elif cell.terrain == Terrains.out_of_bounds:
                            cell_color = pg.color.Color(MapColors.black_tile.value)
                        elif cell.terrain == Terrains.wall:
                            cell_color = pg.color.Color(MapColors.dark_wall_tile.value)
                        elif cell.terrain == Terrains.floor:
                            cell_color = pg.color.Color(MapColors.dark_floor_tile.value)
                        elif cell.terrain == Terrains.fire:
                            cell_color = pg.color.Color(MapColors.dark_floor_tile.value)
                        elif cell.terrain == Terrains.hospital:
                            cell_color = pg.color.Color(MapColors.dark_hospital_tile.value)
                        else:
                            raise ValueError('Invalid cell terrain while rendering game image.')
                    else:
                        if cell.terrain == Terrains.none:
                            cell_color = pg.color.Color(MapColors.black_tile.value)
                        elif cell.terrain == Terrains.out_of_bounds:
                            cell_color = pg.color.Color(MapColors.black_tile.value)
                        elif cell.terrain == Terrains.wall:
                            cell_color = pg.color.Color(MapColors.wall_tile.value)
                        elif cell.terrain == Terrains.floor:
                            cell_color = pg.color.Color(MapColors.floor_tile.value)
                        elif cell.terrain == Terrains.fire:
                            cell_color = pg.color.Color(MapColors.floor_tile.value)
                        elif cell.terrain == Terrains.hospital:
                            cell_color = pg.color.Color(MapColors.hospital_tile.value)
                        else:
                            raise ValueError('Invalid cell terrain while rendering game image.')
                else:
                    cell = self.env.grid.grid[r_][c_]
                    # Set the right background color
                    if cell.terrain == Terrains.none:
                        cell_color = pg.color.Color(MapColors.black_tile.value)
                    elif cell.terrain == Terrains.out_of_bounds:
                        cell_color = pg.color.Color(MapColors.black_tile.value)
                    elif cell.terrain == Terrains.wall:
                        cell_color = pg.color.Color(MapColors.wall_tile.value)
                    elif cell.terrain == Terrains.floor:
                        cell_color = pg.color.Color(MapColors.floor_tile.value)
                    elif cell.terrain == Terrains.fire:
                        cell_color = pg.color.Color(MapColors.floor_tile.value)
                    elif cell.terrain == Terrains.hospital:
                        cell_color = pg.color.Color(MapColors.hospital_tile.value)
                    else:
                        raise ValueError('Invalid cell terrain while rendering game image.')

                # Draw the rectangle with the right color for the terrains
                # rect is play area, color, and (left point, top point, width, height)

                pg.draw.rect(self.play_area, cell_color, (c_ * self.cell_size, r_ * self.cell_size,
                                                          self.cell_size, self.cell_size))
                self.game_screen.blit(self.play_area, self.play_area.get_rect())

        smallText = pg.font.Font("freesansbold.ttf", 60)

        pg.draw.rect(self.game_screen, (0, 100, 255), (810, 80, 160, 95), 5)
        pg.draw.rect(self.game_screen, (255, 255, 255), (810, 80, 160, 95))
        textSurf, textRect = self.text_objects("" + str(self.env.total_score), smallText)
        textRect.center = ((810 + (160 / 2)), (80 + (95 / 2)))
        self.game_screen.blit(textSurf, textRect)

        pg.draw.rect(self.game_screen, (252, 186, 3), (810, 375, 160, 95), 5)
        pg.draw.rect(self.game_screen, (255, 255, 255), (810, 375, 160, 95))
        textSurf, textRect = self.text_objects("" + str(50 + self.env.energy_used), smallText)
        textRect.center = ((810 + (160 / 2)), (375 + (95 / 2)))
        self.game_screen.blit(textSurf, textRect)

        #Displaying images
        for r_ in range(self.env.grid.rows):
            for c_ in range(self.env.grid.cols):
                if self.FOGOFWAR == True:
                    cell = self.env.grid.visible_grid[r_][c_]
                    cell_val = self.env.grid.get_human_cell_value(r_, c_, self.FOGOFWAR)

                    # Trying to display images

                    if [r_, c_] not in self.env.grid.shown:
                        if cell.terrain == Terrains.wall:
                            self.game_screen.blit(wall_d_texture, (c_ * 80, r_ * 80))
                        elif cell.terrain == Terrains.hospital:
                            self.game_screen.blit(hospital_d_texture, (c_ * 80, r_ * 80))
                        elif cell.terrain == Terrains.fire:
                            self.game_screen.blit(fire_d_texture, (c_ * 80, r_ * 80))
                        if cell_val == "I":
                            self.game_screen.blit(patient_d_texture, (c_ * 80, r_ * 80))
                    else:
                        if cell.terrain == Terrains.wall:
                            self.game_screen.blit(wall_b_texture, (c_ * 80, r_ * 80))
                        elif cell.terrain == Terrains.hospital:
                            self.game_screen.blit(hospital_b_texture, (c_ * 80, r_ * 80))
                        elif cell.terrain == Terrains.fire:
                            self.game_screen.blit(fire_b_texture, (c_ * 80, r_ * 80))
                        if cell_val == "N":
                            self.game_screen.blit(zombing_texture, (c_*80, r_*80))
                        if cell_val == "Z":
                            if cell.zombie_pedestrian_orientation == 0:
                                self.game_screen.blit(zombie_texture_up, (c_ * 80, r_ * 80))
                            elif cell.zombie_pedestrian_orientation == 1:
                                self.game_screen.blit(zombie_texture_right, (c_ * 80, r_ * 80))
                            elif cell.zombie_pedestrian_orientation == 2:
                                self.game_screen.blit(zombie_texture_down, (c_ * 80, r_ * 80))
                            elif cell.zombie_pedestrian_orientation == 3:
                                self.game_screen.blit(zombie_texture_left, (c_ * 80, r_ * 80))
                        if cell_val == "^":
                            self.game_screen.blit(ambulance_texture_up, (c_ * 80, r_ * 80))
                        elif cell_val == ">":
                            self.game_screen.blit(ambulance_texture_right, (c_ * 80, r_ * 80))
                        elif cell_val == "v":
                            self.game_screen.blit(ambulance_texture_down, (c_ * 80, r_ * 80))
                        elif cell_val == "<":
                            self.game_screen.blit(ambulance_texture_left, (c_ * 80, r_ * 80))
                        elif cell_val == "P":
                            if cell.zombie_pedestrian_orientation == 0:
                                self.game_screen.blit(pedestrian_texture_up, (c_ * 80, r_ * 80))
                            elif cell.zombie_pedestrian_orientation == 1:
                                self.game_screen.blit(pedestrian_texture_right, (c_ * 80, r_ * 80))
                            elif cell.zombie_pedestrian_orientation == 2:
                                self.game_screen.blit(pedestrian_texture_down, (c_ * 80, r_ * 80))
                            elif cell.zombie_pedestrian_orientation == 3:
                                self.game_screen.blit(pedestrian_texture_left, (c_ * 80, r_ * 80))
                        elif cell_val == "^I":
                            self.game_screen.blit(ambulance_texture_up_full, (c_*80, r_*80))
                        elif cell_val == ">I":
                            self.game_screen.blit(ambulance_texture_right_full, (c_*80, r_*80))
                        elif cell_val == "vI":
                            self.game_screen.blit(ambulance_texture_down_full, (c_*80, r_*80))
                        elif cell_val == "<I":
                            self.game_screen.blit(ambulance_texture_left_full, (c_*80, r_*80))
                        elif cell_val == "^N":
                            self.game_screen.blit(ambulance_texture_up_full, (c_*80, r_*80))
                        elif cell_val == ">N":
                            self.game_screen.blit(ambulance_texture_right_full, (c_*80, r_*80))
                        elif cell_val == "vN":
                            self.game_screen.blit(ambulance_texture_down_full, (c_*80, r_*80))
                        elif cell_val == "<N":
                            self.game_screen.blit(ambulance_texture_left_full, (c_*80, r_*80))
                        if cell_val == "I":
                            self.game_screen.blit(patient_texture, (c_ * 80, r_ * 80))
                else:

                    cell = self.env.grid.grid[r_][c_]
                    cell_val = self.env.grid.get_human_cell_value(r_, c_, self.FOGOFWAR)

                    # Trying to display images

                    if cell.terrain == Terrains.wall:
                        self.game_screen.blit(wall_b_texture, (c_ * 80, r_ * 80))
                    elif cell.terrain == Terrains.hospital:
                        self.game_screen.blit(hospital_b_texture, (c_ * 80, r_ * 80))
                    elif cell.terrain == Terrains.fire:
                        self.game_screen.blit(fire_b_texture, (c_ * 80, r_ * 80))
                    if cell_val == "N":
                        self.game_screen.blit(zombing_texture, (c_ * 80, r_ * 80))
                    if cell_val == "Z":
                        if cell.zombie_pedestrian_orientation == 0:
                            self.game_screen.blit(zombie_texture_up, (c_ * 80, r_ * 80))
                        elif cell.zombie_pedestrian_orientation == 1:
                            self.game_screen.blit(zombie_texture_right, (c_ * 80, r_ * 80))
                        elif cell.zombie_pedestrian_orientation == 2:
                            self.game_screen.blit(zombie_texture_down, (c_ * 80, r_ * 80))
                        elif cell.zombie_pedestrian_orientation == 3:
                            self.game_screen.blit(zombie_texture_left, (c_ * 80, r_ * 80))
                    if cell_val == "^":
                        self.game_screen.blit(ambulance_texture_up, (c_ * 80, r_ * 80))
                    elif cell_val == ">":
                        self.game_screen.blit(ambulance_texture_right, (c_ * 80, r_ * 80))
                    elif cell_val == "v":
                        self.game_screen.blit(ambulance_texture_down, (c_ * 80, r_ * 80))
                    elif cell_val == "<":
                        self.game_screen.blit(ambulance_texture_left, (c_ * 80, r_ * 80))
                    elif cell_val == "P":
                        if cell.zombie_pedestrian_orientation == 0:
                            self.game_screen.blit(pedestrian_texture_up, (c_ * 80, r_ * 80))
                        elif cell.zombie_pedestrian_orientation == 1:
                            self.game_screen.blit(pedestrian_texture_right, (c_ * 80, r_ * 80))
                        elif cell.zombie_pedestrian_orientation == 2:
                            self.game_screen.blit(pedestrian_texture_down, (c_ * 80, r_ * 80))
                        elif cell.zombie_pedestrian_orientation == 3:
                            self.game_screen.blit(pedestrian_texture_left, (c_ * 80, r_ * 80))
                    elif cell_val == "^I":
                        self.game_screen.blit(ambulance_texture_up_full, (c_ * 80, r_ * 80))
                    elif cell_val == ">I":
                        self.game_screen.blit(ambulance_texture_right_full, (c_ * 80, r_ * 80))
                    elif cell_val == "vI":
                        self.game_screen.blit(ambulance_texture_down_full, (c_ * 80, r_ * 80))
                    elif cell_val == "<I":
                        self.game_screen.blit(ambulance_texture_left_full, (c_ * 80, r_ * 80))
                    elif cell_val == "^N":
                        self.game_screen.blit(ambulance_texture_up_full, (c_ * 80, r_ * 80))
                    elif cell_val == ">N":
                        self.game_screen.blit(ambulance_texture_right_full, (c_ * 80, r_ * 80))
                    elif cell_val == "vN":
                        self.game_screen.blit(ambulance_texture_down_full, (c_ * 80, r_ * 80))
                    elif cell_val == "<N":
                        self.game_screen.blit(ambulance_texture_left_full, (c_ * 80, r_ * 80))
                    if cell_val == "I":
                        self.game_screen.blit(patient_texture, (c_ * 80, r_ * 80))
        exit_image = pg.image.load("assets/UI/exit.png")
        score_image = pg.image.load("assets/UI/score.png")
        energy_image = pg.image.load("assets/UI/energy.png")
        score_image = pg.transform.smoothscale(score_image, (175, 75))
        self.game_screen.blit(score_image, (800, 0))
        energy_image = pg.transform.smoothscale(energy_image, (200, 200))
        self.game_screen.blit(energy_image, (790, 200))
        exit_image = pg.transform.smoothscale(exit_image, (170, 65))
        self.game_screen.blit(exit_image, (805, 700))
        self.area = pg.Rect(805, 700, 170, 65)

        pg.display.update()

    def run(self):

        print('Starting new game with human play!')
        # Set up pygame loop for game, capture actions, and redraw the screen on action
        self.env.reset()
        #self.env.render_mode = PlayTypes.machine  # We'll draw the screen manually and not render each turn
        pg.init()
        self.game_screen = pg.display.set_mode((1000, 800))
        pg.display.set_caption('SGW Human Play')
        self.play_area = pg.Surface((self.env.grid.rows * self.cell_size, self.env.grid.cols * self.cell_size))
        self.play_area.fill(pg.color.Color(MapColors.play_area.value))
        self.game_screen.fill(pg.color.Color(MapColors.game_screen.value))

        """Tk().wm_withdraw()  # to hide the main window
        messagebox.showinfo('Rules & Information', "1. Fog of War: This game is based off a city disaster, so your map starts out with "
                                                   "perfect knowledge of where fires, walls, and hospitals are, but as the "
                                                   "situation progresses, the environment will change, so in the fog of war, "
                                                   "tiles are displayed as their last seen value \n "
                                                   "    - Injured will always be shown, as we assume"
                                                   "they have sent out a call for help and will remain stationary \n"
                                                   "    - Humans and zombies outside your view radius will not be shown "
                                                   "on a last seen basis as they are guaranteed to move \n \n"
                                                    "2. Changing Environment: As the player moves, the environment will also"
                                                   " change. Fires can spread to surrounding floor tiles, walls can fall, and most importantly, humans "
                                                   "and zombies can move. \n "
                                                   "    - When fire spreads to a floor tile with a zombing, zombie, or pedestrian, the "
                                                   "fire will destroy the zombing, zombie, or pedestrian\n"
                                                   "    - Zombies and pedestrians are limited to moving to places without other objects, ex. fire, injured, hospitals, zombings, etc. \n \n"
                                                    "3. Infection: When zombies enter the view radius of pedestrians, they will "
                                                   "chase the pedestrians and the pedestrians will run away, but zombies "
                                                   "in a chasing state move quicker than pedestrians, and thus will (nearly) always catch "
                                                   "the pedestrian. Once the zombie catches the pedestrian, the pedestrian is infected"
                                                   " and becomes a zombing for 10 turns before turning into a zombie. \n"
                                                   "    - Zombings are essentially injured people, except they have a time limit before they "
                                                   "can't be saved")
        messagebox.showinfo('Rules & Information', "2. Points: \n"
                                                   "    Squishing Pedestrian: -5 \n"
                                                   "    Squishing Zombies: 0 \n"
                                                   "    Squishing Injured or Zombings: -5\n"
                                                   "    Delivering Zombings or Injured: 20 \n"
                                                   "    Entering Fire: -2 \n")
"""
        self._draw_screen()

        # Main game loop, capture window events, actions, and redraw the screen with updates until game over
        game_exit = False
        while not game_exit:
            for event in pg.event.get():

                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button.
                        if self.area.collidepoint(event.pos):
                            game_exit = True
                    # Exit game upon window close


                # Exit game upon window close
                if event.type == pg.QUIT:
                    game_exit = True


                elif self.turn < self.max_turn and not self.is_game_over:

                    # Execute main turn logic
                    # Start by getting the action, only process a turn if there is an actual action
                    # Catch the player inputs, capture key stroke
                    action = None
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            print('escape key exit')
                            game_exit = True

                        if event.key in [pg.K_w, pg.K_SPACE, pg.K_UP, pg.K_3]:
                            action = Actions.step_forward
                        if event.key in [pg.K_a, pg.K_LEFT, pg.K_1]:
                            action = Actions.turn_left
                        if event.key in [pg.K_d, pg.K_RIGHT, pg.K_2]:
                            action = Actions.turn_right
                        if event.key in [pg.K_s, pg.K_DOWN, pg.K_0]:
                            action = Actions.none

                    if action is not None:
                        if action in [Actions.step_forward, Actions.turn_right, Actions.turn_left, Actions.none]:
                            # We have a valid action, so let's process it and update the screen
                            encoded_action = self.env.encode_raw_action(action)  # Ensures clean action
                            action_decoded = self.env.decode_raw_action(encoded_action)

                            # Take a step, print the status, render the new state
                            observation, reward, done, info = self.env.step(encoded_action)
                            self.env.pp_info()
                            self.is_game_over = done

                            # Write action and stuff out to disk.
                            data_to_log = {
                                'game_id': str(self.GAME_ID),
                                'turn': self.turn,
                                'raw_action': action,
                                'action': action_decoded,
                                'reward': reward,
                                'game_done': done,
                                'game_info': {k.replace('.', '_'): v for (k, v) in info.items()},
                                'raw_state': observation
                            }
                            with open(self.DATA_LOG_FILE_NAME, 'a') as f_:
                                f_.write(json.dumps(data_to_log) + '\n')
                                f_.close()

                            # Tick up turn
                            self.turn += 1
                            if self.is_game_over:
                                print('if game over')
                                game_exit = True

                            # Draw the screen
                            if not self.is_game_over:
                                self._draw_screen()

                else:
                    # Else end the game
                    print('else ended game')
                    game_exit = True
        pg.quit()
        self.done()
