import csv
import os

class Formatting:
    def __init__(self, num_leagues=30):
        self.num_leagues = num_leagues
        clanker_ordered_leagues = [
            # International events
            'wlds.csv', 'msi.csv', 'ewc.csv', 'asia_master.csv',

            # Top-tier regional leagues
            'lck.csv', 'lpl.csv', 'lec.csv', 'lcp.csv', 'lta.csv', 'lta_n.csv',
            'lta_s.csv', 'lcs.csv', 'na_lcs.csv', 'eu_lcs.csv', 'cblol.csv',
            'ljl.csv', 'pcs.csv', 'vcs.csv', 'lms.csv', 'lcl.csv', 'lla.csv',
            'las.csv', 'lco.csv', 'tcl.csv', 'lplol.csv',

            # Second-tier leagues and developmental tournaments
            'lckc.csv', 'ldl.csv', 'eum.csv', 'em.csv', 'lfl.csv', 'lvp_sl.csv',
            'prm.csv', 'ebl.csv', 'nlc.csv', 'hll.csv', 'tal.csv', 'lit.csv',
            'lfl2.csv', 'uklc.csv', 'slo.csv', 'lrn.csv', 'lrs.csv', 'lhe.csv',
            'cblola.csv', 'ljlcs.csv', 'ljla.csv', 'lcsa.csv', 'nacl.csv',
            'nasg.csv', 'nlc_aurora_open.csv', 'ocs.csv', 'opl.csv', 'pgn.csv',
            'prmp.csv', 'upl.csv', 'eslol.csv', 'el.csv', 'epl.csv',
            'sl_(latam).csv', 'gll.csv', 'gllpa.csv', 'lmf.csv', 'ignis.csv',
            'nerd.csv', 'nest.csv', 'les.csv', 'lgl.csv', 'lln.csv', 'cls.csv',
            'kespa.csv', 'kespa_cup.csv', 'tcs.csv',

            # Minor regional, collegiate and amateur competitions
            'gpl.csv', 'cisc.csv', 'cd.csv', 'al.csv', 'asci.csv', 'ct.csv',
            'cu.csv', 'gsg.csv', 'ul.csv', 'brcc.csv', 'eblpa.csv', 'fst.csv',
            'ddh.csv', 'riot.csv', 'hw.csv', 'rl.csv', 'gl.csv', 'hc.csv',
            'ccws.csv', 'ic.csv', 'aol.csv', 'dcup.csv', 'ugp.csv', 'pcl.csv',
            'dl.csv', 'rol.csv', 'big.csv', 'hm.csv', 'usp.csv', 'rcl.csv',
            'vl.csv', 'msc.csv', 'tsc.csv', 'cdf.csv', 'pgc.csv', 'egl.csv',
            'asi.csv', 'nexo.csv', 'ck.csv', 'ac.csv', 'nl.csv', 'otblx.csv',
            'bm.csv', 'bl.csv',
        ]

        self.files_dir = "output"
        league_files = [f for f in os.listdir(self.files_dir) if f in clanker_ordered_leagues[:self.num_leagues]]
        self.files = [os.path.join(self.files_dir, f) for f in league_files]

        self.type_fixed_dir = "correct_types"
        self.typeFixed = [os.path.join(self.type_fixed_dir, f) for f in league_files]

        self.winnerFixed_dir = "prev_data"
        self.winnerFixed = [os.path.join(self.winnerFixed_dir, f) for f in league_files]

        self.vectorised_dir = "vectorised"
        self.vectorised = [os.path.join(self.vectorised_dir, f) for f in league_files]

        self.one_line_files_dir = "oneLine_data"
        self.one_line_files = [os.path.join(self.one_line_files_dir, f) for f in league_files]


        self.correct_format = ['row_type', 'gameid', 'league', 'split', 'playoffs', 'game_in_series', 'series_score_before_game', 'patch', 'datetime', 'url', 'datacompleteness', 'team1_blue', 'team2_red', 'winner', 'gamelength_sec', 'team1_patch_winrate', 'team2_patch_winrate', 'head_to_head', 'team1_last5', 'team2_last5', 'lpl_limited_objectives', 'ban_b1', 'ban_r1', 'ban_b2', 'ban_r2', 'ban_b3', 'ban_r3', 'ban_b4', 'ban_r4', 'ban_b5', 'ban_r5', 'draft_pick_1', 'draft_pick_2', 'draft_pick_3', 'draft_pick_4', 'draft_pick_5', 'draft_pick_6', 'draft_pick_7', 'draft_pick_8', 'draft_pick_9', 'draft_pick_10', 'blue_top_pick', 'blue_jng_pick', 'blue_mid_pick', 'blue_bot_pick', 'blue_sup_pick', 'red_top_pick', 'red_jng_pick', 'red_mid_pick', 'red_bot_pick', 'red_sup_pick', 'blue_gamelength', 'blue_result', 'blue_teamkills', 'blue_teamdeaths', 'blue_firstblood', 'blue_firstbloodkill', 'blue_firstbloodassist', 'blue_firstbloodvictim', 'blue_team kpm', 'blue_ckpm', 'blue_firstdragon', 'blue_dragons', 'blue_opp_dragons', 'blue_elementaldrakes', 'blue_opp_elementaldrakes', 'blue_infernals', 'blue_mountains', 'blue_clouds', 'blue_oceans', 'blue_chemtechs', 'blue_hextechs', 'blue_dragons (type unknown)', 'blue_elders', 'blue_opp_elders', 'blue_firstherald', 'blue_heralds', 'blue_opp_heralds', 'blue_void_grubs', 'blue_opp_void_grubs', 'blue_firstbaron', 'blue_barons', 'blue_opp_barons', 'blue_atakhans', 'blue_opp_atakhans', 'blue_firsttower', 'blue_towers', 'blue_opp_towers', 'blue_firstmidtower', 'blue_firsttothreetowers', 'blue_turretplates', 'blue_opp_turretplates', 'blue_inhibitors', 'blue_opp_inhibitors', 'red_gamelength', 'red_result', 'red_teamkills', 'red_teamdeaths', 'red_firstblood', 'red_firstbloodkill', 'red_firstbloodassist', 'red_firstbloodvictim', 'red_team kpm', 'red_ckpm', 'red_firstdragon', 'red_dragons', 'red_opp_dragons', 'red_elementaldrakes', 'red_opp_elementaldrakes', 'red_infernals', 'red_mountains', 'red_clouds', 'red_oceans', 'red_chemtechs', 'red_hextechs', 'red_dragons (type unknown)', 'red_elders', 'red_opp_elders', 'red_firstherald', 'red_heralds', 'red_opp_heralds', 'red_void_grubs', 'red_opp_void_grubs', 'red_firstbaron', 'red_barons', 'red_opp_barons', 'red_atakhans', 'red_opp_atakhans', 'red_firsttower', 'red_towers', 'red_opp_towers', 'red_firstmidtower', 'red_firsttothreetowers', 'red_turretplates', 'red_opp_turretplates', 'red_inhibitors', 'red_opp_inhibitors', 'playername', 'participantid', 'side', 'position', 'champion', 'firstpick', 'player_result', 'has_snapshot_data', 'champion_patch_winrate', 'kills', 'deaths', 'assists', 'doublekills', 'triplekills', 'quadrakills', 'pentakills', 'firstblood', 'firstbloodkill', 'firstbloodassist', 'firstbloodvictim', 'damagetochampions', 'dpm', 'damageshare', 'damagetakenperminute', 'damagemitigatedperminute', 'damagetotowers', 'wardsplaced', 'wpm', 'wardskilled', 'wcpm', 'controlwardsbought', 'visionscore', 'vspm', 'totalgold', 'earnedgold', 'earned gpm', 'earnedgoldshare', 'goldspent', 'gspd', 'gpr', 'total cs', 'minionkills', 'monsterkills', 'monsterkillsownjungle', 'monsterkillsenemyjungle', 'cspm', 'goldat10', 'xpat10', 'csat10', 'opp_goldat10', 'opp_xpat10', 'opp_csat10', 'golddiffat10', 'xpdiffat10', 'csdiffat10', 'killsat10', 'assistsat10', 'deathsat10', 'opp_killsat10', 'opp_assistsat10', 'opp_deathsat10', 'goldat15', 'xpat15', 'csat15', 'opp_goldat15', 'opp_xpat15', 'opp_csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15', 'killsat15', 'assistsat15', 'deathsat15', 'opp_killsat15', 'opp_assistsat15', 'opp_deathsat15', 'goldat20', 'xpat20', 'csat20', 'opp_goldat20', 'opp_xpat20', 'opp_csat20', 'golddiffat20', 'xpdiffat20', 'csdiffat20', 'killsat20', 'assistsat20', 'deathsat20', 'opp_killsat20', 'opp_assistsat20', 'opp_deathsat20', 'goldat25', 'xpat25', 'csat25', 'opp_goldat25', 'opp_xpat25', 'opp_csat25', 'golddiffat25', 'xpdiffat25', 'csdiffat25', 'killsat25', 'assistsat25', 'deathsat25', 'opp_killsat25', 'opp_assistsat25', 'opp_deathsat25']

        self.game = [2, 4, 5, 6, 7, 8, 12, 13, 14, 16, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 55, 56, 57, 61, 62, 63, 64, 66, 67, 68, 69, 70, 71, 73, 74, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 88, 89, 94, 95, 97, 99, 100, 101, 102, 103, 104, 106, 109, 111, 112, 114, 117, 118]
        self.player = [119, 124, 127, 128, 129, 130, 131, 132, 133, 134, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 159, 160, 161, 162, 163, 164, 165, 166, 167, 171, 172, 173, 174, 175, 176, 180, 181, 182, 186, 187, 188, 189, 190, 191, 195, 196, 197, 201, 202, 203, 204, 205, 206, 210, 211, 212, 216, 217, 218, 219, 220, 221]
        
        to_count = [["split"], ["team1_blue", "team2_red"], ["playername"]]
        to_count.append("ban_b1	ban_r1	ban_b2	ban_r2	ban_b3	ban_r3	ban_b4	ban_r4	ban_b5	ban_r5	draft_pick_1	draft_pick_2	draft_pick_3	draft_pick_4	draft_pick_5	draft_pick_6	draft_pick_7	draft_pick_8	draft_pick_9	draft_pick_10	blue_top_pick	blue_jng_pick	blue_mid_pick	blue_bot_pick	blue_sup_pick	red_top_pick	red_jng_pick	red_mid_pick	red_bot_pick	red_sup_pick".split())

        self.default_to_count = to_count

        # Some constants
        self.TO_FIX = ["league", "patch", "head_to_head", "team1_last5", "team2_last5", "series_score_before_game"]
        self.TIME_CATEGORIES = [['league', 'playoffs', 'game_in_series', 'series_score_before_game', 'patch', 'head_to_head', 'team1_last5', 'team2_last5', 'firstpick', 'champion_patch_winrate'], ['goldat10', 'xpat10', 'csat10', 'golddiffat10', 'xpdiffat10', 'csdiffat10', 'killsat10', 'assistsat10', 'deathsat10', 'goldat15', 'xpat15', 'csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15', 'killsat15', 'assistsat15', 'deathsat15', 'goldat20', 'xpat20', 'csat20', 'golddiffat20', 'xpdiffat20', 'csdiffat20', 'killsat20', 'assistsat20', 'deathsat20', 'goldat25', 'xpat25', 'csat25', 'golddiffat25', 'xpdiffat25', 'csdiffat25', 'killsat25', 'assistsat25', 'deathsat25'], ['winner', 'gamelength_sec', 'blue_teamkills', 'blue_teamdeaths', 'blue_firstblood', 'blue_team kpm', 'blue_ckpm', 'blue_firstdragon', 'blue_dragons', 'blue_infernals', 'blue_mountains', 'blue_clouds', 'blue_oceans', 'blue_chemtechs', 'blue_hextechs', 'blue_elders', 'blue_firstherald', 'blue_void_grubs', 'blue_firstbaron', 'blue_barons', 'blue_atakhans', 'blue_firsttower', 'blue_towers', 'blue_firstmidtower', 'blue_firsttothreetowers', 'blue_turretplates', 'blue_inhibitors', 'red_teamkills', 'red_teamdeaths', 'red_team kpm', 'red_ckpm', 'red_dragons', 'red_infernals', 'red_mountains', 'red_clouds', 'red_oceans', 'red_chemtechs', 'red_hextechs', 'red_elders', 'red_void_grubs', 'red_barons', 'red_atakhans', 'red_towers', 'red_turretplates', 'red_inhibitors', 'kills', 'deaths', 'assists', 'doublekills', 'triplekills', 'quadrakills', 'pentakills', 'firstbloodkill', 'firstbloodassist', 'firstbloodvictim', 'damagetochampions', 'dpm', 'damageshare', 'damagetakenperminute', 'damagemitigatedperminute', 'damagetotowers', 'wardsplaced', 'wpm', 'wardskilled', 'wcpm', 'controlwardsbought', 'visionscore', 'vspm', 'totalgold', 'earnedgold', 'earned gpm', 'earnedgoldshare', 'goldspent', 'gspd', 'total cs', 'minionkills', 'monsterkills', 'monsterkillsownjungle', 'monsterkillsenemyjungle', 'cspm']]

    def main(self):
        #self.decide_IO()
        pass

    def from_winner_fix(self):
        to_count = [["split"], ["team1_blue", "team2_red"], ["playername"]]
        to_count.append("ban_b1	ban_r1	ban_b2	ban_r2	ban_b3	ban_r3	ban_b4	ban_r4	ban_b5	ban_r5	draft_pick_1	draft_pick_2	draft_pick_3	draft_pick_4	draft_pick_5	draft_pick_6	draft_pick_7	draft_pick_8	draft_pick_9	draft_pick_10	blue_top_pick	blue_jng_pick	blue_mid_pick	blue_bot_pick	blue_sup_pick	red_top_pick	red_jng_pick	red_mid_pick	red_bot_pick	red_sup_pick".split())

        for file in self.winnerFixed:
            self.format(file)
        self.format("all.csv")

        for file in self.typeFixed:
            self.vectorise(file, to_count)
        self.vectorise("all.csv", to_count)

    def decide_IO(self):
        with open(self.vectorised[0], "r") as f:
            print("reading " + self.vectorised[0])
            reader = csv.reader(f)
            labels_bad = self.linIndex(reader, 0)
            good = []
            for item in labels_bad:
                if not item.isnumeric():
                    good.append(item)

        self.manual_classify(list(dict.fromkeys(good)), 3, "1-BEFORE, 2-Mid, 3-AFTER ")

    def get_league_name(self, file):
        return self.get_file_name(file).split(".")[0]

    def linIndex(self, enumerable, index):
        count = 0
        for row in enumerable:            
            if count == index:
                return row
            count += 1

        raise IndexError
            
    def checkFormat(self):
        for file in self.files:
            with open(file, "r") as f:
                reader = csv.reader(f)
                data_points = self.linIndex(reader, 0)
                if not (data_points == self.correct_format):
                    print(file + " is wrong.")
                else:
                    print(file + " is correct")

    def decide_useful(self):
        with open('lec.csv', 'r', newline='') as f:
            reader = csv.reader(f)
            data_points = self.linIndex(reader, 0)

        game = set({})
        player = set({})

        index = 0 

        while (index < len(data_points)):
            decision = input(data_points[index] + "                 b = back,  a = game,  s = player    ")
            if decision == "b":
                index -= 2
            elif decision == "a":
                game.add(index)
            elif decision == "s":
                player.add(index)
            else:
                if index in game:
                    game.remove(index)
                if index in player:
                    player.remove(index)

            index += 1

        print(game)
        print(player)

        game = list(game)
        game.sort()
        player = list(player)
        player.sort()

        print()
        print()
        print(game)
        print()
        print()
        print(player)

    def tempReadTxt(self):
        count = 0
        game = []
        player = []

        with open("classified.txt", "r") as f:
            for line in f.readlines():
                x = line.strip()[-1]
                if x == "a":
                    game.append(count)
                if x == "s":
                    player.append(count)

                count += 1

        print(game)
        print(player)

    def intoOneLine(self, file):
        with open("oneLine_data/" + self.get_file_name(file), "w", newline="") as fw:
            print("writing to oneLine_" + file)
            with open(file, "r") as f:
                print("reading from " + file)
                reader = csv.reader(f)
                writer = csv.writer(fw)

                finData = [[]]
                count = 0


                for row in reader:
                    if count == 0: # Adds labels
                        labels = []
                        playerLabels = []
                        for (index, value) in enumerate(row):
                            if index in self.game:
                                labels.append(value)
                            elif index in self.player:
                                playerLabels.append(value)
                        labels = labels + (playerLabels * 10)
                        writer.writerow(labels)

                    elif (count - 1) % 11 == 0:
                        # Game
                        finData.append([])
                        for (index, item) in enumerate(row):
                            if index in self.game:
                                finData[-1].append(item)

                    else:
                        for (index, item) in enumerate(row):
                            if index in self.player:
                                finData[-1].append(item)

                        if (count - 1) % 11 == 10: # Final row of the game
                            writer.writerow(finData[-1])

                    count += 1



    def oneLineAll(self):
        for file in self.files:
            try:
                self.intoOneLine(file)
            except Exception as e:
                print("error in file: " + file)
                print(e)

    def get_mapping(self, file): # In oneLine csv, index to name and vice versa
        print("getting mapping for " + file)
        mapping = {}
        with open(file, "r") as f:
            reader = csv.reader(f)
            names = self.linIndex(reader, 0)
            for (index, name) in enumerate(names):
                mapping[index] = [name]
                if name in mapping:
                    mapping[name].append(index)
                else:
                    mapping[name] = [index]

        return mapping

    def unique(self, file, col_names):
        names = set({})
        with open(file, "r") as f:
            reader = csv.reader(f)
            next(reader)
            indeces = []
            for name in col_names:
                indeces.extend(self.get_mapping(file)[name])
            for row in reader:
                for index in indeces:
                    value = row[index]
                    if value != "": # Data missing if value == ""
                        names.add(row[index])

        return names

    def get_label_to_options_mapping(self, file, to_count):
        # Maps the column label to the possible choices.
        rowToOptionsMap = {}
        for count in to_count:
            unique = self.unique(file, count)
            for item in count:
                rowToOptionsMap[item] = unique

        return rowToOptionsMap

    def vectorise(self, file_IDK, to_fix, default_files="Y"):
        file = file_IDK
        # An element of col_names is a list. This list contains column names with shared datatypes.
        if default_files == "Y":
            write_file = "vectorised/" + self.get_file_name(file)
            read_file = "correct_types/" + self.get_file_name(file)
            file = read_file
        elif default_files == "N":
            write_file = file + "_vectorised.csv"
            read_file = file + ".csv"
            file = "correct_types/all.csv"

        with open(write_file, "w") as fw:
            with open(read_file, "r") as f:
                print("writing to " + write_file)
                print("reading from " + read_file)
                reader = csv.reader(f)
                writer = csv.writer(fw)
                oneLineCsvMap = self.get_mapping(file)
                rowToChoices = self.get_label_to_options_mapping(file, to_fix)

                for (row_index, row) in enumerate(reader):
                    new_row = []
                    for (index,item) in enumerate(row):
                        # Check if the column should be turned into a one-hot
                        column = oneLineCsvMap[index][0]
                        if column in rowToChoices:
                            choices = list(rowToChoices[column])
                            if row_index == 0:
                                oneHot = [item for _ in range(len(choices))]
                            elif item != "":
                                choices.sort()
                                if item not in choices:
                                    oneHotLocation = list(map(str.lower, choices)).index(item.lower())
                                    print(choices)
                                else:
                                    oneHotLocation = choices.index(item)
                                oneHot = [1 if y == oneHotLocation else 0 for y in range(len(choices))]
                            else:
                                oneHot = [0 for _ in range(len(choices))] 
                            new_row.extend(oneHot)
                        else:
                            new_row.append(item)
                    writer.writerow(new_row)

        return write_file

    def fix_winner(self, file):
        # Rather than being the team name, I want it to just be -1 or 1 for team1/team2
        writeFile = "prev_data/" + self.get_file_name(file)
        readFile = "oneLine_data/" + self.get_file_name(file)

        with open(writeFile, "w") as fw:
            with open(readFile, "r") as f:
                print("writing to " + writeFile)
                print("reading from " + readFile)
                reader = csv.reader(f)
                writer = csv.writer(fw)

                mapping = self.get_mapping(readFile)
                for (index, row) in enumerate(reader):
                    new_row = []
                    if index != 0:
                        for (col_num, item) in enumerate(row):
                            label = mapping[col_num][0]
                            if label == "team1_blue":
                                team1 = item
                            elif label == "team2_red":
                                team2 = item
                            if label == "winner":
                                winner = item
                                if winner == team1:
                                    new_row.append(-1)
                                elif winner == team2:
                                    new_row.append(1)
                                else: 
                                    print(f"in {file} winner={winner}, team1={team1}, team2={team2} on row {index}")
                                    print("Winner left empty? Putting a -1")
                                    new_row.append(-1)
                            else:
                                new_row.append(item)
                    else:
                        new_row = row

                    writer.writerow(new_row)

    def combineAll(self): 
        with open("oneLine_data/all.csv", "w") as fw:
            print("writing to oneLine_data/all.csv")
            writer = csv.writer(fw)
            first = True
            for file in self.one_line_files:
                print("reading from " + file)
                with open(file, "r") as f:
                    reader = csv.reader(f)
                    for (index, row) in enumerate(reader):
                        if index != 0:
                            writer.writerow(row)
                        elif first:
                            writer.writerow(row)
                            first = False

    def get_file_name(self, filename):
        return filename.split("/")[-1]

    def format(self, file):
        # Make everything a float/int
        # league
        # patch
        # head-to-head
        # team1_last5
        # team2_last5
        # self.TO_FIX = ["league", "patch", "head-to-head", "team1_last5", "team2_last5", "game_in_series"]
        
        write_file = "correct_types/" + self.get_file_name(file)
        read_file = "prev_data/" + self.get_file_name(file)

        label_index_mapping = self.get_mapping(read_file)

        with open(write_file, "w") as fw:
            with open(read_file, "r") as f:
                print("writing to  " + write_file)
                print("reading from " + read_file)
                reader = csv.reader(f)
                writer = csv.writer(fw)

                for (row_index, row) in enumerate(reader):
                    if row_index == 0:
                        new_row = row
                        pass
                    else:
                        new_row = []
                        for (column_index, item) in enumerate(row):
                            if label_index_mapping[column_index][0] in self.TO_FIX:
                                new_row.append(self.format_item(item, self.TO_FIX.index(label_index_mapping[column_index][0])))
                            else:
                                new_row.append(item)

                    writer.writerow(new_row)

    def format_item(self, item, index):
        # self.TO_FIX = ["league", "patch", "head-to-head", "team1_last5", "team2_last5", "series_score_before_game"]
        try:
            match index:
                case 0:
                    return 0      # FIX THIS LATER 
                case 1:
                    try: 
                        (major, minor) = item.split(".")
                        return int(major)*100 + int(minor)
                    except ValueError:
                        print("something went wrong with patch formatting")
                        return 1200
                case 2 | 5: 
                    # X-Y
                    t1_wins = item.split("-")[0]
                    t2_wins = item.split("-")[1]
                    return int(t2_wins) - int(t1_wins)
                case 3 | 4:
                    # XW-YL
                    new = item.split("W-")
                    wins =  new[0]
                    losses = new[1][:-1]
                    return int(wins) - int(losses)
        except Exception as e:
            print(item)
            raise e

    def manual_classify(self, labels: list, num_categories: int, explanation) -> list:
        # Given a list, takes user input to decide what category something belongs in.
        print(explanation)
        print(len(labels))
        categorised = [[] for _ in range(num_categories)]

        for x in range(len(labels)):
            print(f"{x} - {labels[x]}")

        for y in range(num_categories-1):
            choice = input(f"for category {y+1}?")
            for index in choice.split(","):
                r = index.split("-")
                if len(r) == 1:
                    categorised[y].append(labels[int(r[0])])
                else:
                    categorised[y].extend(labels[int(r[0]):int(r[1])+1])

        for x in range(len(labels)):
            hasC = False
            for c in categorised:
                if labels[x] in c:
                    hasC = True

            if not hasC:
                categorised[-1].append(labels[x])

        print(categorised)

#bob.decide_useful()
#bob.tempReadTxt()

bob = Formatting()
#bob.main()