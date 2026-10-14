import torch
from test import Formatting
import csv
import numpy as np
import os 

class AI:
    def __init__(self):
        self.TIME_CATEGORIES = [
            ['league', 'playoffs', 'game_in_series', 'series_score_before_game', 'patch', 'head_to_head', 'team1_last5', 'team2_last5', 'firstpick', 'champion_patch_winrate'], 
            ['goldat10', 'xpat10', 'csat10', 'golddiffat10', 'xpdiffat10', 'csdiffat10', 'killsat10', 'assistsat10', 'deathsat10', 'goldat15', 'xpat15', 'csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15', 'killsat15', 'assistsat15', 'deathsat15', 'goldat20', 'xpat20', 'csat20', 'golddiffat20', 'xpdiffat20', 'csdiffat20', 'killsat20', 'assistsat20', 'deathsat20', 'goldat25', 'xpat25', 'csat25', 'golddiffat25', 'xpdiffat25', 'csdiffat25', 'killsat25', 'assistsat25', 'deathsat25'], 
            ['winner', 'gamelength_sec', 'blue_teamkills', 'blue_teamdeaths', 'blue_firstblood', 'blue_team kpm', 'blue_ckpm', 'blue_firstdragon', 'blue_dragons', 'blue_infernals', 'blue_mountains', 'blue_clouds', 'blue_oceans', 'blue_chemtechs', 'blue_hextechs', 'blue_elders', 'blue_firstherald', 'blue_void_grubs', 'blue_firstbaron', 'blue_barons', 'blue_atakhans', 'blue_firsttower', 'blue_towers', 'blue_firstmidtower', 'blue_firsttothreetowers', 'blue_turretplates', 'blue_inhibitors', 'red_teamkills', 'red_teamdeaths', 'red_team kpm', 'red_ckpm', 'red_dragons', 'red_infernals', 'red_mountains', 'red_clouds', 'red_oceans', 'red_chemtechs', 'red_hextechs', 'red_elders', 'red_void_grubs', 'red_barons', 'red_atakhans', 'red_towers', 'red_turretplates', 'red_inhibitors', 'kills', 'deaths', 'assists', 'doublekills', 'triplekills', 'quadrakills', 'pentakills', 'firstbloodkill', 'firstbloodassist', 'firstbloodvictim', 'damagetochampions', 'dpm', 'damageshare', 'damagetakenperminute', 'damagemitigatedperminute', 'damagetotowers', 'wardsplaced', 'wpm', 'wardskilled', 'wcpm', 'controlwardsbought', 'visionscore', 'vspm', 'totalgold', 'earnedgold', 'earned gpm', 'earnedgoldshare', 'goldspent', 'gspd', 'total cs', 'minionkills', 'monsterkills', 'monsterkillsownjungle', 'monsterkillsenemyjungle', 'cspm']
        ]

        self.AFTER_10 = ['goldat15', 'xpat15', 'csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15', 'killsat15', 'assistsat15', 'deathsat15', 'goldat20', 'xpat20', 'csat20', 'golddiffat20', 'xpdiffat20', 'csdiffat20', 'killsat20', 'assistsat20', 'deathsat20', 'goldat25', 'xpat25', 'csat25', 'golddiffat25', 'xpdiffat25', 'csdiffat25', 'killsat25', 'assistsat25', 'deathsat25']
        self.DRAFT_LABELS = ['ban_b1', 'ban_r1', 'ban_b2', 'ban_r2', 'ban_b3', 'ban_r3', 'ban_b4', 'ban_r4', 'ban_b5', 'ban_r5', 'draft_pick_1', 'draft_pick_2', 'draft_pick_3', 'draft_pick_4', 'draft_pick_5', 'draft_pick_6', 'draft_pick_7', 'draft_pick_8', 'draft_pick_9', 'draft_pick_10']
        self.MID_UP_TO_20_NO_DIFF_STATS = ['goldat10', 'xpat10', 'csat10', 'killsat10', 'assistsat10', 'deathsat10', 'goldat15', 'xpat15', 'csat15', 'killsat15', 'assistsat15', 'deathsat15', 'goldat20', 'xpat20', 'csat20', 'killsat20', 'assistsat20', 'deathsat20']
        self.AFTER_25_OR_CONTAINS_DIFF_STATS = ['golddiffat10', 'xpdiffat10', 'csdiffat10', 'golddiffat15', 'xpdiffat15', 'csdiffat15', 'golddiffat20', 'xpdiffat20', 'csdiffat20', 'goldat25', 'xpat25', 'csat25', 'golddiffat25', 'xpdiffat25', 'csdiffat25', 'killsat25', 'assistsat25', 'deathsat25']
        

        self.databox = Formatting()

        self.LEAGUES = ["all", "cblol", "lck", "lcs", "lec", "lpl", "pcs"]

    def convert(self, aString):
        try:
            a = float(aString)
        except:
            a = 0
        return a

    def store_data(self, file, in_ignore, output, directory="tensors/", hard_code_mapping=False):
        if hard_code_mapping:
            mapping = self.databox.get_mapping("vectorised/all.csv")
        else:
            mapping = self.databox.get_mapping(file)


        X = []
        Y = []
        labels = {}
        o_labels = {}
        with open(file, "r") as f:
            reader = csv.reader(f)
            for (rowIndex, row) in enumerate(reader):
                if rowIndex == 0:
                    pass
                else:
                    oneInput = []
                    oneOutput = []
                    for (columnIndex, item) in enumerate(row):
                        label = mapping[columnIndex][0]
                        if not (label in (in_ignore)):
                            labels[label] = ""
                            oneInput.append(self.convert(item))
                        elif (label in output):
                            o_labels[label] = ""
                            oneOutput.append(self.convert(item))
                    X.append(oneInput)
                    Y.append(oneOutput)

        print(labels)    
        print(o_labels)
        tensorX = torch.tensor(X)
        print(tensorX.shape)
        tensorY = torch.tensor(Y)
        print(tensorY.shape)
        torch.save(tensorX, directory + self.databox.get_league_name(file) + "_I")
        torch.save(tensorY, directory + self.databox.get_league_name(file) + "_O")

    def toTensor(self,file, output="winner", directory="tensors/", hard_code_mapping=False):
        self.store_data(file, self.TIME_CATEGORIES[1] + self.TIME_CATEGORIES[2] + self.DRAFT_LABELS, output, directory,hard_code_mapping)

    def toTensorWithMidGame(self,file, output=["winner"], directory="tensors/"):
        self.store_data(file, self.AFTER_10 + self.TIME_CATEGORIES[2] + self.DRAFT_LABELS, output, directory)

    def onlyTensorProcessingWithMidGame(self, directory="tensorsUpTo10/", output=["winner"]):
        if not os.path.exists(directory):
            os.makedirs(directory)

        for file in self.databox.vectorised:
            self.toTensorWithMidGame(file, output, directory)

    def onlyTensorProcessing(self, directory="tensors/", output=["winner"], input_files=[],hard_code_mapping=False):
        if len(input_files) == 0:
            input_files = self.databox.vectorised

        if not os.path.exists(directory):
            os.makedirs(directory)

        for file in input_files:
            self.toTensor(file, output, directory,hard_code_mapping)

    def from_winner_fix(self):
        self.databox.from_winner_fix()
        for file in self.databox.vectorised:
            self.toTensor(file)
        self.toTensor("vectorised/all.csv")
        

    def beginningToEnd(self):
        # GET DATA
        # ONE LINE
        #           COMBINE
        # WINNERFIX
        # FORMAT
        # VECTORISE
        # TO TENSOR



        self.databox.oneLineAll()
        print("all one lined")
        self.databox.combineAll()
        print("combined")
        for file in self.databox.files:
            self.databox.fix_winner(file)
        self.databox.fix_winner("all.csv")
        self.from_winner_fix()




# As far as I'm aware, once you've got berks file, just add it to beginningToEnd().
# Then run that once per day. NOTHING ELSE 
        
bob = AI()
o = ['winner']
o=['goldat10', 'xpat10', 'csat10', 'golddiffat10', 'xpdiffat10', 'csdiffat10', 'killsat10', 'assistsat10', 'deathsat10', 'goldat15', 'xpat15', 'csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15', 'killsat15', 'assistsat15', 'deathsat15', 'goldat20', 'xpat20', 'csat20', 'golddiffat20', 'xpdiffat20', 'csdiffat20', 'killsat20', 'assistsat20', 'deathsat20', 'goldat25', 'xpat25', 'csat25', 'golddiffat25', 'xpdiffat25', 'csdiffat25', 'killsat25', 'assistsat25', 'deathsat25']
dir = "all_mid/"

#bob.beginningToEnd()

bob.onlyTensorProcessing(directory=dir, output=o, input_files=["vectorised/all.csv"])
#bob.onlyTensorProcessing(directory=dir,output=o)