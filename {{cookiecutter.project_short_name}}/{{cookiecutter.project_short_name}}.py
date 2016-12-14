#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created by Gavin Cooper for Alex Provost.
University of Newcastle
2016
"""
# Imports
from __future__ import division, print_function
from psychopy import visual, core, data, event, logging, gui, sound, parallel
import csv
import os  # handy system and path functions
import sys


def parseSoundList(filename):
    """Read and parse the sound specification filename
    The sound file has columns specifying each sound
    Automatically converts columns named PortCode, Frequency,
    Volume and Duration to the appropriate type"""
    with open(filename) as soundfile:
        casts = {'PortCode': int, 'Frequency': int, 'Volume': float, 'Duration': float}
        soundreader = csv.DictReader(soundfile)
        for row in soundreader:
            for field, cast in casts.items():
                if field in row:
                    row[field] = cast(row[field])
            yield row


def obtainDemographics(subject, title='Subject Details'):
    """Obtain subject demographics using keys/values from subject dict"""
    dlg = gui.DlgFromDict(dictionary=subject, title=title)
    if dlg.OK is False:
        core.quit()  # user pressed cancel


class Experiment(object):
    """Holds all experiment details such as implementation, run data (date etc)
    and creates resources like file descriptors and display adapters"""
    def __init__(self, name='{{cookiecutter.project_short_name}}'):
        """Setup the experiment, create windows and gather subject details"""
        super(Experiment, self).__init__()
        self.subject = {'Subject ID': ''}
        obtainDemographics(self.subject, title='Please Enter Subject Details')
        self.date = data.getDateStr()
        self.name = name
        self._filehandling()
        self._hwsetup()

    def _filehandling(self):
        """Create file paths, setup logging, change working directories"""
        # Ensure that relative paths start from the same directory as script
        _thisDir = os.path.dirname(os.path.abspath(__file__)).decode(
            sys.getfilesystemencoding())
        os.chdir(_thisDir)
        # Create base output filename
        filestruct = '{0.subject[Subject ID]}_{0.name}_{0.date}'.format(self)
        self.filename = os.path.join(_thisDir, 'data/'+filestruct)
        # save a log file for detail verbose info
        self.logFile = logging.LogFile(self.filename + '.log',
                                       level=logging.EXP)
        logging.console.setLevel(logging.WARNING)  # this outputs to the screen
        # An ExperimentHandler isn't essential but helps with data saving
        self.handler = data.ExperimentHandler(name=self.name,
                                              extraInfo=self.subject,
                                              dataFileName=self.filename)

    def _hwsetup(self):
        """Set up hardware like displays, sounds, etc"""
        # See documentation for visual.Window parameters
        self.win = visual.Window()
        # store frame rate of monitor if we can measure it successfully
        self.frameRate = self.win.getActualFrameRate()
        if self.frameRate is not None:
            self.frameDur = 1.0/round(self.frameRate)
        else:
            self.frameDur = 1.0/60.0  # couldn't get a reliable measure/guess
        # Set up the sound card
        sound.init(rate=48000, stereo=True, buffer=256)
        # Create some handy timers
        self.clock = core.Clock()  # to track the time since experiment started
        # Create a parallel port handler
        self.port = parallel.ParallelPort(address=0x0378)

    def buildStimuli(self):
        """Build individual stimuli for use in the experiment"""
        self.stimuli = {'generated_sounds': {}}
        self.sound_specifications = list(parseSoundList('soundlist.csv'))

    def getSound(self, freq, dur, vol):
        """return a pre-made sound, or generate and return"""
        try:
            return self.stimuli['generated_sounds'][(freq, dur, vol)]
        except KeyError:
            newSound = sound.Sound(value=freq, secs=dur, volume=vol)
            self.stimuli['generated_sounds'][(freq, dur, vol)] = newSound
            return newSound

    def send_code(self, code=1, duration=0.005, stimulus=None):
        """Send a code and clear it after duration, use code from stimulus if
        it exists"""
        if stimulus:
            self.port.setData(stimulus['PortCode'])
        else:
            self.port.setData(code)
        core.wait(duration)
        self.port.setData(0)

    def check_keys(self, response_window=None, timer=None, keymap=None, quitkey='escape'):
        """Wait for first keypress or timer, return keypress details"""
        if not timer:
            timer = self.clock
        event.clearEvents()
        while timer.getTime() < response_window:
            allkeys = set(keymap.keys()) | {quitkey}
            theseKeys = event.getKeys(keyList=allkeys, timeStamped=timer)
            # check for quit:
            for key, _ in theseKeys:
                if key == quitkey:
                    self.cleanQuit()
            if len(theseKeys) > 0:  # at least one key was pressed
                # grab just the first key pressed
                key, rt = theseKeys[0]
                # was this 'correct'?
                corr = keymap[key]
                return dict(Correct=corr, Key=key, ReactionTime=rt)
        return dict(Correct=0)

    def runTask(self):
        # SAMPLE PSEUDOCODE
        # for block in self.blocks
        #     self.send_code(code=254)
        #     for stimulus in block:
        #         soundspec = [stimulus[k] for k in ['Frequency', 'Duration', 'Volume']]
        #         thisSound = self.getSound(stimulus)
        #         for key, val in stimulus.items():
        #             self.handler.addData(key, val)
        #         while soaClock.getTime() > 0:
        #             timeleft = soaClock.getTime()
        #             if timeleft > 0.2:
        #                 core.wait(timeleft-0.2, hogCPUperiod=0.2)
        #         soaClock.reset()  # clock
        #         self.handler.addData('Timestamp', self.clock.getTime())
        #         thisSound.play()
        #         self.send_code(stimulus=stimulus)
        #         self.handler.nextEntry()
        #     self.send_code(code=255)
        pass

    def cleanQuit(self):
        """Cleanly quit psychopy and run any internal cleanup"""
        # Finalising data writing etc
        # these shouldn't be strictly necessary (should auto-save)
        self.handler.saveAsWideText(self.filename+'.csv')
        self.handler.saveAsPickle(self.filename)
        logging.flush()
        # make sure everything is closed down
        self.handler.abort()  # or data files will save again on exit
        self.win.close()
        core.quit()

    def run(self, debug=False):
        """Run the whole experiment"""
        # Setup
        self.buildStimuli()
        self.runTask()
        self.cleanQuit()


if __name__ == '__main__':
    exp = Experiment()
    exp.run()
