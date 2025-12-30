from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ExtractionConfig(BaseModel):
    input_pdfs_dir: str
    chunk_size: int = 1000
    chunk_overlap: int = 200


class ExperimentConfig(BaseModel):
    name: str
    mode: str = "single_step"
    model: str
    temperature: float = 0.5
    num_questions_per_chunk: int = 1
    capture_reasoning: bool = False
    max_questions_per_pdf: Optional[int] = None

    # Optional fields (depending on mode)
    prompt_file: Optional[str] = None
    question_prompt_file: Optional[str] = None
    distractor_prompt_file: Optional[str] = None


class GenerationConfig(BaseModel):
    experiments: List[ExperimentConfig]


class EvaluationConfig(BaseModel):
    prompt_file: str
    model: str
    temperature: float = 0.5


class ExportConfig(BaseModel):
    min_weighted_avg_score: float
    criteria_weights: Dict[str, float]


class AppConfig(BaseModel):
    output_dir: str
    extraction: ExtractionConfig
    generation: GenerationConfig
    evaluation: EvaluationConfig
    export: ExportConfig


class AnswerOption(BaseModel):
    text: str = Field(description="The text of the answer option.")
    is_correct: bool = Field(
        description="Whether this option is the correct answer.")


class SingleStepMCQ(BaseModel):
    question_text: str = Field(description="The text of the question.")
    answer_options: List[AnswerOption] = Field(
        description="List of answer options.")


class SingleStepMCQWithReasoning(BaseModel):
    reasoning: str = Field(
        description="Step-by-step reasoning process for creating the question.")
    question_text: str = Field(description="The text of the question.")
    answer_options: List[AnswerOption] = Field(
        description="List of answer options.")


class TwoStepQuestion(BaseModel):
    question_text: str = Field(description="The text of the question.")
    correct_answer: str = Field(description="The correct answer text.")


class TwoStepQuestionWithReasoning(BaseModel):
    reasoning: str = Field(
        description="Step-by-step reasoning process for creating the question.")
    question_text: str = Field(description="The text of the question.")
    correct_answer: str = Field(description="The correct answer text.")


class TwoStepDistractors(BaseModel):
    distractors: List[str] = Field(description="List of distractor answers.")


class TwoStepDistractorsWithReasoning(BaseModel):
    reasoning: str = Field(
        description="Step-by-step reasoning process for creating the distractors.")
    distractors: List[str] = Field(description="List of distractor answers.")


class EvaluationCriterion(BaseModel):
    score: int = Field(
        description="Score for the criterion (either 0, 1 or 2).")
    reasoning: str = Field(
        description="Reasoning for the score. Not needed if the score is perfect (2).")


class EvaluationResult(BaseModel):
    clarity: EvaluationCriterion
    correctness: EvaluationCriterion
    distractor_quality: EvaluationCriterion
    relevance: EvaluationCriterion
