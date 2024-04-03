'''
This module is a development environment for task list creation
'''

class task_generator():
    def __init__(self, create_jobs_from_setup=True, manual_task_list=[]) -> None:
        # Generate tasks from the setup below.
        self.create_jobs_from_setup = create_jobs_from_setup
        if(not create_jobs_from_setup):
            self.tasks = manual_task_list
        else:
            self.tasks = []

            self.configurations = {
                "global" : {
                    "scope_ip"        : "0.0.0.0",
                    "jbert_ip"        : "0.0.0.0",
                    "switch_ip"       : "0.0.0.0",
                    "switch_map_path" : r"switch\map\path",
                    
                },
                "tcss" : {
                    "global" : {
                        "bin_file_destination_folder" : r"bin\dest",
                        "sigtest_results_folder"      : r"sigtest\results\dest"
                    },
                    "TBT10" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 2
                    },
                    "TBT20" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 2
                    },
                    "DP20" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 1
                    }
                },
                "edp" : {
                    "global"  : {
                        "jitter_data_folder" : r"jitter\data\folder",
                        "eye_data_folder"    : r"eye\data\folder",
                    },
                    "8.1" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 0
                    }
                }
            }
            self.corners =  ["NOM","LVHT","LVLT","HVLT","HVHT"] 
            self.phy_s = ["tcss","edp"]
            self.tests = {
                "tcss"  : [
                    "ui_ssc_eye",
                    "rise_fall_time",
                    "jitter",
                    "ac_common_mode",
                    "transmitter_equalization",
                    "electrical_idle_voltage"
                ],
                "edp"   : ["EHEW","Jitters"],
            }
            self.instances = {
                "tcss"  : [1],
                "edp"   : [0],
            }
            self.lanes = {
                "tcss"  : [0,3],
                "edp"   : [0,2],
            }
            self.protocols = {
                "tcss"  : ["TBT20","TBT10","DP20"],
                "edp"   : ["8.1"],
            }
            ##  Create Task List  ##########################################################
            for corner in self.corners:
                for phy in self.phy_s:
                    for instance in self.instances[phy]:
                        for lane in self.lanes[phy]:
                            for protocol in self.protocols[phy]:
                                for test in self.tests[phy]:
                                    new_task = [corner,phy,instance,lane,protocol,test]
                                    #print(f"Adding task to list: {new_task}")
                                    self.tasks.append(new_task)
            ################################################################################
