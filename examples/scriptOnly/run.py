"""
ioHub
.. file: ioHub/examples/simpleScriptOnly/run.py

-------------------------------------------------------------------------------

simpleScriptOnly
++++++++++++++++

Overview:
---------

This script is implemented using psychopy and the core ioHubConnection class 
only. It shows how to integrate the ioHub into a PsychoPy script in a minimal
way, without the need to use any of the ioHub's extra features such as automatic 
event storage.

To Run:
-------

1. Ensure you have followed the ioHub installation instructions 
   at http://www.github.com/isolver/iohub/wiki
2. Open a command prompt to the directory containing this file.
3. Start the test program by running:
   python.exe run.py

"""
from psychopy import visual, core
from ioHub.constants import EventConstants
from ioHub.devices import Computer
from ioHub import OrderedDict,quickStartHubServer

# PLEASE REMEMBER , THE SCREEN ORIGIN IS ALWAYS IN THE CENTER OF THE SCREEN,
# REGARDLESS OF THE COORDINATE SPACE YOU ARE RUNNING IN. THIS MEANS 0,0 IS SCREEN CENTER,
# -x_min, -y_min is the screen bottom left
# +x_max, +y_max is the screen top right
#
# *** RIGHT NOW, ONLY PIXEL COORD SPACE IS SUPPORTED. THIS WILL BE FIXED SOON. ***

# create and start the ioHub Server Process, enabling the 
# the default ioHub devices: Keyboard, Mouse, and Display.
# The first arg is the experiment code to use for the ioDataStore Event storage,
# the second arg is the session code to give to the current session of the 
# experiment. Session codes must be unique for a given experiment code within an
# ioDataStore hdf5 event file.
import random
io=quickStartHubServer("exp_code","sess_%d"%(random.randint(1,10000)))
        
# By default, keyboard, mouse, and display devices are created if you 
# do not pass any config info to the ioHubConnection class above.        
mouse=io.devices.mouse
display=io.devices.display
keyboard=io.devices.keyboard

# Lets switch to high priority on the psychopy process.
Computer.enableHighPriority()

# Create a psychopy window, full screen resolution, full screen mode, pix units,
# with no boarder, using the monitor default profile name used by ioHub, 
# which is created on the fly right now by the script. (ioHubDefault)
psychoWindow = visual.Window(display.getPixelResolution(), 
                             monitor=display.getPsychopyMonitorName(), 
                             units=display.getCoordinateType(), 
                             fullscr=True, 
                             allowGUI=False,
                             screen=display.getIndex())

# Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
mouse.setSystemCursorVisibility(False)

# Set the mouse position to 0,0, which means the 'center' of the screen.
mouse.setPosition((0.0,0.0))

# Create an ordered dictionary of psychopy stimuli. An ordered dictionary is 
# one that returns keys in the order they are added, you you can use it to 
# reference stim by a name or by 'zorder'

psychoStim=OrderedDict()

psychoStim['grating'] = visual.PatchStim(psychoWindow, mask="circle", 
                                        size=75,pos=[-100,0], sf=.075)

psychoStim['fixation'] =visual.PatchStim(psychoWindow, size=25, 
                                        pos=[0,0], sf=0,  
                                        color=[-1,-1,-1],
                                        colorSpace='rgb')
                                        
psychoStim['mouseDot'] =visual.GratingStim(psychoWindow,tex=None,
                                            mask="gauss", 
                                            pos=mouse.getPosition(),
                                            size=(50,50),color='purple')

# Clear all events from the global event buffer, 
# and from the device level event buffers.
io.clearEvents('all')

[psychoStim[stimName].draw() for stimName in psychoStim]
psychoWindow.flip()
first_flip_time=Computer.currentSec()

display_index=display.getIndex()

QUIT_EXP=False
# Loop until we get a keyboard event with the space, Enter (Return), 
# or Escape key is pressed.
while QUIT_EXP is False:

    # for each loop, update the grating phase
    # advance phase by 0.05 of a cycle
    psychoStim['grating'].setPhase(0.05, '+')

    # and update the mouse contingent gaussian based on the 
    # current mouse location
    mp,di=mouse.getPosition(return_display_index=True)
    if di == display_index:
        psychoStim['mouseDot'].setPos(mp)

    #draw all the stim
    [psychoStim[stimName].draw() for stimName in psychoStim]

    # flip the psychopy window buffers, so the 
    # stim changes you just made get displayed.
    psychoWindow.flip()
    # It is on this side of the call that you know the changes have 
    # been displayed, so you can make a call to one of the built-in time 
    # methods and get the event time of the flip, as the built in
    # time methods represent both experiment process and ioHub server
    # process time. NOTE: Integration between the ioHub times and 
    # psychopy clock times needs to be done, so for now when using ioHub
    # you should use the ioHub times so that the event time fields
    # can be related to Computer.getTime() current time readings.
    flip_time=Computer.currentSec()

    # for each new keyboard press event, check if it matches one
    # of the end example keys.
    for k in keyboard.getEvents(EventConstants.KEYBOARD_PRESS):
        if k.key in ['SPACE','RETURN','ESCAPE']:
            print 'Quit key pressed: ',k.key
            QUIT_EXP=True

    io.clearEvents('all')
    
print "You played around with the mouse cursor for {0} seconds.".format(
                                            k.time-first_flip_time)
print ''

# wait 250 msec before ending the experiment 
# (makes it feel less abrupt after you press the key)
actualDelay=io.wait(0.250)
print "Delay requested %.6f, actual delay %.6f, Diff: %.6f"%(
                                        0.250,actualDelay,actualDelay-0.250)
print ''

# for fun, test getting a bunch of events at once, 
# likely causing a mutlipacket getEvents() since we have not cleared the
# event buffer or retrieved events from anything but the keyboard since
# the start.
stime = Computer.currentSec()
events=io.getEvents()
etime=Computer.currentSec()
print 'event count: ', len(events),' delay (msec): ',(etime-stime)*1000.0

# close neccessary files / objects, 'disable high priority.
Computer.disableHighPriority()
 
psychoWindow.close()

# be sure to shutdown your ioHub server!
io.quit()
core.quit()
### End of experiment logic

