import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
import time
import csv

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

rows, cols = 9, 6

def num_of_moves(state):
    return np.sum(np.abs(state))

def curr_player(state):
    return 1 if(np.sum(np.abs(state))%2==0) else -1


def win(state):
    all_pos = np.all(state >= 0)
    all_neg = np.all(state <= 0)

    if ((num_of_moves(state) >= 2) and (all_neg or all_pos)):
        return 1 if all_pos else -1
    return 0

max_atoms = np.full((rows, cols), 3)
max_atoms[:, 0] -= 1
max_atoms[:, -1] -= 1
max_atoms[0, :] -= 1
max_atoms[-1, :] -= 1


# def add_atom(state, row, col, player):

def add_atom(state, row, col, player):
    if num_of_moves(state) > 132:
        return None

    if row < 0 or row >= rows or col < 0 or col >= cols:
        return None
    elif abs(state[row, col]) < max_atoms[row, col]:
        state[row, col] = (abs(state[row, col]) + 1) * player
    else:
        state[row, col] = (abs(state[row, col]) + 1) * player
        state = make_stable(state, player)
    
    return state

def make_stable(state, p):
    while True:
        unstable = np.abs(state) > max_atoms
        if not unstable.any():
            break

        indices = np.argwhere(unstable)
        for i, j in indices:
            q, r = divmod(abs(state[i, j]), max_atoms[i, j] + 1)
            state[i, j] = r * p
            if i != 0:
                state[i - 1, j] = (abs(state[i - 1, j]) + q) * p
            if j != 0:
                state[i, j - 1] = (abs(state[i, j - 1]) + q) * p
            if i != rows - 1:
                state[i + 1, j] = (abs(state[i + 1, j]) + q) * p
            if j != cols - 1:
                state[i, j + 1] = (abs(state[i, j + 1]) + q) * p

        if num_of_moves(state) > 80 and (win(state) != 0):
            return np.full((rows, cols), p)
    
    return state

def state_to_tensor(state):
    tensor = np.zeros((rows, cols, 8), dtype=np.float32)
    for i in range(rows):
        for j in range(cols):
            val = state[i, j]
            # if val != 0:
            tensor[i, j, val + 3] = 1
    tensor[:, :, 7] = curr_player(state)
    return torch.tensor(tensor).permute(2, 0, 1).unsqueeze(0).to(device)

def legal_moves(state):
    if(curr_player(state) == 1):
        return (state>=0).astype(int)
    else:
        return (state<=0).astype(int)

############################## AI MODEL ##############################

class ResNet(nn.Module):

    def __init__(self, game, num_resBlocks, num_hidden):
        super().__init__()

        self.startBlock = nn.Sequential(
            nn.Conv2d(8, num_hidden, kernel_size=3, padding= 1),
            nn.BatchNorm2d(num_hidden),
            nn.ReLU()
        )

        self.backBone = nn.ModuleList(
            [ResBlock(num_hidden) for i in range(num_resBlocks)]
        )

        self.policyHead = nn.Sequential(
            nn.Conv2d(num_hidden, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * game.n_r * game.n_c, game.n_r*game.n_c)
        )

        self.valueHead = nn.Sequential(
            nn.Conv2d(num_hidden, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(32 * game.n_r * game.n_c, 1),
            nn.Tanh()
        )
    
    def forward(self, x):
        x = self.startBlock(x)

        for resBlock in self.backBone:
            x = resBlock(x)
        
        policy = self.policyHead(x)
        policy = F.softmax(policy, dim=-1)
        value = self.valueHead(x)

        return policy, value

class ResBlock(nn.Module):
    def __init__(self, num_hidden):
        super().__init__()

        self.conv1 = nn.Conv2d(num_hidden, num_hidden, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(num_hidden)
        self.conv2 = nn.Conv2d(num_hidden, num_hidden, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(num_hidden)
        self.conv3 = nn.Conv2d(num_hidden, num_hidden, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(num_hidden)

    def forward(self, x):
        residual = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.bn3(self.conv3(x))

        x += residual
        x = F.relu(x)

        return x

class Game:
    n_r = 9
    n_c = 6
game = Game()

Agent1 = ResNet(game, num_resBlocks=8, num_hidden=64).to(device)
Agent2 = ResNet(game, num_resBlocks=8, num_hidden=64).to(device)

optimizer1 = Adam(Agent1.parameters(), lr=0.001)
optimizer2 = Adam(Agent2.parameters(), lr=0.001)

def load_checkpoint(seed):
    check1 = torch.load(f"/root/App/Chain_Reaction_Backend/app/agent1_{seed}.pt", map_location=device)
    Agent1.load_state_dict(check1["agent1_state_dict"])
    optimizer1.load_state_dict(check1["optimizer1_state_dict"])

    check2 = torch.load(f"/root/App/Chain_Reaction_Backend/app/agent2_{seed}.pt", map_location=device)
    Agent2.load_state_dict(check2["agent2_state_dict"])
    optimizer2.load_state_dict(check2["optimizer2_state_dict"])

    print("Ai agents loaded successfully!!!!")


def sort_legal_moves(policy, legal_moves):
    policy_cpu = policy.detach().cpu()
    # policy_cpu = 
    legal_moves_flat = legal_moves.flatten()

    legal_indices = np.where(legal_moves_flat == 1)[0]
    legal_policy_probs = policy_cpu.flatten()[legal_indices]
    # sorted_indices = legal_indices[legal_policy_probs.argsort()[::-1]]
    # sorted_moves = [(idx // legal_moves.shape[1], idx % legal_moves.shape[1]) for idx in sorted_indices]
    if(len(legal_indices) == 1):
        sorted_indices = legal_indices
    else:
        sorted_indices = legal_indices[legal_policy_probs.argsort(descending=True)]

    sorted_moves = [(idx // legal_moves.shape[1], idx % legal_moves.shape[1]) for idx in sorted_indices]

    return sorted_moves

load_checkpoint("999")

def best_moves(state):

    lgl_moves = legal_moves(state)
    p = curr_player(state)

    winning_moves = []
    for i in range(rows):
        for j in range(cols):
            if(lgl_moves[i][j]==1):
                new_state = add_atom(state.copy(), i, j, p)

                if(win(new_state)!=0):
                    winning_moves.append((i, j))

    return winning_moves


def AI_agent_move(state_a):

    state = np.array(state_a)
    moves = legal_moves(state)
    p = curr_player(state)

    policy, value = Agent1(state_to_tensor(state)) if(p==1) else Agent2(state_to_tensor(state))
    sorted_moves = sort_legal_moves(policy, moves)
    best_mvs = best_moves(state)

    if(best_mvs):
        return best_mvs[0][0], best_mvs[0][1]

    for i in range(len(sorted_moves)):
        if(sorted_moves[i] in best_mvs):
            return sorted_moves[i][0], sorted_moves[i][1]
        
        new_state = add_atom(state.copy(), sorted_moves[i][0], sorted_moves[i][1], p)

        if(not best_moves(new_state)):
            return sorted_moves[i][0], sorted_moves[i][1]

        del new_state
    
    return sorted_moves[0][0], sorted_moves[0][1]

