import os
import sys
import argparse
import json
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import concurrent.futures
from fpdf import FPDF
from prompt import GRADING_PROMPT, MODERATOR_PROMPT

def setup_api_key():
    """
    Loads the Gemini API key from environment variables.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{pdf_path}' was not found.")
    except Exception as e:
        raise IOError(f"Error reading PDF file '{pdf_path}': {e}")

def extract_text_from_json(json_path):
    """
    Extracts text from a JSON file.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data.get('rubric', '')
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{json_path}' was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error: The file '{json_path}' is not a valid JSON file.")
    except Exception as e:
        raise IOError(f"Error reading JSON file '{json_path}': {e}")

def get_rubric_text(rubric_path):
    """
    Extracts text from a rubric file (PDF or JSON).
    """
    if rubric_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(rubric_path)
    elif rubric_path.lower().endswith('.json'):
        return extract_text_from_json(rubric_path)
    else:
        raise ValueError("Unsupported rubric file format. Please use a .pdf or .json file.")

def get_evaluation(prompt, temperature, rubric_text, paper_text):
    """
    Performs a single evaluation of the paper against the rubric.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    full_prompt = f"""Calibrate evaluations for community college freshmen: Be fair, constructive, and motivational. Typical papers should score 10-15/20, not failing unless severely deficient.

{prompt}

Rubric:
{rubric_text}

Student Paper:
{paper_text}
"""
    response = model.generate_content(full_prompt, generation_config=genai.types.GenerationConfig(temperature=temperature))
    return response.text

def moderate_evaluations(evaluation_a, evaluation_b, rubric_text, paper_text):
    """
    Moderates between two evaluations to produce a final evaluation.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Calibrate evaluations for community college freshmen: Be fair, constructive, and motivational. Typical papers should score 10-15/20, not failing unless severely deficient.

{MODERATOR_PROMPT}

Rubric:
{rubric_text}

Student Paper:
{paper_text}

Evaluation from Grader A:
{evaluation_a}

Evaluation from Grader B:
{evaluation_b}
"""
    response = model.generate_content(prompt)
    return response.text

def evaluate_paper(rubric_text, paper_text):
    """
    Evaluates the student paper using a multi-agent system.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_a = executor.submit(get_evaluation, GRADING_PROMPT, 0.4, rubric_text, paper_text)
            future_b = executor.submit(get_evaluation, GRADING_PROMPT, 0.8, rubric_text, paper_text)
            evaluation_a = future_a.result()
            evaluation_b = future_b.result()

        final_evaluation = moderate_evaluations(evaluation_a, evaluation_b, rubric_text, paper_text)
        return evaluation_a, evaluation_b, final_evaluation

    except Exception as e:
        raise RuntimeError(f"Error during Gemini API call: {e}")

def save_evaluation_to_pdf(evaluation_text, output_path):
    """
    Saves the evaluation text to a PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, evaluation_text.encode('latin-1', 'replace').decode('latin-1'))
    pdf.output(output_path)

def evaluate_batch(rubric_text, input_folder, output_folder):
    """
    Evaluates a batch of papers in a folder.
    """
    if not os.path.isdir(input_folder):
        raise FileNotFoundError(f"Input folder not found: {input_folder}")
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            paper_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            print(f"Evaluating {paper_path}...")

            try:
                paper_text = extract_text_from_pdf(paper_path)
                evaluation_a, evaluation_b, final_evaluation = evaluate_paper(rubric_text, paper_text)

                evaluation_text = f"--- Agent 1 Evaluation ---\n{evaluation_a}\n--- End of Agent 1 Evaluation ---\n\n"
                evaluation_text += f"--- Agent 2 Evaluation ---\n{evaluation_b}\n--- End of Agent 2 Evaluation ---\n\n"
                evaluation_text += f"--- Final Moderator Evaluation ---\n{final_evaluation}\n--- End of Final Moderator Evaluation ---\n"

                save_evaluation_to_pdf(evaluation_text, output_path)
                print(f"Saved evaluation to {output_path}")

            except Exception as e:
                print(f"Error evaluating {paper_path}: {e}", file=sys.stderr)

def main():
    """
    Main function to run the evaluation script.
    """
    parser = argparse.ArgumentParser(description="Evaluate a student paper against a rubric.")
    parser.add_argument("--batch", action="store_true", help="Enable batch processing.")
    parser.add_argument("rubric_file", help="The path to the rubric file (PDF or JSON).")
    parser.add_argument("input_path", help="The path to the student paper PDF file or a folder of papers for batch processing.")
    parser.add_argument("output_path", nargs="?", help="The path to the output folder for batch processing.")
    args = parser.parse_args()

    try:
        setup_api_key()
        rubric_text = get_rubric_text(args.rubric_file)

        if args.batch:
            if not args.output_path:
                raise ValueError("Output path is required for batch processing.")
            evaluate_batch(rubric_text, args.input_path, args.output_path)
        else:
            paper_text = extract_text_from_pdf(args.input_path)
            evaluation_a, evaluation_b, final_evaluation = evaluate_paper(rubric_text, paper_text)

            print("\n--- Agent 1 Evaluation ---")
            print(evaluation_a)
            print("--- End of Agent 1 Evaluation ---\n")

            print("\n--- Agent 2 Evaluation ---")
            print(evaluation_b)
            print("--- End of Agent 2 Evaluation ---\n")

            print("\n--- Final Moderator Evaluation ---")
            print(final_evaluation)
            print("--- End of Final Moderator Evaluation ---\n")

    except (ValueError, FileNotFoundError, IOError, RuntimeError) as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()