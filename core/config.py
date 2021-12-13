import os
# For possible Question Answering Modells look at huggingface.com

######
# Directories
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
TMP_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "files/tmp")
INPUT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, 'files/tmp/input')
OUTPUT_DIRECTORY = os.path.join(CURRENT_DIRECTORY, 'files/tmp/output')

QUESTIONTEMPLATE_PATH = os.path.join(CURRENT_DIRECTORY, 'files/q_pool.json')
######
# Development settings
debug_mode = False


#######
# Table Question Answering

T_QA_TOKENIZER = "google/tapas-base-finetuned-wikisql-supervised"
T_QA_MODELL = "google/tapas-base-finetuned-wikisql-supervised"
T_QA_MODELL = os.path.join(CURRENT_DIRECTORY, "apis/_internal_/QA_Pipeline/models/table_model")
T_QA_TOKENIZER = os.path.join(CURRENT_DIRECTORY, "apis/_internal_/QA_Pipeline/models/table_model")
# T_QA_TOKENIZER = "google/tapas-large-finetuned-wikisql-supervised"
# T_QA_MODELL = "google/tapas-large-finetuned-wikisql-supervised"
#######
# Text Question Answering
QA_TOKENIZER = "ktrapeznikov/scibert_scivocab_uncased_squad_v2"
QA_MODEL = "ktrapeznikov/scibert_scivocab_uncased_squad_v2"
QA_MODEL = os.path.join(CURRENT_DIRECTORY, "apis/_internal_/QA_Pipeline/models/text_model")
QA_TOKENIZER = os.path.join(CURRENT_DIRECTORY, "apis/_internal_/QA_Pipeline/models/text_model")