from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ExtractionConfig(BaseModel):
    input_pdfs_dir: str


class ExperimentConfig(BaseModel):
    name: str
    mode: str = "single_step"
    model: str
    temperature: float = 0.5
    num_questions_per_chunk: int = 1
    pages_per_chunk: int = 0
    chunk_overlap: int = 0
    
    # Optional fields (depending on mode)
    prompt_file: Optional[str] = None
    question_prompt_file: Optional[str] = None
    distractor_prompt_file: Optional[str] = None


class GenerationConfig(BaseModel):
    experiments: List[ExperimentConfig]


class EvaluationConfig(BaseModel):
    prompt_file: str
    model: str
    temperature: float = 0.3
    criteria_weights: Dict[str, float]



class AppConfig(BaseModel):
    output_dir: str
    extraction: ExtractionConfig
    generation: GenerationConfig
    evaluation: EvaluationConfig
