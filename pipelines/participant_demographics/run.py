""" Extract participant demographics from HTML files. """
import os
from publang.extract import extract_from_text
from openai import OpenAI
from pathlib import Path
import json
import pandas as pd
import logging

from . import prompts
from .clean import clean_predictions

<<<<<<< HEAD
from pipelines.pipeline import IndependentPipeline

def extract(extraction_model, extraction_client, docs, output_dir, prompt_set='', **extract_kwargs):
=======
def extract(extraction_model, extraction_client, docs, **extract_kwargs):
>>>>>>> f3ce9c24f4aaea67df4a5fb3b7d6a53e892ac747
    extract_kwargs.pop('search_query', None)

    # Extract
    predictions = extract_from_text(
        docs['body'].to_list(),
        model=extraction_model, client=extraction_client,
        **extract_kwargs
    )

    # Add PMCID to predictions
    for i, pred in enumerate(predictions):
        if not pred:
            logging.warning(f"No prediction for document {docs['pmid'].iloc[i]}")
            continue
        pred['pmid'] = int(docs['pmid'].iloc[i])

    clean_preds = clean_predictions(predictions)

    return predictions, clean_preds


def _load_client(model_name):
    if 'gpt' in model_name:
        client = OpenAI(api_key=os.getenv('MYOPENAI_API_KEY'))

    else:
        raise ValueError(f"Model {model_name} not supported")

    return client

def _load_prompt_config(prompt_set):
    return getattr(prompts, prompt_set)

def _save_predictions(predictions, clean_preds, extraction_model, prompt_set, output_dir):
    short_model_name = extraction_model.split('/')[-1]
    outname = f"{prompt_set}_{short_model_name}"
    predictions_path = output_dir / f'{outname}.json'
    clean_predictions_path = output_dir / f'{outname}_clean.csv'

    json.dump(predictions, predictions_path.open('w'))

    clean_preds.to_csv(
        clean_predictions_path, index=False
    )

def __main__(extraction_model, docs_path, prompt_set, output_dir=None, **kwargs):
    """ Run the participant demographics extraction pipeline. 

    Args:
        extraction_model (str): The model to use for extraction.
        docs_path (str): The path to the csv file containing the documents.
        prompt_set (str): The prompt set to use for the extraction.
        output_dir (str): The directory to save the output files.
        **kwargs: Additional keyword arguments to pass to the extraction function.
    """

    docs = pd.read_csv(docs_path)

    extraction_client = _load_client(extraction_model)

    prompt_config = _load_prompt_config(prompt_set)
    if kwargs is not None:
        prompt_config.update(kwargs)

    output_dir = Path(output_dir)

    predictions, clean_preds = extract(
        extraction_model, extraction_client, docs,
        **prompt_config
    )

    if output_dir is not None:
         _save_predictions(predictions, clean_preds, extraction_model, prompt_set, output_dir)

    return predictions, clean_preds


def ParticipantDemographics(IndependentPipeline):
    """Participant demographics extraction pipeline."""

    _version = "1.0.0"
    _hash_args = ["extraction_model", "prompt_set", "kwargs", "_inputs", "_input_sources"]

    def __init__(
        self,
        extraction_model,
        prompt_set, inputs=("text",),
        input_sources=("pubget", "ace"),
        **kwargs
    ):
        super().__init__(inputs=inputs, input_sources=input_sources)
        self.extraction_model = extraction_model
        self.prompt_set = prompt_set
        self.kwargs = kwargs

    def function(self, study_inputs):
        """Run the participant demographics extraction pipeline."""
        extraction_client = _load_client(self.extraction_model)

        prompt_config = _load_prompt_config(self.prompt_set)
        if self.kwargs is not None:
            prompt_config.update(self.kwargs)


        predictions, clean_preds = extract(
            self.extraction_model,
            extraction_client,
            study_inputs["text"],
            prompt_set=self.prompt_set,
            **prompt_config
        )

        # Save predictions

        return {"predictions": predictions, "clean_predictions": clean_preds}
