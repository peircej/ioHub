"""
Tests the round trip time to request and reveive events from the I/O hub. 
The test is performed 'numEventRequests' times. Only responses with >= 1 event count
toward the tally.

See the experiment_config.yaml and ioHub_config.yaml files for changes you need to make 
for this program to run in your environement, as well as the ioHub github project README for
a list of dependencies and install instructions.

Only keyboard and mouse events are enabled for this test, so once you start the program and see
the example psychopy application, move the mouse around, press mouse button, press keyboard keys,
etc. This will generate events. After a minute or so, the default 1000 requests will be satisfied
and the test will exit, printing out some stat's.

If you get high MAX delays, turn off cloud drive apps, especially Google Drive; that fixes it for me.
"""
import ioHub.psychopyIOHubRuntime
from ioHub.psychopyIOHubRuntime import *
import numpy as N

class ExperimentRuntime(SimpleIOHubRuntime):
    def __init__(self,configFileDirectory, configFile):
        SimpleIOHubRuntime.__init__(self,configFileDirectory,configFile)
        
    def run(self,*args,**kwargs):
        '''
        tests the round trip time to request and reveive events from the I/O hub. 
        The test is performed 'numEventRequests' times. Only responses with >= 1 event count
        toward the tally.
        
        Only keyboard and mouse events are enabled for this test, so once you start the program and see
        the example psychopy application, move the mouse around, press mouse button, press keyboard keys,
        etc. This will generate events. After a minute or so, the default 1000 requests will be satisfied
        and the test will exit, printing out some stat's.
        
        If you get high MAX delays, turn off cloud drive apps, especially Google Drive; that fixes it for me.
        
        psychopy code is taken from an example psychopy scipt in the coder documentation.
        '''
        
        self.totalEventRequestsForTest=kwargs['numEventRequests']
        
        # try sending an Experiment Event
        self.hub.sendMessageEvent("This is a test message")
        self.hub.sendCommandEvent("Command","Command Value")
        

        # create fullscreen pyglet window at current resolution, as well as required resources / drawings
        mywin=self.createPsychoGraphicsWindow()

        # create stats numpy arrays, set system to high priority.
        self.initTestResourcesAndState()
        
        #draw and flip to the updated graphics state.
        ifi=self.drawAndFlipPsychoWindow()        
                
        # START TEST LOOP >>>>>>>>>>>>>>>>>>>>>>>>>>

        while self.numEventRequests < self.totalEventRequestsForTest:
            # try sending an Experiment Event
            self.hub.sendMessageEvent("This is a test message %.3f"%self.flipTime)
            self.hub.sendCommandEvent("Command","Command Value %d"%self.numEventRequests)

            
            #draw and flip to the updated graphics state.
            ifi=self.drawAndFlipPsychoWindow()

            events,callDuration=self.checkForEvents()
            
            if events:
                # events were available
                self.updateStats(events, callDuration, ifi)
                        
        # END TEST LOOP <<<<<<<<<<<<<<<<<<<<<<<<<<
        
        # close neccessary files / objects, 'disable high priority. 
        self.spinDownTest()
        
        # plot collected delay and retrace detection results.
        self.plotResults()

    def createPsychoGraphicsWindow(self):
        from collections import OrderedDict
        
        #create a window
        self.psychoWindow = visual.Window(self.hub.devices.display.getScreenResolution(),monitor="testMonitor", units="deg", fullscr=True)
        
        self.mouse=self.hub.devices.mouse
        currentPosition,displayPositionDelta,devicePositionDelta=self.mouse.getDisplayPositionAndChange()
        
        self.instructionText2Pattern='.... %d event captures left .....'
        
        self.psychoStim=OrderedDict()
        self.psychoStim['grating'] = visual.PatchStim(self.psychoWindow, mask="circle", size=3,pos=[-4,0], sf=3)
        self.psychoStim['fixation'] =visual.PatchStim(self.psychoWindow, size=0.5, pos=[0,0], sf=0,  color=[-1,-1,-1], colorSpace='rgb')
        self.psychoStim['title'] =visual.TextStim(win=self.psychoWindow, text="ioHub getEvents Delay Test", pos = [0,6],  color=[1,.5,0], colorSpace='rgb',alignHoriz='center',wrapWidth=15.0)
        self.psychoStim['instructions'] =visual.TextStim(win=self.psychoWindow, text='Move the mouse around, press keyboard keys and mouse buttons', pos = [0,-3],  color=[-1,-1,-1], colorSpace='rgb',alignHoriz='center',wrapWidth=30.0)
        self.psychoStim['instructions2'] =visual.TextStim(win=self.psychoWindow, text=self.instructionText2Pattern%(self.totalEventRequestsForTest,), pos = [0,-6],  color=[-1,-1,-1], colorSpace='rgb',alignHoriz='center',wrapWidth=30.0)
        self.psychoStim['keytext'] =visual.TextStim(win=self.psychoWindow, text='key', pos = [0,10],  color=[-1,-1,-1], colorSpace='rgb',alignHoriz='left',wrapWidth=40.0)
        self.psychoStim['mouseDot'] =visual.GratingStim(win=self.psychoWindow,tex=None, mask="gauss", pos=currentPosition,size=(1,1),color='purple')

    def drawAndFlipPsychoWindow(self):
        self.psychoStim['grating'].setPhase(0.05, '+')#advance phase by 0.05 of a cycle
        currentPosition,displayPositionDelta,devicePositionDelta=self.mouse.getDisplayPositionAndChange()
        self.psychoStim['mouseDot'].setPos(currentPosition)
        r=[self.psychoStim[stimName].draw() for stimName in self.psychoStim]
        self.flipTime=self.psychoWindow.flip()
        d=self.flipTime-self.lastFlipTime       
        self.lastFlipTime=self.flipTime
        return d

    def checkForEvents(self):
        # get the time we reqquest events from the ioHub
        stime=self.currentTime()
        r = self.getEvents()
        if r and len(r) > 0:
            # so there were events returned in the request, so include this getEvent request in the tally
            etime=self.currentTime()    
            dur=etime-stime
            return r, dur*1000.0
        return None,None
            
    def initTestResourcesAndState(self):

        self.mouse=self.hub.devices.mouse
        
        if self.hub is None:
            print "Error: ioHub must be enabled to run the testEventRetrievalTiming test."
            return
        
        # Init Results numpy array
        self.results=N.zeros((self.totalEventRequestsForTest,3),dtype='f4')
 
        self.numEventRequests=0
        self.flipTime=0.0
        self.lastFlipTime=0.0
        
        # enable high priority mode for the experiment process.
        self.enableHighPriority()
 
        #enable high priority in the ioHub Server process
        #self.hub.sendToHub(('RPC','enableHighPriority'))

        # clear the ioHub event Buffer before starting the test.
        # This is VERY IMPORTANT, given an existing bug in ioHub.
        # You would want to do this before each trial started until the bug is fixed. 
        self.clearEvents()

    def updateStats(self, events, duration, ifi):
        self.results[self.numEventRequests][0]=duration     # ctime it took to get events from ioHub
        self.results[self.numEventRequests][1]=len(events)  # number of events returned
        self.results[self.numEventRequests][2]=ifi*1000.0   # calculating inter flip interval.
        self.numEventRequests+=1        # incrementing tally counter
        
        self.psychoStim['instructions2'].setText(self.instructionText2Pattern%(self.totalEventRequestsForTest-self.numEventRequests,))

        for r in events:
            if not isinstance(r,dict):
                r=self.eventListToDict(r)
            if r['event_type'] == 51: #keypress code
                keystring=r['key']
                self.psychoStim['keytext'].setText(keystring)

    def spinDownTest(self):
        # OK, we have collected the number of requested getEvents, that have returned >0 events
        # so close psychopy window
        self.psychoWindow.close()
        
        # disable high priority in both processes
        self.disableHighPriority()
        #hub.sendToHub(('RPC','disableHighPriority'))
        
    

    def plotResults(self):
        #### calculate stats on collected data and draw some plots ####
        import scipy.stats as stats
        import matplotlib.mlab as mlab
        import matplotlib.pyplot as plt
        import pylab
        
        results= self.results
        
        durations=results[:,0]
        flips=results[1:,2]
        
        dmin=durations.min()
        dmax=durations.max()
        dmean=durations.mean()
        dstd=durations.std()

        fmin=flips.min()
        fmax=flips.max()
        fmean=flips.mean()
        fstd=flips.std()
        median=N.median(flips)

        pylab.figure(figsize=[30,10])
        pylab.subplot(1,3,1)


        # the histogram of the delay data
        n, bins, patches = plt.hist(durations, 50, normed=True, facecolor='blue', alpha=0.75)
        # add a 'best fit' line
        y = mlab.normpdf( bins, dmean, dstd)
        l = plt.plot(bins, y, 'r--', linewidth=1)
        plt.xlabel('ioHub getEvents Delay')
        plt.ylabel('Percentage')
        plt.title(r'$\mathrm{Histogram\ of\ Delay:}\ \min=%.3f,\ \max=%.3f,\ \mu=%.3f,\ \sigma=%.4f$'%(dmin,dmax,dmean,dstd))
        plt.axis([0, dmax+1.0, 0, 25.0])
        plt.grid(True)
        
        
        # graphs of the retrace data ( taken from retrace example in psychopy demos folder)
        intervalsMS = flips
        m=fmean
        sd=fstd
        distString= "Mean=%.1fms,    s.d.=%.1f,    99%%CI=%.1f-%.1f" %(m,sd,m-3*sd,m+3*sd)
        nTotal=len(intervalsMS)
        nDropped=sum(intervalsMS>(1.5*m))
        droppedString = "Dropped/Frames = %i/%i = %.3f%%" %(nDropped,nTotal,nDropped/float(nTotal))

        pylab.subplot(1,3,2)

        #plot the frameintervals
        pylab.plot(intervalsMS, '-')
        pylab.ylabel('t (ms)')
        pylab.xlabel('frame N')
        pylab.title(droppedString)
        
        pylab.subplot(1,3,3)
        pylab.hist(intervalsMS, 50, normed=0, histtype='stepfilled')
        pylab.xlabel('t (ms)')
        pylab.ylabel('n frames')
        pylab.title(distString)

        plt.show()                

##################################################################        
if __name__ == "__main__":
    import sys
    configFile='experiment_config.yaml'
    if len(sys.argv)>1:
        configFile=sys.argv[1]
    try:
        EXPERIMENT_DIR=os.path.dirname(os.path.abspath(__file__))
        
        # create a simple ExperimentRuntime class instance, passing in the experiment_config.yaml data
        runtime=ExperimentRuntime(EXPERIMENT_DIR, configFile)
        
        # run a test on event access delay
        runtime.run(numEventRequests=1000)
        
        runtime.close()
        
    except Exception:
        ExperimentRuntime.printExceptionDetails()