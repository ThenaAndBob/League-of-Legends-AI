import torch
import torch.nn as nn

class Classifier(nn.Module):
    def __init__(self, shape):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(shape, 256),
            nn.Sigmoid(),
            nn.Dropout(0.5),

            nn.Linear(256, 8),
            nn.Sigmoid(),

            nn.Linear(8, 1),
        )

    def forward(self, x):
        return self.net(x)