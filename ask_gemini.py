import os
import argparse
import google.generativeai as genai
import sys
import dotenv
from pathlib import Path

dotenv.load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CODEBASE_PATH = os.environ.get("CODEBASE_PATH")
EXCLUDED_PATHS = os.environ.get("EXCLUDED_PATHS", "").split(",")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-8b")

if GEMINI_API_KEY is None:
    raise ValueError("GEMINI_API_KEY environment variable not set")
if CODEBASE_PATH is None:
    raise ValueError("CODEBASE_PATH environment variable not set")
codebase_path_obj = Path(CODEBASE_PATH).resolve()
if not codebase_path_obj.is_dir():
    raise ValueError(f"CODEBASE_PATH '{CODEBASE_PATH}' is not a valid directory.")

genai.configure(api_key=GEMINI_API_KEY)

def read_codebase(codebase_path, excluded_paths):
    code_files = []
    excluded_paths = [path.strip() for path in excluded_paths if path.strip()]
    excluded_dirs = [codebase_path_obj / Path(excluded_path) for excluded_path in excluded_paths]

    for root, _, filenames in os.walk(codebase_path):
        root_path = Path(root).resolve()

        if any(excluded_dir in root_path.parents or excluded_dir == root_path for excluded_dir in excluded_dirs):
            continue

        for filename in filenames:
            file_path = root_path / filename
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    content = f.read()
                    code_files.append(content)
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}", file=sys.stderr)

    return code_files

def format_code_for_api(code_files):
    return "\n".join(code_files)

def query_gemini(codebase_path, question, excluded_paths):
    code_files = read_codebase(codebase_path, excluded_paths)
    if not code_files:
        print("Error: No code files found to read.", file=sys.stderr)
        return None

    context = format_code_for_api(code_files)
    prompt = f"{context}\n\n{question}"

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"Connected to Gemini model '{GEMINI_MODEL}'.")
    except AttributeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error initializing GenerativeModel: {e}", file=sys.stderr)
        return None

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"Error during content generation: {e}", file=sys.stderr)
        return None

    if not response.candidates:
        print("Error: No candidates returned in the response.", file=sys.stderr)
        return None

    raw_content = response.text
    if raw_content is None:
        print("Error: No text content found in the response.", file=sys.stderr)
        return None

    return raw_content

def get_query_from_editor():
    temp_file = "temp_query.txt"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("")

        if sys.platform.startswith('darwin'):
            os.system(f"open {temp_file}")
        elif sys.platform.startswith('win'):
            os.system(f"start {temp_file}")
        else:
            os.system(f"xdg-open {temp_file}")

        input("Press Enter when you have finished editing the query...")

        with open(temp_file, "r", encoding="utf-8") as f:
            query = f.read().strip()
    except Exception as e:
        print(f"Error during query input: {e}", file=sys.stderr)
        query = ""
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    return query

def main():
    parser = argparse.ArgumentParser(description="Query Gemini with a codebase.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-q", "--question", help="The query to ask Gemini.")
    group.add_argument("-e", "--editor", action="store_true", help="Open an editor to write the query.")
    args = parser.parse_args()

    if args.question:
        question = args.question
    elif args.editor:
        question = get_query_from_editor()
        if not question:
            print("Error: No query provided.", file=sys.stderr)
            sys.exit(1)

    response = query_gemini(codebase_path_obj, question, EXCLUDED_PATHS)
    if response:
        print("\nGemini Response:\n")
        print(response)
    else:
        print("Failed to generate a response from Gemini.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
