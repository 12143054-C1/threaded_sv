'''
This module is a test environment for list creation
'''

configurations = {
    "tcss" : {
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
        "8.1" : {
            "scope_preset_path" : r"scope\path",
            "jbert_preset_path" : r"jbert\path",
            "preset" : 0
        }
    }
}

tasks = []
corners =  ["NOM","LVHT","LVLT","HVLT","HVHT"] 
phy_s = ["tcss","edp"]
tests = {
    "tcss"  : ["TCSS_Tx_Base","Tx_EQ_C1"],
    "edp"   : ["TxTestBaseTXEQ_EH_EW","TxTestBaseTxJitterC1"],
}
instances = {
    "tcss"  : [1],
    "edp"   : [0],
}
lanes = {
    "tcss"  : [0,3],
    "edp"   : [1,2],
}
protocols = {
    "tcss"  : ["TBT20","TBT10","DP20"],
    "edp"   : ["8.1"],
}

for corner in corners:
    for phy in phy_s:
        for instance in instances[phy]:
            for lane in lanes[phy]:
                for protocol in protocols[phy]:
                    for test in tests[phy]:
                        new_task = [corner,phy,instance,lane,protocol,test]
                        print(f"Adding task to list: {new_task}")
                        tasks.append(new_task)