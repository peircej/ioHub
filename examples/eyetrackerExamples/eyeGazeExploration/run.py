# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 09:21:11 2013

@author: isolver
"""
from psychopy import visual
import ioHub
from ioHub.devices import Computer
from ioHub.constants import EventConstants
from ioHub.util.experiment import ioHubExperimentRuntime
from ioHub.util import getCurrentDateTimeString
from ioHub.util.experiment import (DeviceEventTrigger, 
                                   ClearScreen, InstructionScreen, 
                                   FullScreenWindow)

class ExperimentRuntime(ioHubExperimentRuntime):
    def run(self,*args,**kwargs):
        """
        The run method contains your experiment logic. It is equal to what would be in your main psychopy experiment
        script.py file in a standard psychopy experiment setup. That is all there is too it really.
        """

        tracker=self.hub.devices.tracker
        display=self.hub.devices.display
        keyboard=self.hub.devices.kb
        mouse=self.hub.devices.mouse

        trial_count=self.getExperimentConfiguration()['trial_count']
        image_names=self.getExperimentConfiguration()['image_names']
        


        # eye trackers, like other devices, should be conected to when the
        # ioHub Server starts, so this next call is not needed, but should not
        # hurt anythnig either:
        tracker.setConnectionState(True)
        
        # run the eye tracker calibration routine before starting trials
        tracker.runSetupProcedure()

        # Create a psychopy window, full screen resolution, full screen mode, pix units.
        self.window = FullScreenWindow(display)

        # Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
        mouse.setSystemCursorVisibility(False)

        image_cache=dict()
        for i in image_names:
            iname='./images/{0}'.format(i)
            image_cache[i]=visual.ImageStim(self.window, image=iname, name=iname) 
            image_cache[i].draw()
        image_count=len(image_cache)
        self.window.clearBuffer()
        
        gaze_dot =visual.GratingStim(self.window,tex=None, mask="gauss", pos=(-2000,-2000),size=(100,100),color='green')

        # screen state that can be used to just clear the screen to blank.
        self.clearScreen=ClearScreen(self)
        self.clearScreen.setScreenColor((128,128,128))

        self.clearScreen.flip(text='EXPERIMENT_INIT')

        self.clearScreen.sendMessage("IO_HUB EXPERIMENT_INFO START")
        self.clearScreen.sendMessage("ioHub Experiment started {0}".format(getCurrentDateTimeString()))
        self.clearScreen.sendMessage("Experiment ID: {0}, Session ID: {1}".format(self.hub.experimentID,self.hub.experimentSessionID))
        self.clearScreen.sendMessage("Stimulus Screen ID: {0}, Size (pixels): {1}, CoordType: {2}".format(display.getIndex(),display.getPixelResolution(),display.getCoordinateType()))
        self.clearScreen.sendMessage("Calculated Pixels Per Degree: {0} x, {1} y".format(*display.getPixelsPerDegree()))        
        self.clearScreen.sendMessage("IO_HUB EXPERIMENT_INFO END")

        # Screen for showing text and waiting for a keyboard response or something
        instuction_text="Press Space Key".center(32)+'\n'+"to Start Experiment.".center(32)
        dtrigger=DeviceEventTrigger(keyboard,EventConstants.KEYBOARD_CHAR,{'key':'SPACE'})
        timeout=5*60.0
        self.instructionScreen=InstructionScreen(self,instuction_text,dtrigger,timeout)
        self.instructionScreen.setScreenColor((128,128,128))
        #flip_time,time_since_flip,event=self.instructionScreen.switchTo("CALIBRATION_WAIT")

        self.instructionScreen.setText(instuction_text)        
        self.instructionScreen.switchTo("START_EXPERIMENT_WAIT")

        self.experiment_running=True
        
        for t in range(trial_count):
            self.hub.clearEvents('all')
            instuction_text="Press Space Key To Start Trial %d"%t
            self.instructionScreen.setText(instuction_text)        
            self.instructionScreen.switchTo("START_TRIAL")

            tracker.setRecordingState(True)
            self.clearScreen.flip()
            self.hub.clearEvents('all')
    
            # Loop until we get a keyboard event
            runtrial=True
            while runtrial:
                gpos=tracker.getLastGazePosition()
                if gpos:
                    gaze_dot.setPos(gpos)
                    image_cache[i].draw()
                    gaze_dot.draw()
                else:
                    image_cache[i].draw()
                    
                flip_time=self.window.flip()          
                self.hub.sendMessageEvent("SYNCTIME %s"%(image_cache[i].name,),sec_time=flip_time)
                
                keys=keyboard.getEvents(EventConstants.KEYBOARD_CHAR)
                for key in keys:
                    if key.key == 'SPACE':
                       runtrial=False
                       break
                   
            self.clearScreen.flip(text='TRIAL_%d_DONE'%t)
            tracker.setRecordingState(False)

        self.clearScreen.flip(text='EXPERIMENT_COMPLETE')
        instuction_text="Experiment Finished".center(32)+'\n'+"Press 'SPACE' to Quit.".center(32)+'\n'+"Thank You.".center(32)
        self.instructionScreen.setText(instuction_text)        
        self.instructionScreen.switchTo("EXPERIMENT_COMPLETE_WAIT")

        # A key was pressed so exit experiment.
        # Wait 250 msec before ending the experiment 
        # (makes it feel less abrupt after you press the key to quit IMO)
        self.hub.wait(0.250)

        tracker.setConnectionState(False)
        
##################################################################

# The below code should never need to be changed, unless you want to get command
# line arguements or something. 

if __name__ == "__main__":
    def main(configurationDirectory):
        """
        Creates an instance of the ExperimentRuntime class, checks for an experiment config file name parameter passed in via
        command line, and launches the experiment logic.
        """
        import sys
        if len(sys.argv)>1:
            configFile=sys.argv[1]
            runtime=ExperimentRuntime(configurationDirectory, configFile)
        else:
            runtime=ExperimentRuntime(configurationDirectory, "experiment_config.yaml")
    
        runtime.start()
        
    configurationDirectory=ioHub.module_directory(main)

    # run the main function, which starts the experiment runtime
    main(configurationDirectory)

#
#        char_events=keyboard.getEvents(eventTypeID=EventConstants.KEYBOARD_CHAR)
#        if char_events:
#            for char in char_events:
#                if char.key in ['q','ESCAPE']:
#                    print 'Terminating test...'
#                    run=False
#                    result=peg.EgExit(byref(stEgControl))
#                    print 'EgExit: ',result
#                    break
#                elif char.key == 'v':
#                    print 'EgGetVersion REQUESTED .....'
#                    result=peg.EgGetVersion(byref(stEgControl))
#                    print 'EgGetVersion: ',result
#                elif char.key == 'p':
#                    print 'stEgControl STATE PRINTOUT REQUESTED  .....'
#                    for a in stEgControl.__slots__:
#                        v=getattr(stEgControl,a)
#                        print a,' = ', v
#                    print 'stEgControl STATE PRINTOUT DONE.'
#                elif char.key == 'r':
#                    print 'Toggle Data Recording REQUESTED .....'
#                    print 'current status: ',stEgControl.bTrackingActive
#                    stEgControl.bTrackingActive = not stEgControl.bTrackingActive
#                    result=peg.EgGetVersion(byref(stEgControl))
#                    print 'new recording status: ',stEgControl.bTrackingActive                    
#            io.clearEvents('all')        
#        
#        # check for new data
#        while stEgControl.iNPointsAvailable > 0:
#            result=peg.EgGetData(&stEgControl);
