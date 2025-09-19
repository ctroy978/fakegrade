import os
import sys
import argparse
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import concurrent.futures
from prompt import GRADING_PROMPT, ARBITRATOR_PROMPT

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

def get_initial_evaluation(rubric_text, paper_text):
    """
    Performs a single evaluation of the paper against the rubric.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""{GRADING_PROMPT}

Rubric:
{rubric_text}

Student Paper:
{paper_text}
"""
    response = model.generate_content(prompt)
    return response.text

def arbitrate_evaluations(evaluation_a, evaluation_b, rubric_text, paper_text):
    """
    Arbitrates between two evaluations to produce a final evaluation.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""{ARBITRATOR_PROMPT}

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
            future_a = executor.submit(get_initial_evaluation, rubric_text, paper_text)
            future_b = executor.submit(get_initial_evaluation, rubric_text, paper_text)
            evaluation_a = future_a.result()
            evaluation_b = future_b.result()

        final_evaluation = arbitrate_evaluations(evaluation_a, evaluation_b, rubric_text, paper_text)
        return evaluation_a, evaluation_b, final_evaluation

    except Exception as e:
        raise RuntimeError(f"Error during Gemini API call: {e}")

def main():
    """
    Main function to run the evaluation script.
    """
    parser = argparse.ArgumentParser(description="Evaluate a student paper against a rubric.")
    parser.add_argument("rubric_pdf", help="The path to the rubric PDF file.")
    parser.add_argument("student_paper_pdf", help="The path to the student paper PDF file.")
    args = parser.parse_args()

    try:
        setup_api_key()
        rubric_text = extract_text_from_pdf(args.rubric_pdf)
        paper_text = extract_text_from_pdf(args.student_paper_pdf)
        evaluation_a, evaluation_b, final_evaluation = evaluate_paper(rubric_text, paper_text)

        print("\n--- Grader A Evaluation ---")
        print(evaluation_a)
        print("--- End of Grader A Evaluation ---\\n")

        print("\n--- Grader B Evaluation ---")
        print(evaluation_b)
        print("--- End of Grader B Evaluation ---\\n")

        print("\n--- Final Evaluation ---")
        print(final_evaluation)
        print("--- End of Final Evaluation ---\\n")

    except (ValueError, FileNotFoundError, IOError, RuntimeError) as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()