import argparse
import json
import os
import re
import sys
from pathlib import Path
import shutil
from collections import defaultdict

from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

BUILT_IN_PARAMETERS = ["token_url"]

def render(template, props, wrap=True):
    config = json.loads(template.render(** props))
    if type(config) is list or not wrap:
        return config
    else:
        # template is a single component, wrap it a list to make it consistent
        return [config]


def expand_connnector_config(connector_dir, system_placeholder):
    output = []

    main_env = Environment(
        loader=PackageLoader("connector-py"),
        autoescape=select_autoescape(),
        variable_start_string="{{@",
        variable_end_string="@}}"
    )
    shim_template = main_env.get_template("shim.json")

    with open(os.path.join(connector_dir, "manifest.json"), "r") as f:
        system_env = Environment(
            loader=FileSystemLoader(connector_dir),
            autoescape=select_autoescape(),
            variable_start_string="{{@",
            variable_end_string="@}}"
        )

        manifest = json.load(f)

        # generate system config
        system_template = system_env.get_template(manifest["system-template"])
        subst = {**{"system": system_placeholder},
                 **{key: "$ENV(%s)" % key for key in list(manifest.get("additional_parameters", {}).keys()) + BUILT_IN_PARAMETERS}}

        output.extend(render(system_template, subst))

        for datatype, datatype_manifest in manifest.get("datatypes").items():

            datatype_template = system_env.get_template(datatype_manifest["template"])
            datatype_pipes = render(datatype_template, subst)
            # # tag component with datatype we can group them when we download
            # for pipe in datatype_pipes:
            #     metadata = pipe.get("metadata", {})
            #     metadata["$connector"] = {"datatype": datatype}
            #     pipe["metadata"] = metadata
            # datatype_output.extend(datatype_pipes)
            output.extend(datatype_pipes)
            output.extend(render(shim_template, {"system": system_placeholder, "datatype": datatype}))
    return output, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-placeholder", metavar="<string>",
                        default="xxxxxx", type=str, help="Name of the system _id placeholder")
    parser.add_argument("-d", dest="connector_dir", metavar="<string>",
                        default=".", type=str, help="Connector folder to work with")    
    parser.add_argument("-e", dest="expanded_dir", metavar="<string>",
                        default=".expanded", type=str, help="Directory to expand the config into")
    parser.add_argument("command", metavar="command", nargs="?", help="expand, collapse, init, add-type")

    args = parser.parse_args()

    connector_dir = args.connector_dir
    system_placeholder = args.system_placeholder
    expanded_dir = args.expanded_dir

    if args.command == "expand":
        # put the expanded configuration into a subfolder in the connector directory in a form that can be used by sesam-py
        output, manifest = expand_connnector_config(connector_dir, system_placeholder)
        dirpath = Path(connector_dir, expanded_dir)
        if dirpath.exists() and dirpath.is_dir():
            shutil.rmtree(dirpath)
        os.makedirs(dirpath)
        os.makedirs(dirpath / "pipes")
        os.makedirs(dirpath / "systems")
        with open(dirpath / "test-env.json", "w") as f:
            new_manifest = {**{"node-env": "test"}, **{key:"" for key in list(manifest.get("additional_parameters", {}).keys()) + BUILT_IN_PARAMETERS}}
            json.dump(new_manifest, f, indent=2, sort_keys=True)
        for component in output:
            if component["type"] == "pipe":
                with open(dirpath / f"pipes/{component['_id']}.conf.json", "w") as f:
                    json.dump(component, f, indent=2, sort_keys=True)
            elif component["type"].startswith("system:"):
                with open(dirpath / f"systems/{component['_id']}.conf.json", "w") as f:
                    json.dump(component, f, indent=2, sort_keys=True)
    elif args.command == "collapse":
        # reconstruct the templates
        input = Path(connector_dir)
        datatypes = defaultdict(list)
        for system in Path(input, "systems").glob('*.json'):
            with open(system, "r") as f:
                datatypes["system"].append(json.load(f))
        for pipe in Path(input, "pipes").glob('*.json'):
            datatype = pipe.name.split("-")[1]
            if pipe.name.endswith("-transform.json"): # shim pipe
                continue
            with open(pipe, "r") as f:
                pipe = json.load(f)
                # skip shim
                if not pipe["_id"] == "%s-%s-transform" % (system_placeholder, datatype):
                    datatypes[datatype].append(pipe)

        dirpath = Path(connector_dir)
        os.makedirs(dirpath / "templates")

        # write the datatype templates
        env_parameters = set()
        p = re.compile('\$ENV\(\w+\)')
        for datatype, new_manifest in datatypes.items():
            with open(Path(dirpath, "templates", "%s.json" % datatype), "w") as f:
                template = json.dumps(new_manifest if len(new_manifest) > 1 else new_manifest[0], indent=4, sort_keys=True)
                fixed = template.replace(system_placeholder, "{{@ system @}}")
                envs = p.findall(fixed)
                for env in envs:
                    e = env.replace("$ENV(", "{{@ ").replace(")", " @}}")
                    env_parameters.add(e.replace("{{@ ", "").replace(" @}}", ""))
                    fixed = fixed.replace(env, e)
                f.write(fixed)

        # create manifest
        manifest_path = Path(connector_dir, "manifest.json")
        existing_manifest = {}
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                existing_manifest = json.load(f)

        with open(dirpath / "manifest.json", "w") as f:
            new_manifest = {
                "additional_parameters": {key:existing_manifest.get("additional_parameters", {}).get(key, {}) for key in env_parameters},
                "system-template": "templates/system.json",
                "datatypes": {datatype: {**{"template": "templates/%s.json" % datatype}, **existing_manifest.get(datatype, {})} for datatype in datatypes.keys() if datatype != "system"}
            }
            manifest = {**existing_manifest, **new_manifest}
            json.dump(manifest, f, indent=2, sort_keys=True)
    elif args.command == "init":
        with open(Path(connector_dir, "manifest.json"), "w") as f:
            json.dump({"datatypes": {}, "additional_parameters": {}}, f, indent=2, sort_keys=True)

    else:
        parser.print_usage()
        sys.exit(1)
