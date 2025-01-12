from transformers import AutoModelForCausalLM, AutoTokenizer

class CoverLetterGenerator:
    def __init__(self, model_name: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def generate_text(self, prompt: str, max_length: int = 300) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7,
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
