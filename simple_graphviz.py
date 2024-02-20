import sys
import os
import yaml
import clipboard
from pathlib import Path

output = ""
documentation = {}
index = 1
nodes = {}
def collect_output(text):
    global output
    output += str(text)+os.linesep

def print_output(output_file_path):
    global output
    print(output,file=sys.stderr)
    try:
        clipboard.copy(output)
        print("result copied into clipboard",file=sys.stderr)
        with open(output_file_path,"w",encoding="utf-8") as fout:
            fout.write(output)
            fout.close
    except:
        pass

def print_doc(output_file_path):
    global documentation
    with open(output_file_path,"w",encoding="utf-8") as fout:
        for item in sorted(documentation.keys()):
            fout.write(f"## {item}\n{documentation[item]}\n")
        fout.close

def init_node(name, is_signal):
    global index, nodesn
    if name not in nodes:
        nodes[name] = {
            "index": index,
            "style": "box",
            "color": "white",
            "doc": "",
            "deps": [],
            "label": name,
            "signal": is_signal
        }
        index += 1
        return True
    if is_signal: # when a dependency node is been written as signel anywhere, the note is set as signal globally
        nodes[name]["signal"]=True
    return False

def transform_nodes(nodes_raw):
    global nodes, documentation
    for node_raw_name, node_raw_data in nodes_raw.items():
        if node_raw_name[:1] == "_":
            node_raw_name = node_raw_name[1:]
            is_signal = True
        else:
            is_signal = False
        # if the node was defined before through a dependency, it might miss it's signal flag
        if not init_node(node_raw_name, is_signal) and is_signal:
            nodes[node_raw_name]["signal"] = is_signal
        this_node = nodes[node_raw_name]
        for node_key, node_value in node_raw_data.items():
            if node_key == "s":
                this_node["style"] = node_value
            elif node_key == "c":
                this_node["color"] = node_value
            elif node_key == "deps":
                for dep_node_name in node_value:
                    if dep_node_name[:1] == "_":
                        real_node_name = dep_node_name[1:]
                        node_is_signal = True
                    else:
                        node_is_signal = False
                        real_node_name = dep_node_name
                    init_node(real_node_name, node_is_signal)
                    this_node["deps"].append(dep_node_name)
            elif node_key == "doc":
                this_node["doc"] = node_value
                documentation[node_raw_name]=node_value


def create_output():
    global nodes,index
    # first we do the root ones
    collect_output("digraph G {")
    collect_output('''ratio="fill";
 size="8.3,11.7!";
 rankdir="LR";
 margin=0;''')
    for node_name, node_data in nodes.items():
        if node_data["signal"]:
            collect_output("{} [shape=cds, style=filled, fillcolor={}, label=\"{}\"]".format(
                "L"+str(node_data["index"]), node_data["color"], node_name))
        else:
            collect_output("{} [shape={},  style=filled, fillcolor={}, label=\"{}\"]".format(
                "L"+str(node_data["index"]), node_data["style"], node_data["color"], node_name))
        # now we do the connections and create the signal nodes
    for node_data in nodes.values():
        for dep_node_name in node_data["deps"]:
            if dep_node_name[:1] == "_":
                dep_node_name = dep_node_name[1:]
            signal_color=nodes[dep_node_name]["color"]
            if nodes[dep_node_name]["signal"]:
                collect_output("{} [shape=cds, style=filled, fillcolor={}, label=\"{}\"]".format(
                "L"+str(index), signal_color, dep_node_name))
                collect_output("{} -> {}".format(
                "L"+str(index), "L"+str(node_data["index"])))
                index+=1
            else:
                dep_node_index=nodes[dep_node_name]["index"]
                collect_output("{} -> {}".format(
                "L"+str(dep_node_index),  "L"+str(node_data["index"])))

    collect_output("}")

if len(sys.argv) > 1:
    input_file_path_array = sys.argv[1:]  # all args except [0] (script path)
else:
    input_file_path_array = ["simple_graphviz.yaml"]
for input_file_path in input_file_path_array:
    file_path = Path(input_file_path)
    with open(input_file_path, "r", encoding="utf-8") as stream:
        try:
            nodes_raw = yaml.safe_load(stream)
            transform_nodes(nodes_raw)
        except yaml.YAMLError as exc:
            print(exc)
create_output()
print_output(file_path.stem+".graphiz")
print_doc(file_path.stem+".md")
