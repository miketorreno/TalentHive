"""
    * Use a pipeline as a high-level helper
"""

from transformers import pipeline


class CoverLetterGenerator:
    def __init__(self, model_name):
        self.generator = pipeline("text-generation", model=model_name)

    async def generate_cover_letter(self, job_title, skills, company):
        # prompt = f"Write a professional cover letter for the position of {job_title} for someone who has the following experience {skills} at {company} company."
        prompt = f"Write a professional cover letter for a {job_title} position at {company}. Highlight the following skills and experiences {skills}."
        response = self.generator(prompt, max_length=300, num_return_sequences=1)
        return response[0]["generated_text"]


# * Load model directly
# from transformers import AutoTokenizer, AutoModelForCausalLM

# class CoverLetterGenerator:
#     def __init__(self, model_name):
#         self.tokenizer = AutoTokenizer.from_pretrained(model_name)
#         self.model = AutoModelForCausalLM.from_pretrained(model_name)

#     async def generate_cover_letter(self, job_title, skills, company):
#         # prompt = f"Write a professional cover letter for the position of {job_title} for someone with the following experience: {skills}"
#         prompt = f"Write a professional cover letter for a {job_title} position at {company}. Highlight the following skills and experiences: {skills}."
#         inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
#         outputs = self.model.generate(inputs.input_ids, max_length=300, num_return_sequences=1)
#         return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
