"""
Distill FinBERT (teacher) into TinyFinBERT (student) using your cleaned dataset.
"""

from pathlib import Path
from typing import Any, Optional, Union

import torch
from torch.utils.data import DataLoader
from datasets import Dataset
from torch import nn
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

# Paths
DATA_FILE = Path(__file__).parent / "training_data/cleaned_dataset.csv"
MODEL_OUTPUT_DIR = Path(__file__).parent.parent / "model"

# Step 1: Load tokenizer and models
teacher_model_name = "ProsusAI/finbert"
student_model_name = "huawei-noah/TinyBERT_General_4L_312D"

teacher = AutoModelForSequenceClassification.from_pretrained(teacher_model_name) # type: ignore
student = AutoModelForSequenceClassification.from_pretrained(student_model_name, num_labels=3) # type: ignore
tokenizer = AutoTokenizer.from_pretrained(teacher_model_name) # type: ignore


# 1. Load CSV into HF Dataset
dataset = Dataset.from_csv(str(DATA_FILE)) # type: ignore

# 2. Drop any rows with missing text or label
dataset = dataset.filter(lambda x: x["text"] is not None and x["label"] is not None) # type: ignore

dataset = dataset.rename_column("label", "labels")

# 3. Split into train / validation / test (80 / 10 / 10)
train_testvalid = dataset.train_test_split(test_size=0.2, seed=42) # type: ignore
test_valid = train_testvalid["test"].train_test_split(test_size=0.5, seed=42) # type: ignore

train_dataset = train_testvalid["train"] # type: ignore
validation_dataset = test_valid["train"] # type: ignore
test_dataset = test_valid["test"] # type: ignore



def tokenize_fn(batch): # type: ignore
    return tokenizer(batch["text"], padding="max_length", truncation=True) # type: ignore


tokenized_train_dataset = train_dataset.map(tokenize_fn, batched=True) # type: ignore
tokenized_validation_dataset = validation_dataset.map(tokenize_fn, batched=True) # type: ignore
tokenized_test_dataset = test_dataset.map(tokenize_fn, batched=True) # type: ignore



#train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)

#batch = next(iter(train_loader))
#print(batch.keys())  # Shows the keys in the batch

# Step 4: Define distillation loss
def distillation_loss(
    teacher_logits, student_logits, temperature: float = 2.0, alpha: float = 0.5
):
    """
    Combine soft distillation loss and standard CE loss.
    """
    soft_labels = torch.nn.functional.softmax(teacher_logits / temperature, dim=1)
    soft_loss = torch.nn.functional.kl_div(
        torch.nn.functional.log_softmax(student_logits / temperature, dim=1),
        soft_labels,
        reduction="batchmean",
    ) * (temperature**2)
    return soft_loss * alpha


# Step 5: Training loop using Hugging Face Trainer
training_args = TrainingArguments(
    output_dir=str(MODEL_OUTPUT_DIR),
    num_train_epochs=3,
    per_device_train_batch_size=16,
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=50,
    learning_rate=5e-5,
    eval_strategy="no",
    remove_unused_columns=False,
)


# Custom Trainer to include distillation
class DistillationTrainer(Trainer):
    def compute_loss(
        self,
        model: nn.Module,
        inputs: dict[str, Union[torch.Tensor, Any]],
        return_outputs: bool = False,
        num_items_in_batch: Optional[torch.Tensor] = None,
    ):
        #labels = inputs.pop("labels")
        outputs_student = model(**inputs)
        with torch.no_grad():
            outputs_teacher = teacher(**inputs)
        student_logits = outputs_student.logits
        teacher_logits = outputs_teacher.logits

        loss = distillation_loss(teacher_logits, student_logits)
        return (loss, outputs_student) if return_outputs else loss


trainer = DistillationTrainer(
    model=student,  # type: ignore
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_validation_dataset,
)

trainer.train()

# Step 6: Save distilled model
trainer.save_model(str(MODEL_OUTPUT_DIR))
tokenizer.save_pretrained(str(MODEL_OUTPUT_DIR))  # type: ignore
