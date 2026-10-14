import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from test import Formatting
from gold_chain import Trainer
import math
from classifier import Classifier
import csv

def weightScaling(weights):
    return 100 * (1 - torch.exp(-0.5*(weights - smallest_patch_regularised)))

def lossScalingFunc(loss, weights):
    w = weightScaling(weights)
    return (loss * w)

def convert(x):
    try:
        a = float(x)
    except:
        a = 0
    return a

def punish_weakness(probabilities, real, indices):
    # certain wrong AND stomp 
    # certain wrong AND close
    # uncertain wrong AND stomp
    # uncertain wrong and close


    # uncertain correct AND stomp 
    # uncertain correct AND close
    # certain correct STOMP close
    # certain correct AND stomp
    confidence = torch.abs(probabilities - 0.5)

    gamelength = (
        game_length_column[indices] - 3
    )

    # Smooth measure of whether the prediction is correct.
    # real must be 0 or 1.
    direction = 2.0 * real - 1.0

    soft_correct = torch.sigmoid(
        20.0 * direction * (probabilities - 0.5)
    )

    # Smooth approximation to your original punishment.
    x = (1 - confidence) * gamelength

    smooth_x = -torch.nn.functional.softplus(
        -x,
        beta=10.0
    )


    correct_punishment = (
        soft_correct
        * 100.0
        * (1.0 - torch.exp(smooth_x))
    )

    incorrect_punishment = (
        (1.0 - soft_correct) * 100.0
    )

    return correct_punishment + incorrect_punishment



# ['league', 'playoffs', 'game_in_series', 'series_score_before_game', 'patch', 'head_to_head', 'team1_last5', 'team2_last5', 'firstpick', 'champion_patch_winrate']


eps = 1e-8

leagues = ["all", "cblol", "lck", "lcs", "lec", "lpl", "pcs"]
league = "all"          # seems bad at lpl, pcs, cblol
file = "vectorised/" + league + ".csv"
tensor_load = "all_mid/"

X = torch.load("tensors/" + league + "_I")
Y = torch.load("tensors/" + league + "_O")

X = X.float()
Y = Y.float()

Yused_for_removing_corrupt_data = torch.load(tensor_load + league + "_O")

Yused_for_removing_corrupt_data = Yused_for_removing_corrupt_data.float()
mask = ~(Yused_for_removing_corrupt_data == 0).all(dim=1)
Y = Y[mask]
X = X[mask]

print("X shape:", X.shape)
print("Y shape:", Y.shape)

# --------------------------------------------------
# Train/test split
# --------------------------------------------------
bob = Formatting()
patch_index = bob.get_mapping(file)["patch"][0]
game_length_index = bob.get_mapping(file)["gamelength_sec"][0]


game_length_column = []
for row in X:
    game_length_column.append(int(row[game_length_index]))

game_length_column = torch.tensor(game_length_column, dtype=torch.float32)
print("got game lengths")
#bob.get_mapping(file)[""]

test_fraction = 0.1

n_samples = X.shape[0]
n_test = int(n_samples * test_fraction)

# Fixed seed so you get the same split every run
generator = torch.Generator()
generator.manual_seed(15)
indices = torch.randperm(n_samples, generator=generator)
#indices = torch.arange(n_samples-1,-1,-1)

print("indices:")
print(indices)

test_indices = indices[:n_test]
train_indices = indices[n_test:]


# STANDARDISING

X_train_unReg = X[train_indices]
Y_train_unReg = Y[train_indices]

X_test_unReg = X[test_indices]
Y_test_unReg = Y[test_indices]

X_train_mean = X_train_unReg.mean(dim=0)
X_train_std = X_train_unReg.std(dim=0)

X_train = (X_train_unReg - X_train_mean) / (X_train_std + eps)
X_train = (X_train_unReg) / (X_train_std + eps)

Y_train = (Y_train_unReg + 1) / 2

X_test = (X_test_unReg - X_train_mean) / (X_train_std + eps)
X_test = (X_test_unReg) / (X_train_std + eps)

Y_test = (Y_test_unReg + 1 ) / 2

Gold_Chain = Trainer()

print(X_train_unReg.shape)
temp_train = X_train
temp_test = X_test
for model in range(3):
    output = Gold_Chain.predict(model, temp_train)
    temp_train = torch.concat([temp_train, output], dim=1)

for model in range(3):
    output = Gold_Chain.predict(model, temp_test)
    temp_test = torch.concat([temp_test, output], dim=1)

print(temp_train.shape)

X_train = temp_train
print(X_train_unReg.shape)
X_test = temp_test



print("Train:", X_train.shape, Y_train.shape)
print("Test: ", X_test.shape, Y_test.shape)
print("Baseline: ", Y_train.mean())

# patch stuff
smallest_patch_regularised = min(X_test[:,patch_index].min().item(), X_train[:, patch_index].min().item())


# --------------------------------------------------
# DataLoaders
# --------------------------------------------------

train_dataset = TensorDataset(X_train, Y_train, train_indices)
test_dataset = TensorDataset(X_test, Y_test, test_indices)

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

# --------------------------------------------------
# Model
# --------------------------------------------------

model = Classifier(shape=X_train.shape[1])

criterion = nn.BCEWithLogitsLoss(reduction="none")

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=1e-5,            #1e-5 works 
    weight_decay=1e-2
)

# --------------------------------------------------
# Training
# --------------------------------------------------

epochs = 100

for epoch in range(epochs):

    # -------------------------
    # Training phase
    # -------------------------

    model.train()

    train_loss = 0
    train_correct = 0
    train_total = 0

    for x_batch, y_batch, indices in train_loader:
        optimizer.zero_grad()

        logits = model(x_batch)

        loss = criterion(logits, y_batch).squeeze()
        loss = lossScalingFunc(loss, x_batch[:, patch_index])
        loss = loss + punish_weakness(torch.sigmoid(logits), y_batch, indices)
        loss = loss.mean()

        loss.backward()
        optimizer.step()

        train_loss += loss.item()

        predictions = (
            torch.sigmoid(logits) >= 0.5
        ).float()

        train_correct += (
            predictions == y_batch
        ).sum().item()

        train_total += y_batch.numel()

    train_accuracy = train_correct / train_total

    # -------------------------
    # Testing phase
    # -------------------------

    model.eval()

    test_loss = 0
    test_correct = 0
    test_total = 0
    average_guess = 0
    square_guess = 0
    avg = 0
    average_guess_diff = 0
    guess_side_share = 0

    with torch.no_grad():
        for x_batch, y_batch, indices in test_loader:
            logits = model(x_batch)
            loss = criterion(logits, y_batch)
            loss = lossScalingFunc(loss, x_batch[:, patch_index])
            loss = loss + punish_weakness(torch.sigmoid(logits), y_batch, indices)
            loss = loss.mean()
            test_loss += loss.item()

            predictions = (
                torch.sigmoid(logits) >= 0.5
            ).float()

            guess_side_share += predictions.sum()
            avg += torch.sigmoid(logits).sum()
            average_guess_diff += (torch.sigmoid(logits) - 0.5).abs().sum()
            square_guess += ((torch.sigmoid(logits) - 0.5) ** 2).sum()
            
            test_correct += (
                predictions == y_batch
            ).sum().item()

            test_total += y_batch.numel()

    test_accuracy = test_correct / test_total
    average_guess_diff = average_guess_diff / test_total
    square_guess = square_guess / test_total
    var = square_guess - average_guess_diff ** 2
    avg = avg / test_total
    guess_side_share = guess_side_share / test_total

    # -------------------------
    # Results
    # -------------------------

    print(
        f"Epoch {epoch + 1:02d} | "
        f"Train Loss: {train_loss / len(train_loader):.4f} | "
        f"Train Acc: {train_accuracy:.4f} | "
        f"Test Loss: {test_loss / len(test_loader):.4f} | "
        f"Test Acc: {test_accuracy:.4f}  | "
        f"Avg Guess Difference: {average_guess_diff:.4f}  | "
        f"Avg Guess: {avg:.4f}  | "
        f"Guess STD: {math.sqrt(var):.4f}  | "
        f"Side Share: {guess_side_share:.4f}"

    )

    torch.save({"state": model.state_dict(), "shape": X_train.shape[1]}, "models/punish_weakness/epoch=" + str(epoch+1))

