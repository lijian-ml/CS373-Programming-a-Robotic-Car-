# ----------
# Part Four
#
# Again, you'll track down and recover the runaway Traxbot. 
# But this time, your speed will be about the same as the runaway bot. 
# This may require more careful planning than you used last time.
#
# ----------
# YOUR JOB
#
# Complete the next_move function, similar to how you did last time. 
#
# ----------
# GRADING
# 
# Same as part 3. Again, try to catch the target in as few steps as possible.

from robot import *
from math import *
from matrix import *
from kalman import *
import random
import time

def x_state(measure, dt=1.0, n=5):
    nn = len(measure)
    parameters = [[0 for j in range(nn)] for i in range(n)]
    parameters[0] = [measure[i][0] for i in range(nn)]
    parameters[1] = [measure[i][1] for i in range(nn)]
    parameters[2] = [0] + [sqrt((parameters[0][i+1]-parameters[0][i])**2+(parameters[1][i+1]-parameters[1][i])**2)/dt for i in range(len(parameters[0])-1)]
    parameters[3] = [0] + [atan2(parameters[1][i+1]-parameters[1][i], parameters[0][i+1]-parameters[0][i]) for i in range(len(parameters[0])-1)]
    parameters[4] = [0,0] + [(parameters[3][i]-parameters[3][i-1])/dt for i in range(2,len(parameters[0]))]

    return matrix([[parameters[0][-1]],
                   [parameters[1][-1]],
                   [parameters[2][-1]],
                   [parameters[3][-1]],
                   [parameters[4][-1]]])

def predict_state(x, dt=1.0):
    v = x.value[2][0]
    theta = x.value[3][0]
    w = x.value[4][0]

    X = matrix([[x.value[0][0]+v*dt*cos(theta+w*dt)],
                [x.value[1][0]+v*dt*sin(theta+w*dt)],
                [v],
                [theta+w*dt],
                [w]])

    return X

def F_mat(x, dt=1.0):
    v = x.value[2][0]
    theta = x.value[3][0]
    w = x.value[4][0]

    F = matrix([[1,  0, dt*cos(theta+w*dt), -v*dt*sin(theta+w*dt),  -v*dt**2*sin(theta+w*dt)],
                [0,  1, dt*sin(theta+w*dt),  v*dt*cos(theta+w*dt),   v*dt**2*cos(theta+w*dt)],
                [0,  0,        1,                    0,                                    0],
                [0,  0,        0,                    1,                                   dt],
                [0,  0,        0,                    0,                                    1]])
    return F

def next_move(hunter_position, hunter_heading, target_measurement, max_distance, OTHER = None):
    # This function will be called after each time the target moves. 
    dt =1.0

    if OTHER ==None :
        target_position = target_measurement
        turning = get_heading(hunter_position, target_position)-hunter_heading
        distance = max_distance
        OTHER = [target_measurement]
        return turning, distance, OTHER
    elif len(OTHER) == 1:
        target_position = (2*target_measurement[0]-OTHER[0][0], 2*target_measurement[1]-OTHER[0][1])
        turning = get_heading(hunter_position, target_position)-hunter_heading
        distance = max_distance
        OTHER.append(target_measurement)
        return turning, distance, OTHER
    elif len(OTHER) == 2:
        OTHER.append(target_measurement)
        x = x_state(OTHER)
        OTHER = [[e for e in OTHER], x, 0]
        x = predict_state(x)
        target_position = (x.value[0][0], x.value[1][0])
        turning = get_heading(hunter_position, target_position)-hunter_heading
        distance = max_distance
        return turning, distance, OTHER
    kalman1 = kalman(matrix([[0] for i in range(5)]))
    x = OTHER[1]
    P = matrix([[1000.0 if i==j else 0.0 for j in range(len(x.value))] for i in range(len(x.value))]) if OTHER[2]==0 else OTHER[2]
    z = target_measurement
    F = F_mat(x)
    x, P = kalman1.extended_kalman_filter(predict_state(OTHER[1]), z, F, P)
    OTHER = [OTHER[0]+[target_measurement], x, P]
    x = predict_state(x)
    target_position = (x.value[0][0], x.value[1][0])
    if distance_between(hunter_position, target_position)>max_distance:
        x = predict_state(x)
        target_position = (x.value[0][0], x.value[1][0])
        turning = angle_trunc(get_heading(hunter_position, target_position)-hunter_heading)
        distance = max_distance
        return turning, distance, OTHER
    turning = angle_trunc(get_heading(hunter_position, target_position)-hunter_heading)
    distance = distance_between(hunter_position, target_position)
    # The OTHER variable is a place for you to store any historical information about
    # the progress of the hunt (or maybe some localization information). Your return format
    # must be as follows in order to be graded properly.
    return turning, distance, OTHER

def distance_between(point1, point2):
    """Computes distance between point1 and point2. Points are (x, y) pairs."""
    x1, y1 = point1
    x2, y2 = point2
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def demo_grading(hunter_bot, target_bot, next_move_fcn, OTHER = None):
    """Returns True if your next_move_fcn successfully guides the hunter_bot
    to the target_bot. This function is here to help you understand how we 
    will grade your submission."""
    max_distance = 0.98 * target_bot.distance # 0.98 is an example. It will change.
    separation_tolerance = 0.02 * target_bot.distance # hunter must be within 0.02 step size to catch target
    caught = False
    ctr = 0

    # We will use your next_move_fcn until we catch the target or time expires.
    while not caught and ctr < 100:

        # Check to see if the hunter has caught the target.
        hunter_position = (hunter_bot.x, hunter_bot.y)
        target_position = (target_bot.x, target_bot.y)
        separation = distance_between(hunter_position, target_position)
        print (separation)
        if separation < separation_tolerance:
            print "You got it right! It took you ", ctr, " steps to catch the target."
            caught = True

        # The target broadcasts its noisy measurement
        target_measurement = target_bot.sense()

        # This is where YOUR function will be called.
        turning, distance, OTHER = next_move_fcn(hunter_position, hunter_bot.heading, target_measurement, max_distance, OTHER)
        
        # Don't try to move faster than allowed!
        if distance > max_distance:
            distance = max_distance

        # We move the hunter according to your instructions
        hunter_bot.move(turning, distance)

        # The target continues its (nearly) circular motion.
        target_bot.move_in_circle()

        ctr += 1            
        if ctr >= 100:
            print "It took too many steps to catch the target."
    return caught

def demo_grading2(hunter_bot, target_bot, next_move_fcn, OTHER = None):
    """Returns True if your next_move_fcn successfully guides the hunter_bot
    to the target_bot. This function is here to help you understand how we 
    will grade your submission."""
    max_distance = 0.98 * target_bot.distance # 0.98 is an example. It will change.
    separation_tolerance = 0.02 * target_bot.distance # hunter must be within 0.02 step size to catch target
    caught = False
    ctr = 0
    #For Visualization
    import turtle
    window = turtle.Screen()
    window.bgcolor('white')
    chaser_robot = turtle.Turtle()
    chaser_robot.shape('arrow')
    chaser_robot.color('blue')
    chaser_robot.resizemode('user')
    chaser_robot.shapesize(0.3, 0.3, 0.3)
    broken_robot = turtle.Turtle()
    broken_robot.shape('turtle')
    broken_robot.color('green')
    broken_robot.resizemode('user')
    broken_robot.shapesize(0.3, 0.3, 0.3)
    size_multiplier = 15.0 #change size of animation
    chaser_robot.hideturtle()
    chaser_robot.penup()
    chaser_robot.goto(hunter_bot.x*size_multiplier, hunter_bot.y*size_multiplier-100)
    chaser_robot.showturtle()
    broken_robot.hideturtle()
    broken_robot.penup()
    broken_robot.goto(target_bot.x*size_multiplier, target_bot.y*size_multiplier-100)
    broken_robot.showturtle()
    measuredbroken_robot = turtle.Turtle()
    measuredbroken_robot.shape('circle')
    measuredbroken_robot.color('red')
    measuredbroken_robot.penup()
    measuredbroken_robot.resizemode('user')
    measuredbroken_robot.shapesize(0.1, 0.1, 0.1)
    broken_robot.pendown()
    chaser_robot.pendown()
    #End of Visualization
    # We will use your next_move_fcn until we catch the target or time expires.
    while not caught and ctr < 100:
        # Check to see if the hunter has caught the target.
        hunter_position = (hunter_bot.x, hunter_bot.y)
        target_position = (target_bot.x, target_bot.y)
        separation = distance_between(hunter_position, target_position)
        if separation < separation_tolerance:
            print "You got it right! It took you ", ctr, " steps to catch the target."
            caught = True

        # The target broadcasts its noisy measurement
        target_measurement = target_bot.sense()

        # This is where YOUR function will be called.
        turning, distance, OTHER = next_move_fcn(hunter_position, hunter_bot.heading, target_measurement, max_distance, OTHER)

        # Don't try to move faster than allowed!
        if distance > max_distance:
            distance = max_distance

        # We move the hunter according to your instructions
        hunter_bot.move(turning, distance)

        # The target continues its (nearly) circular motion.
        target_bot.move_in_circle()
        #Visualize it
        measuredbroken_robot.setheading(target_bot.heading*180/pi)
        measuredbroken_robot.goto(target_measurement[0]*size_multiplier, target_measurement[1]*size_multiplier-100)
        measuredbroken_robot.stamp()
        broken_robot.setheading(target_bot.heading*180/pi)
        broken_robot.goto(target_bot.x*size_multiplier, target_bot.y*size_multiplier-100)
        chaser_robot.setheading(hunter_bot.heading*180/pi)
        chaser_robot.goto(hunter_bot.x*size_multiplier, hunter_bot.y*size_multiplier-100)
        #End of visualization
        #time.sleep(0.5)
        ctr += 1            
        if ctr >= 100:
            print "It took too many steps to catch the target."
    time.sleep(1)
    return caught

def angle_trunc(a):
    """This maps all angles to a domain of [-pi, pi]"""
    while a < 0.0:
        a += pi * 2
    return ((a + pi) % (pi * 2)) - pi

def get_heading(hunter_position, target_position):
    """Returns the angle, in radians, between the target and hunter positions"""
    hunter_x, hunter_y = hunter_position
    target_x, target_y = target_position
    heading = atan2(target_y - hunter_y, target_x - hunter_x)
    heading = angle_trunc(heading)
    return heading

def naive_next_move(hunter_position, hunter_heading, target_measurement, max_distance, OTHER):
    """This strategy always tries to steer the hunter directly towards where the target last
    said it was and then moves forwards at full speed. This strategy also keeps track of all 
    the target measurements, hunter positions, and hunter headings over time, but it doesn't 
    do anything with that information."""
    if not OTHER: # first time calling this function, set up my OTHER variables.
        measurements = [target_measurement]
        hunter_positions = [hunter_position]
        hunter_headings = [hunter_heading]
        OTHER = (measurements, hunter_positions, hunter_headings) # now I can keep track of history
    else: # not the first time, update my history
        OTHER[0].append(target_measurement)
        OTHER[1].append(hunter_position)
        OTHER[2].append(hunter_heading)
        measurements, hunter_positions, hunter_headings = OTHER # now I can always refer to these variables
    
    heading_to_target = get_heading(hunter_position, target_measurement)
    heading_difference = heading_to_target - hunter_heading
    turning =  heading_difference # turn towards the target
    distance = max_distance # full speed ahead!
    return turning, distance, OTHER

target = robot(0.0, 10.0, 0.0, 2*pi / 30, 1.5)
measurement_noise = 0.02*target.distance
target.set_noise(0.0, 0.0, measurement_noise)

hunter = robot(-10.0, -10.0, 0.0)

print demo_grading2(hunter, target, next_move)


