import torch
from gold_chain import Trainer

class Regulariser():
    def __init__(self, league="all"):
        self.league = league

    def get_std_tensors(self):
        X = torch.load("tensors/" + self.league + "_I")
        Y = torch.load("tensors/" + self.league + "_O")

        X = X.float()
        Y = Y.float()

        # --------------------------------------------------
        # Train/test split
        # --------------------------------------------------

        #bob.get_mapping(file)[""]

        eps = 1e-8
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

        # STANDARDISING
        X_train_unReg = X[train_indices]
        Y_train_unReg = Y[train_indices]

        X_test_unReg = X[test_indices]
        Y_test_unReg = Y[test_indices]

        X_train_mean = X_train_unReg.mean(dim=0)
        X_train_std = X_train_unReg.std(dim=0)

        return X_train_std + eps