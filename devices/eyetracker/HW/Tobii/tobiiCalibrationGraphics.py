"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyeTracker/HW/Tobii/TobiiCalibrationGraphics.py

Copyright (C) 2012 Sol Simpson
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

---------------------------------------------------------------------------------------------------------------------
This file uses the pylink module, Copyright (C) SR Research Ltd. License type unknown as it is not provided in the
pylink distribution (atleast when downloaded May 2012). At the time of writing, Pylink is freely avalaible for
download from  www.sr-support.com once you are registered and includes the necessary C DLLs.
---------------------------------------------------------------------------------------------------------------------

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor::
"""

from psychopy import visual

import time, Queue

import ioHub.external_libs
import ioHub.devices
from ioHub.devices import Computer
from ioHub.constants import EventConstants, KeyboardConstants

currentTime=Computer.getTime

class TobiiPsychopyCalibrationGraphics(object):
    IOHUB_HEARTBEAT_INTERVAL=0.050   # seconds between forced run through of
                                     # micro threads, since one is blocking
                                     # on camera setup.
    WINDOW_BACKGROUND_COLOR=(128,128,128)
    CALIBRATION_POINT_OUTER_RADIUS=15.0,15.0
    CALIBRATION_POINT_OUTER_EDGE_COUNT=64
    CALIBRATION_POINT_OUTER_COLOR=(255,255,255)
    CALIBRATION_POINT_INNER_RADIUS=3.0,3.0
    CALIBRATION_POINT_INNER_EDGE_COUNT=32
    CALIBRATION_POINT_INNER_COLOR=(25,25,25)
    CALIBRATION_POINT_LIST=[(0.5, 0.5),(0.1, 0.1),(0.9, 0.1),(0.9, 0.9),(0.1, 0.9),(0.5, 0.5)]

    TEXT_POS=[0,0]
    TEXT_COLOR=[0,0,0]
    TEXT_HEIGHT=48
    
    def __init__(self, eyetrackerInterface, targetForegroundColor=None, 
                 targetBackgroundColor=None, screenColor=None, 
                 targetOuterDiameter=None, targetInnerDiameter=None,
                 calibrationPointList=None):
        ppd_x,ppd_y=ioHub.devices.Display.getPPD()
        self.screenSize = ioHub.devices.Display.getStimulusScreenResolution()
        self._eyetrackerinterface=eyetrackerInterface
        self._tobii = eyetrackerInterface._tobii._eyetracker

        self._lastCalibrationOK=False
        self._lastCalibrationReturnCode=0
        self._lastCalibration=None
        
        if targetForegroundColor is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_OUTER_COLOR=targetForegroundColor

        if targetBackgroundColor is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_INNER_COLOR=targetBackgroundColor

        if screenColor is not None:
            TobiiPsychopyCalibrationGraphics.WINDOW_BACKGROUND_COLOR=screenColor

        if targetOuterDiameter is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_OUTER_RADIUS=targetOuterDiameter/2.0,targetOuterDiameter/2.0
        else:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_OUTER_RADIUS=ppd_x/2.0,ppd_y/2.0

        if targetInnerDiameter is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_INNER_RADIUS=targetInnerDiameter/2.0,targetInnerDiameter/2.0
        else:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_INNER_RADIUS=ppd_x/6.0,ppd_y/6.0


        if calibrationPointList is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST=calibrationPointList

        self._msg_queue=Queue.Queue()
        
        self._ioKeyboard=None
        #self._ioMouse=None
        self._ioServer=None
        
        self.width=self.screenSize[0]
        self.height=self.screenSize[1]

        self.window = visual.Window(self.screenSize, monitor="calibrationMonitor", units='pix', fullscr=True, allowGUI=False, screen=ioHub.devices.Display.getStimulusScreenIndex())
        self.window.setColor(self.WINDOW_BACKGROUND_COLOR,'rgb255')        
        self.window.flip(clearBuffer=True)
        self.window.flip(clearBuffer=True)
        
        self._createStim()
        
        self._registerEventMonitors()
        self._lastMsgPumpTime=currentTime()
        
        self.clearAllEventBuffers()

    def clearAllEventBuffers(self):
        self._ioServer.eventBuffer.clear()
        for d in self._ioServer.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        self._ioServer=self._eyetrackerinterface._ioServer

        if self._ioServer:
            for dev in self._ioServer.devices:
                #ioHub.print2err("dev: ",dev.__class__.__name__)
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice=dev

        if kbDevice:
            self._ioKeyboard=kbDevice
            self._ioKeyboard._addEventListener(self)
        else:
            ioHub.print2err("Warning: Tobii Cal GFX could not connect to Keyboard device for events.")

    def _unregisterEventMonitors(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)
     
    def _handleEvent(self,ioe):
        event_type_index=ioHub.devices.DeviceEvent.EVENT_TYPE_ID_INDEX
        if ioe[event_type_index] == EventConstants.KEYBOARD_PRESS:
            if ioe[-3] == 'SPACE':
                self._msg_queue.put("SPACE_KEY_ACTION")
                self.clearAllEventBuffers()
            if ioe[-3] == 'ESCAPE':
                self._msg_queue.put("QUIT")
                self.clearAllEventBuffers()

    def MsgPump(self):
        #keep the psychopy window happy ;)
        if currentTime()-self._lastMsgPumpTime>self.IOHUB_HEARTBEAT_INTERVAL:                
            # try to keep ioHub, being blocked. ;(
            if self._ioServer:
                for dm in self._ioServer.deviceMonitors:
                    dm.device._poll()
                self._ioServer._processDeviceEventIteration()
            self._lastMsgPumpTime=currentTime()

    def getNextMsg(self):
        try:
            msg=self._msg_queue.get(block=True,timeout=0.05)
            self._msg_queue.task_done()
            return msg
        except Queue.Empty:
            pass

    def _createStim(self):                
        self.calibrationPointOUTER = visual.Circle(self.window,pos=(0,0) ,lineWidth=0.0,radius=self.CALIBRATION_POINT_OUTER_RADIUS,name='CP_OUTER', units='pix',opacity=1.0, interpolate=False)
        self.calibrationPointINNER = visual.Circle(self.window,pos=(0,0),lineWidth=0.0, radius=self.CALIBRATION_POINT_INNER_RADIUS, name='CP_INNER',units='pix',opacity=1.0, interpolate=False)
        
        self.calibrationPointOUTER.setFillColor(self.CALIBRATION_POINT_OUTER_COLOR,'rgb255')
        self.calibrationPointOUTER.setLineColor(None,'rgb255')
        self.calibrationPointINNER.setFillColor(self.CALIBRATION_POINT_INNER_COLOR,'rgb255')
        self.calibrationPointINNER.setLineColor(None,'rgb255 ')

        instuction_text="Press Space Key to Start".center(32)+'\n'+"Eye Tracker Calibration.".center(32)
        self.startCalibrationTextScreen=visual.TextStim(self.window, text=instuction_text, pos = self.TEXT_POS, height=self.TEXT_HEIGHT, color=self.TEXT_COLOR, colorSpace='rgb255',alignHoriz='center',alignVert='center',wrapWidth=self.width*0.8)
        
    def runCalibration(self):
        """
        Performs a simple calibration routine. 
        
        Args: 
            None
        
        Result:
            bool: True if calibration was successful. False if not, in which case exit the application.            
        """
        import tobii

        self._lastCalibrationOK=False
        self._lastCalibrationReturnCode=0
        self._lastCalibration=None
        
        calibration_sequence_completed=False
        quit_calibration_notified=False
        

        instuction_text="Press Space Key to Start".center(32)+'\n'+"Eye Tracker Calibration.".center(32)
        self.startCalibrationTextScreen.setText(instuction_text)
        
        self.startCalibrationTextScreen.draw()
        self.window.flip()
        
        self.clearAllEventBuffers()
 
        stime=currentTime()
        while currentTime()-stime<60*5.0:
            msg=self.getNextMsg()
            if msg == 'SPACE_KEY_ACTION':
                break

            self.MsgPump()

        self.clearAllEventBuffers()
       
        self._tobii.StartCalibration(self.on_start_calibration)   

        i=0
        for pt in self.CALIBRATION_POINT_LIST:
            w,h=self.screenSize
            #ioHub.print2err("Screen Size: ",w," ",h)
            self.clearAllEventBuffers()
            pix_pt=int(w*pt[0]-w/2),int(h*(1.0-pt[1])-h/2)
            #ioHub.print2err( "Cal point Mapping: ",pt," == ",pix_pt)
            self.drawCalibrationTarget(pix_pt)

            stime=currentTime()
            while currentTime()-stime<2.5:
                msg=self.getNextMsg()
                if msg == 'SPACE_KEY_ACTION':
                    break
                elif msg == 'QUIT':
                    quit_calibration_notified=True
                    
                self.MsgPump()
            
            if quit_calibration_notified:
                break
            
            pt2D=tobii.sdk.types.Point2D(pt[0],pt[1])
            self._tobii.AddCalibrationPoint(pt2D,self.on_add_calibration_point)
            time.sleep(0.5)            
            self.clearCalibrationWindow()
            self.clearAllEventBuffers()

            i+=1
            if i == len(self.CALIBRATION_POINT_LIST):
                calibration_sequence_completed=True
        
        if calibration_sequence_completed:
            self._tobii.ComputeCalibration(self.on_compute_calibration)
 
            msg=1
            while msg not in ["CALIBRATION_COMPUTATION_COMPLETE","CALIBRATION_COMPUTATION_FAILED"]:        
                msg=self.getNextMsg()
            
        self._tobii.StopCalibration(self.on_stop_calibration)  
        msg=1
        while msg is not "CALIBRATION_FINISHED":        
            msg=self.getNextMsg()

        if self._lastCalibrationOK is True:
            self._tobii.GetCalibration(self.on_calibration_result)

            msg=1
            while msg is not "CALIBRATION_RESULT_RECEIVED":        
                msg=self.getNextMsg()
            
            cal_data_dict={}

            import math

            for cal_point_result in self._lastCalibration.plot_data:
                left_eye_data=cal_point_result.left.map_point
                left_eye_data=(left_eye_data.x*self.width,left_eye_data.y*self.height),cal_point_result.left.validity
                
                right_eye_data=cal_point_result.right.map_point
                right_eye_data=(right_eye_data.x*self.width,right_eye_data.y*self.height),cal_point_result.right.validity
                
                target_pos=cal_point_result.true_point.x*self.width,cal_point_result.true_point.y*self.height
                
                if target_pos not in cal_data_dict:
                    cal_data_dict[target_pos]=[]
                cal_data_dict[target_pos].append((left_eye_data,right_eye_data))

            cal_stats=dict()
            for (targ_x,targ_y),eye_cal_result_list in cal_data_dict.iteritems():
                left_stats=dict(pos_sample_count=0,invalid_sample_count=0,avg_err=0.0,min_err=100000.0,max_err=0.0)
                right_stats=dict(pos_sample_count=0,invalid_sample_count=0,avg_err=0.0,min_err=100000.0,max_err=0.0)
                
                for ((left_x,left_y),left_validity),((right_x,right_y),right_validity) in eye_cal_result_list:
                    left_stats['pos_sample_count']+=1.0
                    right_stats['pos_sample_count']+=1.0
                    
                    if left_validity==1:
                        x_err=targ_x-left_x
                        y_err=targ_y-left_y
                        left_err=math.sqrt(x_err*x_err+y_err*y_err)
                        if left_err<left_stats['min_err']:
                            left_stats['min_err']=left_err
                        elif left_err>left_stats['max_err']:
                            left_stats['max_err']=left_err
                        left_stats['avg_err']+=left_err
                    else:
                        left_stats['invalid_sample_count']+=1.0

                        
                    if right_validity==1:
                        x_err=targ_x-right_x
                        y_err=targ_y-right_y                        
                        right_err=math.sqrt(x_err*x_err+y_err*y_err)
                        if right_err<right_stats['min_err']:
                            right_stats['min_err']=right_err
                        elif right_err>right_stats['max_err']:
                            right_stats['max_err']=right_err
                        right_stats['avg_err']+=right_err
                    else:
                        right_stats['invalid_sample_count']+=1.0
                    
                if right_stats['invalid_sample_count']==0:
                    right_stats['valid_sample_percentage']=100.0
                else:
                    right_stats['valid_sample_percentage']=(1.0-right_stats['invalid_sample_count']/right_stats['pos_sample_count'])*100.0
                
                if left_stats['invalid_sample_count']==0:
                    left_stats['valid_sample_percentage']=100.0
                else:
                    left_stats['valid_sample_percentage']=(1.0-left_stats['invalid_sample_count']/left_stats['pos_sample_count'])*100.0
             
                if int(right_stats['pos_sample_count']-right_stats['invalid_sample_count'])>0:
                    right_stats['avg_err']=right_stats['avg_err']/(right_stats['pos_sample_count']-right_stats['invalid_sample_count'])
                else:
                    right_stats['avg_err']=-1.0
                    
                if int(left_stats['pos_sample_count']-left_stats['invalid_sample_count'])>0:
                    left_stats['avg_err']=left_stats['avg_err']/(left_stats['pos_sample_count']-left_stats['invalid_sample_count'])
                else:
                    left_stats['avg_err']=-1.0
               
                cal_stats[(targ_x,targ_y)]=dict(left=left_stats,right=right_stats)
            
            # TODO Use calibration stats to show graphical results of calibration
            
            instuction_text="Calibration Passed.".center(32)+'\n'       
            instuction_text+="PRESS 'SPACE' KEY TO CONTINUE.".center(32)+'\n'       
            self.startCalibrationTextScreen.setText(instuction_text)
            self.startCalibrationTextScreen.draw()
            self.window.flip()
            self.clearAllEventBuffers()
        
            while 1:
                msg=self.getNextMsg()
                if msg == 'SPACE_KEY_ACTION':
                    return True
                    
                self.MsgPump()

        if self._lastCalibrationOK is False:
            instuction_text="Calibration Failed. Options:".center(32)+'\n'
            instuction_text=+"SPACE: Re-run Calibration".center(32)+'\n'
            instuction_text=+"ESCAPE: Exit Program".center(32)
            self.startCalibrationTextScreen.setText(instuction_text)
            self.startCalibrationTextScreen.draw()
            self.window.flip()
            self.clearAllEventBuffers()
        
            while 1:
                msg=self.getNextMsg()
                if msg == 'SPACE_KEY_ACTION':
                    return self.runCalibration()
                elif msg == 'QUIT':
                    return False
                    
                self.MsgPump()
        
        return True
            
    def clearCalibrationWindow(self):
        self.window.flip(clearBuffer=True)
        
    def drawCalibrationTarget(self,tp):        
        self.calibrationPointOUTER.setPos(tp)            
        self.calibrationPointINNER.setPos(tp)            
        self.calibrationPointOUTER.draw()          
        self.calibrationPointINNER.draw()            
        self.window.flip(clearBuffer=True)
           
    def on_start_calibration(self,*args,**kwargs):
        #ioHub.print2err('on_start_calibration: ',args,kwargs)
        pass
    
    def on_add_calibration_point(self,*args,**kwargs):
        #ioHub.print2err('on_add_calibration_point: ',args,kwargs)
        self._msg_queue.put('DRAW_NEXT')

    def on_stop_calibration(self,*args,**kwargs):
        #ioHub.print2err('on_stop_calibration: ',args,kwargs)
        self._msg_queue.put("CALIBRATION_FINISHED")
        
    def on_compute_calibration(self,*args,**kwargs):
        self._lastCalibrationReturnCode=args[0]
        if self._lastCalibrationReturnCode!=0:
            ioHub.print2err("ERROR: Tobii Calibration Calculation Failed. Error code: {0}".format(self._lastCalibrationReturnCode))
            self._lastCalibrationOK=False
            self._msg_queue.put("CALIBRATION_COMPUTATION_FAILED")
            
        else:
            self._msg_queue.put("CALIBRATION_COMPUTATION_COMPLETE")
            self._lastCalibrationOK=True

    def on_calibration_result(self,*args,**kwargs):
        self._lastCalibration=args[1]
        self._msg_queue.put("CALIBRATION_RESULT_RECEIVED")
        