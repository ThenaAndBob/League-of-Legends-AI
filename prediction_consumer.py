import torch
import csv
from test import Formatting
from ai import AI
from classifier import Classifier
import json
from gold_chain import Trainer
from normal_regularising import Regulariser

class Prediction:
    def __init__(self):
        self.databox = Formatting()
        self.tensorStuff = AI()
        self.default_file = "user_input/default_file.csv"
        self.REQUIRED_USER_INPUT_LABELS = ['league', 'split', 'playoffs', 'game_in_series', 'series_score_before_game', 'patch', 'team1_blue', 'team2_red', 'head_to_head', 'team1_last5', 'team2_last5', 'blue_top_pick', 'blue_jng_pick', 'blue_mid_pick', 'blue_bot_pick', 'blue_sup_pick', 'red_top_pick', 'red_jng_pick', 'red_mid_pick', 'red_bot_pick', 'red_sup_pick', 'playername', 'firstpick', 'champion_patch_winrate']
        self.EXAMPLE_REQUIRED_ROW = ['0', 'Spring', '0', '1.0', '0', '1101', 'Gen.G', 'KT', 'Rolster', '-1', '0', '0', '0', 'Camille', 'Taliyah', 'Yone', 'Jhin', 'Sett', 'Gnar', 'Nidalee', 'Orianna', "Kai'Sa", 'Alistar']
        self.EXAMPLE_REQUIRE_ROW_STRING = "0,Spring,0,1.0,0,1101,Gen.G,KT,Rolster,-1,0,0,0,Camille,Taliyah,Yone,Jhin,Sett,Gnar,Nidalee,Orianna,Kai'Sa,Alistar"

        self.default_json_file = "user_input/to_consume.json"
        self.regulariser = Regulariser()

        self.tensor_file_path = "user_input/tensors/"

        self.Gold_Chain = Trainer()

        count = 0
        with open(self.default_file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if count == 0:
                    self.correct_types_labels = row
                else:
                    self.correct_types_example_row = row
                count += 1
        
    def take_new(self):
        # Goal of this is to take a user defined vector, then make a prediction.
        file = "user_input/to_consume.csv"
        with open(file, "r") as f:
            reader = csv.reader(f)

            for row in reader:
                print(self.predict(row))

    def predict(self, vector, model_file_path):
        temp = vector
        temp = temp / self.regulariser.get_std_tensors()    # regularise
        for model_id in range(3):
            output = self.Gold_Chain.predict(model_id, temp)
            print(output.reshape(10,6))
            temp = torch.concat([temp, output])

        my_dict = torch.load(model_file_path)
        shape = my_dict["shape"]
        state = my_dict["state"]
        model = Classifier(shape)

        model.load_state_dict(
            state
        )
        model.eval()
        with torch.inference_mode():
            output = torch.sigmoid(model(temp))

        chance = output.item()
        print(f"{1/(1-chance):.4f}, {1/chance:.4f}")
        print(f"{1-chance:.4f}, {chance:.4f}")
        return output

    def flip_json_teams(self):
        file = self.default_json_file
        new = {}
        picks = ['blue_top_pick', 'blue_jng_pick', 'blue_mid_pick', 'blue_bot_pick', 'blue_sup_pick', 'red_top_pick', 'red_jng_pick', 'red_mid_pick', 'red_bot_pick', 'red_sup_pick']
        new_picks = []
        new_players = []
        new_firstpick = []
        new_winrates = []

        with open(file, "r") as f:
            wrong_way_file = json.load(f)

            for key,value in wrong_way_file.items():
                match key:
                    case "team1_blue":
                        t1 = value
                    case "team2_red":
                        new[key] = t1
                        new["team1_blue"] = value
                    case "head_to_head":
                        new[key] = str(-1*int(value))
                    case "series_score_before_game":
                        new[key] = str(-1*int(value))
                    case _ if key in picks:
                        new_picks.append(value)
                    case "playername":
                        new_players = value
                    case "firstpick":
                        new_firstpick = value
                    case "champion_patch_winrate":
                        new_winrates = value
                    case _:
                        new[key] = value

        for (index, role) in enumerate(picks):
            new[role] = new_picks[(index + 5) % 10]

        new["playername"] = new_players[5:] + new_players[:5]
        new["firstpick"] = new_firstpick[5:] + new_firstpick[:5]
        new["champion_patch_winrate"] = new_winrates[5:] + new_winrates[:5]

        with open("user_input/flipped.json", "w") as f:
            json.dump(new, f, indent=4)

    def format_correctly(self, input_file_use_default=True, file_name=""):
        if input_file_use_default:
            input_file = "user_input/to_consume.json"
        else:
            input_file = file_name
        useless_file = "user_input/to_consume_with_useless_data.csv"


        champ_label_counters = {
            "playername": 0, 
            "firstpick": 0,
            "champion_patch_winrate": 0
        }
        with open(useless_file, "w") as fw:
            with open(input_file, "r") as f:
                user_input = json.load(f)
                writer = csv.writer(fw)
                writer.writerow(self.correct_types_labels)

                new_row = []
                for (useless_index, useless_item) in enumerate(self.correct_types_example_row):
                    label = self.correct_types_labels[useless_index] 
                    if label in user_input:
                        if label in champ_label_counters:
                            index = champ_label_counters[label]
                            new_row.append(user_input[label][index])
                            champ_label_counters[label] += 1
                        else:
                            new_row.append(user_input[label])
                    else:
                        new_row.append(useless_item)

                writer.writerow(new_row)


        if len(useless_file.split(".")) != 2:
            raise TypeError("The file should contain exactly one '.',    file = " + useless_file)
        file_suffix_removed = useless_file.split(".")[0]
        
        vectorised_file = self.databox.vectorise(file_suffix_removed, self.databox.default_to_count, "N")

        self.tensorStuff.onlyTensorProcessing("user_input/tensors/", input_files=[vectorised_file], hard_code_mapping=True) #

    def temp(self):
        with open(self.default_file, "w") as fw:
            with open("correct_types/all.csv", "r") as f:
                reader = csv.reader(f)
                writer = csv.writer(fw)
                count = 0
                for row in reader:
                    count += 1
                    writer.writerow(row)
                    if count == 2:
                        break

    def make_json(self):
        dict1 = {'league': '', 'split': '', 'playoffs': '', 'game_in_series': '', 'series_score_before_game': '', 'patch': '', 'team1_blue': '', 'team2_red': '', 'head_to_head': '', 'team1_last5': '', 'team2_last5': '', 'blue_top_pick': '', 'blue_jng_pick': '', 'blue_mid_pick': '', 'blue_bot_pick': '', 'blue_sup_pick': '', 'red_top_pick': '', 'red_jng_pick': '', 'red_mid_pick': '', 'red_bot_pick': '', 'red_sup_pick': '', 'playername': '', 'firstpick': '', 'champion_patch_winrate': ''},
        dict2 = {'winner': ''}

        print(json.dumps(dict1))
        print(json.dumps(dict2))

    def predict_on_user_input_tensor(self):
        predictor_file_path = "models/punish_weakness/epoch=64"        #48
        #predictor_file_path = "models/predict_win_from_gold_chain/epoch=38"        
        tensor = torch.load("user_input/tensors/to_consume_with_useless_data_vectorised_I")
        res = self.predict(tensor[0], predictor_file_path)



bob = Prediction()
bob.format_correctly(input_file_use_default=False, file_name="user_input/1.json")
#bob.format_correctly()
bob.predict_on_user_input_tensor()
bob.flip_json_teams()