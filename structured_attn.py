# loooooots of help from the example here: https://pytorch-tutorials-preview.netlify.app/beginner/transformer_tutorial.html and https://medium.com/@doublekien/lstm-with-pytorch-664065718df4
import math
import os
import torch
from torch import nn, Tensor
from torch.nn import TransformerEncoder, TransformerEncoderLayer

from syllabify import syllabify_line

# based on https://docs.pytorch.org/text/stable/vocab.html
class SyllableVocab:
    def __init__(self):
        # <unk> is the default unknown value following the example
        # of the tutorial above
        self.stoi = {"<unk>": 0}
        self.itos = ["<unk>"]

    # dunders
    def __contains__(self, token):
        return token in self.stoi
    def __getitem__(self, token):
        return self.stoi[token] if token in self else self.stoi["<unk>"]
    def __len__(self):
        return len(self.itos)

    # vocab manipulation
    def append_token(self, token):
        if token in self.stoi:
            raise RuntimeError("tried to add existing token")

        self.stoi[token] = len(self.itos)
        self.itos.append(token)

    def insert_token(self, token, index):
        if token in self.stoi:
            raise RuntimeError("tried to add existing token")
        if index <= 0 or index > len(self.itos):
            raise RuntimeError("attempted to insert token into illegal location")

        self.stoi = { k : (v + 1 if v >= index else v) for k, v in self.stoi.items() }
        self.stoi[token] = index

        self.itos.insert(index, token)

    def lookup_indices(self, tokens):
        return [self[token] for token in tokens]

    def lookup_token(self, index):
        if not (0 <= index < len(self.itos)):
            raise RuntimeError("attempted to look up token at nonexisting index")
        return self.itos[index]

    def lookup_tokens(self, indices):
        return [self.lookup_token(index) for index in indices]

    # metadata getters
    def get_default_index(self):
        return self.stoi["<unk>"]
    def get_itos(self):
        return self.itos
    def get_stoi(self):
        return self.stoi

    # build_from_iterator
    def build_from_line(self, line):
        for syllable in syllabify_line(line):
            self.append_token(syllable)

    def encode(self, syllables):
        # torch.tensor(vocab(tokenizer(item)), dtype=torch.long)
        # vocab: Factory method for creating a vocab object which maps tokens to indices.
        return torch.tensor([self[syl] for syl in syllables], dtype=torch.long)

class TransformerModel(nn.Module):
    def __init__(self, ntoken, d_model, nhead, nlayers, max_len):
        super().__init__()
        encoder_layers = TransformerEncoderLayer(d_model, nhead, d_model*4, activation="gelu", batch_first=True)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)

        self.embedding = nn.Embedding(ntoken, d_model)
        self.pos_embed = nn.Embedding(max_len, d_model) # Position in syllable/line
        self.linear = nn.Linear(d_model, 2) # long or short are the only 2 out_features

    def forward(self, syllables):
        """
        syllables = tensor of IDs for each syllable in a line
        """

        num_syll = syllables.shape[0]
        positions = torch.arange(num_syll, device=syllables.device) # syllables are sequentially ordered

        x = self.embedding(syllables) + self.pos_embed(positions) # Combining position info

        x = x.unsqueeze(0) # for batching
        x = self.transformer_encoder(x)
        x = x.squeeze(0)

        result = self.linear(x)
        return result[:, 0], result[:, 1]

# Turning attention output into syllable probabilities!
def partition_fn(longs, shorts):
    """
    My idea is to treat this whole enterprise like a partition function.
    In statistical mechanics, the partition function Z is the sum over all 
    possible microstates _i_ of a system of e^(-E_i/k_B*T). Exponentiating
    transforms the space to all positive, which is what we want for probabilities.
    When we add up all of these terms, we get the total amount of "probability"
    we have to play with, so that the probability of a single microstate is just
    that state's e^(-E/k_B*T)/Z.
    Here, each microstate is a valid dactylic hexameter sequence, and the 
    microstate for which we are finding the probability is the sequence of
    syllable weights given by taking the higher probability of the two
    longs, shorts arrays at each syllable.
    """

    num_syll = longs.shape[0]

    # Using DP to figure out the hexameter constraints, so the array
    # goes one beyond [# syllables][6]
    MIN = float("-inf")
    dp = [[MIN for _ in range(7)] for _ in range(num_syll+1)]
    dp[0][0] = torch.tensor(0.0)

    for foot in range(1, 7):
        for syll in range(num_syll+1):
            so_far = []

            # Either a spondee, so the last foot ended 2
            # syllables ago...
            if syll >= 2 and dp[syll-2][foot-1] != MIN:
                # long long
                so_far.append(dp[syll-2][foot-1]+longs[syll-2]+longs[syll-1])

            # Or a dactyl, so the last foot ended 3 syllables
            # ago...
            if syll >= 3 and dp[syll-3][foot-1] != MIN:
                # long short short
                so_far.append(dp[syll-3][foot-1]+longs[syll-3]+shorts[syll-2]+shorts[syll-1])

            if so_far:
                # We have valid microstates! Exponentiate + sum them to get Z
                # then take the log
                dp[syll][foot] = torch.logsumexp(torch.stack(so_far), dim=0)

    logZ = dp[num_syll][6]
    if logZ == MIN:
        raise ValueError("no valid readings :(")
    return logZ

def per_syllable_prob(longs, shorts):
    """
    So why did we transform the partition function into a log?

    We've already established that:
    P_s = 1/Z*e^(score of s)
    for a state s

    We know that for a single syllable:
    logZ = log(e^(state 1) + e^(state 2) + e^(state ...))
    by definition

    The operation that turns logs into divisions is the derivative:
    d(logZ)/d(score of s) = 1/Z*dZ/d(score of s)

    ^^ since all the states in Z are combined via sums and are in their own terms,
    we can ignore the rest of the state-based terms:
    d(logZ)/d(score of s) = 1/Z*d(e^(score of s))/d(score of s)

    the nice thing about exponents...
    d(logZ)/d(score of s) = 1/Z*e^(score of s)

    So we want to compute this quantity:
    P_s = d(logZ)/d(score of s)
    """
    logZ = partition_fn(longs, shorts)
    grad_long, grad_short = torch.autograd.grad(logZ, [longs, shorts], create_graph=True)
    return grad_long, grad_short, logZ

def most_likely_scan(longs, shorts):
    num_syll = longs.shape[0]
    longs = longs.tolist()
    shorts = shorts.tolist()

    # Using DP to figure out the hexameter constraints, so the array
    # goes one beyond [# syllables][6]
    MIN = float("-inf")
    dp = [[MIN for _ in range(7)] for _ in range(num_syll+1)]
    curr_labels = [[None for _ in range(7)] for _ in range(num_syll+1)]
    dp[0][0] = torch.tensor(0.0)

    for foot in range(1, 7):
        for syll in range(num_syll+1):
            # Either a spondee, so the last foot ended 2
            # syllables ago...
            if syll >= 2 and dp[syll-2][foot-1] != MIN:
                # long long
                new_score = dp[syll-2][foot-1]+longs[syll-2]+longs[syll-1]
                if new_score > dp[syll][foot]:
                    dp[syll][foot] = new_score
                    curr_labels[syll][foot] = ("spondee", syll-2)

            # Or a dactyl, so the last foot ended 3 syllables
            # ago...
            if syll >= 3 and dp[syll-3][foot-1] != MIN:
                # long short short
                new_score = dp[syll-3][foot-1]+longs[syll-3]+shorts[syll-2]+shorts[syll-1]
                if new_score > dp[syll][foot]:
                    dp[syll][foot] = new_score
                    curr_labels[syll][foot] = ("dactyl", syll-3)

    if curr_labels[num_syll][6] is None:
        raise ValueError("no valid readings :(")

    # Backwards checking
    syll = num_syll
    foot = 6
    labels = [None for _ in range(num_syll)]
    feet = [None for _ in range(6)]
    while foot > 0:
        foot_name, prev_syll = curr_labels[syll][foot]
        feet[foot-1] = foot_name
        if foot_name == "spondee":
            labels[prev_syll], labels[prev_syll+1] = True, True
        else:
            labels[prev_syll], labels[prev_syll+1], labels[prev_syll+2] = True, False, False
        syll = prev_syll
        foot -= 1
    return feet, labels
