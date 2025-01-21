import os
import re
import sys
import logging
import argparse
import tempfile
import subprocess

from dotenv import load_dotenv
import google.generativeai as genai

# Suppress gRPC and absl logging messages
logging.getLogger("grpc").setLevel(logging.ERROR)
logging.getLogger("absl").setLevel(logging.ERROR)


def read_codebase(codebase_path):
    """
    Walks through the given codebase path and reads code files 
    of relevant extensions into a dictionary.
    Skips paths listed in the EXCLUDED_PATHS environment variable.
    """
    # Grab excluded paths from environment (comma-separated).
    excluded_paths_str = os.getenv("EXCLUDED_PATHS", "")
    excluded_paths = [p.strip() for p in excluded_paths_str.split(",") if p.strip()]

    code_files = {}
    for root, _, files in os.walk(codebase_path):
        # Skip if root contains any of the excluded paths
        if any(excluded_path in root for excluded_path in excluded_paths):
            continue

        for file in files:
            if file.endswith((".php", ".py", ".js", ".java", ".cpp", ".h")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        code_files[file] = f.read()
                except UnicodeDecodeError:
                    print(f"Warning: Skipping file {filepath} due to encoding issues.", file=sys.stderr)
    return code_files


def determine_language(filename):
    """
    Returns a code fence language identifier based on file extension.
    """
    if filename.endswith(".php"):
        return "php"
    elif filename.endswith(".py"):
        return "python"
    elif filename.endswith(".js"):
        return "javascript"
    elif filename.endswith(".cpp"):
        return "cpp"
    elif filename.endswith(".java"):
        return "java"
    elif filename.endswith(".h"):
        return "cpp"
    else:
        return ""


def format_code_for_api(code_files):
    """
    Formats the code files into GitHub-flavored code blocks
    for inclusion in the prompt context.
    """
    formatted_code = ""
    for filename, content in code_files.items():
        formatted_code += f"```{determine_language(filename)}\n{content}\n```\n\n"
    return formatted_code


def analyze_codebase(codebase_path, question):
    """
    Configures and calls the Gemini API with the given question and codebase.
    Returns a string with the LLM's response, or None if an error occurred.
    """
    # Gemini API key from system environment (more secure).
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found in environment.", file=sys.stderr)
        return None

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    code_files = read_codebase(codebase_path)
    context = format_code_for_api(code_files)
    prompt = f"{context}\n\n{question}"

    try:
        response = model.generate_content(prompt)

        if not response.candidates:
            print("Error: No candidates returned in the response.", file=sys.stderr)
            return None

        raw_content = response.candidates[0].content
        if raw_content is None:
            print("Error: No text content found in the response.", file=sys.stderr)
            return None

        # Ensure raw_content is a string or convert it to a string
        if isinstance(raw_content, str):
            raw_text = raw_content
        elif hasattr(raw_content, "parts") and hasattr(raw_content.parts, "text"):
            raw_text = raw_content.parts.text
        elif isinstance(raw_content, dict):
            # Attempt to extract 'parts' -> 'text'
            parts = raw_content.get("parts", {})
            if isinstance(parts, dict):
                raw_text = parts.get("text", "")
            else:
                # If 'parts' is not a dict, convert to string
                raw_text = str(parts)
        else:
            # Fallback: convert to string
            raw_text = str(raw_content)

        if not isinstance(raw_text, str):
            print("Error: Extracted content is not a string.", file=sys.stderr)
            return None

        # Define regex pattern to extract text within `parts { text: "..."}`
        pattern = r'parts\s*\{\s*text:\s*"([\s\S]*?)"\s*\}'
        match = re.search(pattern, raw_text, flags=re.DOTALL)
        if match:
            answer_text = match.group(1)
            # Unescape escaped characters
            answer_text = bytes(answer_text, "utf-8").decode("unicode_escape")
        else:
            # If the pattern doesn't match, assume entire raw_text is desired
            answer_text = raw_text
            # Optionally unescape if needed
            answer_text = bytes(answer_text, "utf-8").decode("unicode_escape")

        return answer_text.strip()

    except Exception as e:
        if "DeadlineExceeded" in str(e):
            print("Error: Gemini request timed out.", file=sys.stderr)
        else:
            print(f"An error occurred: {e}", file=sys.stderr)
        return None


def prompt_for_multiline_input():
    """
    Opens the default system editor (or uses 'vi' if EDITOR is unset)
    to let the user input multiline text. Returns the text typed by the user.
    """
    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tf:
        temp_name = tf.name

    editor = os.environ.get("EDITOR", "vi")
    subprocess.call([editor, temp_name])

    with open(temp_name, "r") as tf:
        text = tf.read()

    os.remove(temp_name)
    return text


def main():
    # Load .env variables (for CODEBASE_PATH, EXCLUDED_PATHS, etc.)
    # GEMINI_API_KEY should remain in system environment for security.
    load_dotenv()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Analyze a codebase with Gemini LLM.")
    parser.add_argument(
        "--question", "-q",
        help="The question to ask the LLM. If omitted, you can open an editor via --editor.",
        required=False
    )
    parser.add_argument(
        "--editor", "-e",
        action="store_true",
        help="Open an editor for multiline question input."
    )

    args = parser.parse_args()

    # Retrieve codebase path from the environment (default to current dir if not set)
    codebase_path = os.getenv("CODEBASE_PATH", ".")

    # Determine how to get the question
    if args.question and args.editor:
        print(
            "Error: Please provide either --question or --editor, but not both.",
            file=sys.stderr
        )
        sys.exit(1)
    elif args.question:
        question = args.question
    elif args.editor:
        question = prompt_for_multiline_input()
    else:
        print(
            "Error: No question provided. Use --question <text> or --editor to open a text editor.",
            file=sys.stderr
        )
        sys.exit(1)

    # Perform the analysis
    analysis_result = analyze_codebase(codebase_path, question)
    if analysis_result:
        print(analysis_result)
    else:
        print("No analysis result available.", file=sys.stderr)


if __name__ == "__main__":
    main()
