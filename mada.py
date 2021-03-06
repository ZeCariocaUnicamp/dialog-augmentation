import json
import math
import random
import argparse
from eda import eda
from tqdm import tqdm
from collections import defaultdict
from deanony import gen_placa, gen_cpf, gen_nome, gen_valor

random.seed(20211109)

def augment(sentence):
    return eda(sentence, ["[cpf]", "[placa]", "[valor]"])

def bfs(pflow, intent_sample, rate):
    count = 0
    samples = []
    visit = []
    rate = math.sqrt(rate)
    for flow in pflow:
        visit.append((flow,[]))
    while visit:
        flow, dialog = visit.pop(0)
        if flow:
            agent = "intent" if len(flow) % 2 == 0 else "action"
            if len(intent_sample[agent][flow[0]]) > 5:
                sample = random.sample(intent_sample[agent][flow[0]], 5)
            else:
                sample = intent_sample[agent][flow[0]]
            for turn in sample:
                if random.random() > rate or len(dialog) < 5:
                    visit.append((flow[1:], dialog+[turn]))
        else:
            count += 1
            samples.append(dialog)
            if count % 1000 == 0: print(f"Generated {count} dialogues...")
    return samples

def parse_args():
    parser = argparse.ArgumentParser(description="Applying MADA on a dialog dataset formatted in the MultiWOZ pattern.")
    parser.add_argument("--filename", type=str, default="dialogs.json", help="Path to dialogs dataset.")
    parser.add_argument("--rate", type=float, default=0.91, help="Pruning probability in the MADA tree of possibilities.")
    parser.add_argument("--sample-size", dest='sample', type=int, default=5000, help="Size of sample to pick.")
    parser.add_argument("--no-augment", default=True, help="Augment dataset.", dest='augment', action="store_false")
    return parser.parse_args()

def main():
    args = parse_args()
    possible_flows = []
    utt_counter = defaultdict(int)
    intent_sample = {"intent":defaultdict(list), "action":defaultdict(list)}
    with open(args.filename) as fin:
        data = json.load(fin)
    random.shuffle(data["dialogs"])
    for dialog in data["dialogs"]:
        dialog["id"] = str(dialog["id"])
        curr_flow = []
        for turn in dialog["turns"]:
            agent = "intent" if turn["turn-num"] % 2 == 0 else "action"
            utt = turn[agent]
            utt_counter[utt] += 1
            curr_flow.append(utt)
            intent_sample[agent][utt].append(turn)
        if curr_flow not in possible_flows:
            possible_flows.append(curr_flow)
    for count in sorted(utt_counter.items(), key=lambda x: x[1]):
        print(count)
    samples = bfs(possible_flows, intent_sample, args.rate)
    samples = random.sample(samples, min(args.sample, len(samples)))
    size = len(data["dialogs"])
    out_data = []
    for i, dialog in enumerate(tqdm(samples)):
        new_dialog = []
        current_values = {}
        for num, turn in enumerate(dialog):
            new_turn = turn.copy()
            new_turn["turn-num"] = num
            if turn["speaker"] == "client":
                if args.augment and random.random() >= .5:
                    random.seed(20211109+i)
                    aug_text = augment(new_turn["utterance_delex"].lower())
                    new_turn["utterance_delex"] = random.choice(aug_text)
                else:
                    new_turn["utterance_delex"] = new_turn["utterance_delex"].lower()
            new_turn["utterance"] = new_turn["utterance_delex"]
            if "[cpf]" in new_turn["utterance"]:
                cpf = gen_cpf()
                current_values["cpf"] = cpf
                new_turn["utterance"] = new_turn["utterance"].replace("[cpf]", cpf)
            if "[placa]" in new_turn["utterance"]:
                placa = gen_placa()
                current_values["placa"] = placa
                new_turn["utterance"] = new_turn["utterance"].replace("[placa]", placa)
            if turn["speaker"] == "client":
                new_turn["slot-values"] = current_values.copy()
            new_dialog.append(new_turn)
        out_data.append({
            "id": f"{i*1000}",
            "turns": new_dialog})
    random.shuffle(out_data)
    data["dialogs"] = out_data
    with open("out."+args.filename, "w") as fout:
        json.dump(data, fout, indent=2, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    main()
