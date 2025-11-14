from openai import OpenAI
import torch
import json
import networkx as nx
from pyvis.network import Network
import matplotlib.colors as mcolors
import matplotlib.cm as cm
client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)