import argparse
import sys
#import pdb
import gym
from gym import wrappers, logger
import numpy
from random import randint

move = 1
own_shot = 0

#object is the 
class Agent(object):
    """The world's simplest agent!"""
    def __init__(self, action_space):
        
        self.action_space = action_space
    
    # You should modify this function
    def act(self, observation, reward, done):
        global move
        global own_shot
        danger = []         # coor of laser
        ship_coor  = []     # will hold the coordinates of the 
        barrier= []         # coor for barriers
        aliens = []         # coordinates of aliens
        alien_size = 10     # rough n x n size of alien
        alien_blocked = [[0 for x in range(210)] for y in range (210)]  #works like a hashset for the alien blocks
        """
        will look over the board getting coordinates of stuff using colors 
        when it hits a space with a non-black color (0, 0, 0)
        it will determine its color and do the appropriate stuff
        """
        y = 0           # determine y coordinate
        for layer in observation:
        
            x = 0
            for spot in layer:
                color = find_color(spot)

                #found laser will see if its a new laser to add or not
                if(color == "Laser"):
                    if(x != own_shot):
                        danger.append([(y, x)])
                    
                # will make single alien block representing entire alien
                # will result in representation being slightly off
                # but is much easier then putting all the pieces together
                elif(color == "Alien"):
                    block = blocking(alien_size, x, y, alien_blocked)
                    if (block != "Blocked area"):              
                        aliens.append(block)
                        for space in block:
                            #updates alien_blocked
                            alien_blocked[space[0]][space[1]] = 1


                elif(color == "Ship"):
                    # first ship tile it gets will be the blaster
                    #160 is to prevent it from using the scoreboard
                    if(y > 160):
                        ship_coor.append([y, x])

                # will get enire barriers and then check them later
                elif(color == "Barrier"):
                    barrier.append([(y, x)])
                x = x + 1

            y = y + 1

        """
        Will have important info ready to go
        Will know decide what to do
        Will first avoid being shot unless shot will hit barrier
        Will prevent getting stuck on the edges
        Will fire at any chances it can
        """
        laser_close = False
        behind_barrier = False
        spam = False
        percision = False
        ship_length = 10
        
        laser_close = in_range(ship_length * (2), danger, ship_coor[0][1])
        behind_barrier = in_range(ship_length, barrier, ship_coor[0][1])
        priority_targets = [] 
        for alien in aliens:
            if(alien[0][0] >= 120):
                priority_targets.append([(alien[0][0], alien[0][1])])

        closest = (9, 9)
        if(len(priority_targets) != 0):
            closest_target_index = 0
            counter = 0
            for target in priority_targets:
                if(priority_targets[closest_target_index][0] < priority_targets[counter][0]):
                    closest_target_index = counter                   
                counter = counter + 1
            closest = priority_targets[closest_target_index][0]

        #threat has been determined
        take_shot = fire(ship_coor[0][1], aliens)
        #will find where closest laser is an avoid it 
        #problem being no id between friend and foe shots
        
        #if there is a danger if close it will flip its direction
        if(ship_coor[0][1] >= 115):
            move = 0
        elif(ship_coor[0][1] <= 40):
            move = 1

        elif(laser_close and (ship_coor[0][1] + ship_length < 115) and (ship_coor[0][1] - ship_length > 40)): 
            #laser is to the right of the ship move left
            #will ignore laser if its too close
            too_close =  False
            
            actual_danger = []
            for shot in danger:
                #hieght check 
                if(shot[0][0] >= 150 and shot[0][0] <= 170):
                    #left side check
                    actual_danger.append(shot)
                    too_close = True

            #doesn't check where laser is actually going
            #0 = left
            #1 = right
            right_laser = False
            left_laser = False
            for shot in actual_danger:
                #right laser
                if(shot[0][1] > ship_coor[0][1]):
                    right_laser = True
                elif(shot[0][1] < ship_coor[0][1]):
                    left_laser = True
    
            if(right_laser and left_laser):
                move = 2

            elif(too_close and move == 0):
                if(right_laser):
                    move = 0
                else:
                    move = 1
            elif(too_close and move == 1):
                if(left_laser):
                    move = 1
                else:
                    move = 0
        
        #will have a closest target
        elif(len(priority_targets) != 0):
            if(ship_coor[0][1] > closest[1]):
                move = 0
            elif(ship_coor[0][1] < closest[1]):
                move = 1

        #when few aliens will persue 
        elif(len(aliens) <= 12):
            next_target = find_closest(aliens, ship_coor[0][0], ship_coor[0][1])    
            if(next_target[1] > ship_coor[0][1]):
                move = 1
            else:
                move = 0

        if(take_shot):
            #return fire
            own_shot = ship_coor[0][1] + 1
            if(move == 0):
                return 5
            elif(move == 1):
                return 4
            else:
                return 1
        else:
            if(move == 0):
                return 3
            elif(move == 1):
                return 2
            else:
                return 0

"""
Determines if there is an alien to shoot at given a list of aliens
and the current x position
"""
def fire(start_x, aliens):
    for alien in aliens:
        if((alien[2][1] < start_x) and (start_x < alien[6][1])):
            return True
                
    return False
"""
Finds the next closest enemy and returns its coordinates
Also works for finding closest laser
"""
def find_closest(aliens, start_x, start_y):
    top_dist = 9999999
    top_coor = []
    for alien in aliens:
        distance = ((alien[0][0] - start_y) ** 2 + (alien[0][1] - start_x) ** 2) ** (1/2)
        if(distance < top_dist):
            top_dist = distance
            
            top_coor = (alien[0][0], alien[0][1])

    return top_coor 



"""
Takes in an array of coordinates of some entity and sees if its within "range" of another
This can range from laser close to ship, to the barriers in front of the ship
Or an alien in range of the ship or other cases
[y, x]
"""
def in_range(far, find_array, start_x):
    for coor in find_array:
        if(start_x - far <= coor[0][1] and coor[0][1] <= start_x + far):
            return True
    #default value if nothing found
    return False
    
"""
Blocks off an area to represent an alien
Is slightly off model but works for representation needs
Prevents multiple of the same aliens with alien_blocked
If it creates a space that has already been blocked it will stop
As all aliens have a similair if not same total width and hieght
"""
def blocking(far, start_x, start_y, alien_blocked):
    block_color = []
        
    alien_y = start_y
    for y in range(far):
        alien_x = start_x 
        for x in range(far):
            block_color.append((alien_y, alien_x))
            if(alien_blocked[alien_y][alien_x] == 1):
                return "Blocked area"
            alien_x = alien_x + 1
        alien_y = alien_y + 1

    return block_color

"""
Will look at the spot and determine its color and return its association
Last is for scoreboard, dirt(bottom of level), and the alien at the top of the screen 
"""
def find_color(spot):
    color0 = spot[0]
    color1 = spot[1]
    color2 = spot[2]
    if(color0 == 142 and color1 == 142 and color2 == 142):
        return "Laser"

    elif(color0 == 134 and color1 == 134 and color2 == 29):
        return "Alien"

    elif(color0 == 50 and color1 == 132 and color2 == 50):
        return "Ship"

    elif(color0 == 181 and color1 == 83 and color2 == 40):
        return "Barrier"
    
    else:
        return ""


    


"""
0 = No Op
1 = Fire
2 = Up
3 = Right
4 = left
5 = Down
6 = Up-Right
7 = Up-Left
8 = Down-Right
9 = Down-Left
10 = Up-Fire
11 = Right Fire
12 = Left Fire
13 = Down Fire
14 = Up Right Fire
15 = Up Left Fire
16 = Down Right Fire
17 = Down Left Fire
"""



## YOU MAY NOT MODIFY ANYTHING BELOW THIS LINE OR USE
## ANOTHER MAIN PROGRAM
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('env_id', nargs='?', default='SpaceInvaders-v0', help='Select the environment to run')
    args = parser.parse_args()

    # You can set the level to logger.DEBUG or logger.WARN if you
    # want to change the amount of output.
    logger.set_level(logger.INFO)
    env = gym.make(args.env_id)

    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    outdir = '1st-agent-results'
    
    
    env.seed(0)
    agent = Agent(env.action_space)

    episode_count = 100
    reward = 0
    done = False
    score = 0
    special_data = {}
    special_data['ale.lives'] = 3
    ob = env.reset()
    while not done:

        action = agent.act(ob, reward, done)
        ob, reward, done, _ = env.step(action)
        score += reward
        env.render()
            
# Close the env and write monitor result info to disk
print ("Your score: %d" % score)
env.close()
