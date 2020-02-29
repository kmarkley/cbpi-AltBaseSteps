# -*- coding: utf-8 -*-
################################################################################
import time

from modules.core.props import Property, StepProperty
from modules.core.step import StepBase
from modules import cbpi

################################################################################
@cbpi.step
class AltMashInStep(StepBase):
    # Properties
    a_kettle_prop = StepProperty.Kettle("Kettle", description="Kettle in which the mashing takes place")
    b_target_prop = Property.Number("Temperature", configurable=True, description="Target Temperature of Mash Step")
    c_agitator_prop = Property.Select("Run agitator while heating?", options=["Yes","No"])
    d_kill_heat_prop = Property.Select("Turn off heater when target reached?", options=["Yes","No"])

    #-------------------------------------------------------------------------------
    def init(self):
        self.kettle = int(self.a_kettle_prop)
        self.target = float(self.b_target_prop)
        self.agitator_run = self.c_agitator_prop == "Yes"
        self.kill_heat = self.d_kill_heat_prop == "Yes"
        self.done = False

        self.agitator = zint(cbpi.cache.get("kettle")[self.kettle].agitator)

        # set target temp
        self.set_target_temp(self.target, self.kettle)
        if self.agitator and self.agitator_run:
            self.actor_on(self.agitator)

    #-------------------------------------------------------------------------------
    def finish(self):
        self.set_target_temp(0, self.kettle)

    #-------------------------------------------------------------------------------
    def execute(self):
        # Check if Target Temp is reached
        if (self.get_kettle_temp(self.kettle) >= self.target) and (self.done is False):
            self.done = True
            if self.kill_heat:
                self.set_target_temp(0, self.kettle)
            if self.agitator:
                self.actor_off(self.agitator)
            self.notify("{} complete".format(self.name), "Press next button to continue", type='warning', timeout=None)

################################################################################
@cbpi.step
class AltMashStep(StepBase):
    # Properties
    a_kettle_prop = StepProperty.Kettle("Kettle", description="Kettle in which the mashing takes place")
    b_target_prop = Property.Number("Temperature", configurable=True, description="Target Temperature of Mash Step")
    c_timer_prop = Property.Number("Timer in minutes", configurable=True, description="Amount of time to maintain taget temperature in this step")
    d_offset_prop = Property.Number("Target timer offset", configurable=True, default_value=0, description="Start timer when temperature is this close to target. Useful for PID heaters that approach target slowly.")
    e_agitator_start_prop = Property.Select("Turn agitator on at start?", options=["Yes","No"])
    f_agitator_stop_prop = Property.Select("Turn agitator off at end?", options=["Yes","No"])
    #-------------------------------------------------------------------------------
    def init(self):
        self.kettle = int(self.a_kettle_prop)
        self.target = float(self.b_target_prop)
        self.timer = float(self.c_timer_prop)
        self.offset = float(self.d_offset_prop)
        self.agitator_start = self.e_agitator_start_prop == "Yes"
        self.agitator_stop = self.f_agitator_stop_prop == "Yes"

        self.agitator = zint(cbpi.cache.get("kettle")[self.kettle].agitator)

        # set target temp
        self.set_target_temp(self.target, self.kettle)
        if self.agitator and self.agitator_start:
            self.actor_on(self.agitator)

    #-------------------------------------------------------------------------------
    @cbpi.action("Start Timer Now")
    def start(self):
        if self.is_timer_finished() is None:
            self.start_timer(self.timer * 60)

    #-------------------------------------------------------------------------------
    def reset(self):
        self.stop_timer()
        self.set_target_temp(self.target, self.kettle)

    #-------------------------------------------------------------------------------
    def finish(self):
        self.set_target_temp(0, self.kettle)
        if self.agitator and self.agitator_stop:
            self.actor_off(self.agitator)

    #-------------------------------------------------------------------------------
    def execute(self):
        # Check if Target Temp is reached
        if self.get_kettle_temp(self.kettle) >= self.target - self.offset:
            # Check if Timer is Running
            if self.is_timer_finished() is None:
                self.start_timer(self.timer * 60)

        # Check if timer finished and go to next step
        if self.is_timer_finished() is True:
            self.notify("{} complete".format(self.name), "Starting the next step", type='success', timeout=None)
            self.next()

################################################################################
@cbpi.step
class AltBoilStep(StepBase):
    # Properties
    textDesc = "Brief description of the addition"
    timeDesc = "Time in minutes before end of boil"
    add_1_text = Property.Text("Addition 1 Name", configurable=True, description = textDesc)
    add_1_time = Property.Number("Addition 1 Time", configurable=True, description = timeDesc)
    add_2_text = Property.Text("Addition 2 Name", configurable=True, description = textDesc)
    add_2_time = Property.Number("Addition 2 Time", configurable=True, description = timeDesc)
    add_3_text = Property.Text("Addition 3 Name", configurable=True, description = textDesc)
    add_3_time = Property.Number("Addition 3 Time", configurable=True, description = timeDesc)
    add_4_text = Property.Text("Addition 4 Name", configurable=True, description = textDesc)
    add_4_time = Property.Number("Addition 4 Time", configurable=True, description = timeDesc)
    add_5_text = Property.Text("Addition 5 Name", configurable=True, description = textDesc)
    add_5_time = Property.Number("Addition 5 Time", configurable=True, description = timeDesc)
    add_6_text = Property.Text("Addition 6 Name", configurable=True, description = textDesc)
    add_6_time = Property.Number("Addition 6 Time", configurable=True, description = timeDesc)
    add_7_text = Property.Text("Addition 7 Name", configurable=True, description = textDesc)
    add_7_time = Property.Number("Addition 7 Time", configurable=True, description = timeDesc)
    add_8_text = Property.Text("Addition 8 Name", configurable=True, description = textDesc)
    add_8_time = Property.Number("Addition 8 Time", configurable=True, description = timeDesc)

    kettle_prop = StepProperty.Kettle("Kettle", description="Kettle in which the boiling step takes place")
    target_prop = Property.Number("Temperature", configurable=True, description="Target temperature for boiling")
    timer_prop = Property.Number("Timer in Minutes", configurable=True, default_value=90, description="Timer is started when target temperature is reached")

    warning_addition_prop = Property.Number("Addition Warning", configurable=True, default_value=30, description="Time in seconds to warn before each addition")
    warning_boil_prop = Property.Number("Boil Warning", configurable=True, default_value=1, description="Degrees below target to warn of impending boil")

    #-------------------------------------------------------------------------------
    def init(self):

        self.target = float(self.target_prop)
        self.kettle = int(self.kettle_prop)
        self.timer = float(self.timer_prop) * 60.0
        self.warn_add = float(self.warning_addition_prop)
        self.warn_boil = float(self.warning_boil_prop)

        self.done_boil_warn = False
        self.done_boil_alert = False

        # set the additions dictionary
        self.additions = dict()
        for i in range(1,9):
            additionTime = self.__getattribute__("add_{}_time".format(i))
            additionText = self.__getattribute__("add_{}_text".format(i))
            try:
                if additionText is None:
                    additionText = "Addition {}".format(i)
                self.additions[i] = {
                    'text': additionText,
                    'time': float(additionTime) * 60.0,
                    'mins': int(additionTime),
                    'done': False,
                    'warn': False,
                }
            except:
                # empty or invalid addition
                pass
        # set target temp
        self.set_target_temp(self.target, self.kettle)

    #-------------------------------------------------------------------------------
    @cbpi.action("Start Timer Now")
    def start(self):
        if self.is_timer_finished() is None:
            self.start_timer(self.timer)

    #-------------------------------------------------------------------------------
    def reset(self):
        self.stop_timer()
        self.set_target_temp(self.target, self.kettle)

    #-------------------------------------------------------------------------------
    def finish(self):
        self.set_target_temp(0, self.kettle)

    #-------------------------------------------------------------------------------
    def execute(self):
        # Check if Target Temp is reached
        if self.is_timer_finished() is None:
            self.check_boil_warnings()
            if self.get_kettle_temp(self.kettle) >= self.target:
                self.start_timer(self.timer)
        elif self.is_timer_finished() is True:
            self.notify("{} complete".format(self.name), "Starting the next step", type='success', timeout=None)
            self.next()
        else:
            self.check_addition_timers()

    #-------------------------------------------------------------------------------
    def check_addition_timers(self):
        for i in self.additions:
            addition_time = self.timer_end - self.additions[i]['time']
            warning_time = addition_time - self.warn_add
            now = time.time()
            if not self.additions[i]['warn'] and now > warning_time:
                self.additions[i]['warn'] = True
                self.notify("Warning: {} min Additions".format(self.additions[i]['mins']),
                            "Add {} in {} seconds".format(self.additions[i]['text'],self.warn_add),
                            type='info', timeout=(self.warn_add - 1)*1000)
            if not self.additions[i]['done'] and now > addition_time:
                self.additions[i]['done'] = True
                self.notify("Alert: {} min Additions".format(self.additions[i]['mins']),
                            "Add {} now".format(self.additions[i]['text']),
                            type='warning', timeout=None)

    #-------------------------------------------------------------------------------
    def check_boil_warnings(self):
        if (not self.done_boil_warn) and (self.get_kettle_temp(self.kettle) >= self.target - self.warn_boil):
            self.notify("Warning: Boil Approaching", "Current Temp {:.1f}".format(self.get_kettle_temp(self.kettle)),
                        type="info", timeout=self.warn_add*1000)
            self.done_boil_warn = True
        if (not self.done_boil_alert) and (self.get_kettle_temp(self.kettle) >= self.target):
            self.notify("Alert: Boil Imminent", "Current Temp {:.1f}".format(self.get_kettle_temp(self.kettle)),
                        type="warning", timeout=None)
            self.done_boil_alert = True

################################################################################
# Utilities
################################################################################
def zint(value):
    try: return int(float(value))
    except: return 0
