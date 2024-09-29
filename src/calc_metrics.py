import json
import os
from statistics import mean, median
from collections import defaultdict
from typing import List, Dict, Any

import fire  # type: ignore
import numpy as np
from scipy.stats import spearmanr  # type: ignore
import networkx as nx  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from pyvis.network import Network  # type: ignore
from scipy.stats import spearmanr, kendalltau


def main(input_dir: str) -> None:
    all_scores: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))
    for name in os.listdir(input_dir):
        path = os.path.join(input_dir, name)
        with open(path) as r:
            data = json.load(r)
            for output in data["outputs"]:
                judge = data["judge"]["model_name"]
                scores = output["new_scores"]
                is_refusal = scores.pop("is_refusal")
                if max(is_refusal) == 1:
                    continue
                key = str(output["messages"])
                all_scores[key][judge] = output

    human_scores = []
    sonnet_scores = []
    top_2_scores = []
    for _, example_scores in all_scores.items():
        example_human_scores = None
        example_judge_scores = dict()
        count = 0
        for judge_model, output in example_scores.items():
            example_human_scores = output["human_scores"]
            judge_scores = output["new_scores"]
            output_scores = []
            for value in judge_scores.values():
                output_scores.append(mean(value))
            final_score = mean(output_scores)
            example_judge_scores[judge_model] = final_score
            count += 1
        if not example_human_scores:
            continue
        if "claude-3-5-sonnet-20240620" not in example_judge_scores:
            continue

        final_human_score = mean(example_human_scores.values())
        human_scores.append(final_human_score)

        weights = {"claude-3-5-sonnet-20240620": 0.5, "gpt-4o": 0.5}
        top_2_score = sum([v * weights.get(k, 0.0) for k, v in example_judge_scores.items()])
        top_2_scores.append(top_2_score)
        sonnet_scores.append(example_judge_scores["claude-3-5-sonnet-20240620"])

    print("Support:", len(human_scores))
    print("Sonnet only, Spearman:", spearmanr(human_scores, sonnet_scores)[0])
    print("Sonnet and GPT-4o:", spearmanr(human_scores, top_2_scores)[0])
    print("Sonnet and GPT-4o, Kendall:", kendalltau(human_scores, top_2_scores).statistic)


if __name__ == "__main__":
    fire.Fire(main)