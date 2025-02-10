import logging
import torch
from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)

logging.basicConfig(level=logging.INFO)

# google/flan-t5-large, google/flan-t5-base, google/flan-t5-small, "gpt2"
MODEL_NAME = "google/flan-t5-small"

tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)


def truncate_text(text: str, max_tokens: int = 300) -> str:
    tokens = tokenizer.encode(text, max_length=max_tokens, truncation=True)
    return tokenizer.decode(tokens, skip_special_tokens=True)


# model.eval()

# input_text = "translate English to German: How old are you?"
# input_ids = tokenizer(input_text, return_tensors="pt").input_ids

# outputs = model.generate(input_ids)
# print(tokenizer.decode(outputs[0]))

# Load tokenizer and model
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Optional: Quantize model to reduce memory usage (if using CPU)
# model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)

# Set model to evaluation mode


def test():
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

        logging.info(f"{MODEL_NAME} model and tokenizer loaded successfully!")

        test_letter = cover_letter_generator(
            job_title="Software Engineer",
            company_name="Tech Corp",
            job_description="Looking for Python developers with NLP experience.",
            applicant_skills="Python, PyTorch, NLP",
            applicant_experience="3 years at AI startups.",
        )

        print(f"\n test letter: \n {test_letter} \n")
    except Exception as e:
        logging.error("Failed to load model: %s", e)
        raise


def cover_letter_generator(
    job_title: str,
    company_name: str,
    job_description: str,
    applicant_skills: str,
    applicant_experience: str,
) -> str:
    # Structured prompt
    prompt = f"""
    Task: Generate a formal cover letter for a job application.
    Job Title: {job_title}
    Company: {company_name}
    Job Description: {truncate_text(job_description)}
    Applicant Skills: {applicant_skills}
    Applicant Experience: {truncate_text(applicant_experience)}
    Instructions:
    1. Highlight 2-3 skills from "Applicant Skills" that match the "Job Description".
    2. Mention relevant experience from "Applicant Experience".
    3. Keep it under 400 words.
    Output:
    """

    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(
        inputs.input_ids,
        max_new_tokens=500,
        temperature=0.9,  # Increased for creativity
        do_sample=True,  # Disable beam search for more diversity
        top_k=50,  # Broaden token sampling
        top_p=0.95,  # Use nucleus sampling
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def cover_letter_generator_1(
    job_title: str,
    company_name: str,
    job_description: str,
    applicant_skills: str,
    applicant_experience: str,
) -> str:
    """
    Generate a cover letter based on the job title, company name, job description, and applicant's skills and experience.

    Args:
    job_title (str): The title of the job being applied for.
    company_name (str): The name of the company.
    job_description (str): The description of the job.
    applicant_skills (str): The skills possessed by the applicant.
    applicant_experience (str): The experience of the applicant.

    Returns:
    str: The generated cover letter.
    """

    # Create a detailed prompt
    prompt0 = f"""
        Write a formal cover letter for the job title {job_title} at {company_name}. Job Description: {job_description} Applicant Skills: {applicant_skills} Applicant Experience: {applicant_experience}.
        """

    prompt1 = f"""
        Write a formal cover letter for the job title {job_title} at {company_name}.
        Job Description: {job_description}
        Applicant Skills: {applicant_skills}
        Applicant Experience: {applicant_experience}
        Instructions:
        - Address the hiring manager.
        - Highlight relevant skills and experience.
        - Keep it under 450 words.
        - Use a professional tone.
        """

    prompt2 = f"""
        You are a professional hiring advisor. Write a cover letter for the role of {job_title} at {company_name}.
        Job Requirements: {job_description}
        Applicant Skills: {applicant_skills}
        Applicant Experience: {applicant_experience}
        ---
        Structure:
        1. Greeting and introduction.
        2. Highlight 2-3 relevant skills/experiences.
        3. Explain why you’re a good fit for the company.
        4. Keep it under 450 words.
        5. Closing statement.
        """

    # Count the number of tokens in the prompt
    # num_tokens = len(tokenizer(prompt1, return_tensors="pt").input_ids[0])
    # print(f"\nNumber of tokens in the prompt: {num_tokens}\n")

    # Tokenize and generate
    try:
        input_ids = tokenizer(prompt1, return_tensors="pt").input_ids
        outputs = model.generate(
            input_ids,
        )
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except torch.cuda.OutOfMemoryError:
        return "Error: Out of memory. Please try reducing the input size or using a smaller model."
    except Exception as e:
        return f"An error occurred in cover_letter_generator: {str(e)}"
