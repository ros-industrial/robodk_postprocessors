# Copyright 2017 - RoboDK Software S.L. - http://www.robodk.com/
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ----------------------------------------------------
# This file is a POST PROCESSOR for Robot Offline Programming to generate programs 
# for a generic robot with RoboDK
#
# To edit/test this POST PROCESSOR script file:
# Select "Program"->"Add/Edit Post Processor", then select your post or create a new one.
# You can edit this file using any text editor or Python editor. Using a Python editor allows to quickly evaluate a sample program at the end of this file.
# Python should be automatically installed with RoboDK
#
# You can also edit the POST PROCESSOR manually:
#    1- Open the *.py file with Python IDLE (right click -> Edit with IDLE)
#    2- Make the necessary changes
#    3- Run the file to open Python Shell: Run -> Run module (F5 by default)
#    4- The "test_post()" function is called automatically
# Alternatively, you can edit this file using a text editor and run it with Python
#
# To use a POST PROCESSOR file you must place the *.py file in "C:/RoboDK/Posts/"
# To select one POST PROCESSOR for your robot in RoboDK you must follow these steps:
#    1- Open the robot panel (double click a robot)
#    2- Select "Parameters"
#    3- Select "Unlock advanced options"
#    4- Select your post as the file name in the "Robot brand" box
#
# To delete an existing POST PROCESSOR script, simply delete this file (.py file)
#
# ----------------------------------------------------
# More information about RoboDK Post Processors and Offline Programming here:
#     http://www.robodk.com/help#PostProcessor
#     http://www.robodk.com/doc/PythonAPI/postprocessor.html
# ----------------------------------------------------


# ----------------------------------------------------
# Import RoboDK tools
from robodk import *

# ----------------------------------------------------
def pose_2_str(pose):
    """Prints a pose target"""
    [x,y,z,r,p,w] = pose_2_xyzrpw(pose)
    return ('X%.3f Y%.3f Z%.3f R%.3f P%.3f W%.3f' % (x,y,z,r,p,w))
    
def angles_2_str(angles):
    """Prints a joint target"""
    str = ''
    data = ['A','B','C','D','E','F','G','H','I','J','K','L']
    for i in range(len(angles)):
        str = str + ('%s%.6f ' % (data[i], angles[i]))
    str = str[:-1]
    return str

# ----------------------------------------------------    
# Object class that handles the robot instructions/syntax
class RobotPost(object):
    """Robot post object"""
    PROG_EXT = 'txt'        # set the program extension
    
    # other variables
    ROBOT_POST = ''
    ROBOT_NAME = ''
    PROG_FILES = []
    
    PROG = ''
    LOG = ''
    nAxes = 6
    
    def __init__(self, robotpost=None, robotname=None, robot_axes = 6, **kwargs):
        self.ROBOT_POST = robotpost
        self.ROBOT_NAME = robotname
        self.PROG = ''
        self.LOG = ''
        self.nAxes = robot_axes
        self.COUNT_STATE = 0
        self.COUNT_MOVE = 0
        
        
    def ProgStart(self, progname):
        self.addline('(** This is a program sample generated by RoboDK post processor for Logix5000**)')
        self.addline('(*****  Enable Axis_0 and Axis_1 *****)')
        self.addline('if (input_0 & State = 0) then ')
        self.addline('\tMSO(Axis_0, Axis_0_MSO);')
        self.addline('\tState [:=] 1;')
        self.addline('\tcounter [:=] .5;')
        self.addline('end_if;')
        self.addline('')
        self.addline('(***** Check for servos on *****)');
        self.addline('If (Axis_0.ServoActionStatus & Axis_1.ServoActionStatus & State = 1) then');
        self.addline('\tgear_ratio := counter;');
        self.addline('(**\tMAG(Axis_0, Axis_1, Axis0_1_MAG, 1, gear_ratio, 1, 1, Actual, Real, Disabled, 10, 1 );**)');
        self.addline('\tState := 2;');
        self.addline('end_if;');
        self.addline('')
        self.addline('(********** MOVE AXES START **********)')
        self.COUNT_STATE = 2

        
    def ProgFinish(self, progname):
        self.addline('(***** Check if move is complete and axis is in position *****)')
        MAM_PC_ALL = ''
        for i in range(self.nAxes):
            MAM_PC_ALL = MAM_PC_ALL + ('Axis_%i_MAM.PC & ' % i)
            
        self.addline('If (%sState = %i) then' % (MAM_PC_ALL, self.COUNT_STATE))
        self.COUNT_STATE = self.COUNT_STATE + 1
        self.addline('\tState := %i;' % self.COUNT_STATE)
        self.addline('end_if;')
        self.addline('If (%s & counter = 2 & Axis_1.PositionLockStatus & State = %i) then' % (MAM_PC_ALL, self.COUNT_STATE))
        self.COUNT_STATE = self.COUNT_STATE + 1
        self.addline('\tState := %i;' % self.COUNT_STATE)
        self.addline('end_if;')
        self.addline('If (input_1 & State = %i) then' % self.COUNT_STATE)
        self.addline('\tcounter := counter + .5;')
        self.addline('\tState := 1; (* This directs the program to loop back and re-enter at State = 1 *)        ')
        self.addline('end_if;')
        self.addline('If (Axis_0.ActualVelocity = 0 & Axis_1.ActualVelocity = 0 & State = %i) then' % self.COUNT_STATE)
        self.addline('\tMSF(Axis_0, Axis_0_MSF); MSF(Axis_1, Axis_1_MSF);')
        self.addline('\tJSR(LadderFile, 0 );  (* Jump to Ladder program *) (* Return from Ladder enters here *)')
        self.addline('end_if;')
        self.addline('If timer_1.DN & State = %i then (* Wait for timer done then reset ' % self.COUNT_STATE)
        self.addline('\tState := 0;')
        self.addline('\tcounter := 0;')
        self.addline('end_if;')
        self.addline('')
        self.addline('(** this program contains %i sequential movements **)' % self.COUNT_MOVE)
        
    def ProgSave(self, folder, progname, ask_user = False, show_result = False):
        progname = progname + '.' + self.PROG_EXT
        if ask_user or not DirExists(folder):
            filesave = getSaveFile(folder, progname, 'Save program as...')
            if filesave is not None:
                filesave = filesave.name
            else:
                return
        else:
            filesave = folder + '/' + progname
        # save file
        fid = open(filesave, "w")
        fid.write(self.PROG)
        fid.close()
        print('SAVED: %s\n' % filesave) # tell RoboDK the path of the saved file
        self.PROG_FILES = filesave
        
        # open file with default application
        if show_result:
            if type(show_result) is str:
                # Open file with provided application
                import subprocess
                p = subprocess.Popen([show_result, filesave])
            else:
                # open file with default application
                import os
                os.startfile(filesave)
            if len(self.LOG) > 0:
                mbox('Program generation LOG:\n\n' + self.LOG)
        
    def ProgSendRobot(self, robot_ip, remote_path, ftp_user, ftp_pass):
        """Send a program to the robot using the provided parameters. This method is executed right after ProgSave if we selected the option "Send Program to Robot".
        The connection parameters must be provided in the robot connection menu of RoboDK"""
        UploadFTP(self.PROG_FILES, robot_ip, remote_path, ftp_user, ftp_pass)
        
    def MoveJ(self, pose, joints, conf_RLF=None):
        """Add a joint movement"""
        self.addline('(** move instruction %i (joint move)**)' % self.COUNT_MOVE)
        MAM_PC_ALL = ''
        for i in range(len(joints)):
            MAM_PC_ALL = MAM_PC_ALL + ('Axis_%i_MAM.PC & ' % i)
            
        self.addline('if (%sState = %i) then' % (MAM_PC_ALL,  self.COUNT_STATE))
        self.COUNT_STATE = self.COUNT_STATE + 1
        self.COUNT_MOVE  = self.COUNT_MOVE  + 1
        for i in range(len(joints)):
            self.addline('\tMAM(Axis_%i, Axis_%i_MAM, 1, %.3f, Move_Speed, Unitspersec, 50, %%ofMaximum, 50, %%ofMaximum, 1,100.0,100.0,%%ofTime, 0, 0 ,0,None,0,0);' % (i, i, joints[i]))
            
        self.addline('\tState := %i;' % self.COUNT_STATE)
        self.addline('end_if;')        
        
    def MoveL(self, pose, joints, conf_RLF=None):
        """Add a linear movement"""
        self.addline('(** move instruction %i (linear move)**)' % self.COUNT_MOVE)
        MAM_PC_ALL = ''
        for i in range(len(joints)):
            MAM_PC_ALL = MAM_PC_ALL + ('Axis_%i_MAM.PC & ' % i)
            
        self.addline('if (%sState = %i) then' % (MAM_PC_ALL,  self.COUNT_STATE))
        self.COUNT_STATE = self.COUNT_STATE + 1
        self.COUNT_MOVE  = self.COUNT_MOVE  + 1
        for i in range(len(joints)):
            self.addline('\tMAM(Axis_%i, Axis_%i_MAM, 1, %.3f, Move_Speed, Unitspersec, 50, %%ofMaximum, 50, %%ofMaximum, 1,100.0,100.0,%%ofTime, 0, 0 ,0,None,0,0);' % (i, i, joints[i]))
            
        self.addline('\tState := %i;' % self.COUNT_STATE)
        self.addline('end_if;')        
        
    def MoveC(self, pose1, joints1, pose2, joints2, conf_RLF_1=None, conf_RLF_2=None):
        """Add a circular movement"""
        self.addlog('MoveC not defined')
        
    def setFrame(self, pose, frame_id=None, frame_name=None):
        """Change the robot reference frame"""
        self.addlog('setFrame not defined')
        
    def setTool(self, pose, tool_id=None, tool_name=None):
        """Change the robot TCP"""
        self.addlog('setTool not defined')
        
    def Pause(self, time_ms):
        """Pause the robot program"""
        self.addlog('Pause not defined')
        
    def setSpeed(self, speed_mms):
        """Changes the current robot speed (in mm/s)"""
        self.addlog('setSpeed not defined')
        
    def setAcceleration(self, accel_mmss):
        """Changes the current robot acceleration (in mm/s2)"""
        self.addlog('setAcceleration not defined')
                
    def setSpeedJoints(self, speed_degs):
        """Changes the robot joint speed (in deg/s)"""
        self.addlog('setSpeedJoints not defined')
    
    def setAccelerationJoints(self, accel_degss):
        """Changes the robot joint acceleration (in deg/s2)"""
        self.addlog('setAccelerationJoints not defined')
        
    def setZoneData(self, zone_mm):
        """Changes the zone data approach (makes the movement more smooth)"""
        self.addlog('Zone data not implemented (%.1f mm)' % zone_mm)
        
    def setDO(self, io_var, io_value):
        """Sets a variable (output) to a given value"""
        if type(io_var) != str:  # set default variable name if io_var is a number
            io_var = 'OUT[%s]' % str(io_var)        
        if type(io_value) != str: # set default variable value if io_value is a number            
            if io_value > 0:
                io_value = 'TRUE'
            else:
                io_value = 'FALSE'
        
        # at this point, io_var and io_value must be string values
        self.addline('%s=%s' % (io_var, io_value))
        
    def waitDI(self, io_var, io_value, timeout_ms=-1):
        """Waits for an input io_var to attain a given value io_value. Optionally, a timeout can be provided."""
        if type(io_var) != str:  # set default variable name if io_var is a number
            io_var = 'IN[%s]' % str(io_var)        
        if type(io_value) != str: # set default variable value if io_value is a number            
            if io_value > 0:
                io_value = 'TRUE'
            else:
                io_value = 'FALSE'
        
        # at this point, io_var and io_value must be string values
        if timeout_ms < 0:
            self.addline('WAIT FOR %s==%s' % (io_var, io_value))
        else:
            self.addline('WAIT FOR %s==%s TIMEOUT=%.1f' % (io_var, io_value, timeout_ms))   
        
    def RunCode(self, code, is_function_call = False):
        """Adds code or a function call"""
        self.addlog('RunCode not defined')
        
    def RunMessage(self, message, iscomment = False):
        """Show a message on the controller screen"""
        self.addlog('RunMessage not defined')
        
# ------------------ private ----------------------                
    def addline(self, newline):
        """Add a program line"""
        self.PROG = self.PROG + newline + '\n'
        
    def addlog(self, newline):
        """Add a log message"""
        self.LOG = self.LOG + newline + '\n'

# -------------------------------------------------
# ------------ For testing purposes ---------------   
def Pose(xyzrpw):
    [x,y,z,r,p,w] = xyzrpw
    a = r*math.pi/180
    b = p*math.pi/180
    c = w*math.pi/180
    ca = math.cos(a)
    sa = math.sin(a)
    cb = math.cos(b)
    sb = math.sin(b)
    cc = math.cos(c)
    sc = math.sin(c)
    return Mat([[cb*ca, ca*sc*sb - cc*sa, sc*sa + cc*ca*sb, x],[cb*sa, cc*ca + sc*sb*sa, cc*sb*sa - ca*sc, y],[-sb, cb*sc, cc*cb, z],[0,0,0,1]])

def test_post():
    """Test the post with a basic program"""

    robot = RobotPost()

    robot.ProgStart("Program")
    robot.RunMessage("Program generated by RoboDK", True)
    robot.setFrame(Pose([807.766544, -963.699898, 41.478944, 0, 0, 0]))
    robot.setTool(Pose([62.5, -108.253175, 100, -60, 90, 0]))
    robot.MoveJ(Pose([200, 200, 500, 180, 0, 180]), [-46.18419, -6.77518, -20.54925, 71.38674, 49.58727, -302.54752] )
    robot.MoveL(Pose([200, 250, 348.734575, 180, 0, -150]), [-41.62707, -8.89064, -30.01809, 60.62329, 49.66749, -258.98418] )
    robot.MoveL(Pose([200, 200, 262.132034, 180, 0, -150]), [-43.73892, -3.91728, -35.77935, 58.57566, 54.11615, -253.81122] )
    robot.RunMessage("Setting air valve 1 on")
    robot.RunCode("TCP_On", True)
    robot.Pause(1000)
    robot.MoveL(Pose([200, 250, 348.734575, 180, 0, -150]), [-41.62707, -8.89064, -30.01809, 60.62329, 49.66749, -258.98418] )
    robot.MoveL(Pose([250, 300, 278.023897, 180, 0, -150]), [-37.52588, -6.32628, -34.59693, 53.52525, 49.24426, -251.44677] )
    robot.MoveL(Pose([250, 250, 191.421356, 180, 0, -150]), [-39.75778, -1.04537, -40.37883, 52.09118, 54.15317, -246.94403] )
    robot.RunMessage("Setting air valve off")
    robot.RunCode("TCP_Off", True)
    robot.Pause(1000)
    robot.MoveL(Pose([250, 300, 278.023897, 180, 0, -150]), [-37.52588, -6.32628, -34.59693, 53.52525, 49.24426, -251.44677] )
    robot.MoveL(Pose([250, 200, 278.023897, 180, 0, -150]), [-41.85389, -1.95619, -34.89154, 57.43912, 52.34162, -253.73403] )
    robot.MoveL(Pose([250, 150, 191.421356, 180, 0, -150]), [-43.82111, 3.29703, -40.29493, 56.02402, 56.61169, -249.23532] )
    robot.ProgFinish("Program")
    # robot.ProgSave(".","Program",True)
    print(robot.PROG)
    if len(robot.LOG) > 0:
        mbox('Program generation LOG:\n\n' + robot.LOG)

    input("Press Enter to close...")

if __name__ == "__main__":
    """Function to call when the module is executed by itself: test"""
    test_post()
