import argparse
import os
import importlib.util

def main():
    parser = argparse.ArgumentParser(description="Run MCP with specified folder and port.")
    parser.add_argument("folder", type=str, help="The folder containing the main.py file.")
    parser.add_argument("--port", type=int, default=8090, help="The port to run MCP on (default: 8090).")

    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    port = args.port

    if not os.path.exists(folder):
        raise FileNotFoundError(f"The specified folder does not exist: {folder}")

    main_py_path = os.path.join(folder, "main.py")
    if not os.path.isfile(main_py_path):
        raise FileNotFoundError(f"main.py not found in the specified folder: {folder}")

    spec = importlib.util.spec_from_file_location("main", main_py_path)
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)

    if hasattr(main_module, "run_mcp"):
        main_module.run_mcp(port=port)
    else:
        raise AttributeError("The main.py file does not contain a 'run_mcp' function.")

if __name__ == "__main__":
    main()
