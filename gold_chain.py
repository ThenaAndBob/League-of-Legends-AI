import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from test import Formatting
torch.set_printoptions(sci_mode=False)

class Regressor(nn.Module):
    def forward(self, x):
        return self.net(x)

    def __init__(self, shape):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(shape, 1024),
            nn.ReLU(),
            nn.Dropout(0.5),

            nn.Linear(1024, 256),
            nn.ReLU(),
            nn.Dropout(0.5),

            nn.Linear(256, 60),
        )

class Trainer:
    # This one trains all the AI's

    # 10,15,20,25,           WINNER
    # 5 different ones, encapsulated
    def __init__(self):
        pass

    def predict(self,model_num: int, vector):
        # Weights stored in some file, 
        model_name = "models/num_" + str(model_num)
        model_name = "models/epoch=5_num_" + str(model_num)
        my_dict = torch.load(model_name)
        shape = my_dict["shape"]
        print(shape)
        model = Regressor(shape)
        model.load_state_dict(
            my_dict["state"]
        )
        model.eval()
        with torch.inference_mode():
            output = model(vector)
        return output

    def train(self):
        def weightScaling(weights):
            return 100 * (1 - torch.exp(-1*(weights.unsqueeze(1) - smallest_patch_regularised)))

        def lossScalingFunc(loss, weights):
            w = weightScaling(weights)
            return (loss * w).mean()

        leagues = ["all", "cblol", "lck", "lcs", "lec", "lpl", "pcs"]
        league = "all"

        file = "vectorised/" + league + ".csv"

        tensor_load = "all_mid/"

        X = torch.load(tensor_load + league + "_I")
        Y = torch.load(tensor_load + league + "_O")

        X = X.float()
        Y = Y.float()
        mask = ~(Y == 0).all(dim=1)
        Y = Y[mask]
        X = X[mask]

        print("X shape:", X.shape)
        # --------------------------------------------------
        # Train/test split
        # --------------------------------------------------

        bob = Formatting()
        patch_index = bob.get_mapping(file)["patch"][0]

        # 10,15,20,25
        Y_indeces = []
        at_a_time = [0,1,2,6,7,8]
        for minute in [0,9,18]:
            Y_indeces.append([])
            for player in range(0,360,36):
                for item in at_a_time:
                    Y_indeces[-1].append(player + minute + item)
                
        test_fraction = 0.1

        n_samples = X.shape[0]
        n_test = int(n_samples * test_fraction)

        # Fixed seed so you get the same split every run
        generator = torch.Generator()
        generator.manual_seed(15)
        indices = torch.randperm(n_samples, generator=generator)
        #indices = torch.arange(n_samples-1,-1,-1)

        test_indices = indices[:n_test]
        train_indices = indices[n_test:]

        for (index, columns) in enumerate(Y_indeces):
            model = Regressor(X.shape[1])

            criterion = nn.MSELoss(reduction="none")

            optimizer = torch.optim.Adam(
                model.parameters(),
                lr=5e-5,
                weight_decay=1e-2
            )
            # --------------------------------------------------
            # Standardising
            # --------------------------------------------------

            X_train_unReg = X[train_indices]

            X_train_mean = X_train_unReg.mean(dim=0)
            X_train_std = X_train_unReg.std(dim=0)

            eps = 1e-8

            X_train = X_train_unReg / (X_train_std + eps)
            X_test_unReg = X[test_indices]
            X_test = X_test_unReg / (X_train_std + eps)

            # --------------------------------------------------
            # Patch stuff
            # --------------------------------------------------

            smallest_patch_regularised = min(
                X_test[:, patch_index].min().item(),
                X_train[:, patch_index].min().item()
            )

            # 10,15,20,25       6*10 each time.

            Y_correct = Y[:, columns]         
            Y_train_unReg = Y_correct[train_indices]
            Y_test_unReg = Y_correct[test_indices]
            
            Y_train_mean = Y_train_unReg.mean(dim=0)
            Y_train_std = Y_train_unReg.std(dim=0)

            Y_train = (Y_train_unReg - Y_train_mean ) / (Y_train_std + eps)
            Y_test = (Y_test_unReg - Y_train_mean ) / (Y_train_std + eps)

            train_dataset = TensorDataset(X_train, Y_train)
            test_dataset = TensorDataset(X_test, Y_test)

            train_loader = DataLoader(
                train_dataset,
                batch_size=32,
                shuffle=True
            )

            test_loader = DataLoader(
                test_dataset,
                batch_size=32,
                shuffle=False
            )


            print("Train:", X_train.shape, Y_train.shape)
            print("Test: ", X_test.shape, Y_test.shape)

            # --------------------------------------------------
            # Model
            # --------------------------------------------------


            # --------------------------------------------------
            # Training
            # --------------------------------------------------

            epochs = 10

            for epoch in range(epochs):

                # -------------------------
                # Training phase
                # -------------------------

                model.train()

                train_loss = 0
                train_mae = 0
                train_total = 0

                for x_batch, y_batch in train_loader:

                    optimizer.zero_grad()

                    predictions = model(x_batch)

                    loss = criterion(predictions, y_batch)
                    loss = lossScalingFunc(
                        loss,
                        x_batch[:, patch_index]
                    )

                    loss.backward()
                    optimizer.step()

                    train_loss += loss.item()

                    train_mae += (
                        predictions - y_batch
                    ).abs().sum().item()
                    train_total += y_batch.numel()

                train_loss /= len(train_loader)
                train_mae /= train_total


                # -------------------------
                # Testing phase
                # -------------------------

                model.eval()    

                test_loss = 0
                test_mae = 0
                test_total = 0

                test_mae_per_feature = torch.zeros(60)
                test_samples = 0

                with torch.no_grad():

                    for x_batch, y_batch in test_loader:

                        predictions = model(x_batch)

                        loss = criterion(predictions, y_batch)
                        loss = lossScalingFunc(
                            loss,
                            x_batch[:, patch_index]
                        )

                        test_loss += loss.item()
                        test_mae += (
                            predictions - y_batch
                        ).abs().sum().item()

                        test_mae_per_feature += (
                            predictions - y_batch
                        ).abs().sum(dim=0)
                        #print(predictions * (Y_train_std + eps) + Y_train_mean)

                        test_samples += y_batch.shape[0]

                        test_total += y_batch.numel()

                test_loss /= len(test_loader)
                test_mae /= test_total

                test_mae_per_feature /= test_samples
                test_mae_per_feature_original = (
                    test_mae_per_feature * (Y_train_std + eps)
                )

                labels = ["Gold", "XP", "CS", "Kills", "Deaths", "Assists"]

                original = test_mae_per_feature_original.reshape(10, 6)
                standardised = test_mae_per_feature.reshape(10, 6)
                base_line = Y_train.abs().mean(axis=0).reshape(10, 6)
                percentage_improvement = 100 * (1 - standardised / base_line)

                for mae in [original, standardised, base_line, percentage_improvement]:
                    # Header
                    print("Player", end="  ")
                    for label in labels:
                        print(f"{label:>10}", end="")
                    print()

                    # Rows
                    for i, row in enumerate(mae):
                        print(f"{i + 1:>6}", end="  ")
                        for value in row:
                            print(f"{value.item():>10.4f}", end="")
                        print()
                    print("Mean over all players:")
                    print(mae.mean(axis=0))
                    print("\n")


                # -------------------------
                # Results
                # -------------------------

                print(
                    f"Epoch {epoch + 1:02d} | "
                )

                torch.save({"state": model.state_dict(), "shape": X.shape[1]}, "models/epoch=" + str(epoch) + "_num_" + str(index))
            X = torch.cat([X, Y_correct],dim=1)

    def test(self):
        pass

    def model(self):
        self.train
        self.test
        pass

if __name__ == "__main__":
    bobs = Trainer()
    bobs.train()